import copy
import csv
import io
import os
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, cast

import faker
from sqlalchemy.sql.expression import true

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import PaymentMethod, PaymentTransactionType
from massgov.pfml.delegated_payments.mock.mock_util import MockData, generate_routing_nbr_from_ssn
from massgov.pfml.delegated_payments.mock.scenario_data_generator import (
    INVALID_ADDRESS,
    MATCH_ADDRESS,
    NO_MATCH_ADDRESS,
    ScenarioData,
)
from massgov.pfml.util.datetime import get_now_us_eastern

logger = massgov.pfml.util.logging.get_logger(__name__)

fake = faker.Faker()
fake.seed_instance(1212)


# We may want additional columns here from what we validate
# so these field names extended from the constant values
# This is mainly for new columns we want to implement logic for
# but FINEOS hasn't yet made a change to a particular extract
EMPLOYEE_FEED_FIELD_NAMES = payments_util.FineosExtractConstants.EMPLOYEE_FEED.field_names + [
    "EFFECTIVEFROM",
    "EFFECTIVETO",
]
REQUESTED_ABSENCE_SOM_FIELD_NAMES = (
    payments_util.FineosExtractConstants.VBI_REQUESTED_ABSENCE_SOM.field_names
)
# 1099 Files
VBI_1099DATA_SOM_FIELD_NAMES = payments_util.FineosExtractConstants.VBI_1099DATA_SOM.field_names

# Payment files
PEI_FIELD_NAMES = payments_util.FineosExtractConstants.VPEI.field_names
PEI_PAYMENT_DETAILS_FIELD_NAMES = payments_util.FineosExtractConstants.PAYMENT_DETAILS.field_names
PEI_CLAIM_DETAILS_FIELD_NAMES = payments_util.FineosExtractConstants.CLAIM_DETAILS.field_names
REQUESTED_ABSENCE_FIELD_NAMES = (
    payments_util.FineosExtractConstants.VBI_REQUESTED_ABSENCE.field_names
)

# IAWW files
VBI_LEAVE_PLAN_REQUESTED_ABSENCE_FIELD_NAMES = (
    payments_util.FineosExtractConstants.VBI_LEAVE_PLAN_REQUESTED_ABSENCE.field_names
)
PAID_LEVAVE_INSTRUCTION_FIELD_NAMES = (
    payments_util.FineosExtractConstants.PAID_LEAVE_INSTRUCTION.field_names
)

