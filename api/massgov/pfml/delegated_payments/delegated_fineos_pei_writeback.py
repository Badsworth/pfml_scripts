import csv
import dataclasses
import os
import uuid
from dataclasses import dataclass
from datetime import date
from typing import Callable, Dict, List, Optional

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.util.csv as csv_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    LkState,
    Payment,
    PaymentReferenceFile,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.delegated_payments.delegated_payments_util import Constants, get_now

logger = logging.get_logger(__package__)


@dataclass
class PeiWritebackRecord:
    """
    Based on FINEOS schema from https://lwd.atlassian.net/wiki/spaces/API/pages/585302387/FINEOS#Write-Back-file-schema
    All of these fields are Optional because if they are not, the type checking in lint throws an error even though we check for existence when we convert a Payment to a PeiWritebackRecord
    """

    pei_C_value: Optional[str] = None
    pei_I_value: Optional[str] = None
    status: Optional[str] = None
    statusEffectiveDate: Optional[date] = None
    statusReason: Optional[str] = None
    stockNo: Optional[str] = None
    extractionDate: Optional[date] = None
    transactionNo: Optional[str] = None
    transactionStatus: Optional[str] = None
    transStatusDate: Optional[date] = None


@dataclass
class PeiWritebackItem:
    writeback_record: PeiWritebackRecord
    payment: Payment
    prior_state: LkState
    end_state: LkState
    encoded_row: Dict[str, str]


ACTIVE_WRITEBACK_RECORD_STATUS = "Active"
PENDING_WRITEBACK_RECORD_TRANSACTION_STATUS = "Pending"
WRITEBACK_FILE_SUFFIX = "-pei_writeback.csv"

PEI_WRITEBACK_CSV_ENCODERS: csv_util.Encoders = {
    date: lambda d: d.strftime("%m/%d/%Y"),
}

REQUIRED_FIELDS_FOR_EXTRACTED_PAYMENT = [
    "fineos_pei_c_value",
    "fineos_pei_i_value",
    "fineos_extraction_date",
]
REQUIRED_FIELDS_FOR_DISBURSED_PAYMENT = [
    "fineos_pei_c_value",
    "fineos_pei_i_value",
    "fineos_extraction_date",
    "disb_check_eft_number",
    "disb_check_eft_issue_date",
    "disb_method",
]


def process_payments_for_writeback(db_session: db.Session) -> None:
    """
    Top-level function that calls all the other functions in this file in order
    """
    logger.info("Processing payments for PEI writeback")

    pei_writeback_items: List[PeiWritebackItem] = get_records_to_writeback(db_session=db_session)
    if not pei_writeback_items:
        logger.info("No payment records for PEI writeback. Exiting early.")
        return

    upload_writeback_csv_and_save_reference_files(
        db_session=db_session, pei_writeback_items=pei_writeback_items
    )

    logger.info("Successfully processed payments for PEI writeback")


