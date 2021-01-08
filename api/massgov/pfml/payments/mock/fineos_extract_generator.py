#
# Generate mock fineos payment and vendor extract files and data.
#
# Generates various mock fineos payments files in the local filesystem corresponding data in the database.
#

import argparse
import csv
import io
import os
import random
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict

import massgov.pfml.db as db
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    Claim,
    ClaimType,
    Employee,
    EmployeeAddress,
    Employer,
    PaymentMethod,
    TaxIdentifier,
)
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ClaimFactory,
    CtrAddressPairFactory,
    EftFactory,
    EmployeeFactory,
    EmployerFactory,
    PaymentFactory,
)
from massgov.pfml.payments.fineos_payment_export import CiIndex

logger = logging.get_logger(__name__)


def ssn_validator(arg):
    value = int(arg)
    if value < 250000000:
        raise argparse.ArgumentTypeError("ssn must be at least 250000000")
    return value


def fein_validator(arg):
    value = int(arg)
    if value < 100000000:
        raise argparse.ArgumentTypeError("fein must be at least 100000000")
    return value


parser = argparse.ArgumentParser(description="Generate fake payments files and data")
parser.add_argument("--count", type=str, default="10", help="Number of employees to generate")
parser.add_argument(
    "--folder", type=str, default="payments_files", help="Output folder for generated files"
)
parser.add_argument(
    "--fein", type=fein_validator, default=100000000, help="Base FEIN for employers"
)
parser.add_argument("--ssn", type=ssn_validator, default=250000000, help="Base SSN for employees")

# == CSV file constants
# TODO use file name contats in payment and vendor modules
PEI_FILE_NAME = "vpei.csv"
PEI_PAYMENT_DETAILS_FILE_NAME = "vpeipaymentdetails.csv"
PEI_CLAIM_DETAILS_FILE_NAME = "vpeiclaimdetails.csv"
REQUESTED_ABSENCES_FILE_NAME = "VBI_REQUESTEDABSENCE_SOM.csv"
EMPLOYEE_FEED_FILE_NAME = "Employee_feed.csv"
LEAVE_PLAN_FILE_NAME = "LeavePlan_info.csv"

PEI_FIELD_NAMES = [
    "C",
    "I",
    "PAYEESOCNUMBE",
    "PAYMENTADD1",
    "PAYMENTADD2",
    "PAYMENTADD4",
    "PAYMENTADD6",
    "PAYMENTPOSTCO",
    "PAYMENTMETHOD",
    "PAYMENTDATE",
    "AMOUNT_MONAMT",
    "PAYEEBANKCODE",
    "PAYEEACCOUNTN",
    "PAYEEACCOUNTT",
]
PEI_PAYMENT_DETAILS_FIELD_NAMES = ["PECLASSID", "PEINDEXID", "PAYMENTSTARTP", "PAYMENTENDPER"]
PEI_CLAIM_DETAILS_FIELD_NAMES = ["PECLASSID", "PEINDEXID", "ABSENCECASENU"]

REQUESTED_ABSENCE_FIELD_NAMES = [
    "ABSENCE_CASENUMBER",
    "NOTIFICATION_CASENUMBER",
    "ABSENCE_CASESTATUS",
    "ABSENCEPERIOD_START",
    "ABSENCEPERIOD_END",
    "LEAVEREQUEST_EVIDENCERESULTTYPE",
    "EMPLOYEE_CUSTOMERNO",
    "EMPLOYER_CUSTOMERNO",
]
EMPLOYEE_FEED_FIELD_NAMES = [
    "C",
    "I",
    "DEFPAYMENTPREF",
    "CUSTOMERNO",
    "NATINSNO",
    "DATEOFBIRTH",
    "PAYMENTMETHOD",
    "ADDRESS1",
    "ADDRESS2",
    "ADDRESS4",
    "ADDRESS6",
    "POSTCODE",
    "SORTCODE",
    "ACCOUNTNO",
    "ACCOUNTTYPE",
]
LEAVE_PLAN_FIELD_NAMES = [
    "ABSENCE_CASENUMBER",
    "LEAVETYPE",
]

