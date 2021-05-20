#
# Generate mock payments files and data.
#
# Generates various mock payments files in the local filesystem or S3 and corresponding data in the
# database.
#
# Expects that some fake employees already exist in the database, for example generated via
# `make dor-generate dor-import`.
#

import argparse
import os

import massgov.pfml.api.util.state_log_util
import massgov.pfml.db
import massgov.pfml.db.models.factories
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import (
    EFT,
    BankAccountType,
    Employee,
    PaymentMethod,
    State,
    TaxIdentifier,
)
from massgov.pfml.payments import vcc

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
            .limit(1000)
            .all()
        )

        for employee in employees:
            self.generate_payment_scenario(employee)

        self.write_files()

    def generate_payment_scenario(self, employee):
        scenario = int(employee.tax_identifier.tax_identifier) % 20

        if scenario >= 5:
            # No payment scenario for this employee
            return

        if employee.payment_method is None:
            if int(employee.tax_identifier.tax_identifier) % 3 == 0:
                employee.payment_method_id = PaymentMethod.CHECK.payment_method_id
            else:
                if employee.eft is None:
                    eft = EFT(
                        routing_nbr="345345345",
                        account_nbr="000111222333",
                        bank_account_type_id=BankAccountType.SAVINGS.bank_account_type_id,
                    )
                    employee.eft = eft
                employee.payment_method_id = PaymentMethod.ACH.payment_method_id
            self.db_session.commit()
            self.db_session.refresh(employee)  # To refresh employee.payment_method relationship

        if scenario == 1:
            # State = ...
            pass
        elif scenario == 2:
            # State = ...
            pass
        elif scenario == 3:
            # State = VCC sent
            self.vcc_data.append(employee)
        elif scenario == 4:
            # State = MMARS status confirmed
            pass
        # etc. etc.

    def write_files(self):
        if not self.output_folder.startswith("s3:"):
            os.makedirs(self.output_folder, exist_ok=True)
            os.makedirs(f"{self.output_folder}/ctr/outbound/ready", exist_ok=True)
            os.makedirs(f"{self.output_folder}/ctr/outbound/error", exist_ok=True)

        self.write_vcc_files()

    def write_vcc_files(self):
        """Write VCC files for employees in vcc_data, in chunks to simulate multiple VCC files."""
        for employee_chunk in (self.vcc_data[i : i + 10] for i in range(0, len(self.vcc_data), 10)):
            # Set states to ADD_TO_VCC.
            for employee in employee_chunk:
                massgov.pfml.api.util.state_log_util.create_finished_state_log(
                    end_state=State.ADD_TO_VCC,
                    associated_model=employee,
                    db_session=self.db_session,
                    outcome={},
                )

            self.db_session.commit()

            directory = f"{self.output_folder}/ctr/outbound"
            dat_filepath, inf_filepath = vcc.build_vcc_files(self.db_session, directory)
            logger.info("generated %s %s", dat_filepath, inf_filepath)

            for employee in employee_chunk:
                massgov.pfml.api.util.state_log_util.create_finished_state_log(
                    end_state=State.VCC_SENT,
                    associated_model=employee,
                    db_session=self.db_session,
                    outcome={},
                )

            self.db_session.commit()
