import enum

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import PaymentMethod, State
from massgov.pfml.delegated_payments.step import Step

logger = logging.get_logger(__name__)

READY_STATE = State.DELEGATED_PAYMENT_VALIDATED


class PaymentMethodsSplitError(Exception):
    """An error during the payment methods split step."""


class PaymentMethodsSplitStep(Step):
    class Metrics(str, enum.Enum):
        ACH_PAYMENT_COUNT = "ach_payment_count"
        CHECK_PAYMENT_COUNT = "check_payment_count"
        PAYMENT_COUNT = "payment_count"

    def run_step(self) -> None:
        self.split_payment_methods()

    def _split_payment_methods(self):
        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            state_log_util.AssociatedClass.PAYMENT, READY_STATE, self.db_session
        )
        state_log_count = len(state_logs)
        self.set_metrics({self.Metrics.PAYMENT_COUNT: state_log_count})

        if state_log_count == 0:
            logger.warning(
                "No payments found in state %s, nothing to split", READY_STATE.state_description,
            )
            return

        for state_log in state_logs:
            payment = state_log.payment

            # Shouldn't happen as they should always have a payment attached
            # but due to our unassociated state log logic, it technically can happen
            # elsewhere in the code and we want to be certain it isn't happening here
            if not payment:
                raise Exception(
                    "A state log was found without a payment in the cleanup job: %s",
                    state_log.state_log_id,
                )

            payment_method_id = payment.disb_method_id

            if payment_method_id == PaymentMethod.ACH.payment_method_id:
                self.increment(self.Metrics.ACH_PAYMENT_COUNT)
                message = state_log_util.build_outcome(
                    "Moving payment to the EFT PUB file creation state"
                )
                state_log_util.create_finished_state_log(
                    end_state=State.DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_EFT,
                    associated_model=payment,
                    outcome=message,
                    db_session=self.db_session,
                )
            elif payment_method_id == PaymentMethod.CHECK.payment_method_id:
                self.increment(self.Metrics.CHECK_PAYMENT_COUNT)
                message = state_log_util.build_outcome(
                    "Moving payment to the Check PUB file creation state"
                )
                state_log_util.create_finished_state_log(
                    end_state=State.DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_CHECK,
                    associated_model=payment,
                    outcome=message,
                    db_session=self.db_session,
                )
            else:
                # raise an exception, put more details than just this here so we can trace back to the payment.
                raise PaymentMethodsSplitError(
                    "Unexpected payment method found: id=%s " % payment.payment_id
                )

        logger.info("Successfully split %i  payments state logs", state_log_count)

    def split_payment_methods(self):
        logger.info("Beginning payment methods split for payments in fineos writeback state")
        try:
            self._split_payment_methods()
            self.db_session.commit()
            logger.info("Successfully moved payments into check and EFT PUB states")
        except Exception:
            self.db_session.rollback()
            logger.exception("Error splitting payment methods")
            # We do not want to run any subsequent steps if this fails
            raise