xml_1099_packed_data = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                <ns2:DataSet xmlns:ns2="http://www.fineos.com/ta/common/external">
                    <EnumObject>
                        <name>ENUM</name>
                        <prompt>Provide the reason for the 1099G reissue</prompt>
                        <value>512512002</value>
                        <radiobutton>false</radiobutton>
                    </EnumObject>
                    <StringObject>
                        <name>SPACE1</name>
                        <prompt></prompt>
                        <value></value>
                        <width>0</width>
                    </StringObject>
                    <StringObject>
                        <name>1099GReissueSHARED</name>
                        <prompt>1099-G Reissue</prompt>
                        <value>1099-G Reissue</value>
                        <width>0</width>
                    </StringObject>
                    <StringObject>
                        <name>ReissueInformation3</name>
                        <prompt>Reissue information</prompt>
                        <value>Reissue will mail a new copy of the 1099-G form to the customer with the new 1099-G form that was created from the payment resolution.</value>
                        <width>250</width>
                    </StringObject>
                    <StringObject>
                    <name>INITIALPAGE_HID</name>
                    <prompt></prompt>
                    <value></value>
                    <width>99999</width>
                    </StringObject>
                    <StringObject>
                        <name>ReissueInformation2</name>
                        <prompt>Reissue Information</prompt>
                        <value>Reissue will mail a new copy of the 1099-G form to the customer using the new address that has been added to the customer record.</value>
                        <width>250</width>
                    </StringObject>
                    <StringObject>
                        <name>ReissueInformation1</name>
                        <prompt>Reissue Information</prompt>
                        <value>Reissue will mail a new copy of the 1099-G form to the customer. The mailing address and payment information will be the same as the previous copy sent.</value>
                        <width>250</width>
                    </StringObject>
                    <StringObject>
                        <name>Confirmation</name>
                        <prompt>Confirmation</prompt>
                        <value>Before submitting this eForm please make sure the address change or payment reconciliation is complete in FINEOS.</value>
                        <width>115</width>
                    </StringObject>
                </ns2:DataSet>"""


class FineosPaymentData(MockData):
    """
    FINEOS Data contains all data we care about for processing a FINEOS extract
    With no parameters, will generate a valid, mostly-random valid standard payment
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
        include_employee_feed=True,
        include_absence_case=True,
        include_1099_data=True,
        **kwargs,
    ):
        super().__init__(generate_defaults, **kwargs)
        self.include_vpei = include_vpei
        self.include_claim_details = include_claim_details
        self.include_payment_details = include_payment_details
        self.include_requested_absence = include_requested_absence
        self.include_employee_feed = include_employee_feed
        self.include_absence_case = include_absence_case
        self.include_1099_data = include_1099_data
        self.kwargs = kwargs

        # Values used in various places below
        absence_num = str(fake.unique.random_int())
        self.ssn = self.get_value("ssn", fake.ssn().replace("-", ""))

        # Absence case values
        self.absence_case_number = self.get_value("absence_case_number", f"ABS-{absence_num}")
        self.notification_number = self.get_value("notification_number", f"NTN-{absence_num}")

        self.absence_period_class_id = self.get_value("absence_period_c_value", "14449")
        self.absence_period_index_id = self.get_value(
            "absence_period_i_value", str(fake.unique.random_int())
        )

        self.claim_type = self.get_value("claim_type", "Family")

        self.absence_case_creation_date = self.get_value(
            "absence_case_creation_date", "2020-12-01 07:00:00"
        )
        self.absence_case_status = self.get_value("absence_case_status", "Approved")

        self.leave_request_id = self.get_value("leave_request_id", str(fake.unique.random_int()))
        self.leave_request_decision = self.get_value("leave_request_decision", "Approved")
        self.leave_request_evidence = self.get_value("leave_request_evidence", "Satisfied")
        self.leave_request_start = self.get_value("leave_request_start", "2021-01-01 12:00:00")
        self.leave_request_end = self.get_value("leave_request_end", "2021-04-01 12:00:00")

        self.employer_customer_num = self.get_value(
            "employer_customer_num", str(fake.unique.random_int())
        )

        self.absence_period_type = self.get_value("absence_period_type", "Time off period")
        self.absence_reason_qualifier_one = self.get_value(
            "absence_reason_qualifier_one", "Work Related"
        )
        self.absence_reason_qualifier_two = self.get_value(
            "absence_reason_qualifier_two", "Medical Related"
        )
        self.absence_reason = self.get_value(
            "absence_reason", "Serious Health Condition - Employee"
        )

        # Employee values
        self.date_of_birth = self.get_value("date_of_birth", "1980-01-01 12:00:00")
        self.default_payment_pref = self.get_value("default_payment_pref", "Y")
        self.customer_number = self.get_value("customer_number", fake.ssn().replace("-", ""))
        self.tin = self.get_value("tin", self.ssn)

        self.fineos_employee_first_name = self.get_value(
            "fineos_employee_first_name", fake.first_name()
        )
        self.fineos_employee_middle_name = self.get_value("fineos_employee_middle_name", "")
        self.fineos_employee_last_name = self.get_value(
            "fineos_employee_last_name", fake.last_name()
        )

        self.fineos_address_effective_from = self.get_value(
            "fineos_address_effective_from", "2021-01-01 12:00:00"
        )
        self.fineos_address_effective_to = self.get_value(
            "fineos_address_effective_to", "2022-01-01 12:00:00"
        )
        self.organization_unit_name = self.get_value("organization_unit_name", "")
        self.document_type_1099 = self.get_value("document_type_1099", "1099 Request")
        self.packed_data_1099 = self.get_value("packed_data_1099", xml_1099_packed_data)

        # Payment method values (used for payment and employee files)
        self.address_1 = self.get_value(
            "address_1", f"{fake.building_number()} {fake.street_name()} {fake.street_suffix()}"
        )
        self.payment_address_1 = self.get_value("payment_address_1", self.address_1)
        self.address_2 = self.get_value("address_2", "")
        self.payment_address_2 = self.get_value("payment_address_2", "")
        self.city = self.get_value("city", fake.city())
        self.state = self.get_value("state", fake.state_abbr().upper())
        self.zip_code = self.get_value("zip_code", fake.zipcode_plus4())
        self.payment_method = self.get_value("payment_method", "Elec Funds Transfer")
        self.routing_nbr = self.get_value("routing_nbr", generate_routing_nbr_from_ssn(self.ssn))
        self.account_nbr = self.get_value("account_nbr", self.ssn)
        self.account_type = self.get_value("account_type", "Checking")

        # Payment values
        self.c_value = self.get_value("c_value", "7326")
        self.i_value = self.get_value("i_value", str(fake.unique.random_int()))

        self.payment_date = self.get_value("payment_date", "2021-01-01 12:00:00")
        self.payment_amount = self.get_value("payment_amount", "100.00")
        self.balancing_amount = self.get_value("balancing_amount", self.payment_amount)
        self.business_net_amount = self.get_value("business_net_amount", self.payment_amount)

        self.event_type = self.get_value("event_type", "PaymentOut")
        self.payee_identifier = self.get_value("payee_identifier", "Social Security Number")
        self.event_reason = self.get_value("event_reason", "Automatic Main Payment")
        self.amalgamationc = self.get_value("amalgamationc", "")  # Default blank
        self.payment_type = self.get_value("payment_type", "")

        self.payment_start_period = self.get_value("payment_start", "2021-01-01 12:00:00")
        self.payment_end_period = self.get_value("payment_end", "2021-01-07 12:00:00")

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
            vpei_record["AMALGAMATIONC"] = self.amalgamationc
            vpei_record["PAYMENTTYPE"] = self.payment_type
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

            payment_detail_record["BALANCINGAMOU_MONAMT"] = self.balancing_amount
            payment_detail_record["BUSINESSNETBE_MONAMT"] = self.business_net_amount

        return payment_detail_record

    def get_requested_absence_record(self):
        requested_absence_record = OrderedDict()
        if self.include_requested_absence:
            requested_absence_record["ABSENCEPERIOD_CLASSID"] = self.absence_period_class_id
            requested_absence_record["ABSENCEPERIOD_INDEXID"] = self.absence_period_index_id
            requested_absence_record["LEAVEREQUEST_DECISION"] = self.leave_request_decision
            requested_absence_record["LEAVEREQUEST_ID"] = self.leave_request_id
            requested_absence_record["ABSENCEREASON_COVERAGE"] = self.claim_type
            requested_absence_record["ABSENCE_CASECREATIONDATE"] = self.absence_case_creation_date
            requested_absence_record["ABSENCEPERIOD_TYPE"] = self.absence_period_type
            requested_absence_record["ABSENCEREASON_QUALIFIER1"] = self.absence_reason_qualifier_one
            requested_absence_record["ABSENCEREASON_QUALIFIER2"] = self.absence_reason_qualifier_two
            requested_absence_record["ABSENCEREASON_NAME"] = self.absence_reason

        return requested_absence_record

    def get_employee_feed_record(self):
        employee_feed_record = OrderedDict()
        if self.include_employee_feed:
            employee_feed_record["C"] = self.c_value
            employee_feed_record["I"] = self.i_value
            employee_feed_record["DEFPAYMENTPREF"] = self.default_payment_pref
            employee_feed_record["CUSTOMERNO"] = self.customer_number
            employee_feed_record["NATINSNO"] = self.ssn
            employee_feed_record["DATEOFBIRTH"] = self.date_of_birth
            employee_feed_record["PAYMENTMETHOD"] = self.payment_method
            employee_feed_record["ADDRESS1"] = self.address_1
            employee_feed_record["ADDRESS2"] = self.address_2
            employee_feed_record["ADDRESS4"] = self.city
            employee_feed_record["ADDRESS6"] = self.state
            employee_feed_record["POSTCODE"] = self.zip_code
            employee_feed_record["SORTCODE"] = self.routing_nbr
            employee_feed_record["ACCOUNTNO"] = self.account_nbr
            employee_feed_record["ACCOUNTTYPE"] = self.account_type
            employee_feed_record["FIRSTNAMES"] = self.fineos_employee_first_name
            employee_feed_record["INITIALS"] = self.fineos_employee_middle_name
            employee_feed_record["LASTNAME"] = self.fineos_employee_last_name
            employee_feed_record["EFFECTIVEFROM"] = self.fineos_address_effective_from
            employee_feed_record["EFFECTIVETO"] = self.fineos_address_effective_to

        return employee_feed_record

    def get_requested_absence_som_record(self):
        requested_absence_record = OrderedDict()
        if self.include_absence_case:
            requested_absence_record["ABSENCE_CASENUMBER"] = self.absence_case_number
            requested_absence_record["ABSENCEREASON_COVERAGE"] = self.claim_type
            requested_absence_record["NOTIFICATION_CASENUMBER"] = self.notification_number
            requested_absence_record["ABSENCE_CASESTATUS"] = self.absence_case_status
            requested_absence_record[
                "LEAVEREQUEST_EVIDENCERESULTTYPE"
            ] = self.leave_request_evidence
            requested_absence_record["ABSENCEPERIOD_START"] = self.leave_request_start
            requested_absence_record["ABSENCEPERIOD_END"] = self.leave_request_end
            requested_absence_record["EMPLOYEE_CUSTOMERNO"] = self.customer_number
            requested_absence_record["EMPLOYER_CUSTOMERNO"] = self.employer_customer_num
            requested_absence_record["ABSENCEPERIOD_CLASSID"] = self.absence_period_class_id
            requested_absence_record["ABSENCEPERIOD_INDEXID"] = self.absence_period_index_id
            requested_absence_record["LEAVEREQUEST_ID"] = self.leave_request_id
            requested_absence_record["ORGUNIT_NAME"] = self.organization_unit_name

        return requested_absence_record

    def get_vbi_1099_data_record(self):
        vbi_1099_data_record = OrderedDict()
        if self.include_1099_data:
            vbi_1099_data_record["C"] = self.c_value
            vbi_1099_data_record["CUSTOMERNO"] = self.customer_number
            vbi_1099_data_record["FIRSTNAMES"] = self.fineos_employee_first_name
            vbi_1099_data_record["LASTNAME"] = self.fineos_employee_last_name
            vbi_1099_data_record["PACKEDDATA"] = self.packed_data_1099
            vbi_1099_data_record["DOCUMENTTYPE"] = self.document_type_1099

        return vbi_1099_data_record


