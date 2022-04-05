import csv
import dataclasses
import enum
import os
import uuid
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional, cast

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
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
from massgov.pfml.db.models.payments import (
    FineosWritebackDetails,
    LkFineosWritebackTransactionStatus,
)
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.util.datetime import get_now_us_eastern

logger = logging.get_logger(__package__)


@dataclass
class PeiWritebackRecord:
    """
    Based on FINEOS schema from https://lwd.atlassian.net/wiki/spaces/API/pages/585302387/FINEOS#Write-Back-file-schema
    All of these fields are Optional because if they are not, the type checking in lint throws an error even though we check for existence when we convert a Payment to a PeiWritebackRecord
    """

    pei_C_Value: Optional[str] = None
    pei_I_Value: Optional[str] = None
    status: Optional[str] = None
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


WRITEBACK_FILE_SUFFIX = "-pei_writeback.csv"

PEI_WRITEBACK_CSV_ENCODERS: csv_util.Encoders = {date: lambda d: d.strftime("%Y-%m-%d %H:%M:%S")}

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


class FineosPeiWritebackStep(Step):
    class Metrics(str, enum.Enum):
        FINEOS_WRITEBACK_PATH = "fineos_writeback_path"
        ARCHIVED_WRITEBACK_PATH = "archived_writeback_path"

        WRITEBACK_RECORD_COUNT = "writeback_record_count"

    def run_step(self) -> None:
        # TODO - pre-populate the other metrics
        self.process_payments_for_writeback()

    def process_payments_for_writeback(self) -> None:
        """
        Top-level function that calls all the other functions in this file in order
        """
        logger.info("Processing payments for PEI writeback")

        pei_writeback_items: List[PeiWritebackItem] = self.get_records_to_writeback()

        if not pei_writeback_items:
            logger.info("No payment records for PEI writeback. Exiting early.")
            return

        self.upload_writeback_csv_and_save_reference_files(pei_writeback_items=pei_writeback_items)

        logger.info("Successfully processed payments for PEI writeback")

    def _get_payment_writeback_transaction_status(
        self, payment: Payment
    ) -> Optional[LkFineosWritebackTransactionStatus]:
        writeback_details = (
            self.db_session.query(FineosWritebackDetails)
            .filter(FineosWritebackDetails.payment_id == payment.payment_id)
            .order_by(FineosWritebackDetails.created_at.desc())
            .first()
        )

        if writeback_details is None:
            return None

        writeback_details.writeback_sent_at = get_now_us_eastern()

        return writeback_details.transaction_status

    def get_records_to_writeback(self) -> List[PeiWritebackItem]:
        """
        Get all payments queued up to be written back.
        """

        pei_writeback_items = []

        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            associated_class=state_log_util.AssociatedClass.PAYMENT,
            end_state=State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
            db_session=self.db_session,
        )

        for state_log in state_logs:
            payment = state_log.payment
            extra = payments_util.get_traceable_payment_details(
                payment, State.DELEGATED_ADD_TO_FINEOS_WRITEBACK
            )
            logger.info("Processing payment for PEI writeback", extra=extra)

            validate_required_fields_present(payment)

            transaction_status: Optional[
                LkFineosWritebackTransactionStatus
            ] = self._get_payment_writeback_transaction_status(payment)

            if (
                transaction_status is None
                or transaction_status.transaction_status_description is None
            ):
                raise Exception(
                    f"Can not find writeback details for payment {payment.payment_id} with state {cast(LkState, state_log.end_state).state_description} and outcome {state_log.outcome}"
                )
            metric_name = transaction_status.transaction_status_description.lower().replace(
                " ", "_"
            )
            self.increment(f"{metric_name}_writeback_transaction_status_count")

            transaction_status_date = payments_util.get_transaction_status_date(payment)

            writeback_record = PeiWritebackRecord(
                pei_C_Value=payment.fineos_pei_c_value,
                pei_I_Value=payment.fineos_pei_i_value,
                status=transaction_status.writeback_record_status,
                extractionDate=payment.fineos_extraction_date,
                transactionStatus=transaction_status.transaction_status_description,
                transactionNo=str(payment.check.check_number)
                if payment.check and payment.check.check_number
                else None,
                transStatusDate=transaction_status_date,
            )

            pei_writeback_items.append(
                PeiWritebackItem(
                    payment=payment,
                    writeback_record=writeback_record,
                    prior_state=State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
                    end_state=State.DELEGATED_FINEOS_WRITEBACK_SENT,
                    encoded_row=csv_util.encode_row(writeback_record, PEI_WRITEBACK_CSV_ENCODERS),
                )
            )
            self.increment(self.Metrics.WRITEBACK_RECORD_COUNT)
            extra["transaction_status"] = transaction_status.transaction_status_description
            extra["transaction_status_date"] = transaction_status_date
            extra["status"] = (
                transaction_status.writeback_record_status
                if transaction_status.writeback_record_status
                else "PendingActive"
            )
            logger.info(
                "Sent writeback transaction status of [%s] for payment to FINEOS",
                transaction_status.transaction_status_description,
                extra=extra,
            )

        logger.info(
            "Found %i extracted writeback items in state: %s",
            len(pei_writeback_items),
            State.DELEGATED_ADD_TO_FINEOS_WRITEBACK.state_description,
        )
        return pei_writeback_items

    def upload_writeback_csv_and_save_reference_files(
        self, pei_writeback_items: List[PeiWritebackItem]
    ) -> None:
        """
        Upload PEI writeback CSV to FINEOS S3 bucket and PFML S3 bucket configured in payments_util
        Create and update reference files as uploads complete
        """
        logger.info("Uploading writeback files to FINEOS S3")

        current_datetime = get_now_us_eastern()
        filename_to_upload = current_datetime.strftime("%Y-%m-%d-%H-%M-%S") + WRITEBACK_FILE_SUFFIX

        s3_config = payments_config.get_s3_config()

        # Step 1: Create all the file path objects we are going to need
        pfml_pei_writeback_ready_filepath = payments_util.build_archive_path(
            s3_config.pfml_fineos_writeback_archive_path,
            payments_util.Constants.S3_OUTBOUND_READY_DIR,
            filename_to_upload,
            current_datetime,
        )
        pfml_pei_writeback_sent_filepath = payments_util.build_archive_path(
            s3_config.pfml_fineos_writeback_archive_path,
            payments_util.Constants.S3_OUTBOUND_SENT_DIR,
            filename_to_upload,
            current_datetime,
        )

        fineos_pei_writeback_filepath = os.path.join(
            s3_config.fineos_data_import_path, filename_to_upload
        )
        extra: Dict[str, Any] = {
            "s3_ready_path": pfml_pei_writeback_ready_filepath,
            "s3_sent_path": pfml_pei_writeback_sent_filepath,
            "fineos_s3_path": fineos_pei_writeback_filepath,
        }

        logger.info("Determined S3 paths for PEI writeback", extra=extra)

        # Step 2: Create the file
        encoded_rows = [item.encoded_row for item in pei_writeback_items]
        extra["row_count"] = len(encoded_rows)
        logger.info("Creating writeback file in ready directory", extra=extra)
        _write_rows_to_s3_file(encoded_rows, pfml_pei_writeback_ready_filepath)

        reference_file = ReferenceFile(
            file_location=pfml_pei_writeback_ready_filepath,
            reference_file_type_id=ReferenceFileType.PEI_WRITEBACK.reference_file_type_id,
            reference_file_id=uuid.uuid4(),
        )
        self.db_session.add(reference_file)
        logger.info("Successfully created writeback file in ready directory", extra=extra)

        # Step 3: Copy the file to FINEOS' S3 bucket
        logger.info("Copying writeback file to FINEOS S3", extra=extra)
        file_util.copy_file(pfml_pei_writeback_ready_filepath, fineos_pei_writeback_filepath)
        logger.info("Successfully copied writeback file to FINEOS S3", extra=extra)

        # Step 4: Move the file from "ready" to "sent"
        logger.info("Moving writeback file from ready to sent directory", extra=extra)
        file_util.rename_file(pfml_pei_writeback_ready_filepath, pfml_pei_writeback_sent_filepath)
        reference_file.file_location = pfml_pei_writeback_sent_filepath
        logger.info("Successfully moved writeback file from ready to sent directory", extra=extra)

        # Step 5: Update the state and attach the reference file to the payments
        logger.info("Updating state for payments in writeback file", extra=extra)
        self._create_db_records_for_payments(pei_writeback_items, reference_file)

        self.set_metrics(
            {
                self.Metrics.ARCHIVED_WRITEBACK_PATH: reference_file.file_location,
                self.Metrics.FINEOS_WRITEBACK_PATH: fineos_pei_writeback_filepath,
            }
        )
        logger.info("Successfully uploaded writeback files to FINEOS S3", extra=extra)

    def _create_db_records_for_payments(
        self, pei_writeback_items: List[PeiWritebackItem], ref_file: ReferenceFile
    ) -> None:
        logger.info(
            "Creating payment reference files and state log for writeback items. Count: %i",
            len(pei_writeback_items),
        )

        for item in pei_writeback_items:
            payment_ref_file = PaymentReferenceFile(reference_file=ref_file, payment=item.payment)
            self.db_session.add(payment_ref_file)
            state_log_util.create_finished_state_log(
                associated_model=item.payment,
                end_state=item.end_state,
                outcome=state_log_util.build_outcome("Added Payment to PEI Writeback"),
                db_session=self.db_session,
            )

        logger.info(
            "Successfully created payment reference files and state log for writeback items. Count: %i",
            len(pei_writeback_items),
        )


# Utility Methods
def validate_required_fields_present(payment: Payment) -> None:
    missing_fields = []

    for field in REQUIRED_FIELDS_FOR_EXTRACTED_PAYMENT:
        field_value = getattr(payment, field)
        if not field_value:
            missing_fields.append(field_value)

    if missing_fields:
        extra = payments_util.get_traceable_payment_details(payment)
        error_msg = f"Payment {payment.payment_id} cannot be converted to PeiWritebackRecord for extracted payments because it is missing fields."
        extra["missing_fields"] = ",".join(missing_fields)  # New Relic won't handle a list well
        logger.error(error_msg, extra=extra)
        raise Exception(error_msg)


def _write_rows_to_s3_file(rows: List[Dict[str, str]], s3_dest: str) -> None:
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
