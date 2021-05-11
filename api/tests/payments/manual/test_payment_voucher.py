#
# Tests for massgov.pfml.payments.manual.payment_voucher.
#
# Payment Voucher Scenarios:
# See massgov.pfml.payments.mock.payments_test_scenario_generator for definitions
#
#
# Positive cases:
# --------------
# SCENARIO_VOUCHER_A: medical leave, pay by check, 2 payments for different pay periods, (default) vcm_flag is No
# SCENARIO_VOUCHER_B: bonding leave, pay by check, payment is zero dollar, vcm_flag is Yes
# SCENARIO_VOUCHER_C: medical leave, pay by eft
# SCENARIO_VOUCHER_D: bonding leave, pay by eft
# SCENARIO_VOUCHER_E: multiple vpeipaymentdetails.csv rows for the same CI pair
#
#
# Negative cases regarding payment amounts (writeback should be Active):
# --------------
# SCENARIO_VOUCHER_F: payment is negative, vcm_flag is Missing State
# SCENARIO_VOUCHER_G: payment is missing
#
#
# Negative cases for entries missing in cross-referenced datasets (writeback should be empty):
# --------------
# SCENARIO_VOUCHER_H: missing employee and therefore missing mmars vendor customer code and vcm flag is empty
# SCENARIO_VOUCHER_I: missing entry in vpeiclaimdetails.csv and therefore missing:
#                     absence case number, vendor invoice number, leave type, activity code, case status,
#                     employer ID, leave request ID, leave request decision, check description
# SCENARIO_VOUCHER_J: missing entry in VBI_REQUSTEDABSENCE.csv and therefore missing leave request ID and decision
# SCENARIO_VOUCHER_K: missing entry in VBI_REQUESTEDABSENCE_SOM.csv and therefore missing:
#                     leave type, activity code, case status, employer ID
# SCENARIO_VOUCHER_L: missing entry in vpeipaymentdetails.csv and therefore missing:
#                     payment period start date, payment period end date, check description, vendor invoice date
#
#
# Negative cases for missing individual fields (writeback should be empty):
# --------------
# SCENARIO_VOUCHER_M: missing payment period start dates in vpeipaymentdetails.csv and therefore also missing:
#                     check description
# SCENARIO_VOUCHER_N: missing payment period end dates in vpeipaymentdetails.csv and therefore also missing:
#                     check description, vendor invoice date


import os.path
import random
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List

import faker
import freezegun
import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.mock.fineos_extract_generator as fineos_extract_generator
import massgov.pfml.payments.mock.payments_test_scenario_generator as scenario_generator
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import Address, Payment, State, TaxIdentifier
from massgov.pfml.db.models.factories import EmployeeFactory
from massgov.pfml.payments import fineos_payment_export, fineos_vendor_export, gax
from massgov.pfml.payments.manual import payment_voucher
from massgov.pfml.util.csv import CSVSourceWrapper
from tests.helpers.state_log import AdditionalParams, setup_state_log, setup_state_log_only

# every test in here requires real resources
pytestmark = pytest.mark.integration

# Constants for payment voucher 'vcm_flag'
VCM_FLAG_YES = "Yes"
VCM_FLAG_NO = "No"
VCM_FLAG_MISSING = "Missing State"
VCM_FLAG_EMPTY = ""


class MockCSVWriter:
    def __init__(self):
        self.rows = []

    def writerow(self, row):
        self.rows.append(row)


class MockLogEntry:
    def set_metrics(self, metrics):
        pass

    def increment(self, metric):
        pass


