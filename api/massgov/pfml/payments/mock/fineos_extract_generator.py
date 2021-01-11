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
from typing import Any, Dict, Optional

import massgov.pfml.db as db
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    BankAccountType,
    Claim,
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
parser.add_argument("--cvalue", type=int, default=5000, help="Base C value for FINEOS records")
parser.add_argument(
    "--employeecustomernumber",
    type=int,
    default=100,
    help="Base employee customer number value for FINEOS records",
)
parser.add_argument(
    "--absencecaseid", type=int, default=250, help="Base absence case ID value for FINEOS records"
)

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
        csv_file = file_util.write_file(csv_file_path)
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
    address=None,
) -> (Employee, Employer, Claim):

    eft = None
    if add_eft:
        eft = EftFactory.create()

    mailing_address = AddressFactory.create()
    if address:
        mailing_address = address

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

    payment_date = payments_util.get_now()
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
    leave_type: Optional[str] = None,
    ssn: Optional[str] = None,
    unsatisfied_evidence_result_type: bool = False,
    no_default_payment_preference: bool = False,
    no_routing_number: bool = False,
    payment_method: Optional[str] = None,
    address_4: Optional[str] = None,
    address_6: Optional[str] = None,
):
    # Get file writers
    requested_absence_csv_writer = file_name_to_file_info[REQUESTED_ABSENCES_FILE_NAME].csv_writer
    employee_feed_csv_writer = file_name_to_file_info[EMPLOYEE_FEED_FILE_NAME].csv_writer
    leave_plan_csv_writer = file_name_to_file_info[LEAVE_PLAN_FILE_NAME].csv_writer

    # shared variables
    is_eft = employee.eft is not None
    address = employee.ctr_address_pair.fineos_address

    # Requested Absence file
    application_date = payments_util.get_now()
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
    # requested_absence_row["LEAVEREQUEST_EVIDENCERESULTTYPE"] = (
    #     "Satisfied" if random.random() < 0.8 else "Not Satisfied"
    # )
    requested_absence_row["LEAVEREQUEST_EVIDENCERESULTTYPE"] = (
        "Not Satisfied" if unsatisfied_evidence_result_type else "Satisfied"
    )

    requested_absence_row["EMPLOYEE_CUSTOMERNO"] = employee_customer_number
    requested_absence_row["EMPLOYER_CUSTOMERNO"] = employer.fineos_employer_id

    requested_absence_csv_writer.writerow(requested_absence_row)

    if ssn == "EMPTY":
        ssn_to_use = ""
    elif not ssn:
        ssn_to_use = employee.tax_identifier.tax_identifier
    else:
        ssn_to_use = ssn

    # Employee Feed file
    employee_feed_row = {}
    employee_feed_row["C"] = ci_index.c
    employee_feed_row["I"] = ci_index.i
    employee_feed_row["DEFPAYMENTPREF"] = "N" if no_default_payment_preference else "Y"
    employee_feed_row["CUSTOMERNO"] = employee_customer_number
    employee_feed_row["NATINSNO"] = ssn_to_use
    employee_feed_row["DATEOFBIRTH"] = datetime(
        1978, random.randint(1, 12), 1, 11, 30, 00
    ).strftime("%Y-%m-%d %H:%M:%S")
    employee_feed_row["PAYMENTMETHOD"] = (
        "Elec Funds Transfer" if payment_method == "ACH" else payment_method
    )
    employee_feed_row["ADDRESS1"] = address.address_line_one
    employee_feed_row["ADDRESS2"] = address.address_line_two
    employee_feed_row["ADDRESS4"] = address_4
    employee_feed_row["ADDRESS6"] = address_6
    employee_feed_row["POSTCODE"] = address.zip_code

    if is_eft:
        employee_feed_row["SORTCODE"] = "" if no_routing_number else employee.eft.routing_nbr
        employee_feed_row["ACCOUNTNO"] = employee.eft.account_nbr
        employee_feed_row[
            "ACCOUNTTYPE"
        ] = employee.eft.bank_account_type.bank_account_type_description

    employee_feed_csv_writer.writerow(employee_feed_row)

    # Leave Plan file
    leave_plan_row = {}
    leave_plan_row["ABSENCE_CASENUMBER"] = claim.fineos_absence_id
    leave_plan_row["LEAVETYPE"] = random.sample(
        ["EE Medical Leave", "Family Medical Leave", "Military Related Leave",], 1,
    )[0]

    if leave_type:
        leave_plan_row["LEAVETYPE"] = leave_type

    leave_plan_csv_writer.writerow(leave_plan_row)


def generate(db_session: db.Session, config: GenerateConfig):
    random.seed(config.random_seed)

    try:
        date_prefix = payments_util.get_now().strftime("%Y-%m-%d-%H-%M-%S-")
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
                db_session=db_session,
                ssn=ssn,
                fein=fein,
                fineos_employer_id=fineos_employer_id,
                absence_case_id=absence_case_id,
                add_eft=add_eft,
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
        raise e


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