def get_records_to_writeback(db_session: db.Session) -> List[PeiWritebackItem]:
    zero_dollar_payment_writeback_items = _get_writeback_items_for_state(
        db_session=db_session,
        prior_state=State.DELEGATED_PAYMENT_ADD_ZERO_PAYMENT_TO_FINEOS_WRITEBACK,
        end_state=State.DELEGATED_PAYMENT_ZERO_PAYMENT_FINEOS_WRITEBACK_SENT,
        writeback_record_converter=_extracted_payment_to_pei_writeback_record,
    )
    logger.info(
        "Found %i extracted writeback items in state: %s",
        len(zero_dollar_payment_writeback_items),
        State.DELEGATED_PAYMENT_ADD_ZERO_PAYMENT_TO_FINEOS_WRITEBACK.state_description,
    )

    overpayment_writeback_items = _get_writeback_items_for_state(
        db_session=db_session,
        prior_state=State.DELEGATED_PAYMENT_ADD_OVERPAYMENT_TO_FINEOS_WRITEBACK,
        end_state=State.DELEGATED_PAYMENT_OVERPAYMENT_FINEOS_WRITEBACK_SENT,
        writeback_record_converter=_extracted_payment_to_pei_writeback_record,
    )
    logger.info(
        "Found %i extracted writeback items in state: %s",
        len(overpayment_writeback_items),
        State.DELEGATED_PAYMENT_ADD_OVERPAYMENT_TO_FINEOS_WRITEBACK.state_description,
    )

    accepted_payment_writeback_items = _get_writeback_items_for_state(
        db_session=db_session,
        prior_state=State.DELEGATED_PAYMENT_ADD_ACCEPTED_PAYMENT_TO_FINEOS_WRITEBACK,
        end_state=State.DELEGATED_PAYMENT_ACCEPTED_PAYMENT_FINEOS_WRITEBACK_SENT,
        writeback_record_converter=_extracted_payment_to_pei_writeback_record,
    )
    logger.info(
        "Found %i extracted writeback items in state: %s",
        len(accepted_payment_writeback_items),
        State.DELEGATED_PAYMENT_ADD_ACCEPTED_PAYMENT_TO_FINEOS_WRITEBACK.state_description,
    )

    cancelled_payment_writeback_items = _get_writeback_items_for_state(
        db_session=db_session,
        prior_state=State.DELEGATED_PAYMENT_ADD_CANCELLATION_PAYMENT_TO_FINEOS_WRITEBACK,
        end_state=State.DELEGATED_PAYMENT_CANCELLATION_PAYMENT_FINEOS_WRITEBACK_SENT,
        writeback_record_converter=_extracted_payment_to_pei_writeback_record,
    )
    logger.info(
        "Found %i extracted writeback items in state: %s",
        len(cancelled_payment_writeback_items),
        State.DELEGATED_PAYMENT_ADD_CANCELLATION_PAYMENT_TO_FINEOS_WRITEBACK.state_description,
    )

    # TODO: Add disbursed payments to this writeback using the same pattern as above but with a
    # writeback_record_converter of _disbursed_payment_to_pei_writeback_record.

    return (
        zero_dollar_payment_writeback_items
        + overpayment_writeback_items
        + accepted_payment_writeback_items
        + cancelled_payment_writeback_items
    )


def _get_writeback_items_for_state(
    db_session: db.Session,
    prior_state: LkState,
    end_state: LkState,
    writeback_record_converter: Callable,
) -> List[PeiWritebackItem]:
    pei_writeback_items = []

    state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=prior_state,
        db_session=db_session,
    )

    for log in state_logs:
        try:
            payment = log.payment
            writeback_record = writeback_record_converter(payment)

            pei_writeback_items.append(
                PeiWritebackItem(
                    payment=payment,
                    writeback_record=writeback_record,
                    prior_state=prior_state,
                    end_state=end_state,
                    encoded_row=csv_util.encode_row(writeback_record, PEI_WRITEBACK_CSV_ENCODERS),
                )
            )
        except Exception:
            logger.exception(
                "Error adding payment to list of writeback records",
                extra={"payment_id": log.payment.payment_id},
            )
            continue

    return pei_writeback_items


