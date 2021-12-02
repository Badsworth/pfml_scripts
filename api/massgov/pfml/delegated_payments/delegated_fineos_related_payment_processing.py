import enum
from typing import List, Optional

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import Flow, Payment, PaymentTransactionType, State, StateLog
from massgov.pfml.db.models.payments import (
    FineosWritebackDetails,
    FineosWritebackTransactionStatus,
    LinkSplitPayment,
)
from massgov.pfml.delegated_payments.step import Step

logger = logging.get_logger(__package__)


class RelatedPaymentsProcessingStep(Step):
    class Metrics(str, enum.Enum):
        FEDERAL_WITHHOLDING_RECORD_COUNT = "federal_withholding_record_count"
        STATE_WITHHOLDING_RECORD_COUNT = "state_withholding_record_count"

    def run_step(self) -> None:
        self.process_payments_for_related_withholding_payments()

    def process_payments_for_related_withholding_payments(self) -> None:
        """Top-level function that calls all the other functions in this file in order"""
        logger.info("Processing related payment processing step")

        # get withholding payment records
        payments: List[Payment] = self._get_withholding_payments_records()

        if not payments:
            logger.info("No payment records for related payment. Exiting early.")
            return

        for payment in payments:

            if payment.claim is None:
                raise Exception(
                    "Claim not found for withholding payment id: %s ", payment.payment_id
                )

            primary_payment_records: List[Payment] = (
                self.db_session.query(Payment)
                .filter(Payment.claim_id == payment.claim_id)
                .filter(Payment.period_start_date == payment.period_start_date)
                .filter(Payment.period_end_date == payment.period_end_date)
                .filter(Payment.payment_date == payment.payment_date)
                .filter(
                    Payment.payment_transaction_type_id
                    == PaymentTransactionType.STANDARD.payment_transaction_type_id
                )
                .filter(
                    Payment.fineos_extract_import_log_id == payment.fineos_extract_import_log_id
                )
                .all()
            )
            if len(primary_payment_records) > 1:
                logger.info("Duplicate records exists for %s", payment.claim.fineos_absence_id)

                end_state = (
                    State.STATE_WITHHOLDING_PENDING_AUDIT
                    if (
                        payment.payment_transaction_type_id
                        == PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id
                    )
                    else State.FEDERAL_WITHHOLDING_PENDING_AUDIT
                )
                message = "Duplicate records found for the payment."

                state_log_util.create_finished_state_log(
                    end_state=end_state,
                    outcome=state_log_util.build_outcome(message),
                    associated_model=payment,
                    db_session=self.db_session,
                )
                logger.info(
                    "Payment added to state %s", end_state.state_description,
                )
                message = "Duplicate primay payment records found for the withholding record."
                self._manage_pei_writeback_state(payment, message)
            else:
                primary_payment_record = primary_payment_records[0].payment_id
                if primary_payment_record == "":
                    raise Exception(
                        f"Primary payment id not found for withholding payment id: {payment.payment_id}"
                    )

                #  if primary is in error state set withholding in error and don't enter in link table.
                payment_id = primary_payment_record
                related_payment_id = payment.payment_id
                link_payment = LinkSplitPayment()
                link_payment.payment_id = payment_id
                link_payment.related_payment_id = related_payment_id
                self.db_session.add(link_payment)

                #  If primary payment is has any validation error set withholidng state to error
                payment_state_log: Optional[StateLog] = state_log_util.get_latest_state_log_in_flow(
                    primary_payment_records[0], Flow.DELEGATED_PAYMENT, self.db_session
                )
                if payment_state_log is None:
                    raise Exception(
                        "State log record not found for the primary payment id: %s",
                        primary_payment_records[0].payment_id,
                    )
                if (
                    payment_state_log.end_state_id
                    != State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_id
                ):
                    end_state = (
                        State.STATE_WITHHOLDING_ERROR
                        if (
                            payment.payment_transaction_type_id
                            == PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id
                        )
                        else State.FEDERAL_WITHHOLDING_ERROR
                    )
                    outcome = state_log_util.build_outcome("Primay payment has an error")
                    state_log_util.create_finished_state_log(
                        associated_model=payment,
                        end_state=end_state,
                        outcome=outcome,
                        db_session=self.db_session,
                    )
                    logger.info(
                        "Payment added to state %s", end_state.state_description,
                    )
                    message = "Withholding record error due to an issue with the primary payment."
                    self._manage_pei_writeback_state(payment, message)

    def _manage_pei_writeback_state(self, payment: Payment, message: str) -> None:
        # Create the state log, note this is in the DELEGATED_PEI_WRITEBACK flow
        # So it is added in addition to the state log added in _create_end_state_by_payment_type
        state_log_util.create_finished_state_log(
            end_state=State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
            outcome=state_log_util.build_outcome(message),
            associated_model=payment,
            db_session=self.db_session,
        )
        writeback_details = FineosWritebackDetails(
            payment=payment,
            transaction_status_id=FineosWritebackTransactionStatus.WITHHOLDING_ERROR.transaction_status_id,
            import_log_id=self.get_import_log_id(),
        )
        self.db_session.add(writeback_details)

    def _get_withholding_payments_records(self) -> List[Payment]:
        """this method appends fedral and state withholding payment records"""
        federal_withholding_payments = self._get_payments_for_federal_withholding(self.db_session)
        state_withholding_payments = self._get_payments_for_state_withholding(self.db_session)
        payment_container = []
        for payment in federal_withholding_payments:
            self.increment(self.Metrics.FEDERAL_WITHHOLDING_RECORD_COUNT)
            payment_container.append(payment)

        for payment in state_withholding_payments:
            self.increment(self.Metrics.STATE_WITHHOLDING_RECORD_COUNT)
            payment_container.append(payment)
        return payment_container

    def _get_payments_for_federal_withholding(self, db_session: db.Session) -> List[Payment]:
        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            associated_class=state_log_util.AssociatedClass.PAYMENT,
            end_state=State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING,
            db_session=db_session,
        )
        return [state_log.payment for state_log in state_logs]

    def _get_payments_for_state_withholding(self, db_session: db.Session) -> List[Payment]:
        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            associated_class=state_log_util.AssociatedClass.PAYMENT,
            end_state=State.STATE_WITHHOLDING_READY_FOR_PROCESSING,
            db_session=db_session,
        )
        return [state_log.payment for state_log in state_logs]
