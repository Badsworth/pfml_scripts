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

import massgov.pfml.db
import massgov.pfml.db.models.factories
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import (
    EFT,
    BankAccountType,
    CtrBatchIdentifier,
    Employee,
    EmployeeReferenceFile,
    PaymentMethod,
    ReferenceFile,
    ReferenceFileType,
    TaxIdentifier,
)
from massgov.pfml.payments import payments_util, vcc

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

        if employee.mailing_address is None:
            employee.mailing_address = massgov.pfml.db.models.factories.AddressFactory()
            self.db_session.commit()
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
        now = payments_util.get_now()

        count = 10
        for employee_chunk in (self.vcc_data[i : i + 10] for i in range(0, len(self.vcc_data), 10)):
            batch_id = f"EOL{now.strftime('%m%d')}VCC{count}"
            directory_name = f"EOL{now.strftime('%Y%m%d')}VCC{count}"
            directory = f"{self.output_folder}/ctr/outbound/ready/{directory_name}"
            if not self.output_folder.startswith("s3:"):
                os.makedirs(directory, exist_ok=True)
            (dat_filepath, inf_filepath) = vcc.build_vcc_files(employee_chunk, directory, count)
            logger.info("generated %s %s", dat_filepath, inf_filepath)

            ctr_batch_identifier = CtrBatchIdentifier(
                ctr_batch_identifier=batch_id,
                year=now.year,
                batch_date=now.date(),
                batch_counter=count,
            )
            reference_file = ReferenceFile(
                file_location=directory + "/",
                reference_file_type_id=ReferenceFileType.VCC.reference_file_type_id,
                ctr_batch_identifier=ctr_batch_identifier,
            )
            self.db_session.add(ctr_batch_identifier)
            self.db_session.add(reference_file)
            for employee in employee_chunk:
                self.db_session.add(
                    EmployeeReferenceFile(
                        employee=employee,
                        reference_file=reference_file,
                        ctr_document_identifier=None,  # TODO
                    )
                )
            self.db_session.commit()

            count += 1
