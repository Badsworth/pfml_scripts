import csv
import io
import os
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

import faker

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import PaymentMethod, PaymentTransactionType
from massgov.pfml.delegated_payments.mock.scenario_data_generator import (
    INVALID_ADDRESS,
    MULTI_MATCH_ADDRESS,
    VALID_ADDRESS,
    ScenarioData,
)

fake = faker.Faker()
fake.seed_instance(1212)

# Claimant extract file and field names
EMPLOYEE_FEED_FILE_NAME = "Employee_feed.csv"
LEAVE_PLAN_FILE_NAME = "LeavePlan_info.csv"
REQUESTED_ABSENCE_SOM_FILE_NAME = "VBI_REQUESTEDABSENCE_SOM.csv"

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
REQUESTED_ABSENCE_SOM_FIELD_NAMES = [
    "ABSENCEREASON_COVERAGE",
    "ABSENCE_CASENUMBER",
    "NOTIFICATION_CASENUMBER",
    "ABSENCE_CASESTATUS",
    "ABSENCEPERIOD_START",
    "ABSENCEPERIOD_END",
    "LEAVEREQUEST_EVIDENCERESULTTYPE",
    "EMPLOYEE_CUSTOMERNO",
    "EMPLOYER_CUSTOMERNO",
]

# Payment file and filed Names

PEI_FILE_NAME = "vpei.csv"
PEI_PAYMENT_DETAILS_FILE_NAME = "vpeipaymentdetails.csv"
PEI_CLAIM_DETAILS_FILE_NAME = "vpeiclaimdetails.csv"
REQUESTED_ABSENCE_FILE_NAME = "VBI_REQUESTEDABSENCE.csv"

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
    "PAYEEBANKSORT",
    "PAYEEACCOUNTN",
    "PAYEEACCOUNTT",
    "EVENTTYPE",
    "PAYEEIDENTIFI",
    "EVENTREASON",
]
PEI_PAYMENT_DETAILS_FIELD_NAMES = ["PECLASSID", "PEINDEXID", "PAYMENTSTARTP", "PAYMENTENDPER"]
PEI_CLAIM_DETAILS_FIELD_NAMES = ["PECLASSID", "PEINDEXID", "ABSENCECASENU", "LEAVEREQUESTI"]
REQUESTED_ABSENCE_FIELD_NAMES = ["LEAVEREQUEST_DECISION", "LEAVEREQUEST_ID"]

FINEOS_CLAIMANT_EXPORT_FILES = [
    EMPLOYEE_FEED_FILE_NAME,
    LEAVE_PLAN_FILE_NAME,
]
FINEOS_PAYMENT_EXTRACT_FILES = [
    PEI_FILE_NAME,
    PEI_PAYMENT_DETAILS_FILE_NAME,
    PEI_CLAIM_DETAILS_FILE_NAME,
    REQUESTED_ABSENCE_FILE_NAME,
]

# TODO class FineosClaimantData:


class FineosPaymentData:
    """
    FINEOS Data contains all data we care about for processing a FINEOS extract
    With no parameters,, will generate a valid, mostly-random valid standard payment
    Parameters can be overriden by specifying them as kwargs. If you do not want
    random generated values, set generate_defaults to False in the constructor.
    """

    def __init__(
        self,
        generate_defaults=True,
        include_vpei=True,
        include_claim_details=True,
        include_payment_details=True,
        include_requested_absence=True,
        **kwargs,
    ):
        self.generate_defaults = generate_defaults
        self.include_vpei = include_vpei
        self.include_claim_details = include_claim_details
        self.include_payment_details = include_payment_details
        self.include_requested_absence = include_requested_absence
        self.kwargs = kwargs

        self.c_value = self.get_value("c_value", "7326")
        self.i_value = self.get_value("i_value", str(fake.unique.random_int()))
        self.absence_case_number = self.get_value(
            "absence_case_number", f"ABS-{fake.unique.random_int()}"
        )

        ssn = fake.ssn().replace("-", "")
        self.tin = self.get_value("tin", ssn)

        self.payment_address_1 = self.get_value(
            "payment_address_1",
            f"{fake.building_number()} {fake.street_name()} {fake.street_suffix()}",
        )
        self.payment_address_2 = self.get_value("payment_address_2", "")
        self.city = self.get_value("city", fake.city())
        self.state = self.get_value("state", fake.state_abbr().upper())
        self.zip_code = self.get_value("zip_code", fake.zipcode_plus4())
        self.payment_method = self.get_value("payment_method", "Elec Funds Transfer")
        self.payment_date = self.get_value("payment_date", "2021-01-01 12:00:00")
        self.payment_amount = self.get_value("payment_amount", "100.00")
        self.routing_nbr = self.get_value("routing_nbr", ssn)
        self.account_nbr = self.get_value("account_nbr", ssn)
        self.account_type = self.get_value("account_type", "Checking")
        self.event_type = self.get_value("event_type", "PaymentOut")
        self.payee_identifier = self.get_value("payee_identifier", "Social Security Number")
        self.event_reason = self.get_value("event_reason", "Automatic Main Payment")

        self.payment_start_period = self.get_value("payment_start", "2021-01-01 12:00:00")
        self.payment_end_period = self.get_value("payment_end", "2021-01-08 12:00:00")

        self.leave_request_id = self.get_value("leave_request_id", str(fake.unique.random_int()))
        self.leave_request_decision = self.get_value("leave_request_decision", "Approved")

    def get_vpei_record(self):
        vpei_record = OrderedDict()
        if self.include_vpei:
            vpei_record["C"] = self.c_value
            vpei_record["I"] = self.i_value
            vpei_record["PAYEESOCNUMBE"] = self.tin
            vpei_record["PAYMENTADD1"] = self.payment_address_1
            vpei_record["PAYMENTADD2"] = self.payment_address_2
            vpei_record["PAYMENTADD4"] = self.city
            vpei_record["PAYMENTADD6"] = self.state
            vpei_record["PAYMENTPOSTCO"] = self.zip_code
            vpei_record["PAYMENTMETHOD"] = self.payment_method
            vpei_record["PAYMENTDATE"] = self.payment_date
            vpei_record["AMOUNT_MONAMT"] = self.payment_amount
            vpei_record["PAYEEBANKSORT"] = self.routing_nbr
            vpei_record["PAYEEACCOUNTN"] = self.account_nbr
            vpei_record["PAYEEACCOUNTT"] = self.account_type
            vpei_record["EVENTTYPE"] = self.event_type
            vpei_record["PAYEEIDENTIFI"] = self.payee_identifier
            vpei_record["EVENTREASON"] = self.event_reason
        return vpei_record

    def get_claim_details_record(self):
        claim_detail_record = OrderedDict()
        if self.include_claim_details:
            claim_detail_record["PECLASSID"] = self.c_value
            claim_detail_record["PEINDEXID"] = self.i_value
            claim_detail_record["ABSENCECASENU"] = self.absence_case_number
            claim_detail_record["LEAVEREQUESTI"] = self.leave_request_id
        return claim_detail_record

    def get_payment_details_record(self):
        payment_detail_record = OrderedDict()
        if self.include_payment_details:
            payment_detail_record["PECLASSID"] = self.c_value
            payment_detail_record["PEINDEXID"] = self.i_value

            payment_detail_record["PAYMENTSTARTP"] = self.payment_start_period
            payment_detail_record["PAYMENTENDPER"] = self.payment_end_period

        return payment_detail_record

    def get_requested_absence_record(self):
        requested_absence_record = OrderedDict()
        if self.include_requested_absence:
            requested_absence_record["LEAVEREQUEST_DECISION"] = self.leave_request_decision
            requested_absence_record["LEAVEREQUEST_ID"] = self.leave_request_id
        return requested_absence_record

    def get_value(self, key, default):
        # We want to support setting values as None
        contains_value = key in self.kwargs

        if not contains_value:
            if self.generate_defaults:
                return default
            return ""

        return self.kwargs.get(key)


@dataclass
class FineosPaymentsExportCsvWriter:
    file_name: str
    file_path: str
    file: io.TextIOWrapper
    csv_writer: csv.DictWriter


def _create_file(
    folder_path: str, filename_prefix: str, file_name: str, column_names: List[str]
) -> FineosPaymentsExportCsvWriter:
    csv_file_path = os.path.join(folder_path, f"{filename_prefix}{file_name}")
    csv_file = file_util.write_file(csv_file_path)
    csv_writer = csv.DictWriter(csv_file, fieldnames=column_names)
    csv_writer.writeheader()

    return FineosPaymentsExportCsvWriter(
        file_name=file_name, file_path=csv_file_path, file=csv_file, csv_writer=csv_writer
    )