class FineosIAWWData(MockData):
    """
    This contains all data we care about for extracting IAWW data from FINEOS
    With no parameters, it will generate a valid, mostly-random data set
    Parameters can be overriden by specifying them as kwargs
    """

    def __init__(self, **kwargs):
        super().__init__(true, **kwargs)
        self.kwargs = kwargs

        self.c_value = self.get_value("c_value", "7326")
        self.i_value = self.get_value("i_value", str(fake.unique.random_int()))
        self.leaveplan_c_value = self.get_value("leaveplan_c_value", "14437")

        leaveplan_i_value = str(fake.unique.random_int())
        self.leaveplan_i_value_instruction = self.get_value(
            "leaveplan_i_value_instruction", leaveplan_i_value
        )
        self.leaveplan_i_value_request = self.get_value(
            "leaveplan_i_value_request", leaveplan_i_value
        )
        self.leave_request_id_value = self.get_value(
            "leave_request_id_value", str(fake.unique.random_int())
        )
        self.aww_value = self.get_value("aww_value", str(fake.unique.random_int()))

    def get_leave_plan_request_absence_record(self):
        leave_plan_request_absence_record = OrderedDict()

        leave_plan_request_absence_record["SELECTEDPLAN_CLASSID"] = self.leaveplan_c_value
        leave_plan_request_absence_record["SELECTEDPLAN_INDEXID"] = self.leaveplan_i_value_request
        leave_plan_request_absence_record["LEAVEREQUEST_ID"] = self.leave_request_id_value

        return leave_plan_request_absence_record

    def get_vpaid_leave_instruction_record(self):
        vpaid_leave_instruction_record = OrderedDict()

        vpaid_leave_instruction_record["C"] = self.c_value
        vpaid_leave_instruction_record["I"] = self.i_value
        vpaid_leave_instruction_record["AVERAGEWEEKLYWAGE_MONAMT"] = self.aww_value
        vpaid_leave_instruction_record["C_SELECTEDLEAVEPLAN"] = self.leaveplan_c_value
        vpaid_leave_instruction_record["I_SELECTEDLEAVEPLAN"] = self.leaveplan_i_value_instruction

        return vpaid_leave_instruction_record


