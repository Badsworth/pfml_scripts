#
# Process ACH return files received from the bank.
#
# To run this locally, use `make pub-payments-process-pub-returns`.
#

import os.path
import re
from typing import Optional, Sequence, TextIO, cast

import massgov.pfml.db
import massgov.pfml.util.datetime
import massgov.pfml.util.files
import massgov.pfml.util.logging
from massgov.pfml.api.util import state_log_util
from massgov.pfml.db.models.employees import (
    Flow,
    Payment,
    PaymentReferenceFile,
    PrenoteState,
    PubEft,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.delegated_payments import delegated_config, delegated_payments_util
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.delegated_payments.util.ach import reader

logger = massgov.pfml.util.logging.get_logger(__name__)

EFT_PRENOTE_ID_PATTERN = re.compile(r"^E([1-9][0-9]*)$")
PAYMENT_ID_PATTERN = re.compile(r"^P([1-9][0-9]*)$")


class CopyReturnFilesToS3Step(Step):
    def run_step(self):
        # TODO: Copy all files from the source directory to S3 and create ReferenceFiles.
        # s3://massgov-pfml-prod-agency-transfer/pub/inbound/received/

        return None


class ProcessReturnFileStep(Step):
    """Process an ACH return file received from the bank."""

    received_path: str
    processed_path: str
    error_path: str
    reference_file: ReferenceFile
    more_files_to_process: bool

    def __init__(
        self,
        db_session: massgov.pfml.db.Session,
        log_entry_db_session: massgov.pfml.db.Session,
        s3_config: delegated_config.PaymentsS3Config,
    ) -> None:
        """Constructor."""
        self.compute_paths_from_config(s3_config)
        self.more_files_to_process = True

        super().__init__(db_session, log_entry_db_session)

    def run_step(self) -> None:
        """List incoming directory and process the oldest ACH return file.

        Returns True if there are more incoming files to process.
        """
        s3_objects = massgov.pfml.util.files.list_files(self.received_path)
        s3_objects.sort()

        logger.info("found files in %s: %s", self.received_path, s3_objects)

        if s3_objects:
            file = s3_objects.pop(0)
            path = os.path.join(self.received_path, file)
            self.set_metrics(input_path=path)
            self.process_return_file(path)

        self.more_files_to_process = s3_objects != []

    def have_more_files_to_process(self) -> bool:
        """Determine if there are more incoming files to process.

        If this returns True, the caller may call run() again to process the next file.
        """
        return self.more_files_to_process

    def compute_paths_from_config(self, s3_config: delegated_config.PaymentsS3Config) -> None:
        """Compute the subdirectory paths for received, processed, and error files."""
        self.received_path = os.path.join(
            s3_config.pfml_pub_inbound_path,
            delegated_payments_util.Constants.S3_INBOUND_RECEIVED_DIR,
        )
        self.processed_path = os.path.join(
            s3_config.pfml_pub_inbound_path,
            delegated_payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
        )
        self.error_path = os.path.join(
            s3_config.pfml_pub_inbound_path, delegated_payments_util.Constants.S3_INBOUND_ERROR_DIR,
        )

    def process_return_file(self, path: str) -> None:
        """Parse an ACH return file and process each record."""
        self.reference_file = ReferenceFile(
            file_location=path,
            reference_file_type_id=ReferenceFileType.PUB_ACH_RETURN.reference_file_type_id,
        )
        self.db_session.add(self.reference_file)

        stream = massgov.pfml.util.files.open_stream(path)
        try:
            self.process_stream(stream)
        except Exception:
            self.db_session.rollback()
            logger.exception("fatal error when processing ach return", extra={"path": path})
            delegated_payments_util.move_reference_file(
                self.db_session, self.reference_file, self.received_path, self.error_path
            )
            # TODO: add to general error report
            raise

        self.db_session.commit()
        delegated_payments_util.move_reference_file(
            self.db_session, self.reference_file, self.received_path, self.processed_path
        )

    def process_stream(self, stream: TextIO) -> None:
        ach_reader = reader.ACHReader(stream)

        for warning in ach_reader.get_warnings():
            # TODO: add to general error report (not connected to a prenote or payment)
            logger.info("warning %s", warning)
            self.increment("warning_count")
        self.process_ach_returns(ach_reader.get_ach_returns())
        self.process_change_notifications(ach_reader.get_change_notifications())

    def process_ach_returns(self, ach_returns: Sequence[reader.ACHReturn]) -> None:
        """Process each ACH return record."""
        for ach_return in ach_returns:
            self.process_single_ach_return(ach_return)
            self.increment("ach_return_count")

    def process_change_notifications(
        self, change_notifications: Sequence[reader.ACHChangeNotification]
    ) -> None:
        for change_notification in change_notifications:
            self.process_single_ach_return(change_notification)
            self.increment("change_notification_count")

    def process_single_ach_return(self, ach_return: reader.ACHReturn) -> None:
        """Determine if the ACH return record is prenote or payment and process it."""
        logger.info(
            "ach return %s",
            ach_return.return_reason_code,
            extra={
                "payments.ach.id_number": ach_return.id_number,
                "payments.ach.line_number": ach_return.line_number,
            },
        )

        if pub_individual_id := parse_eft_prenote_pub_individual_id(ach_return.id_number):
            self.process_eft_prenote_return(pub_individual_id, ach_return)
            self.increment("eft_prenote_count")
        elif pub_individual_id := parse_payment_pub_individual_id(ach_return.id_number):
            self.process_payment_return(pub_individual_id, ach_return)
            self.increment("payment_count")
        else:
            # TODO: add to general error report
            logger.warning(
                "id number not in known PFML formats",
                extra={"payments.ach.id_number": ach_return.id_number},
            )
            self.increment("unknown_id_format_count")

    def process_eft_prenote_return(
        self, pub_individual_id: int, ach_return: reader.ACHReturn
    ) -> None:
        """Get an EFT prenote from the database and mark it rejected."""
        pub_eft = (
            self.db_session.query(PubEft)
            .filter(PubEft.pub_individual_id == pub_individual_id)
            .one_or_none()
        )
        if pub_eft is None:
            # TODO: add to a report
            logger.warning(
                "id number not in pub_eft table",
                extra={"payments.ach.id_number": ach_return.id_number},
            )
            self.increment("eft_prenote_id_not_found_count")
            return
        self.reject_pub_eft_prenote(pub_eft, ach_return)

    def reject_pub_eft_prenote(self, pub_eft: PubEft, ach_return: reader.ACHReturn) -> None:
        """Set a pub_eft to rejected in the database and add it to a report."""
        if pub_eft.prenote_state_id == PrenoteState.PENDING_PRE_PUB.prenote_state_id:
            # TODO: add to a report
            logger.warning(
                "got prenote return but in state PENDING_PRE_PUB not PENDING_WITH_PUB",
                extra={"payments.ach.id_number": ach_return.id_number},
            )
            self.increment("eft_prenote_unexpected_state_count")
            return
        elif pub_eft.prenote_state_id == PrenoteState.APPROVED.prenote_state_id:
            # May be a late rejection, approved after n days, then return arrived late
            # TODO: add to a report
            logger.warning(
                "got prenote return but in state APPROVED not PENDING_WITH_PUB",
                extra={"payments.ach.id_number": ach_return.id_number},
            )
            self.increment("eft_prenote_already_approved_count")
            return
        # TODO: add to a report
        pub_eft.prenote_state_id = PrenoteState.REJECTED.prenote_state_id
        pub_eft.prenote_response_at = massgov.pfml.util.datetime.utcnow()
        pub_eft.prenote_response_reason_code = ach_return.return_reason_code
        if ach_return.is_change_notification():
            change_notification = cast(reader.ACHChangeNotification, ach_return)
            logger.info("change notification %s", change_notification.addenda_information)
        self.increment("eft_prenote_rejected_count")

    def process_payment_return(self, pub_individual_id: int, ach_return: reader.ACHReturn) -> None:
        """Get a payment from the database and process it as rejected or paid with change."""
        payment = (
            self.db_session.query(Payment)
            .filter(Payment.pub_individual_id == pub_individual_id)
            .one_or_none()
        )
        if payment is None:
            # TODO: add to a report
            logger.warning(
                "id number not in payment table",
                extra={"payments.ach.id_number": ach_return.id_number},
            )
            self.increment("payment_id_not_found_count")
            return

        payment_reference_file = PaymentReferenceFile(
            payment=payment, reference_file=self.reference_file,
        )
        self.db_session.add(payment_reference_file)

        if ach_return.is_change_notification():
            self.accept_payment_with_change(payment, cast(reader.ACHChangeNotification, ach_return))
        else:
            self.reject_payment(payment, ach_return)

    def reject_payment(self, payment: Payment, ach_return: reader.ACHReturn) -> None:
        """Set a payment to rejected in the state log and add it to a report."""
        payment_state_log = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, self.db_session
        )
        if payment_state_log is None:
            end_state_id = None
        else:
            end_state_id = payment_state_log.end_state_id

        if end_state_id == State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT.state_id:
            # Expected normal state for an ACH returned payment.
            state_log_util.create_finished_state_log(
                payment,
                State.ADD_TO_ERRORED_PEI_WRITEBACK,
                state_log_util.build_outcome(
                    "Add to error PEI writeback",
                    ach_return_reason_code=str(ach_return.return_reason_code),
                    ach_return_line_number=str(ach_return.line_number),
                ),
                self.db_session,
            )
            self.increment("payment_rejected_count")
        elif end_state_id in {
            State.ADD_TO_ERRORED_PEI_WRITEBACK.state_id,
            State.ERRORED_PEI_WRITEBACK_SENT.state_id,
        }:
            # Already processed an ACH return for this payment.
            logger.info(
                "payment already in a PEI_WRITEBACK state",
                extra={
                    "payments.ach.id_number": ach_return.id_number,
                    "payments.state": end_state_id,
                    "payments.payment_id": payment.payment_id,
                },
            )
            self.increment("payment_already_rejected_count")
        else:
            # The latest state for this payment is not compatible with receiving an ACH return.
            # TODO: add to a report
            logger.error(
                "unexpected state for payment",
                extra={
                    "payments.ach.id_number": ach_return.id_number,
                    "payments.state": end_state_id,
                    "payments.payment_id": payment.payment_id,
                },
            )
            self.increment("payment_unexpected_state_count")

    def accept_payment_with_change(
        self, payment: Payment, change_notification: reader.ACHChangeNotification
    ) -> None:
        """Set a payment to paid in the state log and add it to a report."""
        payment_state_log = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, self.db_session
        )
        if payment_state_log is None:
            end_state_id = None
        else:
            end_state_id = payment_state_log.end_state_id

        if end_state_id == State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT.state_id:
            # Expected normal state for an ACH change notification payment.
            state_log_util.create_finished_state_log(
                payment,
                State.DELEGATED_PAYMENT_COMPLETE,
                state_log_util.build_outcome(
                    "Payment complete with change notification",
                    ach_return_reason_code=str(change_notification.return_reason_code),
                    ach_return_line_number=str(change_notification.line_number),
                    ach_return_change_information=change_notification.addenda_information,
                ),
                self.db_session,
            )
            self.increment("payment_complete_with_change_count")
            # TODO: add to a report
        elif end_state_id == State.DELEGATED_PAYMENT_COMPLETE.state_id:
            # Payment already reached a successful state.
            logger.info(
                "payment already in a PAYMENT_COMPLETE state",
                extra={
                    "payments.ach.id_number": change_notification.id_number,
                    "payments.state": end_state_id,
                    "payments.payment_id": payment.payment_id,
                },
            )
            self.increment("payment_already_complete_count")
        else:
            # The latest state for this payment is not compatible with receiving an ACH change
            # notification.
            # TODO: add to a report
            logger.error(
                "unexpected state for payment",
                extra={
                    "payments.ach.id_number": change_notification.id_number,
                    "payments.state": end_state_id,
                    "payments.payment_id": payment.payment_id,
                },
            )
            self.increment("payment_unexpected_state_count")


def parse_eft_prenote_pub_individual_id(id_number: str) -> Optional[int]:
    if match := EFT_PRENOTE_ID_PATTERN.match(id_number):
        return int(match.group(1))
    return None


def parse_payment_pub_individual_id(id_number: str) -> Optional[int]:
    if match := PAYMENT_ID_PATTERN.match(id_number):
        return int(match.group(1))
    return None