def create_fineos_payment_extract_files(
    fineos_payments_dataset: List[FineosPaymentData], folder_path: str, date_of_extract: datetime
) -> None:
    # prefix string
    date_prefix = date_of_extract.strftime("%Y-%m-%d-%H-%M-%S-")

    # create the extract files
    pei_writer = _create_file(folder_path, date_prefix, PEI_FILE_NAME, PEI_FIELD_NAMES)
    pei_payment_details_writer = _create_file(
        folder_path, date_prefix, PEI_PAYMENT_DETAILS_FILE_NAME, PEI_PAYMENT_DETAILS_FIELD_NAMES
    )
    pei_claim_details_writer = _create_file(
        folder_path, date_prefix, PEI_CLAIM_DETAILS_FILE_NAME, PEI_CLAIM_DETAILS_FIELD_NAMES
    )
    requested_absence_writer = _create_file(
        folder_path, date_prefix, REQUESTED_ABSENCE_FILE_NAME, REQUESTED_ABSENCE_FIELD_NAMES
    )

    # write the respective rows
    for fineos_payments_data in fineos_payments_dataset:
        pei_writer.csv_writer.writerow(fineos_payments_data.get_vpei_record())
        pei_payment_details_writer.csv_writer.writerow(
            fineos_payments_data.get_payment_details_record()
        )
        pei_claim_details_writer.csv_writer.writerow(
            fineos_payments_data.get_claim_details_record()
        )
        requested_absence_writer.csv_writer.writerow(
            fineos_payments_data.get_requested_absence_record()
        )

    # close the files
    pei_writer.file.close()
    pei_payment_details_writer.file.close()
    pei_claim_details_writer.file.close()
    requested_absence_writer.file.close()


def generate_payment_extract_files(
    scenario_dataset: List[ScenarioData], folder_path: str, date_of_extract: datetime
) -> None:
    # create the scenario based fineos data for the extract
    fineos_payments_dataset: List[FineosPaymentData] = []

    for scenario_data in scenario_dataset:
        scenario_descriptor = scenario_data.scenario_descriptor
        employee = scenario_data.employee
        claim = scenario_data.claim

        if employee.tax_identifier is None:
            raise Exception("Expected employee with tin")

        ssn = employee.tax_identifier.tax_identifier.replace("-", "")
        if scenario_descriptor.employee_missing_in_db:
            ssn = "UNKNOWNSSN"

        payment_method = scenario_descriptor.payment_method.payment_method_description

        payment_date = payments_util.get_now()
        payment_start_period = payment_date
        payment_end_period = payment_date + timedelta(days=15)

        is_eft = scenario_descriptor.payment_method == PaymentMethod.ACH
        routing_nbr = ssn if is_eft else ""
        account_nbr = ssn if is_eft else ""
        account_type = (
            scenario_descriptor.account_type.bank_account_type_description
            if is_eft and scenario_descriptor.account_type
            else ""
        )

        payment_amount = "-100.00" if scenario_descriptor.negative_payment_amount else "100.00"
        event_type = "PaymentOut"
        payee_identifier = "Social Security Number"
        event_reason = "Automatic Main Payment"

        if scenario_descriptor.payment_transaction_type == PaymentTransactionType.ZERO_DOLLAR:
            payment_amount = "0"
        elif scenario_descriptor.payment_transaction_type == PaymentTransactionType.OVERPAYMENT:
            event_type = "Overpayment"
        elif (
            scenario_descriptor.payment_transaction_type
            == PaymentTransactionType.EMPLOYER_REIMBURSEMENT
        ):
            event_reason = "Automatic Alternate Payment"
            payee_identifier = "Tax Identification Number"
        elif scenario_descriptor.payment_transaction_type == PaymentTransactionType.CANCELLATION:
            event_type = "PaymentOut Cancellation"
        # TODO Unknown

        if scenario_descriptor.fineos_extract_address_valid:
            mock_address = VALID_ADDRESS
        elif scenario_descriptor.fineos_extract_address_multiple_matches:
            mock_address = MULTI_MATCH_ADDRESS
        else:
            mock_address = INVALID_ADDRESS

        # Auto generated: c_value, i_value, leave_request_id
        fineos_payments_data = FineosPaymentData(
            generate_defaults=True,
            c_value=scenario_data.payment_c_value,
            i_value=scenario_data.payment_i_value,
            include_claim_details=scenario_descriptor.include_non_vpei_records,
            include_payment_details=scenario_descriptor.include_non_vpei_records,
            include_requested_absence=scenario_descriptor.include_non_vpei_records,
            tin=ssn,
            absence_case_number=claim.fineos_absence_id,
            payment_address_1=mock_address["line_1"],
            payment_address_2=mock_address["line_2"],
            city=mock_address["city"],
            state=mock_address["state"],
            zip_code=mock_address["zip"],
            payment_method=payment_method,
            payment_date=payment_date.strftime("%Y-%m-%d %H:%M:%S"),
            payment_amount=payment_amount,
            routing_nbr=routing_nbr,
            account_nbr=account_nbr,
            account_type=account_type,
            payment_start_period=payment_start_period.strftime("%Y-%m-%d %H:%M:%S"),
            payment_end_period=payment_end_period.strftime("%Y-%m-%d %H:%M:%S"),
            leave_request_decision=scenario_descriptor.leave_request_decision,
            event_type=event_type,
            event_reason=event_reason,
            payee_identifier=payee_identifier,
        )

        fineos_payments_dataset.append(fineos_payments_data)

    # create the files
    create_fineos_payment_extract_files(fineos_payments_dataset, folder_path, date_of_extract)