def create_test_vendor_export():
    logging.init(__name__)

    db_session = db.init(sync_lookups=True)
    db.models.factories.db_session = db_session

    args = parser.parse_args()

    _generate_test_vendor_export(db_session, args)

    logger.info("done generating files")


FAMILY_LEAVE = "Family Medical Leave"
MEDICAL_LEAVE = "EE Medical Leave"

# Test cases described in this Google Doc:
# https://docs.google.com/document/d/1232xwedUI6d2WNVavRAM8r1GempjSNDlFX7KgzC1va8/edit#

# EmployeeA with real address, payment method is check, leave type is medical leave
employee_a = {
    "first_name": "Alex",
    "payee_payment_method": "Check",
    "leave_type": MEDICAL_LEAVE,
    "payment_address_1": "20 South Ave",
    "payment_address_2": "",
    "payment_address_4": "Burlington",
    "payment_address_6": "MA",
    "payment_post_code": "01803",
}

# EmployeeB with real address, payment method is check, leave type is bonding leave
employee_b = {
    "first_name": "Billie",
    "payee_payment_method": "Check",
    "leave_type": FAMILY_LEAVE,
    "payment_address_1": "177 Columbia St",
    "payment_address_2": "",
    "payment_address_4": "Adams",
    "payment_address_6": "MA",
    "payment_post_code": "01220",
}

# EmployeeC with real address, real routing number, fake bank account number, payment method is ACH, leave type is medical leave
employee_c = {
    "first_name": "Charlie",
    "payee_payment_method": "ACH",
    "leave_type": MEDICAL_LEAVE,
    "payee_aba_number": 211870935,
    "payee_account_type": "Checking",
    "payee_account_number": 123456789,
    "payment_address_1": "73 Mazzeo Dr",
    "payment_address_2": "Suite 230",
    "payment_address_4": "Randolph",
    "payment_address_6": "MA",
    "payment_post_code": "02368",
}

# EmployeeD with real address, real routing number, fake bank account number, payment method is ACH, leave type is bonding leave
employee_d = {
    "first_name": "Dana",
    "payee_payment_method": "ACH",
    "leave_type": FAMILY_LEAVE,
    "payee_aba_number": 211870935,
    "payee_account_type": "Saving",
    "payee_account_number": 234567890,
    "payment_address_1": "204 Massachusetts Ave",
    "payment_address_2": "#84",
    "payment_address_4": "Arlington",
    "payment_address_6": "MA",
    "payment_post_code": "02474",
}

# EmployeeE has non-existent SSN. No StateLog entry should be created.
employee_e = {**employee_c, "first_name": "Edie", "non-existent_ssn": True}

# EmployeeF has no data in the SSN column of the CSV
employee_f = {**employee_c, "first_name": "Frankie", "empty_ssn": True}

# EmployeeG payment method is debit card
employee_g = {**employee_c, "first_name": "Glenn", "payee_payment_method": "Debit"}

# EmployeeH address is missing required field (such as city)
employee_h = {**employee_c, "first_name": "Hunter", "payment_address_4": ""}

# EmployeeI address is improperly formatted (state is “Massachussetts” instead of “MA”)
employee_i = {**employee_c, "first_name": "Isa", "payment_address_6": "Massachussetts"}

# EmployeeJ has payment method is ACH, missing routing number
employee_j = {**employee_c, "first_name": "Jesse", "no_routing_number": True}

# EmployeeK is DEFPAYMENTPREF is “N” (create multiple payment methods for EmployeeJ)
employee_k = {
    "first_name": "Kennedy",
    "payee_payment_method": "ACH",
    "payee_aba_number": 211870935,
    "payee_account_type": "Checking",
    "payee_account_number": 345345345,
    "payment_address_1": "19 Summer St",
    "payment_address_2": "#2",
    "payment_address_4": "Maynard",
    "payment_address_6": "MA",
    "payment_post_code": "01754",
    "no_default_payment_preference": True,
}

# EmployeeL LEAVEREQUEST_EVIDENCERESULTTYPE != “Satisfied” (don’t ID proof someone)
employee_l = {
    "first_name": "Leslie",
    "payee_payment_method": "Check",
    "payment_address_1": "100 Charlton Rd",
    "payment_address_2": "",
    "payment_address_4": "Sturbridge",
    "payment_address_6": "MA",
    "payment_post_code": "01566",
    "unsatisfied_evidence_result_type": True,
}

test_cases = [
    # 1. has some records that validate and should be saved.
    employee_a,
    employee_b,
    employee_c,
    employee_d,
    # 2. has some records that are so invalid that a state log entry cannot be created for them
    # (https://github.com/EOLWD/pfml/pull/2483/files#r548455099).
    # These should be captured in logger.error/logger.exception
    employee_e,
    employee_f,
    # 3. has some records that are invalid, but a state log entry is created for them
    # (https://github.com/EOLWD/pfml/pull/2483/files#r548463121)
    employee_g,
    employee_h,
    employee_i,
    employee_j,
    # 4. Records that should be ignored
    employee_k,
    employee_l,
]


def _get_next_mock_data(key, data_provider):
    data_provider[key] += 1
    return data_provider[key]


