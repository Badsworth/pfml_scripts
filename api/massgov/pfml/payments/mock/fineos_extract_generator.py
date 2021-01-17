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
from typing import Dict, List

import massgov.pfml.db as db
import massgov.pfml.payments.mock.payments_test_scenario_generator as scenario_generator
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import AbsenceStatus, ClaimType, PaymentMethod
from massgov.pfml.payments.mock.payments_test_scenario_generator import (
    ScenarioData,
    ScenarioDataConfig,
    ScenarioName,
    ScenarioNameWithCount,
)

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
parser.add_argument(
    "--folder", type=str, default="payments_files", help="Output folder for generated files"
)
parser.add_argument(
    "--fein", type=fein_validator, default=100000000, help="Base FEIN for employers"
)
parser.add_argument("--ssn", type=ssn_validator, default=250000000, help="Base SSN for employees")

# == Constants
CLAIM_TYPE_TRANSLATION = {}
CLAIM_TYPE_TRANSLATION[ClaimType.FAMILY_LEAVE.claim_type_description] = "Family"
CLAIM_TYPE_TRANSLATION[ClaimType.MEDICAL_LEAVE.claim_type_description] = "Medical"
CLAIM_TYPE_TRANSLATION[ClaimType.MILITARY_LEAVE.claim_type_description] = "Military Related Leave"

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

FINEOS_EXPORT_FILES = {}
FINEOS_EXPORT_FILES[PEI_FILE_NAME] = PEI_FIELD_NAMES
FINEOS_EXPORT_FILES[PEI_PAYMENT_DETAILS_FILE_NAME] = PEI_PAYMENT_DETAILS_FIELD_NAMES
FINEOS_EXPORT_FILES[PEI_CLAIM_DETAILS_FILE_NAME] = PEI_CLAIM_DETAILS_FIELD_NAMES
FINEOS_EXPORT_FILES[REQUESTED_ABSENCES_FILE_NAME] = REQUESTED_ABSENCE_FIELD_NAMES
FINEOS_EXPORT_FILES[EMPLOYEE_FEED_FILE_NAME] = EMPLOYEE_FEED_FIELD_NAMES
FINEOS_EXPORT_FILES[LEAVE_PLAN_FILE_NAME] = LEAVE_PLAN_FIELD_NAMES

FINEOS_VENDOR_EXPORT_FILES = [
    REQUESTED_ABSENCES_FILE_NAME,
    EMPLOYEE_FEED_FILE_NAME,
    LEAVE_PLAN_FILE_NAME,
]
FINEOS_PAYMENT_EXPORT_FILES = [
    PEI_FILE_NAME,
    PEI_PAYMENT_DETAILS_FILE_NAME,
    PEI_CLAIM_DETAILS_FILE_NAME,
]


# == Utility data classes
@dataclass
class FineosPaymentsExportCsvWriter:
    file_name: str
    file_path: str
    file: io.TextIOWrapper
    csv_writer: csv.DictWriter


def _create_files(
    folder_path: str, date_prefix: str, expected_file_names: List[str]
) -> Dict[str, FineosPaymentsExportCsvWriter]:
    file_name_to_fineos_payment_file_info = {}
    for file_name, column_names in FINEOS_EXPORT_FILES.items():
        if file_name not in expected_file_names:
            continue

        csv_file_path = os.path.join(folder_path, f"{date_prefix}{file_name}")
        csv_file = file_util.write_file(csv_file_path)
        csv_writer = csv.DictWriter(csv_file, fieldnames=column_names)
        csv_writer.writeheader()

        file_name_to_fineos_payment_file_info[file_name] = FineosPaymentsExportCsvWriter(
            file_name=file_name, file_path=csv_file_path, file=csv_file, csv_writer=csv_writer
        )

    return file_name_to_fineos_payment_file_info