FINEOS_PAYMENT_EXPORT_FILES = {}
FINEOS_PAYMENT_EXPORT_FILES[PEI_FILE_NAME] = PEI_FIELD_NAMES
FINEOS_PAYMENT_EXPORT_FILES[PEI_PAYMENT_DETAILS_FILE_NAME] = PEI_PAYMENT_DETAILS_FIELD_NAMES
FINEOS_PAYMENT_EXPORT_FILES[PEI_CLAIM_DETAILS_FILE_NAME] = PEI_CLAIM_DETAILS_FIELD_NAMES
FINEOS_PAYMENT_EXPORT_FILES[REQUESTED_ABSENCES_FILE_NAME] = REQUESTED_ABSENCE_FIELD_NAMES
FINEOS_PAYMENT_EXPORT_FILES[EMPLOYEE_FEED_FILE_NAME] = EMPLOYEE_FEED_FIELD_NAMES
FINEOS_PAYMENT_EXPORT_FILES[LEAVE_PLAN_FILE_NAME] = LEAVE_PLAN_FIELD_NAMES


# == Utility data classes
@dataclass
class FineosPaymentsExportCsvWriter:
    file_name: str
    file_path: str
    file: io.TextIOWrapper
    csv_writer: csv.DictWriter


@dataclass
class GenerateConfig:
    folder_path: str
    employee_count: int = 10
    ssn_id_base: int = 100000000
    fein_id_base: int = 250000000
    random_seed: int = 1111


def _create_files(folder_path: str, date_prefix: str) -> Dict[str, FineosPaymentsExportCsvWriter]:
    file_name_to_fineos_payment_file_info = {}
    for file_name, column_names in FINEOS_PAYMENT_EXPORT_FILES.items():
        csv_file_path = os.path.join(folder_path, f"{date_prefix}{file_name}")
        csv_file = file_util.write_file(csv_file_path, mode="w")
        csv_writer = csv.DictWriter(csv_file, fieldnames=column_names)
        csv_writer.writeheader()

        file_name_to_fineos_payment_file_info[file_name] = FineosPaymentsExportCsvWriter(
            file_name=file_name, file_path=csv_file_path, file=csv_file, csv_writer=csv_writer
        )

    return file_name_to_fineos_payment_file_info


def _create_db_models(
    db_session: db.Session,
    ssn: str,
    fein: str,
    fineos_employer_id: str,
    absence_case_id: str,
    add_eft=True,
) -> (Employee, Employer, Claim):

    eft = None
    if add_eft:
        eft = EftFactory.create()

    mailing_address = AddressFactory.create()

    ctr_address_pair = CtrAddressPairFactory.create(fineos_address=mailing_address)
    employee = EmployeeFactory.create(
        tax_identifier=TaxIdentifier(tax_identifier=ssn), ctr_address_pair=ctr_address_pair, eft=eft
    )

    employee.addresses = [
        EmployeeAddress(employee_id=employee.employee_id, address_id=mailing_address.address_id)
    ]

    employer = EmployerFactory.create(employer_fein=fein, fineos_employer_id=fineos_employer_id)
    claim = ClaimFactory.create(
        employer_id=employer.employer_id, employee=employee, fineos_absence_id=absence_case_id,
    )

    return employee, employer, claim