def _generate_test_vendor_export(db_session: db.Session, args: Any):
    try:
        date_prefix = payments_util.get_now().strftime("%Y-%m-%d-%H-%M-%S-")
        file_name_to_file_info: Dict[str, FineosPaymentsExportCsvWriter] = _create_files(
            args.folder, date_prefix
        )

        MOCK_DATA_PROVIDER = {
            "c": args.cvalue,
            "i": 500,  # static start (c changes each run)
            "fein": args.fein,
            "ssn": args.ssn,
            "employer_customer_number": args.employeecustomernumber,
            "absence_case_id": args.absencecaseid,
        }

        for employee_data in test_cases:
            ssn = _get_next_mock_data("ssn", MOCK_DATA_PROVIDER)
            fein = _get_next_mock_data("fein", MOCK_DATA_PROVIDER)

            absence_case_base = _get_next_mock_data("absence_case_id", MOCK_DATA_PROVIDER)
            absence_case_id = f"NTN-{absence_case_base}-ABS-{absence_case_base}"
            employee_customer_number = _get_next_mock_data(
                "employer_customer_number", MOCK_DATA_PROVIDER
            )

            employee, employer, claim = _create_employee_employer_and_claim_from_data(
                db_session, ssn, fein, absence_case_id, employee_customer_number, employee_data
            )

            ci_index = CiIndex(
                _get_next_mock_data("c", MOCK_DATA_PROVIDER),
                _get_next_mock_data("i", MOCK_DATA_PROVIDER),
            )

            leave_type = employee_data.get("leave_type")
            if not leave_type:
                leave_type = FAMILY_LEAVE

            ssn_in_file = None
            if employee_data.get("non-existent_ssn"):
                ssn_in_file = "112319890"
            if employee_data.get("empty_ssn"):
                ssn_in_file = "EMPTY"  # We'll check for this in the subsequent method

            unsatisfied_evidence_result_type = False
            if employee_data.get("unsatisfied_evidence_result_type"):
                unsatisfied_evidence_result_type = True

            no_default_payment_preference = False
            if employee_data.get("no_default_payment_preference"):
                no_default_payment_preference = True

            no_routing_number = False
            if employee_data.get("no_routing_number"):
                no_routing_number = True

            _generate_single_fineos_vendor_row(
                employee=employee,
                employer=employer,
                claim=claim,
                ci_index=ci_index,
                employee_customer_number=employee_customer_number,
                file_name_to_file_info=file_name_to_file_info,
                leave_type=leave_type,
                ssn=ssn_in_file,
                unsatisfied_evidence_result_type=unsatisfied_evidence_result_type,
                no_default_payment_preference=no_default_payment_preference,
                no_routing_number=no_routing_number,
                address_4=employee_data.get("payment_address_4"),
                address_6=employee_data.get("payment_address_6"),
                payment_method=employee_data.get("payee_payment_method"),
            )

        # flush buffer to csv files
        for file_info in file_name_to_file_info.values():
            file_info.file.close()

    except Exception as e:
        logger.exception(e)
        raise e


def _create_employee_employer_and_claim_from_data(
    db_session: db.Session,
    ssn: str,
    fein: str,
    absence_case_id: str,
    employee_customer_number: str,
    data: dict,
) -> (Employee, Employer, Claim):

    eft = None
    payment_method_id = PaymentMethod.CHECK.payment_method_id
    if data.get("payee_payment_method") and data.get("payee_payment_method") == "ACH":
        payment_method_id = PaymentMethod.ACH.payment_method_id

        account_type_id = BankAccountType.CHECKING.bank_account_type_id
        if data.get("payee_account_type") and data.get("payee_account_type") == "Saving":
            account_type_id = BankAccountType.SAVINGS.bank_account_type_id

        eft = EftFactory.create(
            routing_nbr=data["payee_aba_number"],
            account_nbr=data["payee_account_number"],
            bank_account_type_id=account_type_id,
        )

    if data.get("payee_payment_method") and data.get("payee_payment_method") == "Debit":
        payment_method_id = PaymentMethod.DEBIT.payment_method_id

    mailing_address = AddressFactory()
    if data.get("payment_address_1"):
        mailing_address = AddressFactory(
            address_line_one=data["payment_address_1"],
            address_line_two=data["payment_address_2"],
            city=data["payment_address_4"],
            geo_state_id=1,
            zip_code=data["payment_post_code"],
        )

    ctr_address_pair = CtrAddressPairFactory.create(fineos_address=mailing_address)
    employee = EmployeeFactory.create(
        first_name=data["first_name"],
        tax_identifier=TaxIdentifier(tax_identifier=ssn),
        ctr_address_pair=ctr_address_pair,
        eft=eft,
        payment_method_id=payment_method_id,
    )

    employee.addresses = [EmployeeAddress(employee=employee, address=mailing_address)]

    employer = EmployerFactory.create(
        employer_fein=fein, fineos_employer_id=employee_customer_number
    )
    claim = ClaimFactory.create(
        employer_id=employer.employer_id, employee=employee, fineos_absence_id=absence_case_id,
    )

    return employee, employer, claim