def _generate_single_fineos_payment_row(
    scenario_data: scenario_generator.ScenarioData,
    file_name_to_file_info: Dict[str, FineosPaymentsExportCsvWriter],
):
    # Get file writers
    pei_csv_writer = file_name_to_file_info[PEI_FILE_NAME].csv_writer
    pei_payment_details_csv_writer = file_name_to_file_info[
        PEI_PAYMENT_DETAILS_FILE_NAME
    ].csv_writer
    pei_claim_details_csv_writer = file_name_to_file_info[PEI_CLAIM_DETAILS_FILE_NAME].csv_writer

    # Get db models
    employee = scenario_data.employee
    claim = scenario_data.claim

    # PEI File
    is_eft = employee.eft is not None
    address = employee.ctr_address_pair.fineos_address

    payment_date = payments_util.get_now()
    vpei_row = OrderedDict()
    vpei_row["C"] = scenario_data.ci_index.c
    vpei_row["I"] = scenario_data.ci_index.i
    vpei_row["PAYEESOCNUMBE"] = employee.tax_identifier.tax_identifier
    vpei_row["PAYMENTADD1"] = address.address_line_one
    vpei_row["PAYMENTADD2"] = address.address_line_two
    vpei_row["PAYMENTADD4"] = address.city
    vpei_row["PAYMENTADD6"] = (
        address.geo_state_text
        if address.geo_state_id is None
        else address.geo_state.geo_state_description
    )
    vpei_row["PAYMENTPOSTCO"] = address.zip_code
    vpei_row["PAYMENTMETHOD"] = (
        PaymentMethod.ACH.payment_method_description
        if is_eft
        else PaymentMethod.CHECK.payment_method_description
    )
    vpei_row["PAYMENTDATE"] = payment_date.strftime("%Y-%m-%d %H:%M:%S")
    vpei_row["AMOUNT_MONAMT"] = "{:.2f}".format(scenario_data.payment_amount)

    # TODO do we still want this
    # if missing_field:
    #     vpei_row["AMOUNT_MONAMT"] = ""

    if is_eft:
        vpei_row["PAYEEBANKCODE"] = employee.eft.routing_nbr
        vpei_row["PAYEEACCOUNTN"] = employee.eft.account_nbr
        vpei_row["PAYEEACCOUNTT"] = employee.eft.bank_account_type.bank_account_type_description

    pei_csv_writer.writerow(vpei_row)

    # PEI Payment Details File
    payment_start = payment_date - timedelta(weeks=random.randint(2, 12))
    payment_end = payment_date + timedelta(weeks=random.randint(2, 12))

    vpei_payment_details_row = OrderedDict()
    vpei_payment_details_row["PECLASSID"] = scenario_data.ci_index.c
    vpei_payment_details_row["PEINDEXID"] = scenario_data.ci_index.i
    vpei_payment_details_row["PAYMENTSTARTP"] = payment_start.strftime("%Y-%m-%d %H:%M:%S")
    vpei_payment_details_row["PAYMENTENDPER"] = payment_end.strftime("%Y-%m-%d %H:%M:%S")

    # TODO do we still want this
    # if invalid_row:
    #     vpei_payment_details_row["PECLASSID"] = "NON_EXISTENT_C_ID"
    #     vpei_payment_details_row["PEINDEXID"] = "NON_EXISTENT_I_ID"

    pei_payment_details_csv_writer.writerow(vpei_payment_details_row)

    # PEI Claim Details File
    vpei_claim_details_row = OrderedDict()
    vpei_claim_details_row["PECLASSID"] = scenario_data.ci_index.c
    vpei_claim_details_row["PEINDEXID"] = scenario_data.ci_index.i
    vpei_claim_details_row["ABSENCECASENU"] = claim.fineos_absence_id

    pei_claim_details_csv_writer.writerow(vpei_claim_details_row)


