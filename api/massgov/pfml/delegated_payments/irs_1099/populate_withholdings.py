import enum
import uuid

import massgov.pfml.delegated_payments.irs_1099.pfml_1099_util as pfml_1099_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.payments import Pfml1099Withholding, WithholdingType
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class PopulateWithholdingsStep(Step):
    class Metrics(str, enum.Enum):
        WITHHOLDING_COUNT = "withholding_count"

    def run_step(self) -> None:
        self._populate_withholdings()

    def _populate_withholdings(self) -> None:
        logger.info("1099 Documents - Populate Withholdings Step")

        withholdings_result = pfml_1099_util.get_withholdings(self.db_session)

        batch = pfml_1099_util.get_current_1099_batch(self.db_session)

        if batch is None:
            return

        try:
            for withholding_row in withholdings_result:
                payment = withholding_row.Payment
                withholding_date = withholding_row.withholding_date
                withholding_type = withholding_row.withholding_type
                pfml_1099_withholding = Pfml1099Withholding(
                    pfml_1099_withholding_id=uuid.uuid4(),
                    pfml_1099_batch_id=batch.pfml_1099_batch_id,
                    payment_id=payment.payment_id,
                    claim_id=payment.claim.claim_id,
                    employee_id=payment.claim.employee.employee_id,
                    withholding_amount=payment.amount,
                    withholding_date=withholding_date,
                    withholding_type_id=WithholdingType.FEDERAL.withholding_type_id
                    if "Federal" in withholding_type
                    else WithholdingType.STATE.withholding_type_id,
                )

                self.db_session.add(pfml_1099_withholding)
                logger.debug(
                    "Created 1099 withholding.",
                    extra={
                        "pfml_1099_withholding_id": pfml_1099_withholding.pfml_1099_withholding_id
                    },
                )
                self.increment(self.Metrics.WITHHOLDING_COUNT)

            self.db_session.commit()
        except Exception:
            logger.exception(
                "Error processing withholdings in batch: %s",
                batch.pfml_1099_batch_id,
                extra={"batch": batch.pfml_1099_batch_id},
            )
            self.db_session.rollback()
            raise

        logger.info("Successfully moved withholdings to 1099 withholdings batch.")
