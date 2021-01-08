import csv
import dataclasses
import os
from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Tuple

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.payments.config as payments_config
import massgov.pfml.util.csv as csv_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Payment,
    PaymentReferenceFile,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.payments.payments_util import Constants, get_now

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
    (processed_payments, writeback_records) = get_records_to_writeback(db_session=db_session)
    upload_writeback_csv_and_save_reference_files(
        db_session=db_session, pei_writeback_records=writeback_records, payments=processed_payments
    )


def get_records_to_writeback(
    db_session: db.Session,
) -> Tuple[List[Payment], List[PeiWritebackRecord]]:
    """
    Queries DB for payments whose state is "Mark As Extracted in FINEOS" or "Send Payment Details to FINEOS"
    @return (List[Payment], List[PeiWritebackRecord]): tuple of (payments successfully processed into PeiWritebackRecord, PeiWritebackRecords created)
    """
    processed_payments = []
    writeback_records = []

    # Process extracted payments into PeiWritebackRecords
    state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=State.MARK_AS_EXTRACTED_IN_FINEOS,
        db_session=db_session,
    )

    for log in state_logs:
        try:
            writeback_records.append(_extracted_payment_to_pei_writeback_record(log.payment))
            processed_payments.append(log.payment)
        except Exception as e:
            logger.exception(f"Caught exception in get_pending_payments_as_writeback_records: {e}")

    # Process disbursed payments into PeiWritebackRecords
    state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=State.SEND_PAYMENT_DETAILS_TO_FINEOS,
        db_session=db_session,
    )

    for log in state_logs:
        try:
            writeback_records.append(
                _disbursed_payment_to_pei_writeback_record(payment=log.payment)
            )
            processed_payments.append(log.payment)
        except Exception as e:
            logger.exception(
                f"Caught exception in get_disbursed_payments_as_writeback_records: {e}"
            )

    return (processed_payments, writeback_records)


def upload_writeback_csv_and_save_reference_files(
    db_session: db.Session, pei_writeback_records: List[PeiWritebackRecord], payments: List[Payment]
) -> None:
    """
    Upload PEI writeback CSV to FINEOS S3 bucket and PFML S3 bucket configured in payments_util
    Create and update reference files as uploads complete
    """
    current_datetime = get_now()
    filename_to_upload = f"{current_datetime.strftime('%Y-%m-%d-%H-%M-%S')}-pei_writeback.csv"

    s3_config = payments_config.get_s3_config()

    # Step 1: save writeback file to PFML S3 first in the /ready dir and set metadata
    pfml_pei_writeback_ready_filepath = os.path.join(
        s3_config.pfml_fineos_outbound_path, Constants.S3_OUTBOUND_READY_DIR, filename_to_upload
    )
    try:
        write_to_s3(pei_writeback_records, db_session, pfml_pei_writeback_ready_filepath)
        reference_file = save_reference_files(
            payments=payments, db_session=db_session, s3_dest=pfml_pei_writeback_ready_filepath
        )
    except Exception as e:
        raise e

    # Step 2: then try to save it to FINEOS S3 bucket
    fineos_pei_writeback_filepath = os.path.join(
        s3_config.fineos_data_import_path, filename_to_upload
    )
    try:
        file_util.copy_file(pfml_pei_writeback_ready_filepath, fineos_pei_writeback_filepath)
    except Exception as e:
        logger.exception(
            f"Error copying writeback from ${pfml_pei_writeback_ready_filepath} to ${fineos_pei_writeback_filepath}"
        )
        raise e

    # Step 3: move the writeback from /ready to /sent and update ReferenceFile
    try:
        pfml_pei_writeback_sent_filepath = os.path.join(
            s3_config.pfml_fineos_outbound_path, Constants.S3_OUTBOUND_SENT_DIR, filename_to_upload
        )
        file_util.rename_file(pfml_pei_writeback_ready_filepath, pfml_pei_writeback_sent_filepath)
        logger.info(
            f"Successfully renamed writeback CSV ${pfml_pei_writeback_ready_filepath} to ${pfml_pei_writeback_sent_filepath}"
        )
    except Exception as e:
        logger.exception(
            f"Error moving writeback from {pfml_pei_writeback_ready_filepath} to {pfml_pei_writeback_sent_filepath}"
        )
        raise e

    try:
        reference_file.file_location = pfml_pei_writeback_sent_filepath
        db_session.add(reference_file)
        db_session.commit()
    except Exception as e:
        logger.exception(
            f"Error updating ReferenceFile {reference_file.reference_file_id} from {pfml_pei_writeback_ready_filepath} to {pfml_pei_writeback_sent_filepath}"
        )
        raise e


def write_to_s3(
    pei_writeback_records: List[PeiWritebackRecord], db_session: db.Session, s3_dest: str
) -> None:
    """
    Write to S3 path specified by s3_dest
    Save ReferenceFile with s3_dest as file_location and PaymentReferenceFiles to db
    @return ReferenceFile: saved to DB with file location {s3_dest}
    """
    encoded_rows = []
    for pei_writeback_record in pei_writeback_records:
        encoded_rows.append(csv_util.encode_row(pei_writeback_record, PEI_WRITEBACK_CSV_ENCODERS))

    try:
        with file_util.write_file(path=s3_dest, mode="w") as csv_file:
            pei_writer = csv.DictWriter(
                csv_file,
                fieldnames=list(map(lambda f: f.name, dataclasses.fields(PeiWritebackRecord))),
                extrasaction="ignore",
            )
            pei_writer.writeheader()
            pei_writer.writerows(encoded_rows)
        logger.info(f"Successfully uploaded writeback CSV to ${s3_dest}")

    except Exception as e:
        logger.error(f"Error uploading writeback CSV to S3 bucket ${s3_dest}")
        raise e


def save_reference_files(
    payments: List[Payment], db_session: db.Session, s3_dest: str
) -> ReferenceFile:
    """
    Saves a ReferenceFile in db for PEI Writeback File and
    one PaymentReferenceFile for each payment in the Writeback
    @return ReferenceFile created
    """
    try:
        ref_file = ReferenceFile(
            file_location=s3_dest,
            reference_file_type_id=ReferenceFileType.PEI_WRITEBACK.reference_file_type_id,
        )
        db_session.add(ref_file)
    except Exception as e:
        logger.error(f"Error saving ReferenceFile for PEI writeback ${s3_dest}")
        raise e

    try:
        for payment in payments:
            payment_ref_file = PaymentReferenceFile(reference_file=ref_file, payment=payment)
            db_session.add(payment_ref_file)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error saving PaymentReferenceFiles for PEI Writeback ${s3_dest}")
        raise e

    return ref_file


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
        status="Active",
        extractionDate=payment.fineos_extraction_date,
        transactionStatus="Pending",
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
        status="Active",
        extractionDate=payment.fineos_extraction_date,
        stockNo=payment.disb_check_eft_number,
        transStatusDate=payment.disb_check_eft_issue_date,
        transactionStatus=payment.disb_method.payment_method_description,
    )
