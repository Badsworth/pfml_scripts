import enum
import uuid

import massgov.pfml.delegated_payments.irs_1099.pfml_1099_util as pfml_1099_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.payments import Pfml1099MMARSPayment
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class PopulateMmarsPaymentsStep(Step):
    class Metrics(str, enum.Enum):
        MMARS_PAYMENT_COUNT = "mmars_payment_count"

    def run_step(self) -> None:
        self._populate_mmars_payments()

    def _populate_mmars_payments(self) -> None:
        logger.info("1099 Documents - Populate 1099 Mmars Payments Step")

        # Get all MMARS payment data for the 1099 batch
        payment_results = pfml_1099_util.get_mmars_payments(self.db_session)

        # Get the current batch
        batch = pfml_1099_util.get_current_1099_batch(self.db_session)
        if batch is None:
            logger.error("No current batch exists. This should never happen.")
            raise Exception("Batch cannot be empty at this point.")

        try:
            # Create 1099 payment record for each payment
            for payment_row in payment_results:

                pfml_1099_payment = Pfml1099MMARSPayment(
                    pfml_1099_mmars_payment_id=uuid.uuid4(),
                    pfml_1099_batch_id=batch.pfml_1099_batch_id,
                    mmars_payment_id=payment_row.mmars_payment_id,
                    employee_id=payment_row.employee_id,
                    payment_amount=payment_row.payment_amount,
                    payment_date=payment_row.payment_date,
                )

                self.db_session.add(pfml_1099_payment)
                logger.debug(
                    "Created 1099 MMARS payment.",
                    extra={
                        "pfml_1099_mmars_payment_id": pfml_1099_payment.pfml_1099_mmars_payment_id
                    },
                )
                self.increment(self.Metrics.MMARS_PAYMENT_COUNT)

            self.db_session.commit()
        except Exception:
            logger.exception(
                "Error processing payments in batch: %s",
                batch.pfml_1099_batch_id,
                extra={"batch": batch.pfml_1099_batch_id},
            )
            self.db_session.rollback()
            raise

        logger.info("Successfully moved MMARS payments to 1099 payments batch.")