class ScenarioOutput:
    scenario_data: scenario_generator.ScenarioData
    address: Address
    payments: List[Payment]
    payment_voucher_rows: List[Dict[str, Any]]
    writeback_rows: List[Dict[str, str]]
    payment_date: date
    inactive_writeback: bool = False

    def __init__(self, payment_date: date, scenario_data: scenario_generator.ScenarioData) -> None:
        self.scenario_data = scenario_data
        self.payment_date = payment_date

        # Set up some helper vars.
        self.address = self.scenario_data.employee.ctr_address_pair.fineos_address
        self.payments = self.scenario_data.payments

        # Identify if there are errors.
        possible_error_states = [
            "employee_not_in_db",
            "missing_from_vbi_requestedabsence",
            "missing_from_vbi_requestedabsence_som",
            "missing_from_vpeiclaimdetails",
            "missing_from_vpeipaymentdetails",
            "missing_payment_start_date",
            "missing_payment_end_date",
        ]
        for error_state in possible_error_states:
            if getattr(scenario_data.scenario_descriptor, error_state):
                self.inactive_writeback = True
                break

        # Get rows for all payments for this scenario.
        self.payment_voucher_rows = []
        self.writeback_rows = []
        for payment in self.payments:
            self.payment_voucher_rows.append(self.get_payment_voucher_dict(payment))
            self.writeback_rows.append(self.get_writeback_dict(payment))

    def get_payment_voucher_dict(self, payment: Payment) -> Dict[str, Any]:
        """Returns the dictionary representation of a Payment Voucher row for a single payment."""

        # Default these values to empty strings.
        activity_code = ""
        case_status = ""
        check_description = ""
        employer_id = ""
        leave_type = ""
        payment_period_start_date = ""
        payment_period_end_date = ""
        vendor_invoice_date = ""
        vendor_invoice_number = ""
        absence_case_creation_date = ""

        # Override with values if they are accessible.
        try:
            activity_code = gax.get_activity_code(payment.claim.claim_type_id)
        except Exception:
            pass

        try:
            leave_type = gax.get_rfed_doc_id(payment.claim.claim_type_id)
        except Exception:
            pass

        if payment.claim.fineos_absence_status:
            case_status = payment.claim.fineos_absence_status.absence_status_description

        if self.scenario_data.employer:
            employer_id = str(self.scenario_data.employer.fineos_employer_id)

        if payment.period_start_date:
            payment_period_start_date = payment.period_start_date.isoformat()

        if payment.period_end_date:
            payment_period_end_date = payment.period_end_date.isoformat()
            vendor_invoice_date = gax.get_vendor_invoice_date_str(payment.period_end_date)

        if (
            payment.claim.fineos_absence_id
            and payment.period_start_date
            and payment.period_end_date
        ):
            check_description = gax.get_check_description(
                payment.claim.fineos_absence_id, payment.period_start_date, payment.period_end_date
            )

        if payment.claim.fineos_absence_id:
            vendor_invoice_number = gax.get_vendor_invoice_number(
                payment.claim.fineos_absence_id, payment.fineos_pei_i_value
            )

        if self.scenario_data.absence_case_creation_date:
            absence_case_creation_date = self.scenario_data.absence_case_creation_date.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        # Construct and return the dictionary.
        return {
            "absence_case_number": payment.claim.fineos_absence_id,
            "activity_code": activity_code,
            "address_code": "AD010",
            "address_line_1": self.address.address_line_one,
            "address_line_2": self.address.address_line_two,
            "c_value": payment.fineos_pei_c_value,
            "city": self.address.city,
            "description": check_description,
            # "doc_id":  # DOC_ID is generated as part of the payment voucher processes
            "event_type": "AP01",
            "first_last_name": f"{self.scenario_data.employee.first_name} {self.scenario_data.employee.last_name}",
            "i_value": payment.fineos_pei_i_value,
            "fineos_customer_number_employee": self.scenario_data.employee.fineos_customer_number,
            "leave_type": leave_type,
            "mmars_vendor_code": self.scenario_data.employee.ctr_vendor_customer_code,
            "payment_amount": (
                "{:.2f}".format(payment.amount)
                if not self.scenario_data.scenario_descriptor.missing_payment
                else None
            ),
            "payment_doc_id_code": "GAX",
            "payment_doc_id_dept": "EOL",
            "payment_period_end_date": payment_period_end_date,
            "payment_period_start_date": payment_period_start_date,
            "payment_preference": self.scenario_data.employee.payment_method.payment_method_description,
            "scheduled_payment_date": self.payment_date.strftime("%Y-%m-%d"),
            "state": self.address.geo_state.geo_state_description,
            "vendor_invoice_date": vendor_invoice_date,
            "vendor_invoice_line": "1",
            "vendor_invoice_number": vendor_invoice_number,
            "vendor_single_payment": "Yes",
            "zip": self.address.zip_code,
            "case_status": case_status,
            "employer_id": employer_id,
            "leave_request_id": self.scenario_data.leave_request_id,
            "leave_request_decision": self.scenario_data.leave_request_decision,
            "payment_event_type": self.scenario_data.payment_event_type,
            "vcm_flag": "Yes",  # This should be overridden as needed
            "absence_case_creation_date": absence_case_creation_date,
            "absence_reason_name": self.scenario_data.absence_reason_name,
            "claimants_that_have_zero_or_credit_value": (
                "1" if payment.amount is not None and float(payment.amount) <= 0 else ""
            ),
            "good_to_pay_from_prior_batch": "",
            "had_a_payment_in_a_prior_batch_by_vc_code": "",
            "inv": "",
            "payments_offset_to_zero": "",
            "is_exempt": "",
            "leave_decision_not_approved": "",
            "has_a_check_preference_with_an_adl2_issue": "",
            "adl2_corrected": "",
            "removed_or_added_after_audit_of_info": "",
            "to_be_removed_from_file": "",
            "notes": "",
        }

    def get_writeback_dict(self, payment: Payment) -> Dict[str, str]:
        return {
            "c_value": payment.fineos_pei_c_value,
            "i_value": payment.fineos_pei_i_value,
            "status": "" if self.inactive_writeback else "Active",
            "stock_no": "",
            "transaction_status": "",
            "trans_status_date": "2021-01-15 12:00:00",
        }


