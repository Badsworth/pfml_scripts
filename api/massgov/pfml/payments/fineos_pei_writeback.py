import csv
import dataclasses
import os
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.util.csv as csv_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.base import uuid_gen
from massgov.pfml.db.models.employees import (
    Payment,
    PaymentReferenceFile,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.payments.payments_util import get_now, get_s3_config

logger = logging.get_logger(__package__)


@dataclass
class PeiWritebackRecord:
    """
    Based on FINEOS schema from https://lwd.atlassian.net/wiki/spaces/API/pages/585302387/FINEOS#Write-Back-file-schema
    """

    pei_C_value: str
    pei_I_value: str
    status: Optional[str]
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


def process_payments_for_writeback(db_session: db.Session) -> None:
    """
    Top-level function that calls all the other functions in this file in order
    """
    payments = get_payments_to_writeback(db_session)
    upload_writeback_csv(db_session, payments)


def get_payments_to_writeback(db_session: db.Session) -> List[Payment]:
    """
    Queries DB for payments whose state is "Mark As Extracted in FINEOS"
    @return List[Payment]: payments that need to be saved to a PEI writeback
    """
    state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=State.MARK_AS_EXTRACTED_IN_FINEOS,
        db_session=db_session,
    )
    return [log.payment for log in state_logs]


def upload_writeback_csv(db_session: db.Session, payments: List[Payment]) -> str:
    """
    Upload PEI writeback CSV to FINEOS S3 bucket and PFML S3 bucket configured in payments_util
    Create and update reference files as uploads complete
    @return str : complete S3 filepath of the uploaded CSV in PFML S3 bucket
    """
    current_datetime = get_now()
    filename_to_upload = f"{current_datetime.strftime('%Y-%m-%d-%H-%M-%S')}-pei_writeback.csv"

    s3_config = get_s3_config()

    # Step 1: save writeback file to PFML S3 first in the /ready dir and set metadata
    pfml_pei_writeback_ready_filepath = os.path.join(
        s3_config.pfml_fineos_outbound_path, "ready", filename_to_upload
    )
    try:
        reference_file = write_to_s3_and_save_reference_files(
            payments, db_session, pfml_pei_writeback_ready_filepath
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

    # Step 3: move the writeback from /ready to /sent and update metadata
    try:
        pfml_pei_writeback_sent_filepath = os.path.join(
            s3_config.pfml_fineos_outbound_path, "sent", filename_to_upload
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

    return pfml_pei_writeback_sent_filepath


def write_to_s3_and_save_reference_files(
    payments: List[Payment], db_session: db.Session, s3_dest: str
) -> ReferenceFile:
    """
    Write to S3 path specified by s3_dest
    Save ReferenceFile with s3_dest as file_location and PaymentReferenceFiles to db
    @return ReferenceFile: saved to DB with file location {s3_dest}
    """
    encoded_rows = []
    for payment in payments:
        encoded_rows.extend(
            [
                csv_util.encode_row(
                    _payment_to_pei_writeback_record(payment), PEI_WRITEBACK_CSV_ENCODERS
                )
            ]
        )

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

    try:
        ref_file = ReferenceFile(
            reference_file_id=uuid_gen(),
            file_location=s3_dest,
            reference_file_type_id=ReferenceFileType.PEI_WRITEBACK.reference_file_type_id,
        )
        db_session.add(ref_file)
    except Exception as e:
        logger.error(f"Error saving ReferenceFile for PEI writeback ${s3_dest}")
        raise e

    try:
        for payment in payments:
            payment_ref_file = PaymentReferenceFile(
                reference_file_id=ref_file.reference_file_id, payment_id=payment.payment_id
            )
            db_session.add(payment_ref_file)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error saving PaymentReferenceFiles for PEI Writeback ${s3_dest}")
        raise e

    return ref_file


def _payment_to_pei_writeback_record(payment: Payment) -> PeiWritebackRecord:
    if not payment.fineos_pei_c_value:
        error_msg = f"FINEOS PEI C value missing in Payment {payment.payment_id}"
        logger.error(error_msg)
        raise Exception(error_msg)
    if not payment.fineos_pei_i_value:
        error_msg = f"FINEOS PEI I value missing in payment {payment.payment_id}"
        logger.error(error_msg)
        raise Exception(error_msg)
    if not payment.fineos_extraction_date:
        error_msg = f"FINEOS Extraction Date value missing in payment {payment.payment_id}"
        logger.error(error_msg)
        raise Exception(error_msg)
    return PeiWritebackRecord(
        pei_C_value=payment.fineos_pei_c_value,
        pei_I_value=payment.fineos_pei_i_value,
        status="Active",
        statusReason="Pending",
        extractionDate=payment.fineos_extraction_date,
    )
