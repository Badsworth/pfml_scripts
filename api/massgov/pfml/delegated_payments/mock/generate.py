#
# Generate mock payments data.
#
# Generates various mock payments data in the database in various states.
#
# Expects that some fake employees already exist in the database, for example generated via
# `make dor-generate dor-import`.
#

import argparse
import datetime
import decimal

import massgov.pfml.api.util.state_log_util
import massgov.pfml.db
import massgov.pfml.db.models.factories
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import (
    BankAccountType,
    Claim,
    ClaimType,
    Employee,
    EmployeePubEftPair,
    Payment,
    PaymentCheck,
    PaymentMethod,
    PaymentTransactionType,
    PrenoteState,
    PubEft,
    State,
    TaxIdentifier,
)

logger = massgov.pfml.util.logging.get_logger(__name__)

parser = argparse.ArgumentParser(description="Generate fake payments files and data")
parser.add_argument(
    "--folder", type=str, default="payments_files", help="Output folder for generated files"
)


def main():
    """Payments mock files and data generator."""
    massgov.pfml.util.logging.init(__name__)

    db_session = massgov.pfml.db.init()
    massgov.pfml.db.models.factories.db_session = db_session

    args = parser.parse_args()

    output_folder = args.folder
    logger.info("writing to %s", output_folder)

    generator = PaymentScenariosGenerator(db_session, output_folder)
    generator.run()

    logger.info("done")


class PaymentScenariosGenerator:
    def __init__(self, db_session, output_folder):
        self.db_session = db_session
        self.output_folder = output_folder
        self.vcc_data = []

    def run(self):
        employees = (
            self.db_session.query(Employee)
            .join(TaxIdentifier)
            .order_by(TaxIdentifier.tax_identifier)
            .limit(100)
            .all()
        )

        for employee in employees:
            self.generate_payment_scenario(employee)
            self.db_session.commit()

    def generate_payment_scenario(self, employee):
        index = int(employee.tax_identifier.tax_identifier) % 10000
        scenario = index % 10

        logger.info(
            "employee %s %s_%s",
            employee.employee_id,
            employee.tax_identifier.tax_identifier[:3],
            employee.tax_identifier.tax_identifier[3:],
        )

        existing_pub_efts = employee.pub_efts.all()
        if len(existing_pub_efts) == 0:
            pub_eft = PubEft(
                routing_nbr="%09d" % (444000000 + index),
                account_nbr="%011d" % (3030000000 + index),
                bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
                prenote_state_id=PrenoteState.PENDING_PRE_PUB.prenote_state_id,
            )
            self.db_session.add(pub_eft)
            employee.pub_efts.append(EmployeePubEftPair(pub_eft=pub_eft))
            logger.info(".. added pub_eft %s %s", pub_eft.routing_nbr, pub_eft.account_nbr)
        else:
            pub_eft = existing_pub_efts[0].pub_eft

        existing_claims = employee.claims
        if existing_claims:
            claim = existing_claims[0]
        else:
            claim = Claim(
                claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
                employer=employee.wages_and_contributions[0].employer,
                employee=employee,
                fineos_absence_id="NTN-9900%s-ABS-1" % index,
            )
            self.db_session.add(claim)
            self.db_session.commit()
            logger.info(".. added claim %s %s", claim.claim_id, claim.fineos_absence_id)

        payment = Payment(
            payment_transaction_type_id=PaymentTransactionType.STANDARD.payment_transaction_type_id,
            period_start_date=datetime.date(2021, 3, 17),
            period_end_date=datetime.date(2021, 3, 24),
            payment_date=datetime.date(2021, 3, 25),
            amount=decimal.Decimal(100.75 + index),
            fineos_pei_c_value=str(42424),
            fineos_pei_i_value=str(10000 + index),
            fineos_extraction_date=datetime.date(2021, 3, 24),
            disb_method_id=PaymentMethod.ACH.payment_method_id,
            pub_eft=pub_eft,
            claim=claim,
            claim_type_id=claim.claim_type_id,
        )
        self.db_session.add(payment)
        self.db_session.commit()
        logger.info(".. added payment %s %s", payment.payment_id, payment.amount)

        if scenario == 0:
            # Send EFT prenote
            massgov.pfml.api.util.state_log_util.create_finished_state_log(
                end_state=State.DELEGATED_EFT_SEND_PRENOTE,
                associated_model=employee,
                db_session=self.db_session,
                outcome=massgov.pfml.api.util.state_log_util.build_outcome(
                    "Generated state EFT_SEND_PRENOTE"
                ),
            )
            logger.info(".. set finished state DELEGATED_EFT_SEND_PRENOTE")

        elif scenario == 1:
            # EFT prenote sent
            massgov.pfml.api.util.state_log_util.create_finished_state_log(
                end_state=State.DELEGATED_EFT_PRENOTE_SENT,
                associated_model=employee,
                db_session=self.db_session,
                outcome=massgov.pfml.api.util.state_log_util.build_outcome(
                    "Generated state EFT_PRENOTE_SENT"
                ),
            )
            logger.info(".. set finished state DELEGATED_EFT_PRENOTE_SENT")
            pub_eft.prenote_state_id = PrenoteState.PENDING_WITH_PUB.prenote_state_id

        elif scenario == 2:
            # Add to PUB Transaction - EFT
            massgov.pfml.api.util.state_log_util.create_finished_state_log(
                end_state=State.DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_EFT,
                associated_model=payment,
                db_session=self.db_session,
                outcome=massgov.pfml.api.util.state_log_util.build_outcome(
                    "Generated state PAYMENT_ADD_TO_PUB_TRANSACTION_EFT"
                ),
            )
            logger.info("  .. set finished state DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_EFT")

        elif scenario == 3:
            # PUB Transaction sent - EFT
            massgov.pfml.api.util.state_log_util.create_finished_state_log(
                end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
                associated_model=payment,
                db_session=self.db_session,
                outcome=massgov.pfml.api.util.state_log_util.build_outcome(
                    "Generated state PAYMENT_PUB_TRANSACTION_EFT_SENT"
                ),
            )
            logger.info("  .. set finished state DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT")

        elif scenario == 5:
            # PUB Transaction sent - Check
            massgov.pfml.api.util.state_log_util.create_finished_state_log(
                end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT,
                associated_model=payment,
                db_session=self.db_session,
                outcome=massgov.pfml.api.util.state_log_util.build_outcome(
                    "Generated state DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT"
                ),
            )
            payment.check = PaymentCheck(check_number=500 + index)
            logger.info(
                "  .. set finished state DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT,"
                "check_number %i",
                payment.check.check_number,
            )