@dataclass
class StandardTestDataWrapper:
    scenario_outputs: List[ScenarioOutput]
    payment_extract_data: fineos_payment_export.ExtractData
    vendor_extract_data: fineos_vendor_export.ExtractData
    voucher_extract_data: payment_voucher.VoucherExtractData
    input_file_path: str


def get_standard_test_data(*, now, scenario_name, test_db_session, tmp_path, vcm_flag):
    """Helper function that generates mock files and database records

    Uses the FINEOS mock file and scenario generators.

    Requires pre-existing:
        - scenario_generator.ScenarioName
        - matching entry in scenario_generator.EmployeePaymentScenarioDescriptor in
          SCENARIO_DESCRIPTORS

    Parameters:
        - now: datetime.now(); for use with freezegun
        - scenario_name: scenario_generator.ScenarioName
        - vcm_flag: Optional[str]: for creating the correct StateLog entry
                    for a given scenario
    """
    # Seed to get reproducible output.
    random.seed(1)

    # Create a list of Payment Voucher scenarios we want to test.
    scenario_list = [scenario_generator.ScenarioNameWithCount(scenario_name, 1)]

    # Setup scenario configuration with random SSN and FEINs.
    fake = faker.Faker()
    scenario_config = scenario_generator.ScenarioDataConfig(
        scenario_list,
        ssn_id_base=fake.random_number(digits=9),
        fein_id_base=fake.random_number(digits=9),
    )

    # Generate the database records and extract files.
    file_path = os.path.join(tmp_path, "mock_fineos_payments_files")
    scenario_data_list = fineos_extract_generator.generate(scenario_config, file_path)

    # Create a dict of scenario output we assert against.
    scenario_outputs = {}
    for scenario_data in scenario_data_list:
        scenario_name = scenario_data.scenario_descriptor.scenario_name.name
        scenario_outputs[scenario_name] = ScenarioOutput(
            payment_date=now, scenario_data=scenario_data
        )
        employee = scenario_outputs[scenario_name].scenario_data.employee

        # Setup state logs.
        if vcm_flag in [VCM_FLAG_EMPTY, VCM_FLAG_MISSING]:
            setup_state_log_only(
                associated_model=employee,
                end_state=State.VCM_REPORT_SENT if vcm_flag else State.IDENTIFY_MMARS_STATUS,
                now=now,
                test_db_session=test_db_session,
            )

        # Overwrite vcm_flag.
        if vcm_flag == VCM_FLAG_EMPTY:
            vcm_flag_str = ""
        else:
            vcm_flag_str = payment_voucher.get_vcm_flag(employee, test_db_session)
        for row in scenario_outputs[scenario_name].payment_voucher_rows:
            row["vcm_flag"] = vcm_flag_str

    # Process generated extract files.
    input_files = []
    file_names = file_util.list_files(file_path)
    for file_name in file_names:
        input_files.append(os.path.join(file_path, file_name))

    # Read vpei.csv, vpeipaymentdetails.csv, vpeiclaimdetails.csv
    payment_extract_data = fineos_payment_export.ExtractData(input_files, "manual")
    fineos_payment_export.download_and_process_data(payment_extract_data, tmp_path)

    # Read VBI_REQUESTEDABSENCE_SOM.csv, Employee_feed.csv, LeavePlan_info.csv
    vendor_extract_data = fineos_vendor_export.ExtractData(input_files, "manual")
    fineos_vendor_export.download_and_index_data(vendor_extract_data, tmp_path)

    # Read the VBI_REQUESTEDABSENCE.csv
    # Not to be confused with the similarly named VBI_REQUESTEDABSENCE_SOM.csv
    voucher_extract_data = payment_voucher.VoucherExtractData(input_files)
    payment_voucher.download_and_index_voucher_data(voucher_extract_data, tmp_path)

    return StandardTestDataWrapper(
        scenario_outputs=scenario_outputs,
        payment_extract_data=payment_extract_data,
        vendor_extract_data=vendor_extract_data,
        voucher_extract_data=voucher_extract_data,
        input_file_path=file_path,
    )


