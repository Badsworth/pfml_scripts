import enum
import uuid
from typing import Any, Dict, List, Optional, TextIO

import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.api.util import state_log_util
from massgov.pfml.db.models.employees import (
    LkState,
    Payment,
    PrenoteState,
    PubEft,
    PubErrorType,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.db.models.payments import (
    FineosWritebackTransactionStatus,
    LkFineosWritebackTransactionStatus,
)
from massgov.pfml.db.models.state import Flow
from massgov.pfml.delegated_payments import delegated_config, delegated_payments_util
from massgov.pfml.delegated_payments.pub.manual_pub_reject_file_parser import (
    ManualPubReject,
    ManualPubRejectFileParser,
)
from massgov.pfml.delegated_payments.pub.process_files_in_path_step import ProcessFilesInPathStep
from massgov.pfml.delegated_payments.pub.pub_util import (
    parse_eft_prenote_pub_individual_id,
    parse_payment_pub_individual_id,
)
from massgov.pfml.delegated_payments.util.fineos_writeback_util import (
    create_payment_finished_state_log_with_writeback,
)

logger = massgov.pfml.util.logging.get_logger(__name__)

EXPECTED_STATES = [
    State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
    State.DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION,
    State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
]

EXPECTED_STATE_IDS = set([state.state_id for state in EXPECTED_STATES])

EXPECTED_NOTE_STATUSES = [
    FineosWritebackTransactionStatus.INVALID_ROUTING_NUMBER,
    FineosWritebackTransactionStatus.PUB_PAYMENT_RETURNED,
]


class ProcessManualPubRejectionStep(ProcessFilesInPathStep):
    """
    Process a manual PUB rejection file that was created.
    This file is a CSV created to fail payments/prenotes that errored
    with PUB, but did not return in the files as expected. This
    can happen for certain error scenarios where the errors are
    instead emailed to DFML in a PDF for EFT records.

    See https://lwd.atlassian.net/wiki/spaces/API/pages/2241855513/Rejecting+PUB+Payments+Manually+ACH
    for more context on how this is used.
    """

    class Metrics(str, enum.Enum):
        INPUT_PATH = "input_path"

        WARNING_COUNT = "warning_count"

        RECORD_COUNT = "record_count"
        EFT_RECORD_COUNT = "eft_record_count"
        PAYMENT_RECORD_COUNT = "payment_record_count"

        UNKNOWN_RECORD_COUNT = "unknown_record_count"

        EFT_UNEXPECTED_PRENOTE_STATE_COUNT = "eft_unexpected_prenote_state_count"
        EFT_ID_NOT_FOUND_COUNT = "eft_id_not_found_count"

        REJECTED_EFT_CURRENTLY_APPROVED_COUNT = "rejected_prenote_currently_approved_count"
        REJECTED_EFT_ALREADY_REJECTED_COUNT = "rejected_eft_already_rejected_count"
        REJECTED_EFT_PENDING_WITH_PUB_COUNT = "rejected_eft_pending_with_pub_count"
        EFT_REJECTED_SUCCESSFULLY_COUNT = "eft_rejected_successfully_count"

        PAYMENT_NOT_FOUND_COUNT = "payment_not_found_count"
        UNEXPECTED_PAYMENT_STATE_COUNT = "unexpected_payment_state_count"

        PAYMENT_ALREADY_ERRORED_COUNT = "payment_already_errored_count"
        PAYMENT_SWITCHING_CHANGE_NOTIFICATION_TO_ERROR_COUNT = (
            "payment_switching_change_notification_to_error_count"
        )
        PAYMENT_REJECTED_SUCCESSFULLY_COUNT = "payment_rejected_successfully_count"
        MISSING_REJECT_NOTES = "missing_reject_notes"
        MISSING_REJECT_NOTES_MAPPING = "missing_reject_notes_mapping"

    def __init__(
        self,
        db_session: db.Session,
        log_entry_db_session: db.Session,
        should_add_to_report_queue: bool = False,
    ) -> None:
        """Constructor."""
        manual_pub_inbound_path = (
            delegated_config.get_s3_config().pfml_manual_pub_reject_archive_path
        )
        super().__init__(
            db_session, log_entry_db_session, manual_pub_inbound_path, should_add_to_report_queue
        )

    def process_file(self, path: str) -> None:
        self.reference_file = ReferenceFile(
            reference_file_id=uuid.uuid4(),
            file_location=path,
            reference_file_type_id=ReferenceFileType.MANUAL_PUB_REJECT_FILE.reference_file_type_id,
        )

        self.db_session.add(self.reference_file)

        self.process_stream(file_util.open_stream(path))

        delegated_payments_util.move_reference_file(
            self.db_session, self.reference_file, self.received_path, self.processed_path
        )

    def process_stream(self, stream: TextIO) -> None:
        manual_pub_reject_parser = ManualPubRejectFileParser(stream)

        for line_error in manual_pub_reject_parser.get_line_errors():
            logger.warning("line error: %s", line_error.warning, extra=self.log_extra)
            self.increment(self.Metrics.WARNING_COUNT)
            self.add_pub_error(
                pub_error_type=PubErrorType.MANUAL_PUB_REJECT_LINE_ERROR,
                message=line_error.warning,
                line_number=line_error.line_number,
                raw_data=line_error.raw_line,
            )

        self.process_manual_pub_reject_records(manual_pub_reject_parser.get_manual_pub_rejects())

    def process_manual_pub_reject_records(self, manual_pub_rejects: List[ManualPubReject]) -> None:
        """
        Iterate over the records, determine the type of record
        from the ID, and pass on to processing of that individual record
        """
        for manual_pub_reject in manual_pub_rejects:
            extra = self.get_extra_for_log(manual_pub_reject)
            logger.info("Processing manual PUB reject record", extra=extra)
            self.increment(self.Metrics.RECORD_COUNT)

            if pub_individual_id := parse_eft_prenote_pub_individual_id(
                manual_pub_reject.record_id
            ):
                self.increment(self.Metrics.EFT_RECORD_COUNT)
                self.process_single_rejected_eft(manual_pub_reject, pub_individual_id)

            elif pub_individual_id := parse_payment_pub_individual_id(manual_pub_reject.record_id):
                self.increment(self.Metrics.PAYMENT_RECORD_COUNT)
                self.process_single_rejected_payment(manual_pub_reject, pub_individual_id)

            else:
                msg = (
                    "Could not determine what type of record to reject for manual PUB reject record"
                )
                logger.error(msg, extra=extra)
                self.increment(self.Metrics.UNKNOWN_RECORD_COUNT)
                self.add_pub_error(
                    pub_error_type=PubErrorType.MANUAL_PUB_REJECT_ERROR,
                    message=msg,
                    line_number=manual_pub_reject.line_number,
                    raw_data=manual_pub_reject.raw_line,
                    details=extra,
                )

    def process_single_rejected_eft(
        self, manual_pub_reject: ManualPubReject, pub_individual_id: int
    ) -> None:
        """
        Process a reject for a prenote EFT record
        """
        if (pub_eft := self.get_pub_eft_for_id(manual_pub_reject, pub_individual_id)) is None:
            return

        extra = self.get_extra_for_log(manual_pub_reject, pub_eft=pub_eft)

        if pub_eft.prenote_state_id == PrenoteState.PENDING_PRE_PUB.prenote_state_id:
            message = "Unexpected existing prenote state - EFT has not been sent to PUB yet"
            logger.error(message, extra=extra)
            self.increment(self.Metrics.EFT_UNEXPECTED_PRENOTE_STATE_COUNT)

            self.add_pub_error(
                pub_error_type=PubErrorType.MANUAL_PUB_REJECT_ERROR,
                message=message,
                line_number=manual_pub_reject.line_number,
                raw_data=manual_pub_reject.raw_line,
                details=extra,
                pub_eft=pub_eft,
            )
            return

        elif pub_eft.prenote_state_id == PrenoteState.REJECTED.prenote_state_id:
            self.increment(self.Metrics.REJECTED_EFT_ALREADY_REJECTED_COUNT)
            logger.info("EFT has already been moved to an error state, skipping", extra=extra)
            return

        elif pub_eft.prenote_state_id == PrenoteState.PENDING_WITH_PUB.prenote_state_id:
            self.increment(self.Metrics.REJECTED_EFT_PENDING_WITH_PUB_COUNT)

        elif pub_eft.prenote_state_id == PrenoteState.APPROVED.prenote_state_id:
            self.increment(self.Metrics.REJECTED_EFT_CURRENTLY_APPROVED_COUNT)

        # Update the status
        pub_eft.prenote_state_id = PrenoteState.REJECTED.prenote_state_id
        pub_eft.prenote_response_reason_code = manual_pub_reject.notes or "Manual"

        # Add PUB error to note that we rejected it as intended
        self.add_pub_error(
            pub_error_type=PubErrorType.MANUAL_PUB_REJECT_EFT_PROCESSED,
            message=f'EFT manually rejected with notes "{manual_pub_reject.notes}"',
            line_number=manual_pub_reject.line_number,
            raw_data=manual_pub_reject.raw_line,
            details=extra,
            pub_eft=pub_eft,
        )

        self.increment(self.Metrics.EFT_REJECTED_SUCCESSFULLY_COUNT)
        logger.info("EFT record manually rejected", extra=extra)

    def get_pub_eft_for_id(
        self, manual_pub_reject: ManualPubReject, pub_individual_id: int
    ) -> Optional[PubEft]:
        """
        For the given PUB EFT ID, lookup the PUB EFT record in the DB by
        the individual ID that we send in the PUB outbound NACHA files.
        """
        extra = self.get_extra_for_log(manual_pub_reject)
        pub_eft = (
            self.db_session.query(PubEft)
            .filter(PubEft.pub_individual_id == pub_individual_id)
            .one_or_none()
        )

        if not pub_eft:
            msg = "PUB EFT individual ID not found in DB"
            logger.warning(msg, extra=extra)
            self.increment(self.Metrics.EFT_ID_NOT_FOUND_COUNT)

            self.add_pub_error(
                pub_error_type=PubErrorType.MANUAL_PUB_REJECT_ERROR,
                message=msg,
                line_number=manual_pub_reject.line_number,
                raw_data=manual_pub_reject.raw_line,
                details=extra,
            )
            return None

        return pub_eft

    def process_single_rejected_payment(
        self, manual_pub_reject: ManualPubReject, pub_individual_id: int
    ) -> None:
        """
        Process a reject for a single payment record
        """
        if (payment := self.get_payment_for_id(manual_pub_reject, pub_individual_id)) is None:
            return

        if (current_state := self.get_state_for_payment(manual_pub_reject, payment)) is None:
            return

        self.add_payment_reference_file(payment, self.reference_file)
        self.handle_payment_state(manual_pub_reject, payment, current_state)

    def get_payment_for_id(
        self, manual_pub_reject: ManualPubReject, pub_individual_id: int
    ) -> Optional[Payment]:
        """
        For the given payment ID, lookup the payment record in the DB by
        the individual ID that we send in the PUB outbound NACHA files.
        """
        extra = self.get_extra_for_log(manual_pub_reject)

        payment = (
            self.db_session.query(Payment)
            .filter(Payment.pub_individual_id == pub_individual_id)
            .one_or_none()
        )
        if payment is None:
            msg = "Payment individual ID not found in DB"
            logger.warning(msg, extra=extra)
            self.increment(self.Metrics.PAYMENT_NOT_FOUND_COUNT)

            self.add_pub_error(
                pub_error_type=PubErrorType.MANUAL_PUB_REJECT_ERROR,
                message=msg,
                line_number=manual_pub_reject.line_number,
                raw_data=manual_pub_reject.raw_line,
                details=extra,
            )
            return None

        return payment

    def get_state_for_payment(
        self, manual_pub_reject: ManualPubReject, payment: Payment
    ) -> Optional[LkState]:
        """
        Get the latest state for the payment record, verifying it's
        at least one of a few potentially expected states
        """
        latest_state = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, self.db_session
        )

        latest_end_state = None
        if latest_state:
            latest_end_state = latest_state.end_state
            # If the state is an expected one, return it.
            if latest_end_state and latest_end_state.state_id in EXPECTED_STATE_IDS:
                return latest_end_state

        extra = self.get_extra_for_log(
            manual_pub_reject, payment=payment, current_state=latest_end_state
        )

        # If the state wasn't found (very unlikely) or was in
        # a state that wasn't one of the expected ones, we'll
        # log an error so a low priority alert will be created
        # This would most likely indicate the wrong ID was sent
        msg = "Unexpected state for payment in manual invalidation file"
        logger.error(msg, extra=extra)
        self.increment(self.Metrics.UNEXPECTED_PAYMENT_STATE_COUNT)

        self.add_pub_error(
            pub_error_type=PubErrorType.MANUAL_PUB_REJECT_ERROR,
            message=msg,
            line_number=manual_pub_reject.line_number,
            raw_data=manual_pub_reject.raw_line,
            details=extra,
        )

        return None

    def handle_payment_state(
        self, manual_pub_reject: ManualPubReject, payment: Payment, current_state: LkState
    ) -> None:
        """
        Handle updating the state + writeback status of a payment.
        Will only update the state/writeback if the payment hasn't already errored.
        """
        extra = self.get_extra_for_log(
            manual_pub_reject, payment=payment, pub_eft=payment.pub_eft, current_state=current_state
        )

        if current_state.state_id == State.DELEGATED_PAYMENT_ERROR_FROM_BANK.state_id:
            logger.info("Payment has already been moved to an error state, skipping", extra=extra)
            self.increment(self.Metrics.PAYMENT_ALREADY_ERRORED_COUNT)
            return

        if (
            current_state.state_id
            == State.DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION.state_id
        ):
            logger.warning(
                "Payment was previously processed as a change notification/warning and assumed successful",
                extra=extra,
            )
            self.increment(self.Metrics.PAYMENT_SWITCHING_CHANGE_NOTIFICATION_TO_ERROR_COUNT)

        writeback_transaction_status = self.convert_reject_notes_to_writeback_status(
            manual_pub_reject, payment
        )
        if writeback_transaction_status is None:
            return

        create_payment_finished_state_log_with_writeback(
            payment=payment,
            payment_end_state=State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
            payment_outcome=state_log_util.build_outcome(
                "Payment failed due to manual PUB EFT rejection file inclusion",
                line_number=str(manual_pub_reject.line_number),
            ),
            writeback_transaction_status=writeback_transaction_status,
            db_session=self.db_session,
            import_log_id=self.get_import_log_id(),
        )

        # Add PUB error to note that we rejected it as intended
        self.add_pub_error(
            pub_error_type=PubErrorType.MANUAL_PUB_REJECT_PAYMENT_PROCESSED,
            message=f'Payment manually rejected with notes "{manual_pub_reject.notes}"',
            line_number=manual_pub_reject.line_number,
            raw_data=manual_pub_reject.raw_line,
            details=extra,
            payment=payment,
        )

        self.increment(self.Metrics.PAYMENT_REJECTED_SUCCESSFULLY_COUNT)
        logger.info("Payment record manually rejected", extra=extra)

    def convert_reject_notes_to_writeback_status(
        self, manual_pub_reject: ManualPubReject, payment: Payment
    ) -> Optional[LkFineosWritebackTransactionStatus]:
        rejected_notes = manual_pub_reject.notes
        log_extra = delegated_payments_util.get_traceable_payment_details(payment)
        msg = None

        if not rejected_notes:
            msg = "Empty reject note for payment"
            self.increment(self.Metrics.MISSING_REJECT_NOTES)

        if rejected_notes:
            for status in EXPECTED_NOTE_STATUSES:
                if status.transaction_status_description.lower() in rejected_notes.lower():
                    return status

        if not msg:
            self.increment(self.Metrics.MISSING_REJECT_NOTES_MAPPING)
            log_extra |= {"rejected_notes": rejected_notes}
            msg = "Missing reject note writeback status mapping for payment in manual invalidation file"

        # If the reject notes do not contain one of the expected
        # writeback status descriptions log an error so a low
        # priority alert will be created
        logger.error(msg, extra=log_extra)
        self.add_pub_error(
            pub_error_type=PubErrorType.MANUAL_PUB_REJECT_ERROR,
            message=msg,
            line_number=manual_pub_reject.line_number,
            raw_data=manual_pub_reject.raw_line,
            details=log_extra,
        )

        return None

    def get_extra_for_log(
        self,
        manual_pub_reject: ManualPubReject,
        payment: Optional[Payment] = None,
        pub_eft: Optional[PubEft] = None,
        current_state: Optional[LkState] = None,
    ) -> Dict[str, Any]:

        extra = {
            **self.log_extra,
            "manual_pub_reject.line_number": manual_pub_reject.line_number,
            "manual_pub_reject.record_id": manual_pub_reject.record_id,
            "manual_pub_reject.notes": manual_pub_reject.notes,
        }
        # If payment/pub_eft passed in, also add those.
        if payment:
            extra |= delegated_payments_util.get_traceable_payment_details(
                payment, state=current_state
            )
        if pub_eft:
            extra |= delegated_payments_util.get_traceable_pub_eft_details(pub_eft)

        return extra
