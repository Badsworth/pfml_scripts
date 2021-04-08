import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import Payment, State, StateLog
from massgov.pfml.delegated_payments.step import Step

logger = logging.get_logger(__name__)


class PaymentCancellationStep(Step):
    def run_step(self):
        # Get payments eligible to cancel
        eligible_payments_to_cancel = (
            self.db_session.query(StateLog)
            .join(Payment)
            .filter(
                StateLog.end_state_id.in_(
                    [
                        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_CANCELLATION.state_id
                    ]
                ),
            )
            .all()
        )

        # for each of those, get payments that share a claim and leave period
        for state_log in eligible_payments_to_cancel:

            matched_payments_to_cancel = (
                self.db_session.query(StateLog)
                .join(Payment)
                .filter(
                    Payment.claim_id == state_log.payment.claim_id,
                    StateLog.end_state_id.in_(
                        [State.PAYMENT_READY_FOR_ADDRESS_VALIDATION.state_id]
                    ),
                )
                .all()
            )

            # send the payment and any matches to the error report
            if len(matched_payments_to_cancel) > 0:
                state_log_util.create_finished_state_log(
                    associated_model=state_log.payment,
                    end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
                    outcome=state_log_util.build_outcome("Payment cancelled"),
                    db_session=self.db_session,
                    import_log_id=self.get_import_log_id(),
                )

            for matched_state_log in matched_payments_to_cancel:
                state_log_util.create_finished_state_log(
                    associated_model=matched_state_log.payment,
                    end_state=State.DELEGATED_EFT_ADD_TO_ERROR_REPORT,
                    outcome=state_log_util.build_outcome("Payment cancelled"),
                    db_session=self.db_session,
                    import_log_id=self.get_import_log_id(),
                )
