import enum

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import LkState, State
from massgov.pfml.db.models.payments import FineosWritebackTransactionStatus
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.delegated_payments.util.fineos_writeback_util import (
    create_payment_finished_state_log_with_writeback,
)

# This step moves various payment states
# to the ADD_TO_PAYMENT_ERROR_REPORT state.
# The states we move are the states that are
# pending and waiting for the payment audit
# report reject file. If we process the file
# there should not be anything moved, as everything
# should be moved out of the pending states. If there
# are somehow records that we missed, this also would
# move those to the error state
logger = logging.get_logger(__name__)

ERROR_STATE = State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE
ERROR_OUTCOME = state_log_util.build_outcome("Payment timed out waiting for audit reject report")


class StateCleanupStep(Step):
    class Metrics(str, enum.Enum):
        AUDIT_STATE_CLEANUP_COUNT = "audit_state_cleanup_count"

    def run_step(self) -> None:
        self.cleanup_states()

    def _cleanup_state(self, current_state: LkState) -> None:
        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            state_log_util.AssociatedClass.PAYMENT, current_state, self.db_session
        )
        state_log_count = len(state_logs)
        if state_log_count == 0:
            logger.info(
                "No payments found in state %s, nothing to cleanup", current_state.state_description
            )
            return

        logger.warning(
            "%i payments found for state %s, moving them to %s",
            state_log_count,
            current_state.state_description,
            ERROR_STATE.state_description,
        )

        for state_log in state_logs:
            self.increment(self.Metrics.AUDIT_STATE_CLEANUP_COUNT)
            payment = state_log.payment

            # Shouldn't happen as they should always have a payment attached
            # but due to our unassociated state log logic, it technically can happen
            # elsewhere in the code and we want to be certain it isn't happening here
            if not payment:
                raise Exception(
                    "A state log was found without a payment in the cleanup job: %s",
                    state_log.state_log_id,
                )

            create_payment_finished_state_log_with_writeback(
                payment=payment,
                payment_end_state=ERROR_STATE,
                payment_outcome=ERROR_OUTCOME,
                writeback_transaction_status=FineosWritebackTransactionStatus.PENDING_PAYMENT_AUDIT,
                db_session=self.db_session,
                import_log_id=self.get_import_log_id(),
            )
            logger.info(
                "No audit file received for payment, moving to state [%s] to allow us to consume again",
                ERROR_STATE.state_description,
                extra=payments_util.get_traceable_payment_details(payment, ERROR_STATE),
            )

        logger.info(
            "Successfully moved %i state logs from %s to %s",
            state_log_count,
            current_state.state_description,
            ERROR_STATE.state_description,
        )

    def cleanup_states(self) -> None:
        logger.info(
            "Beginning cleanup of payment state logs for payments in audit report pending states"
        )
        for audit_state in payments_util.Constants.REJECT_FILE_PENDING_STATES:
            self._cleanup_state(audit_state)
        self.db_session.commit()
        logger.info(
            "Completed cleanup of payment state logs for payments in audit report pending states"
        )
