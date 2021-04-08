from typing import Any, Dict, Optional

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import Claim, LatestStateLog, Payment, State, StateLog
from massgov.pfml.delegated_payments.step import Step

logger = logging.get_logger(__name__)

REASON_TEXT = "This payment and another payment are waiting for audit response cancellation."


class PaymentCancellationStep(Step):
    def run_step(self):
        # Get payments eligible to cancel
        eligible_payments_to_cancel = state_log_util.get_all_latest_state_logs_in_end_state(
            state_log_util.AssociatedClass.PAYMENT,
            State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_CANCELLATION,
            self.db_session,
        )

        # for each of those, get payments that share a claim and leave period
        for state_log in eligible_payments_to_cancel:
            matched_payments_to_cancel = (
                self.db_session.query(StateLog)
                .join(LatestStateLog)
                .join(Payment, Payment.payment_id == StateLog.payment_id)
                .join(Claim, Claim.claim_id == Payment.claim_id)
                .filter(
                    Claim.employee_id == state_log.payment.claim.employee_id,
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
                    outcome=_build_outcome(state_log),
                    db_session=self.db_session,
                    import_log_id=self.get_import_log_id(),
                )

            for matched_state_log in matched_payments_to_cancel:
                state_log_util.create_finished_state_log(
                    associated_model=matched_state_log.payment,
                    end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
                    outcome=_build_outcome(matched_state_log, state_log),
                    db_session=self.db_session,
                    import_log_id=self.get_import_log_id(),
                )


def _build_outcome(
    state_log: StateLog, related_state_log: Optional[StateLog] = None
) -> Dict[str, Any]:
    validation_container = payments_util.ValidationContainer(
        f"{state_log.payment.fineos_pei_c_value},{state_log.payment.fineos_pei_i_value}"
    )

    # TODO: improve validation reason and message
    if related_state_log is None:
        validation_container.add_validation_issue(
            reason=payments_util.ValidationReason.CANCELLATION_ERROR,
            details=f"{state_log.payment.payment_id} cancelled in address validation state.",
        )
    else:
        validation_container.add_validation_issue(
            reason=payments_util.ValidationReason.CANCELLATION_ERROR,
            details=f"{state_log.payment.payment_id} cancelled {related_state_log.payment.payment_id}",
        )

    return state_log_util.build_outcome(REASON_TEXT, validation_container)