@dataclass
class FineosExportCsvWriter:
    file_name: str
    file_path: str
    file: io.TextIOWrapper
    csv_writer: csv.DictWriter


def _create_file(
    folder_path: str, filename_prefix: str, file_name: str, column_names: List[str]
) -> FineosExportCsvWriter:
    csv_file_path = os.path.join(folder_path, f"{filename_prefix}{file_name}")
    logger.info("writing CSV file %s", csv_file_path)
    csv_file = file_util.write_file(csv_file_path)
    csv_writer = csv.DictWriter(csv_file, fieldnames=column_names)
    csv_writer.writeheader()

    return FineosExportCsvWriter(
        file_name=file_name, file_path=csv_file_path, file=csv_file, csv_writer=csv_writer
    )


def create_fineos_payment_extract_files(
    fineos_payments_dataset: List[FineosPaymentData], folder_path: str, date_of_extract: datetime
) -> None:
    # prefix string
    date_prefix = date_of_extract.strftime("%Y-%m-%d-%H-%M-%S-")

    # create the extract files
    pei_writer = _create_file(
        folder_path,
        date_prefix,
        payments_util.FineosExtractConstants.VPEI.file_name,
        PEI_FIELD_NAMES,
    )
    pei_payment_details_writer = _create_file(
        folder_path,
        date_prefix,
        payments_util.FineosExtractConstants.PAYMENT_DETAILS.file_name,
        PEI_PAYMENT_DETAILS_FIELD_NAMES,
    )
    pei_claim_details_writer = _create_file(
        folder_path,
        date_prefix,
        payments_util.FineosExtractConstants.CLAIM_DETAILS.file_name,
        PEI_CLAIM_DETAILS_FIELD_NAMES,
    )

    # write the respective rows
    for fineos_payments_data in fineos_payments_dataset:
        if vpei_record := fineos_payments_data.get_vpei_record():
            pei_writer.csv_writer.writerow(vpei_record)

        pei_payment_details_writer.csv_writer.writerow(
            fineos_payments_data.get_payment_details_record()
        )
        pei_claim_details_writer.csv_writer.writerow(
            fineos_payments_data.get_claim_details_record()
        )

    # close the files
    pei_writer.file.close()
    pei_payment_details_writer.file.close()
    pei_claim_details_writer.file.close()


