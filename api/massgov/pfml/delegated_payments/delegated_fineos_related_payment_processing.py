import enum
from typing import List, Optional

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import Payment, PaymentTransactionType, StateLog
from massgov.pfml.db.models.payments import (
    FineosWritebackDetails,
    LinkSplitPayment,
    LkFineosWritebackTransactionStatus,
)
from massgov.pfml.db.models.state import Flow, State
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.delegated_payments.util.fineos_writeback_util import (
    stage_payment_fineos_writeback,
)
from massgov.pfml.util.datetime import get_now_us_eastern

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
                .filter(Payment.period_start_date <= payment.period_start_date)
                .filter(Payment.period_end_date >= payment.period_end_date)
                .filter(
                    Payment.payment_transaction_type_id
                    == PaymentTransactionType.STANDARD.payment_transaction_type_id
                )
                .filter(
                    Payment.fineos_extract_import_log_id == payment.fineos_extract_import_log_id
                )
                .all()
            )

            payment_log_details = payments_util.get_traceable_payment_details(payment)
            if len(primary_payment_records) > 1:
                logger.info(
                    "Duplicate primary records exist for related payment %s",
                    payment.claim.fineos_absence_id,
                    extra=payment_log_details,
                )

                end_state = (
                    State.STATE_WITHHOLDING_ORPHANED_PENDING_AUDIT
                    if (
                        payment.payment_transaction_type_id
                        == PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id
                    )
                    else State.FEDERAL_WITHHOLDING_ORPHANED_PENDING_AUDIT
                )
                message = "Duplicate records found for the payment."

                state_log_util.create_finished_state_log(
                    end_state=end_state,
                    outcome=state_log_util.build_outcome(message),
                    associated_model=payment,
                    db_session=self.db_session,
                )
                logger.info(
                    "Payment added to state %s",
                    end_state.state_description,
                    extra=payments_util.get_traceable_payment_details(payment, end_state),
                )
                message = "Duplicate primary payment records found for the withholding record."
            elif len(primary_payment_records) == 0:
                logger.info(
                    "No primary payment record exists for related payment %s",
                    payment.claim.fineos_absence_id,
                    extra=payment_log_details,
                )

                end_state = (
                    State.STATE_WITHHOLDING_ORPHANED_PENDING_AUDIT
                    if (
                        payment.payment_transaction_type_id
                        == PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id
                    )
                    else State.FEDERAL_WITHHOLDING_ORPHANED_PENDING_AUDIT
                )
                message = "No primary payment found for the withholding payment record."

                state_log_util.create_finished_state_log(
                    end_state=end_state,
                    outcome=state_log_util.build_outcome(message),
                    associated_model=payment,
                    db_session=self.db_session,
                )
                logger.info(
                    "Payment added to state %s",
                    end_state.state_description,
                    extra=payments_util.get_traceable_payment_details(payment, end_state),
                )
                message = "No primary payment record found for the withholding record."
            else:
                primary_payment_record = primary_payment_records[0].payment_id
                if primary_payment_record == "":
                    raise Exception(
                        f"Primary payment id not found for withholding payment id: {payment.payment_id}"
                    )

                payment_id = primary_payment_record
                related_payment_id = payment.payment_id
                link_payment = LinkSplitPayment()
                link_payment.payment_id = payment_id
                link_payment.related_payment_id = related_payment_id
                self.db_session.add(link_payment)

                logger.info(
                    "Added related payment to link_payment: Primary payment id %s , Related Payment Id %s",
                    payment_id,
                    related_payment_id,
                    extra=payment_log_details,
                )

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

                    if (
                        payment_state_log.end_state_id
                        in payments_util.Constants.RESTARTABLE_PAYMENT_STATE_IDS
                    ):
                        end_state = (
                            State.STATE_WITHHOLDING_ERROR_RESTARTABLE
                            if (
                                payment.payment_transaction_type_id
                                == PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id
                            )
                            else State.FEDERAL_WITHHOLDING_ERROR_RESTARTABLE
                        )
                        outcome = state_log_util.build_outcome(
                            "Primary payment is in Error restartable state"
                        )
                    else:
                        end_state = (
                            State.STATE_WITHHOLDING_ERROR
                            if (
                                payment.payment_transaction_type_id
                                == PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id
                            )
                            else State.FEDERAL_WITHHOLDING_ERROR
                        )
                        outcome = state_log_util.build_outcome("Primary payment has an error")
                    state_log_util.create_finished_state_log(
                        associated_model=payment,
                        end_state=end_state,
                        outcome=outcome,
                        db_session=self.db_session,
                    )
                    logger.info(
                        "Payment added to state %s",
                        end_state.state_description,
                        extra=payments_util.get_traceable_payment_details(payment, end_state),
                    )

                    transaction_status: Optional[
                        LkFineosWritebackTransactionStatus
                    ] = self._get_payment_writeback_transaction_status(primary_payment_records[0])
                    if transaction_status and transaction_status.transaction_status_description:
                        message = (
                            "Withholding record error due to an issue with the primary payment."
                        )
                        stage_payment_fineos_writeback(
                            payment=payment,
                            writeback_transaction_status=transaction_status,
                            outcome=state_log_util.build_outcome(message),
                            db_session=self.db_session,
                            import_log_id=self.get_import_log_id(),
                        )

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