def upload_writeback_csv_and_save_reference_files(
    db_session: db.Session, pei_writeback_items: List[PeiWritebackItem],
) -> None:
    """
    Upload PEI writeback CSV to FINEOS S3 bucket and PFML S3 bucket configured in payments_util
    Create and update reference files as uploads complete
    """
    logger.info("Uploading writeback files to FINEOS S3")

    current_datetime = get_now()
    filename_to_upload = current_datetime.strftime("%Y-%m-%d-%H-%M-%S") + WRITEBACK_FILE_SUFFIX

    s3_config = payments_config.get_s3_config()

    # Step 1: save writeback file to PFML S3 first in the /ready dir and set metadata
    pfml_pei_writeback_ready_filepath = os.path.join(
        s3_config.pfml_fineos_outbound_path, Constants.S3_OUTBOUND_READY_DIR, filename_to_upload
    )
    try:
        reference_file = ReferenceFile(
            file_location=pfml_pei_writeback_ready_filepath,
            reference_file_type_id=ReferenceFileType.PEI_WRITEBACK.reference_file_type_id,
            reference_file_id=uuid.uuid4(),
        )
        db_session.add(reference_file)

        _create_db_records_for_payments(pei_writeback_items, db_session, reference_file)

        encoded_rows = [item.encoded_row for item in pei_writeback_items]
        _write_rows_to_s3_file(encoded_rows, reference_file.file_location)

        # Commit after creating the file in S3 so that we have records in the database before we
        # attempt to move the file to FINEOS' S3 bucket.
        db_session.commit()

        logger.info(
            "Successfully saved writeback files to PFML S3",
            extra={"s3_path": pfml_pei_writeback_ready_filepath},
        )
    except Exception as e:
        db_session.rollback()
        logger.exception(
            "Error saving writeback file to PFML S3",
            extra={"s3_path": pfml_pei_writeback_ready_filepath},
        )
        raise e

    # Step 2: then try to save it to FINEOS S3 bucket
    fineos_pei_writeback_filepath = os.path.join(
        s3_config.fineos_data_import_path, filename_to_upload
    )
    try:
        file_util.copy_file(pfml_pei_writeback_ready_filepath, fineos_pei_writeback_filepath)
        logger.info(
            "Successfully copied writeback files to FINEOS S3",
            extra={
                "s3_path": pfml_pei_writeback_ready_filepath,
                "fineos_s3_path": fineos_pei_writeback_filepath,
            },
        )
    except Exception as e:
        logger.exception(
            "Error copying writeback to FINEOS",
            extra={
                "pfml_pei_writeback_ready_filepath": pfml_pei_writeback_ready_filepath,
                "fineos_pei_writeback_filepath": fineos_pei_writeback_filepath,
            },
        )
        raise e

    # Step 3: move the writeback from /ready to /sent and update ReferenceFile
    try:
        pfml_pei_writeback_sent_filepath = os.path.join(
            s3_config.pfml_fineos_outbound_path, Constants.S3_OUTBOUND_SENT_DIR, filename_to_upload
        )
        file_util.rename_file(pfml_pei_writeback_ready_filepath, pfml_pei_writeback_sent_filepath)
        logger.info(
            "Successfully moved PEI writeback file",
            extra={
                "pfml_pei_writeback_ready_filepath": pfml_pei_writeback_ready_filepath,
                "pfml_pei_writeback_sent_filepath": pfml_pei_writeback_sent_filepath,
            },
        )
    except Exception as e:
        logger.exception(
            "Error moving PEI writeback files",
            extra={
                "pfml_pei_writeback_ready_filepath": pfml_pei_writeback_ready_filepath,
                "pfml_pei_writeback_sent_filepath": pfml_pei_writeback_sent_filepath,
            },
        )
        raise e

    try:
        state_log_util.create_finished_state_log(
            associated_model=reference_file,
            end_state=State.PEI_WRITEBACK_SENT,
            outcome=state_log_util.build_outcome("Archived PEI writeback after sending to FINEOS"),
            db_session=db_session,
        )

        reference_file.file_location = pfml_pei_writeback_sent_filepath
        db_session.add(reference_file)
        db_session.commit()

        logger.info("Successfully updated reference file location and created state log.")
    except Exception as e:
        db_session.rollback()
        logger.exception(
            "Error updating ReferenceFile %s from %s to %s",
            reference_file.reference_file_id,
            pfml_pei_writeback_ready_filepath,
            pfml_pei_writeback_sent_filepath,
            extra={
                "reference_file_id": reference_file.reference_file_id,
                "pfml_pei_writeback_ready_filepath": pfml_pei_writeback_ready_filepath,
                "pfml_pei_writeback_sent_filepath": pfml_pei_writeback_sent_filepath,
            },
        )
        raise e

    logger.info("Successfully uploaded writeback files to FINEOS S3")