def generate_payment_extract_files(
    scenario_dataset: List[ScenarioData],
    folder_path: str,
    date_of_extract: datetime,
    round: int = 1,
) -> None:
    # create the scenario based fineos data for the extract
    fineos_payments_dataset: List[FineosPaymentData] = []

    for scenario_data in scenario_dataset:
        scenario_descriptor = scenario_data.scenario_descriptor

        employee = scenario_data.employee

        prior_payment = scenario_data.payment if round > 1 else None

        if employee.tax_identifier is None:
            raise Exception("Expected employee with tin")

        ssn = employee.tax_identifier.tax_identifier.to_unformatted_str()
        if scenario_descriptor.employee_in_payment_extract_missing_in_db:
            ssn = "999999999"  # SSNs are generated by counting up, so this won't be found

        payment_method = scenario_descriptor.payment_method.payment_method_description

        payment_date = get_now_us_eastern()

        # This'll be a new payment based on different C/I values
        if round > 1 and scenario_descriptor.has_additional_payment_in_period and prior_payment:
            payment_start_period = cast(date, prior_payment.period_start_date)
            payment_end_period = cast(date, prior_payment.period_end_date)
            c_value = scenario_data.additional_payment_c_value
            i_value = scenario_data.additional_payment_i_value
            absence_case_id = scenario_data.additional_payment_absence_case_id
        else:
            payment_start_period = payment_date
            payment_end_period = payment_date + timedelta(days=15)
            c_value = scenario_data.payment_c_value
            i_value = scenario_data.payment_i_value
            absence_case_id = scenario_data.absence_case_id

        is_eft = scenario_descriptor.payment_method == PaymentMethod.ACH
        routing_nbr = generate_routing_nbr_from_ssn(ssn) if is_eft else ""
        account_nbr = ssn if is_eft else ""
        account_type = (
            scenario_descriptor.account_type.bank_account_type_description
            if is_eft and scenario_descriptor.account_type
            else ""
        )

        if scenario_descriptor.payment_close_to_cap:
            # The cap is $850.00
            payment_amount = "800.00"
        else:
            payment_amount = "100.00"

        if scenario_descriptor.negative_payment_amount:
            payment_amount = "-" + payment_amount

        event_type = "PaymentOut"
        payee_identifier = "Social Security Number"
        event_reason = "Automatic Main Payment"
        amalgamationc = ""
        payment_type = ""

        if scenario_descriptor.is_adhoc_payment:
            payment_type = "Adhoc"

        claim_type = scenario_descriptor.claim_type

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
            mock_address = MATCH_ADDRESS
        else:
            if scenario_descriptor.fineos_extract_address_valid_after_fix and round > 1:
                mock_address = MATCH_ADDRESS
            else:
                mock_address = NO_MATCH_ADDRESS

        fix_address = scenario_descriptor.invalid_address_fixed and round > 1
        if scenario_descriptor.invalid_address and (not fix_address):
            mock_address = INVALID_ADDRESS

        # We have one payment record as withholding
        if scenario_descriptor.is_tax_withholding_record_without_primary_payment:
            event_reason = "Automatic Alternate Payment"
            payee_identifier = "ID"
            amalgamationc = "ScheduledAlternate65424"
            ssn = "SITPAYEE001"
            payment_amount = "22.00"

        fineos_payments_data = FineosPaymentData(
            generate_defaults=True,
            c_value=c_value,
            i_value=i_value,
            include_vpei=scenario_descriptor.create_payment,
            include_claim_details=scenario_descriptor.include_claim_details,
            include_payment_details=True,
            include_requested_absence=False,
            include_absence_case=False,
            tin=ssn,
            absence_case_number=absence_case_id,
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
            payment_start=payment_start_period.strftime("%Y-%m-%d %H:%M:%S"),
            payment_end=payment_end_period.strftime("%Y-%m-%d %H:%M:%S"),
            event_type=event_type,
            event_reason=event_reason,
            payee_identifier=payee_identifier,
            amalgamationc=amalgamationc,
            payment_type=payment_type,
            claim_type=claim_type,
            absence_period_c_value=scenario_data.absence_period_c_value,
            absence_period_i_value=scenario_data.absence_period_i_value,
            leave_request_id=scenario_data.leave_request_id,
        )

        if (
            scenario_descriptor.is_tax_withholding_records_exists
            and scenario_data.tax_withholding_payment_i_values
        ):
            for item in range(2):
                withholding_payment = copy.deepcopy(fineos_payments_data)
                withholding_payment.event_reason = "Automatic Alternate Payment"
                withholding_payment.payee_identifier = "ID"
                withholding_payment.amalgamationc = "ScheduledAlternate65424"

                # always have valid address for withholding payments
                mock_address = MATCH_ADDRESS
                withholding_payment.payment_address_1 = mock_address["line_1"]
                withholding_payment.payment_address_2 = mock_address["line_2"]
                withholding_payment.city = mock_address["city"]
                withholding_payment.state = mock_address["state"]
                withholding_payment.zip_code = mock_address["zip"]

                if item == 0:
                    withholding_payment.tin = "123456789"
                    withholding_payment.payment_amount = "22.00"
                    withholding_payment.i_value = scenario_data.tax_withholding_payment_i_values[
                        item
                    ]
                if item == 1:
                    withholding_payment.tin = "123456780"
                    withholding_payment.payment_amount = "35.00"
                    withholding_payment.i_value = scenario_data.tax_withholding_payment_i_values[
                        item
                    ]
                fineos_payments_dataset.append(withholding_payment)
        fineos_payments_dataset.append(fineos_payments_data)

    # create the files
    create_fineos_payment_extract_files(fineos_payments_dataset, folder_path, date_of_extract)


