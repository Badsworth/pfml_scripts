import uuid
from decimal import Decimal
from typing import Iterable

import massgov.pfml.delegated_payments.irs_1099.pfml_1099_util as pfml_1099_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.payments import FineosExtractEmployeeFeed, Pfml1099, Pfml1099Batch
from massgov.pfml.delegated_payments.irs_1099.pfml_1099_util import Constants as Constants
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class Populate1099Step(Step):
    def run_step(self) -> None:

        # Get the current batch
        batch = pfml_1099_util.get_current_1099_batch(self.db_session)

        if batch is None:
            logger.error("No current batch exists. This should never happen.")
            raise Exception("Batch cannot be empty at this point.")

        # Get all relevant claimants for the 1099 batch
        claimants = pfml_1099_util.get_1099_claimants(self.db_session)

        try:
            self._populate_1099(batch, claimants)
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

    def _populate_1099(
        self, batch: Pfml1099Batch, claimants: Iterable[FineosExtractEmployeeFeed]
    ) -> None:
        logger.info("1099 Documents - Populate 1099 Step")

        # NEED TO REVISIT ADDRESS BEING APPLIED HERE
        # When the address validation is finalized, this logic should reference the
        # validated address for the claimant, not the address data on the extract.

        # Create 1099 record for each claimant
        for claimant in claimants:

            employee = pfml_1099_util.get_employee(self.db_session, claimant)

            if (
                not claimant.address1
                or not claimant.address4
                or not claimant.address6
                or not claimant.postcode
            ):
                logger.info("Address is not valid.")
                continue

            address_line_2 = ""
            if claimant.address2 is not None:
                address_line_2 = claimant.address2

            if employee is not None:
                payments = pfml_1099_util.get_1099_payments(self.db_session, batch, employee)

                if (
                    not employee.tax_identifier
                    or not employee.fineos_employee_first_name
                    or not employee.fineos_employee_last_name
                ):
                    logger.error("Invalid employee: %s", employee.employee_id)
                    continue

                if len(payments) == 0:
                    logger.debug("No Payments for claimant: %s", employee.employee_id)
                    continue

                payments_gross = Decimal(sum((payment.payment_amount for payment in payments), 0))
                logger.debug(
                    "Payments Gross for %s: %s", employee.employee_id, payments_gross,
                )

                mmars_payments = pfml_1099_util.get_1099_mmars_payments(
                    self.db_session, batch, employee
                )
                mmars_gross = Decimal(
                    sum((payment.payment_amount for payment in mmars_payments), 0)
                )
                logger.debug(
                    "MMARS Payments Gross for %s: %s", employee.employee_id, mmars_gross,
                )

                refunds = pfml_1099_util.get_1099_refunds(self.db_session, batch, employee)
                refunds_gross = Decimal(sum((refund.refund_amount for refund in refunds), 0))
                logger.debug(
                    "Refunds Gross for %s: %s", employee.employee_id, refunds_gross,
                )

                state_withholdings = pfml_1099_util.get_1099_withholdings(
                    self.db_session, batch, employee, Constants.STATE_WITHHOLDING_TYPE
                )
                state_withholdings_gross = Decimal(
                    sum((payment.withholding_amount for payment in state_withholdings), 0)
                )
                logger.debug(
                    "State Withholdings Gross for %s: %s",
                    employee.employee_id,
                    state_withholdings_gross,
                )

                federal_withholdings = pfml_1099_util.get_1099_withholdings(
                    self.db_session, batch, employee, Constants.FEDERAL_WITHHOLDING_TYPE
                )
                federal_withholdings_gross = Decimal(
                    sum(payment.withholding_amount for payment in federal_withholdings)
                )
                logger.debug(
                    "Federal Withholdings Gross for %s: %s",
                    employee.employee_id,
                    federal_withholdings_gross,
                )

                pfml_1099_payment = Pfml1099(
                    pfml_1099_id=uuid.uuid4(),
                    pfml_1099_batch_id=batch.pfml_1099_batch_id,
                    tax_year=batch.tax_year,
                    employee_id=employee.employee_id,
                    tax_identifier_id=employee.tax_identifier.tax_identifier_id,
                    first_name=employee.fineos_employee_first_name,
                    last_name=employee.fineos_employee_last_name,
                    address_line_1=claimant.address1,
                    address_line_2=address_line_2,
                    city=claimant.address4,
                    state=claimant.address6,
                    zip=claimant.postcode,
                    gross_payments=payments_gross + mmars_gross,
                    state_tax_withholdings=state_withholdings_gross,
                    federal_tax_withholdings=federal_withholdings_gross,
                    overpayment_repayments=refunds_gross,
                    correction_ind=batch.correction_ind,
                )

                self.db_session.add(pfml_1099_payment)
                logger.debug(
                    "Created 1099.", extra={"pfml_1099_id": pfml_1099_payment.pfml_1099_id},
                )