# === TESTS BEGIN === #


@pytest.mark.parametrize(
    "scenario_name, vcm_flag",
    [
        (scenario_generator.ScenarioName.SCENARIO_VOUCHER_A, VCM_FLAG_NO),
        (scenario_generator.ScenarioName.SCENARIO_VOUCHER_B, VCM_FLAG_YES),
        (scenario_generator.ScenarioName.SCENARIO_VOUCHER_C, VCM_FLAG_NO),
        (scenario_generator.ScenarioName.SCENARIO_VOUCHER_D, VCM_FLAG_NO),
        (scenario_generator.ScenarioName.SCENARIO_VOUCHER_E, VCM_FLAG_NO),
        (scenario_generator.ScenarioName.SCENARIO_VOUCHER_F, VCM_FLAG_MISSING),
        (scenario_generator.ScenarioName.SCENARIO_VOUCHER_G, VCM_FLAG_NO),
        (scenario_generator.ScenarioName.SCENARIO_VOUCHER_H, VCM_FLAG_EMPTY),
        (scenario_generator.ScenarioName.SCENARIO_VOUCHER_I, VCM_FLAG_NO),
        (scenario_generator.ScenarioName.SCENARIO_VOUCHER_J, VCM_FLAG_NO),
        (scenario_generator.ScenarioName.SCENARIO_VOUCHER_K, VCM_FLAG_NO),
        (scenario_generator.ScenarioName.SCENARIO_VOUCHER_L, VCM_FLAG_NO),
        (scenario_generator.ScenarioName.SCENARIO_VOUCHER_M, VCM_FLAG_NO),
        (scenario_generator.ScenarioName.SCENARIO_VOUCHER_N, VCM_FLAG_NO),
    ],
)
@freezegun.freeze_time("2021-01-15 08:00:00", tz_offset=0)
def test_process_payment_record(
    initialize_factories_session, scenario_name, test_db_session, tmp_path, vcm_flag
):
    """Test the data within the CSVs is calculated and formatted as expected

    - Modify the scenarios and the mock file generators to modify the test data.
    - Modify ScenarioOutput and get_standard_test_data() to modify the logic.
    """
    output_csv = MockCSVWriter()
    writeback_csv = MockCSVWriter()

    standard_test_data = get_standard_test_data(
        now=datetime.now(),
        scenario_name=scenario_name,
        test_db_session=test_db_session,
        tmp_path=tmp_path,
        vcm_flag=vcm_flag,
    )
    voucher_scenario = standard_test_data.scenario_outputs[scenario_name.name]

    for i, payment in enumerate(voucher_scenario.scenario_data.payments):
        payment_ci = fineos_payment_export.CiIndex(
            c=payment.fineos_pei_c_value, i=payment.fineos_pei_i_value
        )
        pei_record = standard_test_data.payment_extract_data.pei.indexed_data[payment_ci]

        payment_voucher.process_payment_record(
            payment_extract_data=standard_test_data.payment_extract_data,
            vendor_extract_data=standard_test_data.vendor_extract_data,
            voucher_extract_data=standard_test_data.voucher_extract_data,
            ci_index=payment_ci,
            pei_record=pei_record,
            output_csv=output_csv,
            writeback_csv=writeback_csv,
            payment_date=date.today(),
            db_session=test_db_session,
            log_entry=MockLogEntry(),
        )

        doc_id = output_csv.rows[i]["doc_id"]
        assert re.match("^GAXMDFMLAAAA........$", doc_id)
        voucher_row = voucher_scenario.payment_voucher_rows[i]
        # DOC_ID is generated by the payment voucher process, so we substitute it in the output
        voucher_row["doc_id"] = doc_id
        assert output_csv.rows[i] == voucher_row
        assert writeback_csv.rows[i] == voucher_scenario.writeback_rows[i]

    assert len(output_csv.rows) == len(voucher_scenario.payment_voucher_rows)
    assert len(writeback_csv.rows) == len(voucher_scenario.writeback_rows)