def create_fineos_claimant_extract_files(
    fineos_claimant_dataset: List[FineosPaymentData], folder_path: str, date_of_extract: datetime
) -> None:
    # prefix string
    date_prefix = date_of_extract.strftime("%Y-%m-%d-%H-%M-%S-")

    # create the extract files
    employee_feed_writer = _create_file(
        folder_path,
        date_prefix,
        payments_util.FineosExtractConstants.EMPLOYEE_FEED.file_name,
        EMPLOYEE_FEED_FIELD_NAMES,
    )
    requested_absence_som_writer = _create_file(
        folder_path,
        date_prefix,
        payments_util.FineosExtractConstants.VBI_REQUESTED_ABSENCE_SOM.file_name,
        REQUESTED_ABSENCE_SOM_FIELD_NAMES,
    )
    vbi_1099_data_writer = _create_file(
        folder_path,
        date_prefix,
        payments_util.FineosExtractConstants.VBI_1099DATA_SOM.file_name,
        VBI_1099DATA_SOM_FIELD_NAMES,
    )

    requested_absence_writer = _create_file(
        folder_path,
        date_prefix,
        payments_util.FineosExtractConstants.VBI_REQUESTED_ABSENCE.file_name,
        REQUESTED_ABSENCE_FIELD_NAMES,
    )

    # write the respective rows
    for fineos_claimant_data in fineos_claimant_dataset:
        employee_feed_writer.csv_writer.writerow(fineos_claimant_data.get_employee_feed_record())
        requested_absence_som_writer.csv_writer.writerow(
            fineos_claimant_data.get_requested_absence_som_record()
        )
        requested_absence_writer.csv_writer.writerow(
            fineos_claimant_data.get_requested_absence_record()
        )
        vbi_1099_data_writer.csv_writer.writerow(fineos_claimant_data.get_vbi_1099_data_record())

    # close the files
    employee_feed_writer.file.close()
    requested_absence_som_writer.file.close()
    requested_absence_writer.file.close()
    vbi_1099_data_writer.file.close()