def _generate_single_fineos_payment_row(
    employee: Employee,
    claim: Claim,
    ci_index: CiIndex,
    file_name_to_file_info: Dict[str, FineosPaymentsExportCsvWriter],
    missing_field: bool = False,
    invalid_row: bool = False,
):
    # Get file writers
    pei_csv_writer = file_name_to_file_info[PEI_FILE_NAME].csv_writer
    pei_payment_details_csv_writer = file_name_to_file_info[
        PEI_PAYMENT_DETAILS_FILE_NAME
    ].csv_writer
    pei_claim_details_csv_writer = file_name_to_file_info[PEI_CLAIM_DETAILS_FILE_NAME].csv_writer

    # PEI File
    is_eft = employee.eft is not None
    address = employee.ctr_address_pair.fineos_address

    payment_date = datetime.now()
    vpei_row = OrderedDict()
    vpei_row["C"] = ci_index.c
    vpei_row["I"] = ci_index.i
    vpei_row["PAYEESOCNUMBE"] = employee.tax_identifier.tax_identifier
    vpei_row["PAYMENTADD1"] = address.address_line_one
    vpei_row["PAYMENTADD2"] = address.address_line_two
    vpei_row["PAYMENTADD4"] = address.city
    vpei_row["PAYMENTADD6"] = address.geo_state.geo_state_description
    vpei_row["PAYMENTPOSTCO"] = address.zip_code
    vpei_row["PAYMENTMETHOD"] = (
        PaymentMethod.ACH.payment_method_description
        if is_eft
        else PaymentMethod.CHECK.payment_method_description
    )
    vpei_row["PAYMENTDATE"] = payment_date.strftime("%Y-%m-%d %H:%M:%S")
    vpei_row["AMOUNT_MONAMT"] = "{:.2f}".format(1000 * random.uniform(0.3, 0.95))

    if missing_field:
        vpei_row["AMOUNT_MONAMT"] = ""

    if is_eft:
        vpei_row["PAYEEBANKCODE"] = employee.eft.routing_nbr
        vpei_row["PAYEEACCOUNTN"] = employee.eft.account_nbr
        vpei_row["PAYEEACCOUNTT"] = employee.eft.bank_account_type.bank_account_type_description

    pei_csv_writer.writerow(vpei_row)

    # PEI Payment Details File
    payment_start = payment_date - timedelta(weeks=random.randint(2, 12))
    payment_end = payment_date + timedelta(weeks=random.randint(2, 12))

    vpei_payment_details_row = OrderedDict()
    vpei_payment_details_row["PECLASSID"] = ci_index.c
    vpei_payment_details_row["PEINDEXID"] = ci_index.i
    vpei_payment_details_row["PAYMENTSTARTP"] = payment_start.strftime("%Y-%m-%d %H:%M:%S")
    vpei_payment_details_row["PAYMENTENDPER"] = payment_end.strftime("%Y-%m-%d %H:%M:%S")

    if invalid_row:
        vpei_payment_details_row["PECLASSID"] = "NON_EXISTENT_C_ID"
        vpei_payment_details_row["PEINDEXID"] = "NON_EXISTENT_I_ID"

    pei_payment_details_csv_writer.writerow(vpei_payment_details_row)

    # PEI Claim Details File
    vpei_claim_details_row = OrderedDict()
    vpei_claim_details_row["PECLASSID"] = ci_index.c
    vpei_claim_details_row["PEINDEXID"] = ci_index.i
    vpei_claim_details_row["ABSENCECASENU"] = claim.fineos_absence_id

    pei_claim_details_csv_writer.writerow(vpei_claim_details_row)


def _generate_single_fineos_vendor_row(
    employee: Employee,
    employer: Employer,
    claim: Claim,
    ci_index: CiIndex,
    employee_customer_number: str,
    file_name_to_file_info: Dict[str, FineosPaymentsExportCsvWriter],
    missing_field: bool = False,
    invalid_row: bool = False,
):
    # Get file writers
    requested_absence_csv_writer = file_name_to_file_info[REQUESTED_ABSENCES_FILE_NAME].csv_writer
    employee_feed_csv_writer = file_name_to_file_info[EMPLOYEE_FEED_FILE_NAME].csv_writer
    leave_plan_csv_writer = file_name_to_file_info[LEAVE_PLAN_FILE_NAME].csv_writer

    # shared variables
    is_eft = employee.eft is not None
    address = employee.ctr_address_pair.fineos_address

    # Requested Absence file
    application_date = datetime.now()
    absence_start = application_date + timedelta(weeks=random.randint(1, 3))
    absence_end = application_date + timedelta(weeks=random.randint(4, 12))

    requested_absence_row = {}
    requested_absence_row["ABSENCE_CASENUMBER"] = claim.fineos_absence_id
    requested_absence_row["NOTIFICATION_CASENUMBER"] = claim.fineos_absence_id[:8]
    requested_absence_row[
        "ABSENCE_CASESTATUS"
    ] = AbsenceStatus.ADJUDICATION.absence_status_description
    requested_absence_row["ABSENCEPERIOD_START"] = absence_start.strftime("%Y-%m-%d %H:%M:%S")
    requested_absence_row["ABSENCEPERIOD_END"] = absence_end.strftime("%Y-%m-%d %H:%M:%S")
    requested_absence_row["LEAVEREQUEST_EVIDENCERESULTTYPE"] = (
        "Satisfied" if random.random() < 0.8 else "Not Satisfied"
    )
    requested_absence_row["EMPLOYEE_CUSTOMERNO"] = employee_customer_number
    requested_absence_row["EMPLOYER_CUSTOMERNO"] = employer.fineos_employer_id

    requested_absence_csv_writer.writerow(requested_absence_row)

    # Employee Feed file
    employee_feed_row = {}
    employee_feed_row["C"] = ci_index.c
    employee_feed_row["I"] = ci_index.i
    employee_feed_row["DEFPAYMENTPREF"] = "Y" if random.random() < 0.8 else "N"
    employee_feed_row["CUSTOMERNO"] = employee_customer_number
    employee_feed_row["NATINSNO"] = employee.tax_identifier.tax_identifier
    employee_feed_row["DATEOFBIRTH"] = datetime(
        1978, random.randint(1, 12), 1, 11, 30, 00
    ).strftime("%Y-%m-%d %H:%M:%S")
    employee_feed_row["PAYMENTMETHOD"] = (
        PaymentMethod.ACH.payment_method_description
        if is_eft
        else PaymentMethod.CHECK.payment_method_description
    )
    employee_feed_row["ADDRESS1"] = address.address_line_one
    employee_feed_row["ADDRESS2"] = address.address_line_two
    employee_feed_row["ADDRESS4"] = address.city
    employee_feed_row["ADDRESS6"] = address.geo_state.geo_state_description
    employee_feed_row["POSTCODE"] = address.zip_code

    if is_eft:
        employee_feed_row["SORTCODE"] = employee.eft.routing_nbr
        employee_feed_row["ACCOUNTNO"] = employee.eft.account_nbr
        employee_feed_row[
            "ACCOUNTTYPE"
        ] = employee.eft.bank_account_type.bank_account_type_description

    employee_feed_csv_writer.writerow(employee_feed_row)

    # Leave Plan file
    leave_plan_row = {}
    leave_plan_row["ABSENCE_CASENUMBER"] = claim.fineos_absence_id
    leave_plan_row["LEAVETYPE"] = random.sample(
        [
            "EE Medical Leave",
            "Family Medical Leave",
            ClaimType.MILITARY_LEAVE.claim_type_description,
        ],
        1,
    )[0]

    leave_plan_csv_writer.writerow(leave_plan_row)