@freezegun.freeze_time("2021-01-21 13:12:30", tz_offset=0)
def test_process_extracts_to_payment_voucher(
    test_db_session, initialize_factories_session, tmp_path
):
    """Test the CSVs are written out in the expected format

    - Modify the test files to modify the test data.
    """
    input_path = os.path.join(os.path.dirname(__file__), "test_files")

    for ssn in (
        "390666954",
        "235702221",
        "158786713",
        "037408790",
        "135407982",
        "003061455",
        "066360920",
    ):
        setup_state_log(
            associated_class=state_log_util.AssociatedClass.EMPLOYEE,
            end_states=[State.IDENTIFY_MMARS_STATUS],
            test_db_session=test_db_session,
            additional_params=AdditionalParams(
                tax_identifier=TaxIdentifier(tax_identifier=ssn),
                ctr_vendor_customer_code="VC00012300" + ssn[-2:],
            ),
        )

    test_db_session.add(
        EmployeeFactory(
            tax_identifier=TaxIdentifier(tax_identifier="375563922"), ctr_vendor_customer_code=None,
        )
    )

    # DOC ID in output is randomized so seed to get reproducible output.
    random.seed(1)

    payment_voucher.process_extracts_to_payment_voucher(
        input_path, tmp_path, None, None, test_db_session, MockLogEntry()
    )

    # Outcome:
    # Of the 22 vpei rows:
    # - 7 have employees seeded in the database and should have all the expected columns
    # - 1 has an employee without a VC code, state log entry, and from
    #   VBI_REQUSTEDABSENCE.csv so it should be missing a number of columns
    # - 14 are missing employees and missing from VBI_REQUESTEDABSENCE.csv, so should be
    #   missing a number of columns

    csv_output = open(os.path.join(tmp_path, "20210121_131230_payment_voucher.csv")).readlines()
    expected_output = open(os.path.join(input_path, "expected_payment_voucher.csv")).readlines()
    assert csv_output == expected_output

    writeback = open(os.path.join(tmp_path, "20210121_131230_writeback.csv")).readlines()
    expected_writeback = open(os.path.join(input_path, "expected_writeback.csv")).readlines()
    assert writeback == expected_writeback


