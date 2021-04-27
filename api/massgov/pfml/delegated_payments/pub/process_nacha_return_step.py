#
# Process ACH return files received from the bank.
#
# To run this locally, use `make pub-payments-process-pub-returns`.
#

import re
import uuid
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
    PubErrorType,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.delegated_payments import delegated_config, delegated_payments_util
from massgov.pfml.delegated_payments.pub import process_files_in_path_step
from massgov.pfml.delegated_payments.util.ach import reader

logger = massgov.pfml.util.logging.get_logger(__name__)

EFT_PRENOTE_ID_PATTERN = re.compile(r"^E([1-9][0-9]*)$")
PAYMENT_ID_PATTERN = re.compile(r"^P([1-9][0-9]*)$")


class ProcessNachaReturnFileStep(process_files_in_path_step.ProcessFilesInPathStep):
    """Process an ACH return file received from the bank."""

    def __init__(
        self, db_session: massgov.pfml.db.Session, log_entry_db_session: massgov.pfml.db.Session,
    ) -> None:
        """Constructor."""
        pub_ach_inbound_path = delegated_config.get_s3_config().pfml_pub_ach_archive_path
        super().__init__(db_session, log_entry_db_session, pub_ach_inbound_path)

    def process_file(self, path: str) -> None:
        """Parse an ACH return file and process each record."""
        self.reference_file = ReferenceFile(
            reference_file_id=uuid.uuid4(),
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
            logger.warning("ACH Warning: %s", warning.warning, extra=warning.get_details_for_log())
            self.increment("warning_count")

            self.add_pub_error(
                pub_error_type=PubErrorType.ACH_WARNING,
                message=warning.warning,
                line_number=warning.raw_record.line_number,
                raw_data=warning.raw_record.data,
                type_code=warning.raw_record.type_code.value,
            )

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
            logger.warning(
                "ACH Return: id number not in known PFML formats",
                extra=ach_return.get_details_for_log(),
            )
            self.increment("unknown_id_format_count")

            self.add_pub_error(
                pub_error_type=PubErrorType.ACH_RETURN,
                message="id number not in known PFML formats",
                line_number=ach_return.line_number,
                raw_data=ach_return.raw_record.data,
                type_code=ach_return.raw_record.type_code.value,
                details=ach_return.get_details_for_error(),
            )

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
            logger.warning(
                "Prenote: id number not in pub_eft table", extra=ach_return.get_details_for_log(),
            )
            self.increment("eft_prenote_id_not_found_count")

            self.add_pub_error(
                pub_error_type=PubErrorType.ACH_PRENOTE,
                message="id number not in pub_eft table",
                line_number=ach_return.line_number,
                raw_data=ach_return.raw_record.data,
                type_code=ach_return.raw_record.type_code.value,
                details=ach_return.get_details_for_error(),
            )
            return

        self.reject_pub_eft_prenote(pub_eft, ach_return)

    def reject_pub_eft_prenote(self, pub_eft: PubEft, ach_return: reader.ACHReturn) -> None:
        """Set a pub_eft to rejected in the database and add it to a report."""
        if pub_eft.prenote_state_id == PrenoteState.PENDING_PRE_PUB.prenote_state_id:
            message = f"got prenote return but in state {PrenoteState.PENDING_PRE_PUB.prenote_state_description} not {PrenoteState.PENDING_WITH_PUB.prenote_state_description}"
            logger.warning(
                f"Prenote: {message}", extra=ach_return.get_details_for_log(),
            )
            self.increment("eft_prenote_unexpected_state_count")

            self.add_pub_error(
                pub_error_type=PubErrorType.ACH_PRENOTE,
                message=message,
                line_number=ach_return.line_number,
                raw_data=ach_return.raw_record.data,
                type_code=ach_return.raw_record.type_code.value,
                details=ach_return.get_details_for_error(),
                pub_eft=pub_eft,
            )
            return
        elif pub_eft.prenote_state_id == PrenoteState.APPROVED.prenote_state_id:
            # May be a late rejection, approved after n days, then return arrived late
            message = f"got prenote return but in state {PrenoteState.APPROVED.prenote_state_description} not {PrenoteState.PENDING_WITH_PUB.prenote_state_description}"
            logger.warning(
                f"Prenote: {message}", extra=ach_return.get_details_for_log(),
            )
            self.increment("eft_prenote_already_approved_count")

            self.add_pub_error(
                pub_error_type=PubErrorType.ACH_PRENOTE,
                message=message,
                line_number=ach_return.line_number,
                raw_data=ach_return.raw_record.data,
                type_code=ach_return.raw_record.type_code.value,
                details=ach_return.get_details_for_error(),
                pub_eft=pub_eft,
            )
            return

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
            logger.warning(
                "ACH Return: id number not in payment table",
                extra=ach_return.get_details_for_log(),
            )
            self.increment("payment_id_not_found_count")

            self.add_pub_error(
                pub_error_type=PubErrorType.ACH_RETURN,
                message="id number not in payment table",
                line_number=ach_return.line_number,
                raw_data=ach_return.raw_record.data,
                type_code=ach_return.raw_record.type_code.value,
                details=ach_return.get_details_for_error(),
            )
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

        if end_state_id == State.DELEGATED_PAYMENT_FINEOS_WRITEBACK_EFT_SENT.state_id:
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
            self.add_pub_error(
                pub_error_type=PubErrorType.ACH_RETURN,
                message="Payment rejected by PUB",
                line_number=ach_return.line_number,
                raw_data=ach_return.raw_record.data,
                type_code=ach_return.raw_record.type_code.value,
                details=ach_return.get_details_for_error(),
                payment=payment,
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
            details = {
                **ach_return.get_details_for_log(),
                "payments.state": end_state_id,
            }

            logger.error(
                "ACH Return: unexpected state for payment", extra=details,
            )
            self.increment("payment_unexpected_state_count")

            self.add_pub_error(
                pub_error_type=PubErrorType.ACH_RETURN,
                message="unexpected state for payment",
                line_number=ach_return.line_number,
                raw_data=ach_return.raw_record.data,
                type_code=ach_return.raw_record.type_code.value,
                details=details,
                payment=payment,
            )

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

        if end_state_id == State.DELEGATED_PAYMENT_FINEOS_WRITEBACK_EFT_SENT.state_id:
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

            logger.warning(
                "ACH Notification: Payment complete with change notification",
                extra=change_notification.get_details_for_log(),
            )
            self.increment("payment_complete_with_change_count")

            self.add_pub_error(
                pub_error_type=PubErrorType.ACH_SUCCESS_WITH_NOTIFICATION,
                message="Payment complete with change notification",
                line_number=change_notification.line_number,
                raw_data=change_notification.raw_record.data,
                type_code=change_notification.raw_record.type_code.value,
                details=change_notification.get_details_for_error(),
                payment=payment,
            )
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
            details = {
                **change_notification.get_details_for_log(),
                "payments.state": end_state_id,
            }

            logger.error(
                "ACH Notification: unexpected state for payment", extra=details,
            )
            self.increment("payment_notification_unexpected_state_count")

            self.add_pub_error(
                pub_error_type=PubErrorType.ACH_NOTIFICATION,
                message="unexpected state for payment",
                line_number=change_notification.line_number,
                raw_data=change_notification.raw_record.data,
                type_code=change_notification.raw_record.type_code.value,
                details=details,
                payment=payment,
            )


def parse_eft_prenote_pub_individual_id(id_number: str) -> Optional[int]:
    if match := EFT_PRENOTE_ID_PATTERN.match(id_number):
        return int(match.group(1))
    return None


def parse_payment_pub_individual_id(id_number: str) -> Optional[int]:
    if match := PAYMENT_ID_PATTERN.match(id_number):
        return int(match.group(1))
    return None