def generate_claimant_data_files(
    scenario_dataset: List[ScenarioData],
    folder_path: str,
    date_of_extract: datetime,
    round: int = 1,
) -> None:
    # create the scenario based fineos data for the extract
    fineos_claimant_dataset: List[FineosPaymentData] = []

    for scenario_data in scenario_dataset:
        scenario_descriptor = scenario_data.scenario_descriptor
        employee = scenario_data.employee
        employer = scenario_data.employer

        if employee.tax_identifier is None:
            raise Exception("Expected employee with tin")

        ssn = employee.tax_identifier.tax_identifier.to_unformatted_str()
        if scenario_descriptor.claim_extract_employee_identifier_unknown:
            ssn = "999999999"

        if round > 1 and scenario_descriptor.has_additional_payment_in_period:
            absence_case_number = scenario_data.additional_payment_absence_case_id
        else:
            absence_case_number = scenario_data.absence_case_id

        date_of_birth = "1991-01-01 12:00:00"
        payment_method = scenario_descriptor.payment_method.payment_method_description
        account_type = scenario_descriptor.account_type.bank_account_type_description
        address_1 = (
            employee.ctr_address_pair.fineos_address.address_line_one
            if employee.ctr_address_pair
            else ""
        )
        address_2 = (
            employee.ctr_address_pair.fineos_address.address_line_two
            if employee.ctr_address_pair
            else ""
        )

        city = employee.ctr_address_pair.fineos_address.city if employee.ctr_address_pair else ""
        state = ""
        if employee.ctr_address_pair:
            if employee.ctr_address_pair.fineos_address.geo_state:
                state = str(
                    employee.ctr_address_pair.fineos_address.geo_state.geo_state_description
                )
            else:
                state = str(employee.ctr_address_pair.fineos_address.geo_state_text)
        post_code = (
            employee.ctr_address_pair.fineos_address.zip_code if employee.ctr_address_pair else ""
        )
        routing_nbr = generate_routing_nbr_from_ssn(ssn)
        account_nbr = ssn
        natinsno = ssn
        default_payment_pref = "Y"
        customer_number = ssn
        absence_case_number = absence_case_number
        absence_case_status = "Approved"
        leave_request_evidence = "Satisfied" if scenario_descriptor.is_id_proofed else "Rejected"
        leave_request_start = "2021-01-01 12:00:00"
        leave_request_end = "2021-04-01 12:00:00"
        notification_number = f"NTN-{absence_case_number}"
        fineos_employer_id = employer.fineos_employer_id
        claim_type = scenario_descriptor.claim_type

        fineos_employee_first_name: Optional[str] = employee.fineos_employee_first_name
        fineos_employee_middle_name: Optional[str] = employee.fineos_employee_middle_name
        fineos_employee_last_name: Optional[str] = employee.fineos_employee_last_name

        if scenario_descriptor.dor_fineos_name_mismatch:
            fineos_employee_first_name = "Mismatch"
            fineos_employee_middle_name = "Mismatch"
            fineos_employee_last_name = "Mismatch"

        # Auto generated: leave_request_id
        fineos_claimant_data = FineosPaymentData(
            generate_defaults=True,
            absence_period_c_value=scenario_data.absence_period_c_value,
            absence_period_i_value=scenario_data.absence_period_i_value,
            date_of_birth=date_of_birth,
            payment_method=payment_method,
            account_type=account_type,
            address_1=address_1,
            address_2=address_2,
            city=city,
            state=state,
            post_code=post_code,
            routing_nbr=routing_nbr,
            account_nbr=account_nbr,
            ssn=natinsno,
            default_payment_pref=default_payment_pref,
            customer_number=customer_number,
            absence_case_number=absence_case_number,
            claim_type=claim_type,
            absence_case_status=absence_case_status,
            notification_number=notification_number,
            employer_customer_num=fineos_employer_id,
            fineos_employee_first_name=fineos_employee_first_name,
            fineos_employee_middle_name=fineos_employee_middle_name,
            fineos_employee_last_name=fineos_employee_last_name,
            leave_request_evidence=leave_request_evidence,
            leave_request_start=leave_request_start,
            leave_request_end=leave_request_end,
            leave_request_decision=scenario_descriptor.leave_request_decision,
            leave_request_id=scenario_data.leave_request_id,
        )

        fineos_claimant_dataset.append(fineos_claimant_data)
    # create the files
    create_fineos_claimant_extract_files(fineos_claimant_dataset, folder_path, date_of_extract)