@freezegun.freeze_time("2021-01-21 13:12:30", tz_offset=0)
def test_payment_voucher_step(
    test_db_session, initialize_factories_session, tmp_path, test_db_other_session
):
    # Verify that PaymentVoucher.run_step() is functionally equivalent
    # to process_extracts_to_payment_voucher().
    input_path = os.path.join(os.path.dirname(__file__), "test_files")

    for ssn in (
        "390666954",
        "235702221",
        "158786713",
        "037408790",
        "135407982",
        "003061455",
        "066360920",
    ):
        setup_state_log(
            associated_class=state_log_util.AssociatedClass.EMPLOYEE,
            end_states=[State.IDENTIFY_MMARS_STATUS],
            test_db_session=test_db_session,
            additional_params=AdditionalParams(
                tax_identifier=TaxIdentifier(tax_identifier=ssn),
                ctr_vendor_customer_code="VC00012300" + ssn[-2:],
            ),
        )

    test_db_session.add(
        EmployeeFactory(
            tax_identifier=TaxIdentifier(tax_identifier="375563922"), ctr_vendor_customer_code=None,
        )
    )

    # DOC ID in output is randomized so seed to get reproducible output.
    random.seed(1)

    output_file_path = os.path.join(tmp_path, "voucher_output")
    config = payment_voucher.Configuration([input_path, output_file_path])
    payment_voucher.PaymentVoucherStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session, config=config
    ).run_step()

    # Outcome:
    # Of the 22 vpei rows:
    # - 7 have employees seeded in the database and should have all the expected columns
    # - 1 has an employee without a VC code, state log entry, and from
    #   VBI_REQUSTEDABSENCE.csv so it should be missing a number of columns
    # - 14 are missing employees and missing from VBI_REQUESTEDABSENCE.csv, so should be
    #   missing a number of columns

    csv_output = open(
        os.path.join(tmp_path, "voucher_output", "20210121_131230_payment_voucher.csv")
    ).readlines()
    expected_output = open(os.path.join(input_path, "expected_payment_voucher.csv")).readlines()
    assert csv_output == expected_output

    writeback = open(
        os.path.join(tmp_path, "voucher_output", "20210121_131230_writeback.csv")
    ).readlines()
    expected_writeback = open(os.path.join(input_path, "expected_writeback.csv")).readlines()
    assert writeback == expected_writeback


def test_run_voucher_process(initialize_factories_session, test_db_session, tmp_path):
    # Create files with one payment.
    standard_test_data = get_standard_test_data(
        now=datetime.now(),
        scenario_name=scenario_generator.ScenarioName.SCENARIO_VOUCHER_A,
        test_db_session=test_db_session,
        tmp_path=tmp_path,
        vcm_flag=False,
    )

    # Run the process.
    output_file_path = os.path.join(tmp_path, "voucher_output")
    config = payment_voucher.Configuration([standard_test_data.input_file_path, output_file_path])
    payment_voucher.run_voucher_process(config)

    # Validate the outcome.
    output_files = file_util.list_files(output_file_path)
    voucher_file = None
    writeback_file = None
    for file_path in output_files:
        if file_path.endswith("payment_voucher.csv"):
            voucher_file = os.path.join(output_file_path, file_path)
        if file_path.endswith("writeback.csv"):
            writeback_file = os.path.join(output_file_path, file_path)

    # Validate that files were generated.
    assert len(output_files) == 9
    assert voucher_file is not None
    assert writeback_file is not None

    # Validate the payment voucher.
    payment_voucher_rows = list(CSVSourceWrapper(voucher_file))
    assert len(payment_voucher_rows) == 2

    # Validate the writeback.
    writeback_rows = list(CSVSourceWrapper(writeback_file))
    assert len(writeback_rows) == 2
