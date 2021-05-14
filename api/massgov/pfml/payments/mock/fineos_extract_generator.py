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
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List

import massgov.pfml.db as db
import massgov.pfml.payments.mock.payments_test_scenario_generator as scenario_generator
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import AbsenceStatus, ClaimType, PaymentMethod
from massgov.pfml.db.models.factories import TaxIdentifierFactory
from massgov.pfml.payments.mock.payments_test_scenario_generator import (
    SCENARIO_DESCRIPTORS,
    ScenarioData,
    ScenarioDataConfig,
    ScenarioNameWithCount,
)
from massgov.pfml.util.sentry import initialize_sentry

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
CLAIM_TYPE_TRANSLATION[ClaimType.MEDICAL_LEAVE.claim_type_description] = "Employee"
CLAIM_TYPE_TRANSLATION[ClaimType.MILITARY_LEAVE.claim_type_description] = "Family"

# == CSV file constants
# TODO use file name contats in payment and vendor modules
PEI_FILE_NAME = "vpei.csv"
PEI_PAYMENT_DETAILS_FILE_NAME = "vpeipaymentdetails.csv"
PEI_CLAIM_DETAILS_FILE_NAME = "vpeiclaimdetails.csv"
REQUESTED_ABSENCE_SOM_FILE_NAME = "VBI_REQUESTEDABSENCE_SOM.csv"
REQUESTED_ABSENCE_FILE_NAME = "VBI_REQUESTEDABSENCE.csv"
EMPLOYEE_FEED_FILE_NAME = "Employee_feed.csv"
LEAVE_PLAN_FILE_NAME = "LeavePlan_info.csv"

PEI_FIELD_NAMES = [
    "C",
    "I",
    "PAYEESOCNUMBE",
    "PAYEEFULLNAME",
    "PAYEECUSTOMER",
    "EVENTTYPE",
    "PAYMENTADD1",
    "PAYMENTADD2",
    "PAYMENTADD4",
    "PAYMENTADD6",
    "PAYMENTPOSTCO",
    "PAYMENTMETHOD",
    "PAYMENTDATE",
    "AMOUNT_MONAMT",
    "PAYEEBANKSORT",
    "PAYEEACCOUNTN",
    "PAYEEACCOUNTT",
]
PEI_PAYMENT_DETAILS_FIELD_NAMES = ["PECLASSID", "PEINDEXID", "PAYMENTSTARTP", "PAYMENTENDPER"]
PEI_CLAIM_DETAILS_FIELD_NAMES = ["PECLASSID", "PEINDEXID", "ABSENCECASENU", "LEAVEREQUESTI"]

