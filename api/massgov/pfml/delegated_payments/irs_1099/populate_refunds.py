import uuid

import massgov.pfml.delegated_payments.irs_1099.pfml_1099_util as pfml_1099_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.payments import Pfml1099Refund
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class PopulateRefundsStep(Step):
    def run_step(self) -> None:
        self._populate_refunds()

    def _populate_refunds(self) -> None:
        logger.info("1099 Documents - Populate Refunds Step")

        # Get all overpayment data for the 1099 batch
        overpayments = pfml_1099_util.get_overpayments(self.db_session)

        # Get the current batch
        batch = pfml_1099_util.get_current_1099_batch(self.db_session)
        if batch is None:
            logger.error("No current batch exists. This should never happen.")
            raise Exception("Batch cannot be empty at this point.")

        try:
            # Create 1099 refund record for each overpayment
            for overpayment in overpayments:

                refund_date = overpayment.payment_date

                if refund_date is None:
                    logger.debug(
                        "Overpayment: %s does not have a date associated with it.",
                        overpayment.payment_id,
                    )
                    continue

                pfml_1099_overpayment = Pfml1099Refund(
                    pfml_1099_refund_id=uuid.uuid4(),
                    pfml_1099_batch_id=batch.pfml_1099_batch_id,
                    payment_id=overpayment.payment_id,
                    employee_id=overpayment.claim.employee.employee_id,
                    refund_amount=overpayment.amount,
                    refund_date=refund_date,
                )

                self.db_session.add(pfml_1099_overpayment)
                logger.debug(
                    "Created 1099 refund.",
                    extra={"pfml_1099_refund_id": pfml_1099_overpayment.pfml_1099_refund_id},
                )

            self.db_session.commit()
        except Exception:
            logger.exception(
                "Error processing overpayments in batch: %s",
                batch.pfml_1099_batch_id,
                extra={"batch": batch.pfml_1099_batch_id},
            )
            self.db_session.rollback()
            raise

        logger.info("Successfully moved overpayments to 1099 payments batch.")
