import enum
import uuid
from typing import NamedTuple

import massgov.pfml.delegated_payments.irs_1099.pfml_1099_util as pfml_1099_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.payments import Pfml1099, Pfml1099Batch
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class Populate1099Step(Step):
    class Metrics(str, enum.Enum):
        IRS_1099_COUNT = "irs_1099_count"

    def run_step(self) -> None:

        # Get the current batch
        batch = pfml_1099_util.get_current_1099_batch(self.db_session)

        if batch is None:
            logger.error("No current batch exists. This should never happen.")
            raise Exception("Batch cannot be empty at this point.")

        # Get all relevant claimants for the 1099 batch
        claimant_results = pfml_1099_util.get_1099s(self.db_session, batch)

        try:
            self._populate_1099(batch, claimant_results)
            self.db_session.commit()
        except Exception:
            self.db_session.rollback()
            logger.exception(
                "Error processing claimants in batch: %s",
                batch.pfml_1099_batch_id,
                extra={"batch": batch.pfml_1099_batch_id},
            )
            raise

        logger.info("Successfully moved claimants to 1099 payments batch.")

    def _populate_1099(self, batch: Pfml1099Batch, claimant_results: NamedTuple) -> None:
        logger.info("1099 Documents - Populate 1099 Step")

        # Create 1099 records for each claimant
        for claimant_row in claimant_results:

            gross_payments = claimant_row.GROSS_PAYMENTS
            if gross_payments is None:
                gross_payments = 0

            gross_mmars_payments = claimant_row.GROSS_MMARS_PAYMENTS
            if gross_mmars_payments is None:
                gross_mmars_payments = 0

            state_tax_withholdings = claimant_row.STATE_TAX_WITHHOLDINGS
            if state_tax_withholdings is None:
                state_tax_withholdings = 0

            federal_tax_withholdings = claimant_row.FEDERAL_TAX_WITHHOLDINGS
            if federal_tax_withholdings is None:
                federal_tax_withholdings = 0

            overpayment_repayments = claimant_row.OVERPAYMENT_REPAYMENTS
            if overpayment_repayments is None:
                overpayment_repayments = 0

            # TODO: Add other credits to table and form.
            # Other Credits will not apply in 2021.  PAY-73 is for tracking this work.
            other_credits = claimant_row.OTHER_CREDITS
            if other_credits is None:
                other_credits = 0

            pfml_1099_payment = Pfml1099(
                pfml_1099_id=uuid.uuid4(),
                pfml_1099_batch_id=batch.pfml_1099_batch_id,
                tax_year=batch.tax_year,
                employee_id=claimant_row.employee_id,
                tax_identifier_id=claimant_row.tax_identifier_id,
                first_name=claimant_row.first_name,
                last_name=claimant_row.last_name,
                address_line_1=claimant_row.address1,
                address_line_2=claimant_row.address2,
                city=claimant_row.address4,
                state=claimant_row.address6,
                zip=claimant_row.postcode,
                gross_payments=gross_payments + gross_mmars_payments,
                state_tax_withholdings=state_tax_withholdings,
                federal_tax_withholdings=federal_tax_withholdings,
                overpayment_repayments=overpayment_repayments,
                correction_ind=batch.correction_ind,
            )

            self.db_session.add(pfml_1099_payment)
            logger.debug(
                "Created 1099.", extra={"pfml_1099_id": pfml_1099_payment.pfml_1099_id},
            )
            self.increment(self.Metrics.IRS_1099_COUNT)
