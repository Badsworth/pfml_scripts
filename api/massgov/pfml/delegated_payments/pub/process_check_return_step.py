#
# Process check payment return files received from the bank.
#
# To run this locally, use `make pub-payments-process-pub-returns`.
#

import enum
import uuid
from typing import Dict, Optional, Sequence, TextIO, Union

import massgov.pfml.db
import massgov.pfml.util.datetime
import massgov.pfml.util.files
import massgov.pfml.util.logging
from massgov.pfml.api.util import state_log_util
from massgov.pfml.db.models.employees import (
    Flow,
    LkState,
    Payment,
    PaymentCheck,
    PaymentCheckStatus,
    PubErrorType,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.db.models.payments import FineosWritebackTransactionStatus
from massgov.pfml.delegated_payments import delegated_config, delegated_payments_util
from massgov.pfml.delegated_payments.pub import check_return, process_files_in_path_step
from massgov.pfml.delegated_payments.util.fineos_writeback_util import (
    create_payment_finished_state_log_with_writeback,
)

logger = massgov.pfml.util.logging.get_logger(__name__)

EXPECTED_STATE_IDS = set(
    [
        State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT.state_id,
        State.DELEGATED_PAYMENT_COMPLETE.state_id,
        State.DELEGATED_PAYMENT_ERROR_FROM_BANK.state_id,
    ]
)


class ProcessCheckReturnFileStep(process_files_in_path_step.ProcessFilesInPathStep):
    """Process a check payment return file received from the bank."""

    class Metrics(str, enum.Enum):
        INPUT_PATH = "input_path"
        CHECK_NUMBER_NOT_FOUND_COUNT = "check_number_not_found_count"
        CHECK_PAYMENT_COUNT = "check_payment_count"
        PAYMENT_COMPLETE_BY_PAID_CHECK = "payment_complete_by_paid_check"
        PAYMENT_FAILED_BY_CHECK = "payment_failed_by_check"
        PAYMENT_STILL_OUTSTANDING = "payment_still_outstanding"
        PAYMENT_UNEXPECTED_STATE_COUNT = "payment_unexpected_state_count"
        WARNING_COUNT = "warning_count"
        PAYMENT_PAID_COUNT = "payment_paid_count"
        PAYMENT_OUTSTANDING_COUNT = "payment_outstanding_count"
        PAYMENT_FUTURE_COUNT = "payment_future_count"
        PAYMENT_VOID_COUNT = "payment_void_count"
        PAYMENT_STALE_COUNT = "payment_stale_count"
        PAYMENT_STOP_COUNT = "payment_stop_count"
        PAYMENT_ALREADY_COMPLETE_BY_PAID_CHECK = "payment_already_complete_by_paid_check"
        PAYMENT_ALREADY_FAILED_BY_CHECK = "payment_already_failed_by_check"
        PAYMENT_SWITCHING_ERROR_TO_SUCCESS = "payment_switching_error_to_success"
        PAYMENT_SWITCHING_SUCCESS_TO_ERROR = "payment_switching_success_to_error"
        PROCESSED_CHECKS_PAID_FILE = "processed_checks_paid_file"
        PROCESSED_CHECKS_OUTSTANDING_FILE = "processed_checks_outstanding_file"

    def __init__(
        self,
        db_session: massgov.pfml.db.Session,
        log_entry_db_session: massgov.pfml.db.Session,
        inbound_path: str = "",
    ) -> None:
        """Constructor."""
        pub_check_inbound_path = inbound_path
        if not inbound_path:
            pub_check_inbound_path = delegated_config.get_s3_config().pfml_pub_check_archive_path
        super().__init__(db_session, log_entry_db_session, pub_check_inbound_path)

    def process_file(self, path: str) -> None:
        """Parse a check payment return file and process each record."""
        self.reference_file = ReferenceFile(
            reference_file_id=uuid.uuid4(),
            file_location=path,
            reference_file_type_id=ReferenceFileType.PUB_CHECK_RETURN.reference_file_type_id,
        )
        self.db_session.add(self.reference_file)

        stream = massgov.pfml.util.files.open_stream(path)
        try:
            self.process_stream(stream)
        except Exception as err:
            self.db_session.rollback()
            logger.exception("%s: %s", type(err).__name__, str(err), extra={"path": path})
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
        check_reader = check_return.CheckReader(stream)

        for line_error in check_reader.get_line_errors():
            logger.warning("line error: %s", line_error.warning)
            self.increment(self.Metrics.WARNING_COUNT)
            self.add_pub_error(
                pub_error_type=PubErrorType.CHECK_PAYMENT_LINE_ERROR,
                message=line_error.warning,
                line_number=line_error.line_number,
                raw_data=line_error.raw_line,
            )

        self.process_check_payments(check_reader.get_check_payments())

        if check_reader.is_outstanding_issues:
            self.increment(self.Metrics.PROCESSED_CHECKS_OUTSTANDING_FILE)
        elif check_reader.is_paid_checks:
            self.increment(self.Metrics.PROCESSED_CHECKS_PAID_FILE)

    def process_check_payments(self, check_payments: Sequence[check_return.CheckPayment]) -> None:
        """Process each check payment record."""
        for check_payment in check_payments:
            self.process_single_check_payment(check_payment)
            self.increment(self.Metrics.CHECK_PAYMENT_COUNT)

    def process_single_check_payment(self, check_payment: check_return.CheckPayment) -> None:
        """Get a check payment from the database and update its state."""
        if (payment := self.get_payment_from_check_payment(check_payment)) is None:
            return
        if (payment_state := self.get_current_payment_state(payment, check_payment)) is None:
            return

        self.add_payment_reference_file(payment, self.reference_file)

        self.increment_metric_by_paid_status(check_payment.status)
        if check_payment.status == check_return.PaidStatus.PAID:
            self.paid_check_payment(payment, check_payment, payment_state)
        elif check_payment.status in {
            check_return.PaidStatus.OUTSTANDING,
            check_return.PaidStatus.FUTURE,
        }:
            self.outstanding_check_payment(payment, check_payment)
        else:
            self.reject_check_payment(payment, check_payment, payment_state)

    def increment_metric_by_paid_status(self, paid_status: check_return.PaidStatus) -> None:
        if paid_status == check_return.PaidStatus.PAID:
            self.increment(self.Metrics.PAYMENT_PAID_COUNT)
        elif paid_status == check_return.PaidStatus.OUTSTANDING:
            self.increment(self.Metrics.PAYMENT_OUTSTANDING_COUNT)
        elif paid_status == check_return.PaidStatus.FUTURE:
            self.increment(self.Metrics.PAYMENT_FUTURE_COUNT)
        elif paid_status == check_return.PaidStatus.VOID:
            self.increment(self.Metrics.PAYMENT_VOID_COUNT)
        elif paid_status == check_return.PaidStatus.STALE:
            self.increment(self.Metrics.PAYMENT_STALE_COUNT)
        elif paid_status == check_return.PaidStatus.STOP:
            self.increment(self.Metrics.PAYMENT_STOP_COUNT)

    def get_payment_from_check_payment(
        self, check_payment: check_return.CheckPayment
    ) -> Optional[Payment]:
        """Read the payment from the database that matches the given check payment."""
        payment = (
            self.db_session.query(Payment)
            .join(PaymentCheck)
            .filter(PaymentCheck.check_number == check_payment.check_number)
            .one_or_none()
        )
        if payment is not None:
            return payment

        logger.warning(
            "check number not in payment table",
            extra={
                "payments.check.line_number": check_payment.line_number,
                "payments.check.check_number": check_payment.check_number,
                "payments.check.status": check_payment.status,
            },
        )
        self.increment(self.Metrics.CHECK_NUMBER_NOT_FOUND_COUNT)
        self.add_pub_error(
            pub_error_type=PubErrorType.CHECK_PAYMENT_ERROR,
            message="check number not in payment table",
            line_number=check_payment.line_number,
            raw_data=check_payment.raw_line,
            details=dict(check_number=check_payment.check_number),
        )

        return None

    def get_current_payment_state(
        self, payment: Payment, check_payment: check_return.CheckPayment
    ) -> Optional[LkState]:
        """Validate that the latest state log of the payment is CHECK_SENT."""
        end_state_id = None
        state_description = "NONE"
        latest_state = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, self.db_session
        )
        if latest_state is not None and latest_state.end_state is not None:
            end_state_id = latest_state.end_state_id
            state_description = str(latest_state.end_state.state_description)

            # We only return the latest state from this method if they're an expected state
            if end_state_id in EXPECTED_STATE_IDS:
                return latest_state.end_state

        extra = extra_for_log(check_payment, payment)
        extra["payments.state"] = end_state_id

        # The latest state for this payment is not compatible with a check return.
        logger.error("unexpected state for check payment", extra=extra)
        self.increment(self.Metrics.PAYMENT_UNEXPECTED_STATE_COUNT)
        self.add_pub_error(
            pub_error_type=PubErrorType.CHECK_PAYMENT_ERROR,
            message="unexpected state for payment: %s (%s)" % (state_description, end_state_id),
            line_number=check_payment.line_number,
            raw_data=check_payment.raw_line,
            details=dict(check_number=check_payment.check_number),
            payment=payment,
        )
        return None

    def paid_check_payment(
        self, payment: Payment, check_payment: check_return.CheckPayment, payment_state: LkState
    ) -> None:
        """Handle a check payment that has been paid."""
        extra = extra_for_log(check_payment, payment)
        # Don't recreate state logs and writebacks if we've already done it
        if payment_state.state_id == State.DELEGATED_PAYMENT_COMPLETE.state_id:
            logger.info("Payment previously processed and marked complete", extra=extra)
            self.increment(self.Metrics.PAYMENT_ALREADY_COMPLETE_BY_PAID_CHECK)
            return

        if payment_state.state_id == State.DELEGATED_PAYMENT_ERROR_FROM_BANK.state_id:
            logger.warning(
                "Payment previously errored, but has now been marked as paid", extra=extra
            )
            self.increment(self.Metrics.PAYMENT_SWITCHING_ERROR_TO_SUCCESS)

            # Add an error for payments switching from error -> complete
            self.add_pub_error(
                pub_error_type=PubErrorType.CHECK_PAYMENT_FAILED,
                message="payment previously processed errored, unsure of correct behavior",
                line_number=check_payment.line_number,
                raw_data=check_payment.raw_line,
                details=dict(
                    check_number=check_payment.check_number, status=check_payment.status.name
                ),
                payment=payment,
            )

            return

        writeback_transaction_status = FineosWritebackTransactionStatus.POSTED

        create_payment_finished_state_log_with_writeback(
            payment=payment,
            payment_end_state=State.DELEGATED_PAYMENT_COMPLETE,
            payment_outcome=state_log_util.build_outcome(
                "Payment complete by paid check",
                check_paid_date=str(check_payment.paid_date),
                check_line_number=str(check_payment.line_number),
            ),
            writeback_transaction_status=writeback_transaction_status,
            db_session=self.db_session,
            import_log_id=self.get_import_log_id(),
        )

        payment.check.check_posted_date = check_payment.paid_date
        payment.check.payment_check_status_id = PaymentCheckStatus.PAID.payment_check_status_id

        # Keep track of how long it took for checks to be cashed
        if check_payment.paid_date and payment.check.created_at:
            check_time_to_cash = (check_payment.paid_date - payment.check.created_at.date()).days
            extra["check_time_to_cash"] = check_time_to_cash

        logger.info(
            "payment complete by paid check", extra=extra,
        )

        self.increment(self.Metrics.PAYMENT_COMPLETE_BY_PAID_CHECK)

    def outstanding_check_payment(
        self, payment: Payment, check_payment: check_return.CheckPayment
    ) -> None:
        """Handle a check payment that remains in an outstanding status."""
        logger.info(
            "check still outstanding, no state change", extra=extra_for_log(check_payment, payment),
        )
        self.increment(self.Metrics.PAYMENT_STILL_OUTSTANDING)

    def reject_check_payment(
        self, payment: Payment, check_payment: check_return.CheckPayment, payment_state: LkState
    ) -> None:
        """Handle a check payment that was void, stale, or stopped."""
        extra = extra_for_log(check_payment, payment)
        # Don't recreate state logs and writebacks if we've already done it
        if payment_state.state_id == State.DELEGATED_PAYMENT_ERROR_FROM_BANK.state_id:
            logger.info("Payment previously processed and marked as errored", extra=extra)
            self.increment(self.Metrics.PAYMENT_ALREADY_FAILED_BY_CHECK)
            return

        if payment_state.state_id == State.DELEGATED_PAYMENT_COMPLETE.state_id:
            logger.warning(
                "Payment previously processed and marked as success, but has now errored",
                extra=extra,
            )
            self.increment(self.Metrics.PAYMENT_SWITCHING_SUCCESS_TO_ERROR)

        payment.check.payment_check_status_id = PaymentCheckStatus.get_id(
            description=check_payment.status.value
        )

        writeback_transaction_status = FineosWritebackTransactionStatus.BANK_PROCESSING_ERROR

        create_payment_finished_state_log_with_writeback(
            payment=payment,
            payment_end_state=State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
            payment_outcome=state_log_util.build_outcome(
                "Payment failed by check status %s" % check_payment.status.name,
                check_line_number=str(check_payment.line_number),
                check_status=check_payment.status.name,
            ),
            writeback_transaction_status=writeback_transaction_status,
            db_session=self.db_session,
            import_log_id=self.get_import_log_id(),
        )

        logger.info(
            "payment failed by check", extra=extra,
        )
        self.increment(self.Metrics.PAYMENT_FAILED_BY_CHECK)
        self.add_pub_error(
            pub_error_type=PubErrorType.CHECK_PAYMENT_FAILED,
            message="payment failed by check: %s" % check_payment.status.name,
            line_number=check_payment.line_number,
            raw_data=check_payment.raw_line,
            details=dict(check_number=check_payment.check_number, status=check_payment.status.name),
            payment=payment,
        )


def extra_for_log(
    check_payment: check_return.CheckPayment, payment: Payment
) -> Dict[str, Union[None, int, str]]:
    return {
        **delegated_payments_util.get_traceable_payment_details(payment),
        "absence_case_id": payment.claim.fineos_absence_id if payment.claim else None,
        "payments.check.line_number": check_payment.line_number,
        "payments.check.check_number": check_payment.check_number,
        "payments.check.status": check_payment.status.name,
        "payments.payment_id": str(payment.payment_id),
        "payments.absence_case_id": payment.claim.fineos_absence_id if payment.claim else None,
    }