def _generate_single_fineos_vendor_row(
    scenario_data: scenario_generator.ScenarioData,
    file_name_to_file_info: Dict[str, FineosPaymentsExportCsvWriter],
):
    # Get file writers
    requested_absence_csv_writer = file_name_to_file_info[REQUESTED_ABSENCES_FILE_NAME].csv_writer
    employee_feed_csv_writer = file_name_to_file_info[EMPLOYEE_FEED_FILE_NAME].csv_writer
    leave_plan_csv_writer = file_name_to_file_info[LEAVE_PLAN_FILE_NAME].csv_writer

    # Get db models
    scenario_descriptor = scenario_data.scenario_descriptor
    employee = scenario_data.employee
    employer = scenario_data.employer
    claim = scenario_data.claim

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
    requested_absence_row["LEAVEREQUEST_EVIDENCERESULTTYPE"] = (
        "Not Satisfied" if not scenario_descriptor.evidence_satisfied else "Satisfied"
    )

    requested_absence_row["EMPLOYEE_CUSTOMERNO"] = scenario_data.employee_customer_number
    requested_absence_row["EMPLOYER_CUSTOMERNO"] = employer.fineos_employer_id

    requested_absence_csv_writer.writerow(requested_absence_row)

    if scenario_descriptor.missing_ssn:
        ssn_to_use = ""
    else:
        ssn_to_use = employee.tax_identifier.tax_identifier

    # Employee Feed file
    employee_feed_row = {}
    employee_feed_row["C"] = scenario_data.ci_index.c
    employee_feed_row["I"] = scenario_data.ci_index.i
    employee_feed_row["DEFPAYMENTPREF"] = (
        "N" if not scenario_descriptor.default_payment_preference else "Y"
    )
    employee_feed_row["CUSTOMERNO"] = scenario_data.employee_customer_number
    employee_feed_row["NATINSNO"] = ssn_to_use
    employee_feed_row["DATEOFBIRTH"] = datetime(
        1978, random.randint(1, 12), 1, 11, 30, 00
    ).strftime("%Y-%m-%d %H:%M:%S")
    employee_feed_row["PAYMENTMETHOD"] = (
        "Elec Funds Transfer"
        if scenario_descriptor.payee_payment_method == PaymentMethod.ACH
        else scenario_descriptor.payee_payment_method.payment_method_description
    )
    employee_feed_row["ADDRESS1"] = address.address_line_one
    employee_feed_row["ADDRESS2"] = address.address_line_two
    employee_feed_row["ADDRESS4"] = address.city
    employee_feed_row["ADDRESS6"] = (
        address.geo_state_text
        if address.geo_state_id is None
        else address.geo_state.geo_state_description
    )
    employee_feed_row["POSTCODE"] = address.zip_code

    if is_eft:
        employee_feed_row["SORTCODE"] = (
            "" if scenario_descriptor.missing_routing else employee.eft.routing_nbr
        )
        employee_feed_row["ACCOUNTNO"] = employee.eft.account_nbr
        employee_feed_row[
            "ACCOUNTTYPE"
        ] = employee.eft.bank_account_type.bank_account_type_description

    employee_feed_csv_writer.writerow(employee_feed_row)

    # Leave Plan file
    # TODO remove this file - no longer used
    leave_plan_row = {}
    leave_plan_row["ABSENCE_CASENUMBER"] = claim.fineos_absence_id
    # TODO use in EmployeeFeed file column
    leave_plan_row["LEAVETYPE"] = CLAIM_TYPE_TRANSLATION[
        scenario_descriptor.leave_type.claim_type_description
    ]

    leave_plan_csv_writer.writerow(leave_plan_row)


def generate_vendor_extract_files(
    scenario_data_set: List[ScenarioData], folder_path, date_prefix: str
):
    file_name_to_file_info: Dict[str, FineosPaymentsExportCsvWriter] = _create_files(
        folder_path, date_prefix, FINEOS_VENDOR_EXPORT_FILES
    )

    for scenario_data in scenario_data_set:
        _generate_single_fineos_vendor_row(scenario_data, file_name_to_file_info)

    # TODO better abstraction
    for file_info in file_name_to_file_info.values():
        file_info.file.close()


def generate_payment_extract_files(
    scenario_data_set: List[ScenarioData], folder_path, date_prefix: str
):
    file_name_to_file_info: Dict[str, FineosPaymentsExportCsvWriter] = _create_files(
        folder_path, date_prefix, FINEOS_PAYMENT_EXPORT_FILES
    )

    for scenario_data in scenario_data_set:
        _generate_single_fineos_payment_row(scenario_data, file_name_to_file_info)

    # TODO better abstraction
    for file_info in file_name_to_file_info.values():
        file_info.file.close()


def generate(config: ScenarioDataConfig, folder_path: str):
    # Generate the data set
    scenario_dataset = scenario_generator.generate_scenario_dataset(config)

    # Generate the files with the same date prefix
    date_prefix = payments_util.get_now().strftime("%Y-%m-%d-%H-%M-%S-")
    generate_vendor_extract_files(scenario_dataset, folder_path, date_prefix)
    generate_payment_extract_files(scenario_dataset, folder_path, date_prefix)


DEFAULT_SCENARIOS_CONFIG: List[ScenarioNameWithCount] = [
    ScenarioNameWithCount(ScenarioName.SCENARIO_A, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_B, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_C, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_D, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_E, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_F, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_G, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_H, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_I, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_J, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_K, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_L, 1),
]


def main():
    # generate sample
    logging.init(__name__)

    db_session = db.init(sync_lookups=True)
    db.models.factories.db_session = db_session

    args = parser.parse_args()
    folder_path = args.folder
    fein_id_base = int(args.fein)
    ssn_id_base = int(args.ssn)

    config = ScenarioDataConfig(
        fein_id_base=fein_id_base,
        ssn_id_base=ssn_id_base,
        scenario_config=DEFAULT_SCENARIOS_CONFIG,
    )
    generate(config, folder_path)
