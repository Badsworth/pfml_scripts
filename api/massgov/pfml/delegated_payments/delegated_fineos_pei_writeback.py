import csv
import dataclasses
import datetime
import enum
import os
import uuid
from dataclasses import dataclass
from datetime import date
from typing import Callable, Dict, List, Optional

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.csv as csv_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    LkState,
    Payment,
    PaymentMethod,
    PaymentReferenceFile,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.delegated_payments.delegated_payments_util import get_now
from massgov.pfml.delegated_payments.step import Step

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


ACTIVE_WRITEBACK_RECORD_STATUS = "Active"
PAID_WRITEBACK_RECORD_TRANSACTION_STATUS = "Paid"
POSTED_WRITEBACK_RECORD_TRANSACTION_STATUS = "Posted"
PROCESSED_WRITEBACK_RECORD_TRANSACTION_STATUS = "Processed"
ERROR_WRITEBACK_RECORD_TRANSACTION_STATUS = "Error"
WRITEBACK_FILE_SUFFIX = "-pei_writeback.csv"

PEI_WRITEBACK_CSV_ENCODERS: csv_util.Encoders = {
    date: lambda d: d.strftime("%Y-%m-%d %H:%M:%S"),
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


class FineosPeiWritebackStep(Step):
    class Metrics(str, enum.Enum):
        CANCELLED_PAYMENT_COUNT = "cancelled_payment_count"
        CHECK_PAYMENT_COUNT = "check_payment_count"
        EFT_PAYMENT_COUNT = "eft_payment_count"
        EMPLOYER_REIMBURSEMENT_PAYMENT_COUNT = "employer_reimbursement_payment_count"
        ERRORED_PAYMENT_WRITEBACK_ITEMS_COUNT = "errored_payment_writeback_items_count"
        OVERPAYMENT_COUNT = "overpayment_count"
        PAYMENT_WRITEBACK_TWO_ITEMS_COUNT = "payment_writeback_two_items_count"
        WRITEBACK_RECORD_COUNT = "writeback_record_count"
        ZERO_DOLLAR_PAYMENT_COUNT = "zero_dollar_payment_count"

    def run_step(self) -> None:
        # TODO - we need a way to have this distinguish between
        #        writeback #1 and #2 - for now only #1 can be run
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

    def get_records_to_writeback(self) -> List[PeiWritebackItem]:
        zero_dollar_payment_writeback_items = self._get_writeback_items_for_state(
            prior_state=State.DELEGATED_PAYMENT_ADD_ZERO_PAYMENT_TO_FINEOS_WRITEBACK,
            end_state=State.DELEGATED_PAYMENT_ZERO_PAYMENT_FINEOS_WRITEBACK_SENT,
            writeback_record_converter=self._extracted_payment_to_pei_writeback_record,
            transaction_status=PROCESSED_WRITEBACK_RECORD_TRANSACTION_STATUS,
        )
        zero_dollar_payment_count = len(zero_dollar_payment_writeback_items)
        logger.info(
            "Found %i extracted writeback items in state: %s",
            zero_dollar_payment_count,
            State.DELEGATED_PAYMENT_ADD_ZERO_PAYMENT_TO_FINEOS_WRITEBACK.state_description,
        )
        self.set_metrics({self.Metrics.ZERO_DOLLAR_PAYMENT_COUNT: zero_dollar_payment_count})

        overpayment_writeback_items = self._get_writeback_items_for_state(
            prior_state=State.DELEGATED_PAYMENT_ADD_OVERPAYMENT_TO_FINEOS_WRITEBACK,
            end_state=State.DELEGATED_PAYMENT_OVERPAYMENT_FINEOS_WRITEBACK_SENT,
            writeback_record_converter=self._extracted_payment_to_pei_writeback_record,
            transaction_status=PROCESSED_WRITEBACK_RECORD_TRANSACTION_STATUS,
        )
        overpayment_count = len(overpayment_writeback_items)
        logger.info(
            "Found %i extracted writeback items in state: %s",
            overpayment_count,
            State.DELEGATED_PAYMENT_ADD_OVERPAYMENT_TO_FINEOS_WRITEBACK.state_description,
        )
        self.set_metrics({self.Metrics.OVERPAYMENT_COUNT: overpayment_count})

        check_payment_writeback_items = self._get_writeback_items_for_state(
            prior_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT,
            end_state=State.DELEGATED_PAYMENT_FINEOS_WRITEBACK_CHECK_SENT,
            writeback_record_converter=self._extracted_payment_to_pei_writeback_record,
            transaction_status=PAID_WRITEBACK_RECORD_TRANSACTION_STATUS,
        )
        check_payment_count = len(check_payment_writeback_items)
        logger.info(
            "Found %i extracted writeback items in state: %s",
            check_payment_count,
            State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT.state_description,
        )
        self.set_metrics({self.Metrics.CHECK_PAYMENT_COUNT: check_payment_count})

        eft_payment_writeback_items = self._get_writeback_items_for_state(
            prior_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
            end_state=State.DELEGATED_PAYMENT_FINEOS_WRITEBACK_EFT_SENT,
            writeback_record_converter=self._extracted_payment_to_pei_writeback_record,
            transaction_status=PAID_WRITEBACK_RECORD_TRANSACTION_STATUS,
        )
        eft_payment_count = len(eft_payment_writeback_items)
        logger.info(
            "Found %i extracted writeback items in state: %s",
            eft_payment_count,
            State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT.state_description,
        )
        self.set_metrics({self.Metrics.EFT_PAYMENT_COUNT: eft_payment_count})

        cancelled_payment_writeback_items = self._get_writeback_items_for_state(
            prior_state=State.DELEGATED_PAYMENT_ADD_CANCELLATION_PAYMENT_TO_FINEOS_WRITEBACK,
            end_state=State.DELEGATED_PAYMENT_CANCELLATION_PAYMENT_FINEOS_WRITEBACK_SENT,
            writeback_record_converter=self._extracted_payment_to_pei_writeback_record,
            transaction_status=PROCESSED_WRITEBACK_RECORD_TRANSACTION_STATUS,
        )
        cancelled_payment_count = len(cancelled_payment_writeback_items)
        logger.info(
            "Found %i extracted writeback items in state: %s",
            cancelled_payment_count,
            State.DELEGATED_PAYMENT_ADD_CANCELLATION_PAYMENT_TO_FINEOS_WRITEBACK.state_description,
        )
        self.set_metrics({self.Metrics.CANCELLED_PAYMENT_COUNT: cancelled_payment_count})

        employer_reimbursement_payment_writeback_items = self._get_writeback_items_for_state(
            prior_state=State.DELEGATED_PAYMENT_ADD_EMPLOYER_REIMBURSEMENT_PAYMENT_TO_FINEOS_WRITEBACK,
            end_state=State.DELEGATED_PAYMENT_EMPLOYER_REIMBURSEMENT_PAYMENT_FINEOS_WRITEBACK_SENT,
            writeback_record_converter=self._extracted_payment_to_pei_writeback_record,
            transaction_status=PROCESSED_WRITEBACK_RECORD_TRANSACTION_STATUS,
        )
        employer_reimbursement_payment_count = len(employer_reimbursement_payment_writeback_items)
        logger.info(
            "Found %i extracted writeback items in state: %s",
            employer_reimbursement_payment_count,
            State.DELEGATED_PAYMENT_ADD_EMPLOYER_REIMBURSEMENT_PAYMENT_TO_FINEOS_WRITEBACK.state_description,
        )
        self.set_metrics(
            {
                self.Metrics.EMPLOYER_REIMBURSEMENT_PAYMENT_COUNT: employer_reimbursement_payment_count
            }
        )

        errored_payment_writeback_items = self._get_writeback_items_for_state(
            prior_state=State.ADD_TO_ERRORED_PEI_WRITEBACK,
            end_state=State.ERRORED_PEI_WRITEBACK_SENT,
            writeback_record_converter=self._extracted_payment_to_pei_writeback_record,
            transaction_status=ERROR_WRITEBACK_RECORD_TRANSACTION_STATUS,
        )

        errored_payment_writeback_items_count = len(errored_payment_writeback_items)
        logger.info(
            "Found %i extracted writeback items in state: %s",
            errored_payment_writeback_items_count,
            State.ADD_TO_ERRORED_PEI_WRITEBACK.state_description,
        )
        self.set_metrics(
            {
                self.Metrics.ERRORED_PAYMENT_WRITEBACK_ITEMS_COUNT: errored_payment_writeback_items_count
            }
        )
        payment_writeback_two_items = self._get_writeback_items_for_state(
            prior_state=State.DELEGATED_PAYMENT_FINEOS_WRITEBACK_2_ADD_CHECK,
            end_state=State.DELEGATED_PAYMENT_FINEOS_WRITEBACK_2_SENT_CHECK,
            writeback_record_converter=self._extracted_payment_to_pei_writeback_record,
            transaction_status=POSTED_WRITEBACK_RECORD_TRANSACTION_STATUS,
        )

        payment_writeback_two_items_count = len(payment_writeback_two_items)
        logger.info(
            "Found %i extracted writeback items in state: %s",
            payment_writeback_two_items_count,
            State.ADD_TO_ERRORED_PEI_WRITEBACK.state_description,
        )
        self.set_metrics(
            {self.Metrics.PAYMENT_WRITEBACK_TWO_ITEMS_COUNT: payment_writeback_two_items_count}
        )

        # TODO: Add disbursed payments to this writeback using the same pattern as above but with a
        # writeback_record_converter of _disbursed_payment_to_pei_writeback_record.

        return (
            zero_dollar_payment_writeback_items
            + overpayment_writeback_items
            + check_payment_writeback_items
            + eft_payment_writeback_items
            + cancelled_payment_writeback_items
            + employer_reimbursement_payment_writeback_items
            + errored_payment_writeback_items
            + payment_writeback_two_items
        )

    def _get_writeback_items_for_state(
        self,
        prior_state: LkState,
        end_state: LkState,
        writeback_record_converter: Callable,
        transaction_status: str,
    ) -> List[PeiWritebackItem]:
        pei_writeback_items = []

        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            associated_class=state_log_util.AssociatedClass.PAYMENT,
            end_state=prior_state,
            db_session=self.db_session,
        )

        for log in state_logs:
            try:
                payment = log.payment
                valid_pub_payment = transaction_status == PAID_WRITEBACK_RECORD_TRANSACTION_STATUS
                writeback_record = writeback_record_converter(
                    payment, transaction_status, valid_pub_payment, log
                )

                pei_writeback_items.append(
                    PeiWritebackItem(
                        payment=payment,
                        writeback_record=writeback_record,
                        prior_state=prior_state,
                        end_state=end_state,
                        encoded_row=csv_util.encode_row(
                            writeback_record, PEI_WRITEBACK_CSV_ENCODERS
                        ),
                    )
                )
                self.increment(self.Metrics.WRITEBACK_RECORD_COUNT)
            except Exception:
                logger.exception(
                    "Error adding payment to list of writeback records",
                    extra={"payment_id": log.payment.payment_id},
                )
                continue

        return pei_writeback_items

    def upload_writeback_csv_and_save_reference_files(
        self, pei_writeback_items: List[PeiWritebackItem],
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
        pfml_pei_writeback_ready_filepath = payments_util.build_archive_path(
            s3_config.pfml_fineos_writeback_archive_path,
            payments_util.Constants.S3_OUTBOUND_READY_DIR,
            filename_to_upload,
            current_datetime,
        )

        try:
            reference_file = ReferenceFile(
                file_location=pfml_pei_writeback_ready_filepath,
                reference_file_type_id=ReferenceFileType.PEI_WRITEBACK.reference_file_type_id,
                reference_file_id=uuid.uuid4(),
            )
            self.db_session.add(reference_file)

            self._create_db_records_for_payments(pei_writeback_items, reference_file)

            encoded_rows = [item.encoded_row for item in pei_writeback_items]
            self._write_rows_to_s3_file(encoded_rows, reference_file.file_location)

            # Commit after creating the file in S3 so that we have records in the database before we
            # attempt to move the file to FINEOS' S3 bucket.
            self.db_session.commit()

            logger.info(
                "Successfully saved writeback files to PFML S3",
                extra={"s3_path": pfml_pei_writeback_ready_filepath},
            )
        except Exception as e:
            self.db_session.rollback()
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
            pfml_pei_writeback_sent_filepath = payments_util.build_archive_path(
                s3_config.pfml_fineos_writeback_archive_path,
                payments_util.Constants.S3_OUTBOUND_SENT_DIR,
                filename_to_upload,
                current_datetime,
            )

            file_util.rename_file(
                pfml_pei_writeback_ready_filepath, pfml_pei_writeback_sent_filepath
            )
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
                end_state=State.PEI_WRITEBACK_SENT,  # TODO - we should create a new state and not reuse the old one
                outcome=state_log_util.build_outcome(
                    "Archived PEI writeback after sending to FINEOS"
                ),
                db_session=self.db_session,
            )

            reference_file.file_location = pfml_pei_writeback_sent_filepath
            self.db_session.add(reference_file)
            self.db_session.commit()

            logger.info("Successfully updated reference file location and created state log.")
        except Exception as e:
            self.db_session.rollback()
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
        self, pei_writeback_items: List[PeiWritebackItem], ref_file: ReferenceFile
    ) -> None:
        logger.info(
            "Creating payment reference files and state log for writeback items. Count: %i",
            len(pei_writeback_items),
        )

        for item in pei_writeback_items:
            try:
                payment_ref_file = PaymentReferenceFile(
                    reference_file=ref_file, payment=item.payment
                )
                self.db_session.add(payment_ref_file)
                state_log_util.create_finished_state_log(
                    associated_model=item.payment,
                    end_state=item.end_state,
                    outcome=state_log_util.build_outcome("Added Payment to PEI Writeback"),
                    db_session=self.db_session,
                )
            except Exception as e:
                self.db_session.rollback()
                logger.exception(
                    "Error saving PaymentReferenceFiles for PEI Writeback",
                    extra={"payment_id": item.payment.payment_id},
                )
                raise e

        logger.info(
            "Successfully created payment reference files and state log for writeback items. Count: %i",
            len(pei_writeback_items),
        )

    def _write_rows_to_s3_file(self, rows: List[Dict[str, str]], s3_dest: str) -> None:
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

    def _extracted_payment_to_pei_writeback_record(
        self,
        payment: Payment,
        transaction_status: str,
        valid_pub_payment: bool,
        state_log: StateLog,
    ) -> PeiWritebackRecord:
        missing_fields = []

        for field in REQUIRED_FIELDS_FOR_EXTRACTED_PAYMENT:
            field_value = getattr(payment, field)
            if not field_value:
                missing_fields.append(field_value)

        if missing_fields:
            error_msg = f"Payment {payment.payment_id} cannot be converted to PeiWritebackRecord for extracted payments because it is missing fields."
            logger.error(error_msg, extra={"missing_fields": missing_fields})
            raise Exception(error_msg)

        transaction_status_date = None

        if state_log.end_state_id == State.DELEGATED_PAYMENT_FINEOS_WRITEBACK_2_ADD_CHECK.state_id:
            transaction_status_date = payment.check.check_posted_date

        elif (
            state_log.end_state_id == State.ADD_TO_ERRORED_PEI_WRITEBACK.state_id
            and payment.check is not None
        ):
            if payment.check.payment_check_status.payment_check_status_description is not None:
                transaction_status = (
                    payment.check.payment_check_status.payment_check_status_description
                )

            current_datetime = get_now()
            transaction_status_date = current_datetime

        if payment.fineos_extraction_date is not None:
            if valid_pub_payment:
                if payment.disb_method_id == PaymentMethod.CHECK.payment_method_id:
                    transaction_status_date = payment.fineos_extraction_date + datetime.timedelta(
                        days=1
                    )
                else:
                    transaction_status_date = payment.fineos_extraction_date + datetime.timedelta(
                        days=2
                    )
            else:
                transaction_status_date = payment.fineos_extraction_date

        return PeiWritebackRecord(
            pei_C_Value=payment.fineos_pei_c_value,
            pei_I_Value=payment.fineos_pei_i_value,
            status=ACTIVE_WRITEBACK_RECORD_STATUS,
            extractionDate=payment.fineos_extraction_date,
            transactionStatus=transaction_status,
            transactionNo=str(payment.check.check_number)
            if payment.check and payment.check.check_number
            else None,
            transStatusDate=transaction_status_date,
        )

    def _disbursed_payment_to_pei_writeback_record(self, payment: Payment) -> PeiWritebackRecord:
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
            pei_C_Value=payment.fineos_pei_c_value,
            pei_I_Value=payment.fineos_pei_i_value,
            status=ACTIVE_WRITEBACK_RECORD_STATUS,
            extractionDate=payment.fineos_extraction_date,
            transactionNo=payment.disb_check_eft_number,
            transStatusDate=payment.disb_check_eft_issue_date,
            transactionStatus=f"Distributed {payment.disb_method.payment_method_description}",
        )
