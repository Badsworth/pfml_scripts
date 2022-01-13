import enum
from typing import List

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import Payment, PaymentTransactionType, State
from massgov.pfml.db.models.payments import FineosWritebackTransactionStatus
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.delegated_payments.util.fineos_writeback_util import (
    create_payment_finished_state_log_with_writeback,
)

logger = logging.get_logger(__package__)


class RelatedPaymentsPostProcessingStep(Step):
    class Metrics(str, enum.Enum):
        FEDERAL_WITHHOLDING_SEND_FUNDS_RECORD_COUNT = "federal_withholding_send_funds_record_count"
        STATE_WITHHOLDING_SEND_FUNDS_RECORD_COUNT = "state_withholding_send_funds_record_count"

    def run_step(self) -> None:
        self.process_related_withholding_payments()

    def process_related_withholding_payments(self) -> None:
        """Top-level function that calls all the other functions in this file in order"""
        logger.info("Processing related payment post processing step")

        # get withholding payment records
        payments: List[Payment] = self._get_withholding_payments_records()

        if not payments:
            logger.info("No payment records for related payment. Exiting early.")
            return

        for payment in payments:
            outcome = state_log_util.build_outcome("PUB transaction sent")

            end_state = (
                State.STATE_WITHHOLDING_FUNDS_SENT
                if (
                    payment.payment_transaction_type_id
                    == PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id
                )
                else State.FEDERAL_WITHHOLDING_FUNDS_SENT
            )
            transaction_status = FineosWritebackTransactionStatus.PAID

            logger.info(
                "Related payment for post-processing set to state %s",
                end_state.state_description,
                extra=payments_util.get_traceable_payment_details(payment, end_state),
            )

            create_payment_finished_state_log_with_writeback(
                payment=payment,
                payment_end_state=end_state,
                payment_outcome=outcome,
                writeback_transaction_status=transaction_status,
                writeback_outcome=outcome,
                db_session=self.db_session,
                import_log_id=self.get_import_log_id(),
            )

            payments_util.create_payment_log(payment, self.get_import_log_id(), self.db_session)

    def _get_withholding_payments_records(self) -> List[Payment]:
        """this method appends fedral and state withholding payment records"""
        federal_withholding_payments = self._get_payments_for_federal_withholding(self.db_session)
        state_withholding_payments = self._get_payments_for_state_withholding(self.db_session)
        payment_container = []
        for payment in federal_withholding_payments:
            self.increment(self.Metrics.FEDERAL_WITHHOLDING_SEND_FUNDS_RECORD_COUNT)
            payment_container.append(payment)

        for payment in state_withholding_payments:
            self.increment(self.Metrics.STATE_WITHHOLDING_SEND_FUNDS_RECORD_COUNT)
            payment_container.append(payment)
        return payment_container

    def _get_payments_for_federal_withholding(self, db_session: db.Session) -> List[Payment]:
        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            associated_class=state_log_util.AssociatedClass.PAYMENT,
            end_state=State.FEDERAL_WITHHOLDING_SEND_FUNDS,
            db_session=db_session,
        )
        return [state_log.payment for state_log in state_logs]

    def _get_payments_for_state_withholding(self, db_session: db.Session) -> List[Payment]:
        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            associated_class=state_log_util.AssociatedClass.PAYMENT,
            end_state=State.STATE_WITHHOLDING_SEND_FUNDS,
            db_session=db_session,
        )
        return [state_log.payment for state_log in state_logs]
