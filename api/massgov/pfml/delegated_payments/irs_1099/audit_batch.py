import uuid
from datetime import date

import massgov.pfml.delegated_payments.irs_1099.pfml_1099_util as pfml_1099_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.payments import Pfml1099Batch
from massgov.pfml.delegated_payments.irs_1099.pfml_1099_util import Constants as Constants
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class AuditBatchStep(Step):
    def run_step(self) -> None:
        self._audit_batch()

    def _audit_batch(self) -> None:
        logger.info("1099 Documents - Audit Batch Step")

        # Determine Tax Year
        year = pfml_1099_util.get_tax_year()

        # Get existing batch
        existing_batch = pfml_1099_util.get_current_1099_batch(self.db_session)

        # Determine Correction Indicator
        correction_indicator = pfml_1099_util.is_correction_batch()

        # Establish the batch for this run.
        new_batch = Pfml1099Batch(
            pfml_1099_batch_id=uuid.uuid4(),
            tax_year=year,
            batch_run_date=date.today(),
            correction_ind=correction_indicator,
            batch_status=Constants.CREATED_STATUS,
        )

        try:
            # Create 1099 payment batch record
            self.db_session.add(new_batch)

            # Update existing batch with proper status if not already marked
            if existing_batch is not None:
                status = ""
                status += (
                    str(existing_batch.batch_status)
                    + "; "
                    + Constants.REPLACED_STATUS
                    + str(new_batch.pfml_1099_batch_id)
                )
                existing_batch.batch_status = status

            self.db_session.commit()
        except Exception:
            self.db_session.rollback()
            logger.exception(
                "Error processing payments in batch: %s",
                new_batch.pfml_1099_batch_id,
                extra={"batch": new_batch.pfml_1099_batch_id},
            )
            raise

        logger.info("Successfully created/updated 1099 payments batch.")