def generate_payment_reconciliation_extract_files(
    folder_path: str, date_prefix: str, row_count: int
) -> Dict[str, List[Dict]]:
    extract_records = {}
    for extract_file in payments_util.PAYMENT_RECONCILIATION_EXTRACT_FILES:
        csv_handle = _create_file(
            folder_path, date_prefix, extract_file.file_name, extract_file.field_names
        )

        # write the respective rows
        records = []
        for i in range(row_count):
            row = {}
            for field_name in extract_file.field_names:
                row[field_name] = "test"
            row["C"] = "1"
            row["I"] = str(i)

            csv_handle.csv_writer.writerow(row)
            records.append(row)

        csv_handle.file.close()
        extract_records[extract_file.file_name] = records

    return extract_records


def generate_iaww_extract_files(
    dataset: List[FineosIAWWData], folder_path: str, date_prefix: str
) -> Dict[str, List[Dict]]:
    extract_records = {}

    # create the extract files
    leave_plan_requested_absence_writer = _create_file(
        folder_path,
        date_prefix,
        payments_util.FineosExtractConstants.VBI_LEAVE_PLAN_REQUESTED_ABSENCE.file_name,
        VBI_LEAVE_PLAN_REQUESTED_ABSENCE_FIELD_NAMES,
    )
    paid_leave_instruction_writer = _create_file(
        folder_path,
        date_prefix,
        payments_util.FineosExtractConstants.PAID_LEAVE_INSTRUCTION.file_name,
        PAID_LEVAVE_INSTRUCTION_FIELD_NAMES,
    )

    # write the respective rows
    # we can leave most of the fields empty and just populate the columns we care about
    leave_plan_requested_records = []
    leave_instruction_records = []

    for data in dataset:
        leave_plan_requested_absence_record = data.get_leave_plan_request_absence_record()
        leave_instruction_record = data.get_vpaid_leave_instruction_record()

        row = {}
        row["SELECTEDPLAN_CLASSID"] = leave_plan_requested_absence_record["SELECTEDPLAN_CLASSID"]
        row["SELECTEDPLAN_INDEXID"] = leave_plan_requested_absence_record["SELECTEDPLAN_INDEXID"]
        row["LEAVEREQUEST_ID"] = leave_plan_requested_absence_record["LEAVEREQUEST_ID"]

        leave_plan_requested_absence_writer.csv_writer.writerow(row)
        leave_plan_requested_records.append(row)

        row = {}
        row["C"] = leave_instruction_record["C"]
        row["I"] = leave_instruction_record["I"]
        row["AVERAGEWEEKLYWAGE_MONAMT"] = leave_instruction_record["AVERAGEWEEKLYWAGE_MONAMT"]
        row["C_SELECTEDLEAVEPLAN"] = leave_instruction_record["C_SELECTEDLEAVEPLAN"]
        row["I_SELECTEDLEAVEPLAN"] = leave_instruction_record["I_SELECTEDLEAVEPLAN"]

        paid_leave_instruction_writer.csv_writer.writerow(row)
        leave_instruction_records.append(row)

    leave_plan_requested_absence_writer.file.close()
    extract_records[
        payments_util.FineosExtractConstants.VBI_LEAVE_PLAN_REQUESTED_ABSENCE.file_name
    ] = leave_plan_requested_records

    paid_leave_instruction_writer.file.close()
    extract_records[
        payments_util.FineosExtractConstants.PAID_LEAVE_INSTRUCTION.file_name
    ] = leave_instruction_records

    return extract_records