def _create_db_records_for_payments(
    pei_writeback_items: List[PeiWritebackItem], db_session: db.Session, ref_file: ReferenceFile
) -> None:
    logger.info(
        "Creating payment reference files and state log for writeback items. Count: %i",
        len(pei_writeback_items),
    )

    for item in pei_writeback_items:
        try:
            payment_ref_file = PaymentReferenceFile(reference_file=ref_file, payment=item.payment)
            db_session.add(payment_ref_file)
            state_log_util.create_finished_state_log(
                associated_model=item.payment,
                end_state=item.end_state,
                outcome=state_log_util.build_outcome("Added Payment to PEI Writeback"),
                db_session=db_session,
            )
        except Exception as e:
            db_session.rollback()
            logger.exception(
                "Error saving PaymentReferenceFiles for PEI Writeback",
                extra={"payment_id": item.payment.payment_id},
            )
            raise e

    logger.info(
        "Successfully created payment reference files and state log for writeback items. Count: %i",
        len(pei_writeback_items),
    )


def _write_rows_to_s3_file(rows: List[Dict[str, str]], s3_dest: str) -> None:
    try:
        with file_util.write_file(path=s3_dest, mode="w") as csv_file:
            pei_writer = csv.DictWriter(
                csv_file,
                fieldnames=list(map(lambda f: f.name, dataclasses.fields(PeiWritebackRecord))),
                extrasaction="ignore",
            )
            pei_writer.writeheader()
            pei_writer.writerows(rows)
        logger.info(
            "Successfully uploaded PEI writeback to S3: %s, rows: %i",
            s3_dest,
            len(rows),
            extra={"destination": s3_dest},
        )
    except Exception as e:
        logger.exception(
            "Error uploading PEI writeback to S3: %s, rows: %i",
            s3_dest,
            len(rows),
            extra={"destination": s3_dest},
        )
        raise e


def _extracted_payment_to_pei_writeback_record(payment: Payment) -> PeiWritebackRecord:
    missing_fields = []

    for field in REQUIRED_FIELDS_FOR_EXTRACTED_PAYMENT:
        field_value = getattr(payment, field)
        if not field_value:
            missing_fields.append(field_value)

    if missing_fields:
        error_msg = f"Payment {payment.payment_id} cannot be converted to PeiWritebackRecord for extracted payments because it is missing fields."
        logger.error(error_msg, extra={"missing_fields": missing_fields})
        raise Exception(error_msg)

    return PeiWritebackRecord(
        pei_C_value=payment.fineos_pei_c_value,
        pei_I_value=payment.fineos_pei_i_value,
        status=ACTIVE_WRITEBACK_RECORD_STATUS,
        extractionDate=payment.fineos_extraction_date,
        transactionStatus=PENDING_WRITEBACK_RECORD_TRANSACTION_STATUS,
        transStatusDate=get_now(),
    )


def _disbursed_payment_to_pei_writeback_record(payment: Payment) -> PeiWritebackRecord:
    missing_fields = []

    for field in REQUIRED_FIELDS_FOR_DISBURSED_PAYMENT:
        field_value = getattr(payment, field)
        if not field_value:
            missing_fields.append(field_value)

    if missing_fields:
        error_msg = f"Payment {payment.payment_id} cannot be converted to PeiWritebackRecord for disbursed payments because it is missing fields."
        logger.error(error_msg, extra={"missing_fields": missing_fields})
        raise Exception(error_msg)

    return PeiWritebackRecord(
        pei_C_value=payment.fineos_pei_c_value,
        pei_I_value=payment.fineos_pei_i_value,
        status=ACTIVE_WRITEBACK_RECORD_STATUS,
        extractionDate=payment.fineos_extraction_date,
        stockNo=payment.disb_check_eft_number,
        transStatusDate=payment.disb_check_eft_issue_date,
        transactionStatus=f"Distributed {payment.disb_method.payment_method_description}",
    )