def generate(db_session: db.Session, config: GenerateConfig):
    random.seed(config.random_seed)

    try:
        date_prefix = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-")

        file_name_to_file_info: Dict[str, FineosPaymentsExportCsvWriter] = _create_files(
            config.folder_path, date_prefix
        )

        # generate and write csv rows
        ssn = config.ssn_id_base + 1
        fein = config.fein_id_base + 1

        for i in range(int(config.employee_count)):
            if i % 100 == 0:
                logger.info("generated %i employees", i)

            ssn_part_str = str(ssn)[2:]
            fein_part_str = str(fein)[2:]

            ci_index = CiIndex(ssn_part_str.rjust(9, "1"), fein_part_str.rjust(9, "2"))
            fineos_employer_id = int(fein_part_str.rjust(9, "3"))
            absence_case_id = f"NTN-{ssn_part_str.rjust(9, '4')}-ABS-01"
            employee_customer_number = ssn_part_str.rjust(9, "5")

            add_eft = random.random() < 0.5
            employee, employer, claim = _create_db_models(
                db_session, ssn, fein, fineos_employer_id, absence_case_id, add_eft=add_eft
            )

            if random.random() < 0.2:  # existing payment
                PaymentFactory.create(claim=claim)

            invalid_row = False
            missing_field = random.random() < 0.2
            if not missing_field:
                invalid_row = random.random() < 0.2

            _generate_single_fineos_payment_row(
                employee,
                claim,
                ci_index,
                file_name_to_file_info,
                missing_field=missing_field,
                invalid_row=invalid_row,
            )

            _generate_single_fineos_vendor_row(
                employee,
                employer,
                claim,
                ci_index,
                employee_customer_number,
                file_name_to_file_info,
                missing_field=missing_field,
                invalid_row=invalid_row,
            )

            ssn += 1
            fein += 1

        # flush buffer to csv files
        for file_info in file_name_to_file_info.values():
            file_info.file.close()

    except Exception as e:
        logger.exception(e)


def main():
    logging.init(__name__)

    db_session = db.init(sync_lookups=True)
    db.models.factories.db_session = db_session

    args = parser.parse_args()
    folder_path = args.folder
    employee_count = args.count
    fein_id_base = int(args.fein)
    ssn_id_base = int(args.ssn)

    config = GenerateConfig(
        folder_path=folder_path,
        employee_count=employee_count,
        fein_id_base=fein_id_base,
        ssn_id_base=ssn_id_base,
    )
    generate(db_session, config)

    logger.info("done generating files")