REQUESTED_ABSENCE_SOM_FIELD_NAMES = [
    "ABSENCE_CASENUMBER",
    "NOTIFICATION_CASENUMBER",
    "ABSENCEPERIOD_START",
    "ABSENCEPERIOD_END",
    "LEAVEREQUEST_EVIDENCERESULTTYPE",
    "EMPLOYEE_CUSTOMERNO",
]
REQUESTED_ABSENCE_FIELD_NAMES = [
    "ABSENCE_CASENUMBER",
    "LEAVEREQUEST_ID",
    "LEAVEREQUEST_DECISION",
    "ABSENCE_CASECREATIONDATE",
    "ABSENCEREASON_NAME",
    "ABSENCE_CASESTATUS",
    "EMPLOYER_CUSTOMERNO",
    "ABSENCEREASON_COVERAGE",
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
FINEOS_EXPORT_FILES[REQUESTED_ABSENCE_SOM_FILE_NAME] = REQUESTED_ABSENCE_SOM_FIELD_NAMES
FINEOS_EXPORT_FILES[REQUESTED_ABSENCE_FILE_NAME] = REQUESTED_ABSENCE_FIELD_NAMES
FINEOS_EXPORT_FILES[EMPLOYEE_FEED_FILE_NAME] = EMPLOYEE_FEED_FIELD_NAMES
FINEOS_EXPORT_FILES[LEAVE_PLAN_FILE_NAME] = LEAVE_PLAN_FIELD_NAMES


FINEOS_VENDOR_EXPORT_FILES = [
    REQUESTED_ABSENCE_SOM_FILE_NAME,
    REQUESTED_ABSENCE_FILE_NAME,
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


def _generate_fineos_payment_rows_for_scenario(
    scenario_data: scenario_generator.ScenarioData,
    file_name_to_file_info: Dict[str, FineosPaymentsExportCsvWriter],
):
    scenario_descriptor = scenario_data.scenario_descriptor
    if not scenario_descriptor.has_payment_extract:
        return

    # Get file writers
    pei_csv_writer = file_name_to_file_info[PEI_FILE_NAME].csv_writer
    pei_payment_details_csv_writer = file_name_to_file_info[
        PEI_PAYMENT_DETAILS_FILE_NAME
    ].csv_writer
    pei_claim_details_csv_writer = file_name_to_file_info[PEI_CLAIM_DETAILS_FILE_NAME].csv_writer

    # Get db models
    employee = scenario_data.employee
    payments = scenario_data.payments

    # PEI File
    is_eft = employee.eft is not None
    address = employee.ctr_address_pair.fineos_address

    for payment in payments:
        payment_c_value = payment.fineos_pei_c_value
        payment_i_value = payment.fineos_pei_i_value

        vpei_row = {}
        vpei_row["C"] = payment_c_value
        vpei_row["I"] = payment_i_value
        vpei_row["PAYEEFULLNAME"] = f"{employee.first_name} {employee.last_name}"
        vpei_row["PAYEESOCNUMBE"] = employee.tax_identifier.tax_identifier
        vpei_row["PAYEECUSTOMER"] = employee.fineos_customer_number
        vpei_row["EVENTTYPE"] = scenario_data.payment_event_type
        vpei_row["PAYMENTADD1"] = address.address_line_one
        vpei_row["PAYMENTADD2"] = address.address_line_two
        vpei_row["PAYMENTADD4"] = address.city
        vpei_row["PAYMENTADD6"] = (
            address.geo_state_text
            if address.geo_state_id is None
            else address.geo_state.geo_state_description
        )
        if (
            scenario_descriptor.non_existent_address_update
        ):  # TODO is this accurate change for scenario P
            vpei_row["PAYMENTADD1"] = "123 Fictional Address"
            vpei_row["PAYMENTADD4"] = "Nowhere"
            vpei_row["PAYMENTADD6"] = "Massachusetts"

        vpei_row["PAYMENTPOSTCO"] = address.zip_code
        vpei_row["PAYMENTMETHOD"] = (
            PaymentMethod.ACH.payment_method_description
            if is_eft
            else PaymentMethod.CHECK.payment_method_description
        )
        if scenario_descriptor.payee_payment_method_update:
            vpei_row["PAYMENTMETHOD"] = PaymentMethod.DEBIT.payment_method_description

        payment_date = (
            payments_util.get_now() if payment.payment_date is None else payment.payment_date
        )
        vpei_row["PAYMENTDATE"] = payment_date.strftime("%Y-%m-%d %H:%M:%S")

        # Some cases are missing payment amounts. In those cases, do not write
        # to the AMOUNT_MONAMT column.
        if not scenario_descriptor.missing_payment:
            # Adjust the amount if the scenario calls for a negative payment update.
            if scenario_descriptor.negative_payment_update:
                payment.amount = payment.amount * -1
            vpei_row["AMOUNT_MONAMT"] = "{:.2f}".format(payment.amount)

        # TODO do we still want this
        # if missing_field:
        #     vpei_row["AMOUNT_MONAMT"] = ""

        if is_eft:
            vpei_row["PAYEEBANKSORT"] = employee.eft.routing_nbr
            if scenario_descriptor.routing_number_ten_digits_update:
                vpei_row["PAYEEBANKSORT"] = employee.eft.routing_nbr.rjust(
                    10, "8"
                )  # routing number is originally 9 digits

            vpei_row["PAYEEACCOUNTN"] = employee.eft.account_nbr
            vpei_row["PAYEEACCOUNTT"] = employee.eft.bank_account_type.bank_account_type_description

        pei_csv_writer.writerow(vpei_row)

        # PEI Payment Details File
        if not scenario_descriptor.missing_from_vpeipaymentdetails:
            payment_start = payment.period_start_date
            payment_end = payment.period_end_date

            if scenario_descriptor.future_payment_benefit_week_update:
                payment_start = payments_util.get_now() + timedelta(weeks=1)
                payment_end = payments_util.get_now() + timedelta(weeks=2)

            # A payment can have more than entry in vpeipaymentdetails.csv for a given
            # CI pair. We generate a slightly randomized number of sub-payments for the
            # same CI pair.

            # Split the payment period into segments.
            start_dates = []
            if scenario_descriptor.has_multiple_payment_details and payment_start and payment_end:
                num_pairs = scenario_descriptor.payment_details_count
                date_diff = (payment_end - payment_start) / num_pairs
                for i in range(num_pairs):
                    start_dates.append((payment_start + date_diff * i))
            else:
                start_dates.append(payment_start)

            # For each segment, write a row to vpeipaymentdetails.csv.
            for i, start_date in enumerate(start_dates):
                vpei_payment_details_row = {}
                vpei_payment_details_row[
                    "PECLASSID"
                ] = payment_c_value  # Current setup: 1 payment period per payment
                vpei_payment_details_row["PEINDEXID"] = payment_i_value
                if start_date:
                    vpei_payment_details_row["PAYMENTSTARTP"] = start_date.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                # If this the last start_date, the end date should be the end of the entire time period
                if i == len(start_dates) - 1:
                    if payment_end:
                        vpei_payment_details_row["PAYMENTENDPER"] = payment_end.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                else:
                    # Otherwise, the end date should be one day before the next start date
                    if start_dates[i + 1]:
                        end_date = start_dates[i + 1] - timedelta(days=1)
                        vpei_payment_details_row["PAYMENTENDPER"] = end_date.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )

                # Write out the row.
                pei_payment_details_csv_writer.writerow(vpei_payment_details_row)

                # TODO do we still want this
                # if invalid_row:
                #     vpei_payment_details_row["PECLASSID"] = "NON_EXISTENT_C_ID"
                #     vpei_payment_details_row["PEINDEXID"] = "NON_EXISTENT_I_ID"

        if not scenario_descriptor.missing_from_vpeiclaimdetails:
            # PEI Claim Details File
            vpei_claim_details_row = {}
            vpei_claim_details_row["PECLASSID"] = payment_c_value
            vpei_claim_details_row["PEINDEXID"] = payment_i_value
            vpei_claim_details_row["ABSENCECASENU"] = payment.claim.fineos_absence_id
            vpei_claim_details_row["LEAVEREQUESTI"] = scenario_data.leave_request_id
            pei_claim_details_csv_writer.writerow(vpei_claim_details_row)


def _generate_fineos_vendor_rows_for_scenario(
    scenario_data: scenario_generator.ScenarioData,
    file_name_to_file_info: Dict[str, FineosPaymentsExportCsvWriter],
):
    # Get file writers
    requested_absence_som_csv_writer = file_name_to_file_info[
        REQUESTED_ABSENCE_SOM_FILE_NAME
    ].csv_writer
    requested_absence_csv_writer = file_name_to_file_info[REQUESTED_ABSENCE_FILE_NAME].csv_writer
    employee_feed_csv_writer = file_name_to_file_info[EMPLOYEE_FEED_FILE_NAME].csv_writer

    # Get db models
    scenario_descriptor = scenario_data.scenario_descriptor
    employee = scenario_data.employee
    employer = scenario_data.employer
    claims = scenario_data.claims

    # shared variables
    is_eft = employee.eft is not None
    address = employee.ctr_address_pair.fineos_address

    # Requested Absence file
    application_date = payments_util.get_now()
    absence_start = application_date + timedelta(weeks=random.randint(1, 3))
    absence_end = application_date + timedelta(weeks=random.randint(4, 12))

    for claim in claims:
        if not scenario_descriptor.missing_from_vbi_requestedabsence_som:
            # Most fields are drawn from VBI_REQUESTEDABSENCE_SOM.csv, the customized version
            # of VBI_REQUESTEDOBSENCE.csv
            requested_absence_som_row = {}
            requested_absence_som_row["ABSENCE_CASENUMBER"] = claim.fineos_absence_id
            requested_absence_som_row["NOTIFICATION_CASENUMBER"] = (
                claim.fineos_absence_id[:11] if claim.fineos_absence_id else ""
            )
            requested_absence_som_row["ABSENCEPERIOD_START"] = absence_start.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            requested_absence_som_row["ABSENCEPERIOD_END"] = absence_end.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            requested_absence_som_row["LEAVEREQUEST_EVIDENCERESULTTYPE"] = (
                "Not Satisfied" if not scenario_descriptor.evidence_satisfied else "Satisfied"
            )

            requested_absence_som_row[
                "EMPLOYEE_CUSTOMERNO"
            ] = scenario_data.employee_customer_number

            requested_absence_som_csv_writer.writerow(requested_absence_som_row)

        if not scenario_descriptor.missing_from_vbi_requestedabsence:
            requested_absence_row = {}
            requested_absence_row["ABSENCE_CASENUMBER"] = claim.fineos_absence_id
            requested_absence_row["LEAVEREQUEST_ID"] = scenario_data.leave_request_id
            requested_absence_row["LEAVEREQUEST_DECISION"] = scenario_data.leave_request_decision
            requested_absence_row[
                "ABSENCE_CASECREATIONDATE"
            ] = scenario_data.absence_case_creation_date
            requested_absence_row["ABSENCEREASON_NAME"] = scenario_data.absence_reason_name
            requested_absence_row["ABSENCE_CASESTATUS"] = (
                AbsenceStatus.ADJUDICATION.absence_status_description
                if claim.fineos_absence_status_id is None
                else claim.fineos_absence_status.absence_status_description
            )
            if employer:
                requested_absence_row["EMPLOYER_CUSTOMERNO"] = employer.fineos_employer_id
            requested_absence_row["ABSENCEREASON_COVERAGE"] = CLAIM_TYPE_TRANSLATION[
                scenario_descriptor.leave_type.claim_type_description
            ]
            requested_absence_csv_writer.writerow(requested_absence_row)

    # Employee Feed file
    if scenario_descriptor.missing_from_employee_feed:
        return

    if scenario_descriptor.missing_ssn:
        ssn_to_use = ""
    elif not scenario_descriptor.valid_ssn:
        ssn_to_use = "bad_ssn"
    else:
        ssn_to_use = employee.tax_identifier.tax_identifier

    vendor_ci_index = scenario_data.ci_provider.get_vendor_ci()

    employee_feed_row = {}
    employee_feed_row["C"] = vendor_ci_index.c
    employee_feed_row["I"] = vendor_ci_index.i
    employee_feed_row["DEFPAYMENTPREF"] = (
        "N" if not scenario_descriptor.default_payment_preference else "Y"
    )
    employee_feed_row["CUSTOMERNO"] = scenario_data.employee_customer_number
    employee_feed_row["NATINSNO"] = ssn_to_use
    employee_feed_row["DATEOFBIRTH"] = datetime(
        1978, random.randint(1, 12), 1, 11, 30, 00
    ).strftime("%Y-%m-%d %H:%M:%S")
    employee_feed_row["PAYMENTMETHOD"] = ""
    if scenario_descriptor.payee_payment_method:
        employee_feed_row["PAYMENTMETHOD"] = (
            PaymentMethod.ACH.payment_method_description
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


def generate_vendor_extract_files(
    scenario_data_set: List[ScenarioData], folder_path, date_prefix: str
):
    file_name_to_file_info: Dict[str, FineosPaymentsExportCsvWriter] = _create_files(
        folder_path, date_prefix, FINEOS_VENDOR_EXPORT_FILES
    )

    for scenario_data in scenario_data_set:
        try:
            _generate_fineos_vendor_rows_for_scenario(scenario_data, file_name_to_file_info)
        except Exception as e:
            logger.exception(
                "Error during fineos vendor generation for: %s",
                scenario_data.scenario_descriptor.scenario_name,
            )
            raise e

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
        try:
            _generate_fineos_payment_rows_for_scenario(scenario_data, file_name_to_file_info)
        except Exception as e:
            logger.exception(
                "Error during fineos payment extract generation for: %s",
                scenario_data.scenario_descriptor.scenario_name,
            )
            raise e

    # TODO better abstraction
    for file_info in file_name_to_file_info.values():
        file_info.file.close()


def generate(config: ScenarioDataConfig, folder_path: str) -> List[ScenarioData]:
    # Generate the data set
    scenario_dataset = scenario_generator.generate_scenario_dataset(config)

    # Generate the files with the same date prefix
    date_prefix = payments_util.get_now().strftime("%Y-%m-%d-%H-%M-%S-")
    generate_vendor_extract_files(scenario_dataset, folder_path, date_prefix)
    generate_payment_extract_files(scenario_dataset, folder_path, date_prefix)

    # To make so that it is impossible to lookup the correct employee in the database
    for scenario_data in scenario_dataset:
        if scenario_data.scenario_descriptor.employee_not_in_db:
            scenario_data.employee.tax_identifier = TaxIdentifierFactory.create()

    return scenario_dataset


DEFAULT_SCENARIOS_CONFIG: List[ScenarioNameWithCount] = [
    ScenarioNameWithCount(scenario_name, 1) for scenario_name in SCENARIO_DESCRIPTORS.keys()
]


def main():
    # generate sample
    initialize_sentry()
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
