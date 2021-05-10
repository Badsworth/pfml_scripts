import csv
import os

import pytest
from freezegun import freeze_time
from smart_open import open as smart_open

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.config as payments_config
import massgov.pfml.payments.error_reports as error_reports
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.payments.reporting.error_reporting as error_reporting
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import Flow, LkState, Payment, State, StateLog
from massgov.pfml.db.models.factories import ClaimFactory, PaymentFactory
from tests.helpers.state_log import AdditionalParams, setup_state_log

# every test in here requires real resources
pytestmark = pytest.mark.integration

EXPECTED_DESCRIPTION = (
    "RecordName\nThis is a description of the problem\nMissingInDB:Field1\nMissingField:Field2"
)


def setup_state_log_in_end_state(associated_class, end_state, test_db_session, additional_params):
    # Yep, it's a test util wrapping a test util
    validation_container = payments_util.ValidationContainer("RecordName")
    validation_container.add_validation_issue(
        payments_util.ValidationReason.MISSING_IN_DB, "Field1"
    )
    validation_container.add_validation_issue(
        payments_util.ValidationReason.MISSING_FIELD, "Field2"
    )

    additional_params.outcome = state_log_util.build_outcome(
        "This is a description of the problem", validation_container=validation_container
    )

    # Note, we always create a prior state for each of these
    # from State.PAYMENTS_RETRIVED -> State.VERIFY_VENDOR_STATUS (both unused states)
    state_log_results = setup_state_log(
        associated_class=associated_class,
        end_states=[State.VERIFY_VENDOR_STATUS, end_state],
        test_db_session=test_db_session,
        additional_params=additional_params,
    )

    # If this is set, we want to associate the created payment with a state log as well.
    if additional_params.add_claim_payment_for_employee:
        add_mmars_payments_for_claim(
            state_log_results.state_logs[1].employee.claims[0], test_db_session
        )

    return state_log_results


def parse_csv(s3_prefix, file_name):
    path = os.path.join(s3_prefix, file_name)
    with smart_open(path) as csv_file:
        reader = csv.DictReader(csv_file, delimiter=",")
        records = [record for record in reader]
        # These records tend to come in the same order we created them, but add a sort
        # command to make certain they're sorted by the customer number (which should always be present)
        sorted(records, key=lambda record: record[error_reporting.FINEOS_CUSTOMER_NUM_COLUMN])
        return records


def validate_fineos_files(date_str, file_names):
    # All files are in a subdirectory and will look like
    # 2020-01-01/2020-01-01-07-00-00-filename.csv

    # Date str comes in with a full timestamp, but the folder is just
    # the date, so pull the date out of that.
    date = date_str[:10]

    assert file_names[0] == f"{date}/{date_str}-CPS-payment-export-error-report.csv"
    assert file_names[1] == f"{date}/{date_str}-CPS-vendor-export-error-report.csv"


def validate_ctr_files(date_str, file_names):
    # All files are in a subdirectory and will look like
    # 2020-01-01/2020-01-01-07-00-00-filename.csv

    # Date str comes in with a full timestamp, but the folder is just
    # the date, so pull the date out of that.
    date = date_str[:10]

    # API-1489 disabled time-based error reports, so commenting them out for now
    # assert file_names[0] == f"{date}/{date_str}-EFT-audit-error-report.csv"
    # assert file_names[1] == f"{date}/{date_str}-EFT-error-report.csv"
    # assert file_names[2] == f"{date}/{date_str}-GAX-error-report.csv"
    # assert file_names[3] == f"{date}/{date_str}-VCC-error-report.csv"
    # assert file_names[4] == f"{date}/{date_str}-VCM-report.csv"
    # assert file_names[5] == f"{date}/{date_str}-payment-audit-error-report.csv"
    # assert file_names[6] == f"{date}/{date_str}-vendor-audit-error-report.csv"

    assert file_names[0] == f"{date}/{date_str}-EFT-error-report.csv"
    assert file_names[1] == f"{date}/{date_str}-GAX-error-report.csv"
    assert file_names[2] == f"{date}/{date_str}-VCC-error-report.csv"
    assert file_names[3] == f"{date}/{date_str}-VCM-report.csv"


def add_mmars_payments_for_claim(claim, test_db_session):
    # When we create an employee-based StateLog in setup_state_log_in_end_state
    # It creates a payment associated with the Claim and Employee, but that payment
    # has no state associated.
    payments = test_db_session.query(Payment).filter(Payment.claim_id == claim.claim_id).all()
    for payment in payments:
        state_log_util.create_finished_state_log(
            end_state=State.CONFIRM_VENDOR_STATUS_IN_MMARS,
            associated_model=payment,
            db_session=test_db_session,
            outcome={},
        )

    return payments


def test_parse_outcome(test_db_session, initialize_factories_session):
    # Make a generic state log to put the outcome in
    state_log = StateLog()

    # Test if outcome isn't set
    state_log.outcome = None
    outcome = error_reports._parse_outcome(state_log)
    assert outcome.key is None
    assert outcome.description == error_reports.GENERIC_OUTCOME_MSG

    # Test if outcome is set, but has no message
    state_log.outcome = {"data": "not relevant"}
    outcome = error_reports._parse_outcome(state_log)
    assert outcome.key is None
    assert outcome.description == error_reports.GENERIC_OUTCOME_MSG

    # Test if outcome is set with a message and no validation container
    state_log.outcome = state_log_util.build_outcome("this is a message")
    outcome = error_reports._parse_outcome(state_log)
    assert outcome.key is None
    assert outcome.description == "this is a message"

    # Test if outcome is set with a message + a validation container
    validation_container = payments_util.ValidationContainer("RecordName")
    validation_container.add_validation_issue(
        payments_util.ValidationReason.MISSING_IN_DB, "Field1"
    )
    validation_container.add_validation_issue(
        payments_util.ValidationReason.MISSING_FIELD, "Field2"
    )
    state_log.outcome = state_log_util.build_outcome("message again", validation_container)
    outcome = error_reports._parse_outcome(state_log)

    assert outcome.key == "RecordName"
    assert (
        outcome.description == "RecordName\nmessage again\nMissingInDB:Field1\nMissingField:Field2"
    )


def test_get_employee_claim_payment_from_state_log_single_payment(
    test_db_session, initialize_factories_session
):
    # Testing the scenario when
    # An EMPLOYEE has ONE claim and ONE payment in CONFIRM_VENDOR_STATUS_IN_MMARS
    # This is a sort of happy path where we can get the claim+payment for an employee
    state_log_results = setup_state_log_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.ADD_TO_VCC_ERROR_REPORT,
        test_db_session=test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="012345678",
            fineos_absence_id="NTN-01-ABS-01",
            add_claim_payment_for_employee=True,
        ),
    )
    assert len(state_log_results.state_logs) == 2

    db_models = error_reports._get_employee_claim_payment_from_state_log(
        state_log_util.AssociatedClass.EMPLOYEE, state_log_results.state_logs[1], test_db_session
    )

    # These should all be set
    assert db_models.is_valid
    assert db_models.employee
    assert db_models.claim
    assert db_models.payment

    # Just to be certain, make sure the IDs of the values we had BEFORE the test match what came out
    assert state_log_results.state_logs[1].employee.claims[0].claim_id == db_models.claim.claim_id
    assert state_log_results.state_logs[1].employee.employee_id == db_models.employee.employee_id


def test_get_employee_claim_payment_from_state_log_multiple_mmars_payments(
    test_db_session, initialize_factories_session
):
    # Testing the scenario when
    # An EMPLOYEE has ONE claim and TWO payments in CONFIRM_VENDOR_STATUS_IN_MMARS
    # In this case, we should not return any claim or payment
    state_log_results = setup_state_log_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.ADD_TO_VCC_ERROR_REPORT,
        test_db_session=test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="012345678",
            fineos_absence_id="NTN-01-ABS-01",
            add_claim_payment_for_employee=True,
        ),
    )
    assert len(state_log_results.state_logs) == 2
    # We need to add a second payment to the employee/claim
    claim = state_log_results.state_logs[1].employee.claims[0]
    PaymentFactory(claim=claim)

    add_mmars_payments_for_claim(claim, test_db_session)

    db_models = error_reports._get_employee_claim_payment_from_state_log(
        state_log_util.AssociatedClass.EMPLOYEE, state_log_results.state_logs[0], test_db_session
    )

    assert db_models.is_valid
    assert db_models.employee
    assert db_models.claim is None
    assert db_models.payment is None
    assert state_log_results.state_logs[0].employee.employee_id == db_models.employee.employee_id


def test_get_employee_claim_payment_from_state_log_multiple_mmars_claims(
    test_db_session, initialize_factories_session
):
    # Testing the scenario when
    # An EMPLOYEE has TWO claims each with a payment in CONFIRM_VENDOR_STATUS_IN_MMARS
    # In this case, we should not return any claim or payment
    state_log_results = setup_state_log_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.ADD_TO_VCC_ERROR_REPORT,
        test_db_session=test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="012345678",
            fineos_absence_id="NTN-01-ABS-01",
            add_claim_payment_for_employee=True,
        ),
    )
    assert len(state_log_results.state_logs) == 2
    claim1 = state_log_results.state_logs[1].employee.claims[0]
    # We need to add a second claim to the employee
    claim2 = ClaimFactory.create(
        employer_id=claim1.employer_id,
        fineos_absence_id="NTN-02-ABS-02",
        employee_id=claim1.employee_id,
    )
    PaymentFactory(claim=claim2)
    add_mmars_payments_for_claim(claim2, test_db_session)
    # Make certain that both claims are properly set in the model (it's not going to refetch the state_log)
    state_log_results.state_logs[1].employee.claims = [claim1, claim2]

    db_models = error_reports._get_employee_claim_payment_from_state_log(
        state_log_util.AssociatedClass.EMPLOYEE, state_log_results.state_logs[1], test_db_session
    )

    assert db_models.employee
    assert db_models.claim is None
    assert db_models.payment is None
    assert state_log_results.state_logs[1].employee.employee_id == db_models.employee.employee_id


@freeze_time("2020-01-01 12:00:00")
def test_send_fineos_payments_errors_empty_db(
    test_db_session, initialize_factories_session, mock_ses, set_exporter_env_vars
):
    s3_prefix = payments_config.get_s3_config().pfml_error_reports_path
    # If there is nothing in a bad state, this should just create
    # a bunch of CSVs with just a header
    error_reports._send_fineos_payments_errors(test_db_session)

    file_names = file_util.list_files(s3_prefix, recursive=True)
    assert len(file_names) == 2  # 2 total reports
    file_names.sort()
    validate_fineos_files("2020-01-01-07-00-00", file_names)

    for file_name in file_names:
        with smart_open(os.path.join(s3_prefix, file_name)) as csv_file:
            reader = csv.reader(csv_file, delimiter=",")
            lines = [row for row in reader]
            assert len(lines) == 1
            assert lines[0] == error_reporting.CSV_HEADER

    # As a sanity check, even afterwards, no state logs should
    # be updated/exist
    test_db_session.commit()
    after_state_logs = test_db_session.query(StateLog).all()
    assert len(after_state_logs) == 0


@freeze_time("2020-01-01 12:00:00")
def test_send_ctr_payments_errors_empty_db(
    test_db_session, initialize_factories_session, mock_ses, set_exporter_env_vars
):
    s3_prefix = payments_config.get_s3_config().pfml_error_reports_path
    # If there is nothing in a bad state, this should just create
    # a bunch of CSVs with just a header
    error_reports._send_ctr_payments_errors(test_db_session)

    file_names = file_util.list_files(s3_prefix, recursive=True)
    assert len(file_names) == 4
    # API-1489 disabled time-based reports, so this is now 4 instead of 7 total reports
    file_names.sort()
    validate_ctr_files("2020-01-01-07-00-00", file_names)

    for file_name in file_names:
        with smart_open(os.path.join(s3_prefix, file_name)) as csv_file:
            reader = csv.reader(csv_file, delimiter=",")
            lines = [row for row in reader]
            assert len(lines) == 1
            assert lines[0] == error_reporting.CSV_HEADER

    # As a sanity check, even afterwards, no state logs should
    # be updated/exist
    test_db_session.commit()
    after_state_logs = test_db_session.query(StateLog).all()
    assert len(after_state_logs) == 0


@freeze_time("2020-01-01 12:00:00")
def test_send_fineos_payments_errors(
    test_db_session, initialize_factories_session, mock_ses, set_exporter_env_vars
):
    test_db_session.begin_nested()

    s3_prefix = payments_config.get_s3_config().pfml_error_reports_path
    # Setup for cps_payment_export_report
    setup_state_log_in_end_state(
        state_log_util.AssociatedClass.PAYMENT,
        end_state=State.ADD_TO_PAYMENT_EXPORT_ERROR_REPORT,
        test_db_session=test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="000000000", fineos_absence_id="NTN-00-ABS-00",
        ),
    )

    # Setup for cps_vendor_export_report (adding 2 records)
    setup_state_log_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.ADD_TO_VENDOR_EXPORT_ERROR_REPORT,
        test_db_session=test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="000000001",
            fineos_absence_id="NTN-01-ABS-01",
            add_claim_payment_for_employee=False,  # No payment or claim data will be found
        ),
    )

    setup_state_log_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.ADD_TO_VENDOR_EXPORT_ERROR_REPORT,
        test_db_session=test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="000000002",
            fineos_absence_id="NTN-02-ABS-02",
            add_claim_payment_for_employee=True,  # Will add claim+payment DB entries + payment state log in CONFIRM_VENDOR_STATUS_IN_MMARS
        ),
    )
    test_db_session.commit()
    test_db_session.begin_nested()

    error_reports._send_fineos_payments_errors(test_db_session)

    file_names = file_util.list_files(s3_prefix, recursive=True)
    assert len(file_names) == 2  # 2 total reports
    file_names.sort()
    validate_fineos_files("2020-01-01-07-00-00", file_names)

    cps_payment_records = parse_csv(s3_prefix, file_names[0])
    assert len(cps_payment_records) == 1
    assert cps_payment_records[0] == {
        error_reporting.DESCRIPTION_COLUMN: EXPECTED_DESCRIPTION,
        error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000000",
        error_reporting.FINEOS_ABSENCE_ID_COLUMN: "NTN-00-ABS-00",
        error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "",
        error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",
        error_reporting.PAYMENT_DATE_COLUMN: "01/07/2020",
    }
    cps_vendor_records = parse_csv(s3_prefix, file_names[1])
    assert len(cps_vendor_records) == 2
    assert cps_vendor_records[0] == {
        error_reporting.DESCRIPTION_COLUMN: EXPECTED_DESCRIPTION,
        error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000001",
        error_reporting.FINEOS_ABSENCE_ID_COLUMN: "",  # Not found because no payment/claims attached
        error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "",
        error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",
        error_reporting.PAYMENT_DATE_COLUMN: "",
    }
    assert cps_vendor_records[1] == {
        error_reporting.DESCRIPTION_COLUMN: EXPECTED_DESCRIPTION,
        error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000002",
        error_reporting.FINEOS_ABSENCE_ID_COLUMN: "NTN-02-ABS-02",
        error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "",
        error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",
        error_reporting.PAYMENT_DATE_COLUMN: "01/07/2020",
    }

    # Show that we can do a rollback

    # 7 total state logs:
    # 3 calls to setup_state_log_in_end_state (created employee or payment state logs)
    # 3 prior states created in setup_state_log_in_end_state
    #    the one setup_state_log_in_end_state call with add_claim_payment_for_employee=True created an addtional payment state log
    # the 3 records created to move the payment/employee state logs to the next state.
    state_logs = test_db_session.query(StateLog).all()
    assert len(state_logs) == 10
    test_db_session.rollback()
    # the 3 created as part of processing no longer exist
    rolled_back_state_logs = test_db_session.query(StateLog).all()
    assert len(rolled_back_state_logs) == 7


@freeze_time("2020-01-01 12:00:00")
def test_vendor_extract_error_report_step(
    test_db_session,
    initialize_factories_session,
    mock_ses,
    set_exporter_env_vars,
    test_db_other_session,
):
    test_db_session.begin_nested()
    # Verify that the VendorExtractErrorReportStep.run_step() is functionally equivalent
    # to send_fineos_payments_errors() for just the vendor report.
    s3_prefix = payments_config.get_s3_config().pfml_error_reports_path

    # Setup for cps_vendor_export_report (adding 2 records)
    setup_state_log_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.ADD_TO_VENDOR_EXPORT_ERROR_REPORT,
        test_db_session=test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="000000001",
            fineos_absence_id="NTN-01-ABS-01",
            add_claim_payment_for_employee=False,  # No payment or claim data will be found
        ),
    )

    setup_state_log_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.ADD_TO_VENDOR_EXPORT_ERROR_REPORT,
        test_db_session=test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="000000002",
            fineos_absence_id="NTN-02-ABS-02",
            add_claim_payment_for_employee=True,  # Will add claim+payment DB entries + payment state log in CONFIRM_VENDOR_STATUS_IN_MMARS
        ),
    )
    test_db_session.commit()
    test_db_session.begin_nested()

    error_reports.VendorExtractErrorReportStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    ).run_step()

    file_names = file_util.list_files(s3_prefix, recursive=True)
    assert len(file_names) == 1
    assert file_names[0] == "2020-01-01/2020-01-01-07-00-00-CPS-vendor-export-error-report.csv"

    cps_vendor_records = parse_csv(s3_prefix, file_names[0])
    assert len(cps_vendor_records) == 2
    assert cps_vendor_records[0] == {
        error_reporting.DESCRIPTION_COLUMN: EXPECTED_DESCRIPTION,
        error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000001",
        error_reporting.FINEOS_ABSENCE_ID_COLUMN: "",  # Not found because no payment/claims attached
        error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "",
        error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",
        error_reporting.PAYMENT_DATE_COLUMN: "",
    }
    assert cps_vendor_records[1] == {
        error_reporting.DESCRIPTION_COLUMN: EXPECTED_DESCRIPTION,
        error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000002",
        error_reporting.FINEOS_ABSENCE_ID_COLUMN: "NTN-02-ABS-02",
        error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "",
        error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",
        error_reporting.PAYMENT_DATE_COLUMN: "01/07/2020",
    }

    # Show that we can do a rollback

    # 7 total state logs:
    # 2 calls to setup_state_log_in_end_state (created employee or payment state logs)
    # 2 prior states created in setup_state_log_in_end_state
    #    the one setup_state_log_in_end_state call with add_claim_payment_for_employee=True created an addtional payment state log
    # the 2 records created to move the payment/employee state logs to the next state.
    state_logs = test_db_session.query(StateLog).all()
    assert len(state_logs) == 7
    test_db_session.rollback()
    # the 2 created as part of processing no longer exist
    rolled_back_state_logs = test_db_session.query(StateLog).all()
    assert len(rolled_back_state_logs) == 5


@freeze_time("2020-01-01 12:00:00")
def test_send_ctr_payments_errors_simple_reports(
    local_test_db_session, local_initialize_factories_session, mock_ses, set_exporter_env_vars
):
    s3_prefix = payments_config.get_s3_config().pfml_error_reports_path
    # In the interest of keeping this single test at only 200 lines,
    # the time-based reports are in the next test (test_send_ctr_payments_errors_time_based_reports)

    # Setup for Gax Error Report
    setup_state_log_in_end_state(
        state_log_util.AssociatedClass.PAYMENT,
        end_state=State.ADD_TO_GAX_ERROR_REPORT,
        test_db_session=local_test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="000000000",
            fineos_absence_id="NTN-00-ABS-00",
            ctr_vendor_customer_code="VEND-00",
        ),
    )

    # Setup for VCC Error Report
    setup_state_log_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.ADD_TO_VCC_ERROR_REPORT,
        test_db_session=local_test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="000000001",
            fineos_absence_id="NTN-01-ABS-01",
            ctr_vendor_customer_code="VEND-01",
            add_claim_payment_for_employee=False,  # No payment or claim data will be found
        ),
    )

    setup_state_log_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.ADD_TO_VCC_ERROR_REPORT,
        test_db_session=local_test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="000000002",
            fineos_absence_id="NTN-02-ABS-02",
            ctr_vendor_customer_code="VEND-02",
            add_claim_payment_for_employee=True,  # It will find payment/claim data
        ),
    )

    # Setup for VCM Report
    setup_state_log_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.ADD_TO_VCM_REPORT,
        test_db_session=local_test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="000000003",
            fineos_absence_id="NTN-03-ABS-03",
            ctr_vendor_customer_code="VEND-03",
            add_claim_payment_for_employee=False,  # No payment or claim data will be found
        ),
    )

    setup_state_log_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.ADD_TO_VCM_REPORT,
        test_db_session=local_test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="000000004",
            fineos_absence_id="NTN-04-ABS-04",
            ctr_vendor_customer_code="VEND-04",
            add_claim_payment_for_employee=True,  # It will find payment/claim data
        ),
    )

    setup_state_log_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.VCM_REPORT_SENT,
        test_db_session=local_test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="000000007",
            fineos_absence_id="NTN-07-ABS-07",
            ctr_vendor_customer_code="VEND-07",
            add_claim_payment_for_employee=True,  # It will find payment/claim data
        ),
    )

    # Setup for EFT Error report
    setup_state_log_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.ADD_TO_EFT_ERROR_REPORT,
        test_db_session=local_test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="000000005",
            fineos_absence_id="NTN-05-ABS-05",
            ctr_vendor_customer_code="VEND-05",
            add_claim_payment_for_employee=False,  # No payment or claim data will be found
        ),
    )

    setup_state_log_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.ADD_TO_EFT_ERROR_REPORT,
        test_db_session=local_test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="000000006",
            fineos_absence_id="NTN-06-ABS-06",
            ctr_vendor_customer_code="VEND-06",
            add_claim_payment_for_employee=True,  # It will find payment/claim data
        ),
    )
    local_test_db_session.commit()

    # Finally call the method after all that setup
    error_reports._send_ctr_payments_errors(local_test_db_session)

    file_names = file_util.list_files(s3_prefix, recursive=True)
    assert len(file_names) == 4
    # API-1489 disabled time-based reports, so this is now 4 instead of 7 total reports
    file_names.sort()
    validate_ctr_files("2020-01-01-07-00-00", file_names)

    eft_records = parse_csv(s3_prefix, file_names[0])
    assert len(eft_records) == 2
    assert eft_records[0] == {
        error_reporting.DESCRIPTION_COLUMN: EXPECTED_DESCRIPTION,
        error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000005",
        error_reporting.FINEOS_ABSENCE_ID_COLUMN: "",  # Not found because no payment/claims attached
        error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "VEND-05",
        error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",  # Explicitly not set
        error_reporting.PAYMENT_DATE_COLUMN: "",  # Not found because no payment/claims attached
    }
    assert eft_records[1] == {
        error_reporting.DESCRIPTION_COLUMN: EXPECTED_DESCRIPTION,
        error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000006",
        error_reporting.FINEOS_ABSENCE_ID_COLUMN: "NTN-06-ABS-06",
        error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "VEND-06",
        error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",  # Explicitly not set
        error_reporting.PAYMENT_DATE_COLUMN: "01/07/2020",
    }

    gax_records = parse_csv(s3_prefix, file_names[1])
    assert len(gax_records) == 1
    assert gax_records[0] == {
        error_reporting.DESCRIPTION_COLUMN: EXPECTED_DESCRIPTION,
        error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000000",
        error_reporting.FINEOS_ABSENCE_ID_COLUMN: "NTN-00-ABS-00",
        error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "VEND-00",
        error_reporting.MMARS_DOCUMENT_ID_COLUMN: "RecordName",
        error_reporting.PAYMENT_DATE_COLUMN: "01/07/2020",
    }

    vcc_records = parse_csv(s3_prefix, file_names[2])
    assert len(vcc_records) == 2
    assert vcc_records[0] == {
        error_reporting.DESCRIPTION_COLUMN: EXPECTED_DESCRIPTION,
        error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000001",
        error_reporting.FINEOS_ABSENCE_ID_COLUMN: "",  # Not found because no payment/claims attached
        error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "VEND-01",
        error_reporting.MMARS_DOCUMENT_ID_COLUMN: "RecordName",
        error_reporting.PAYMENT_DATE_COLUMN: "",  # Not found because no payment/claims attached
    }
    assert vcc_records[1] == {
        error_reporting.DESCRIPTION_COLUMN: EXPECTED_DESCRIPTION,
        error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000002",
        error_reporting.FINEOS_ABSENCE_ID_COLUMN: "NTN-02-ABS-02",
        error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "VEND-02",
        error_reporting.MMARS_DOCUMENT_ID_COLUMN: "RecordName",
        error_reporting.PAYMENT_DATE_COLUMN: "01/07/2020",
    }

    vcm_records = parse_csv(s3_prefix, file_names[3])
    assert len(vcm_records) == 3
    assert vcm_records[0] == {
        error_reporting.DESCRIPTION_COLUMN: EXPECTED_DESCRIPTION,
        error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000003",
        error_reporting.FINEOS_ABSENCE_ID_COLUMN: "",  # Not found because no payment/claims attached
        error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "VEND-03",
        error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",  # Explicitly not set
        error_reporting.PAYMENT_DATE_COLUMN: "",  # Not found because no payment/claims attached
    }
    assert vcm_records[1] == {
        error_reporting.DESCRIPTION_COLUMN: EXPECTED_DESCRIPTION,
        error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000004",
        error_reporting.FINEOS_ABSENCE_ID_COLUMN: "NTN-04-ABS-04",
        error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "VEND-04",
        error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",  # Explicitly not set
        error_reporting.PAYMENT_DATE_COLUMN: "01/07/2020",
    }

    assert vcm_records[2] == {
        error_reporting.DESCRIPTION_COLUMN: EXPECTED_DESCRIPTION,
        error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000007",
        error_reporting.FINEOS_ABSENCE_ID_COLUMN: "NTN-07-ABS-07",
        error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "VEND-07",
        error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",  # Explicitly not set
        error_reporting.PAYMENT_DATE_COLUMN: "01/07/2020",
    }

    # Show that we can do a rollback

    # 28 total state logs
    # 8 calls to setup_state_log_in_end_state (created employee or payment state logs)
    # 8 prior states created in setup_state_log_in_end_state
    #   4 additional created when we add_claim_payment_for_employee=True and created an additional payment state log
    # the 8 records created to move the payment/employee state logs to the next state.
    state_logs = local_test_db_session.query(StateLog).all()
    assert len(state_logs) == 28
    local_test_db_session.rollback()
    # the 8 created as part of processing no longer exist
    rolled_back_state_logs = local_test_db_session.query(StateLog).all()
    assert len(rolled_back_state_logs) == 20


@freeze_time("2020-01-01 12:00:00")
def test_send_ctr_payments_errors_eft_pending(
    test_db_session, initialize_factories_session, mock_ses, set_exporter_env_vars
):
    test_db_session.begin_nested()

    # Setup for VCM Report
    setup_state_log_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.ADD_TO_VCM_REPORT,
        test_db_session=test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="000000003",
            fineos_absence_id="NTN-03-ABS-03",
            ctr_vendor_customer_code="VEND-03",
            add_claim_payment_for_employee=False,  # No payment or claim data will be found
            add_eft=True,
        ),
    )

    setup_state_log_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.ADD_TO_VCM_REPORT,
        test_db_session=test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="000000004",
            fineos_absence_id="NTN-04-ABS-04",
            ctr_vendor_customer_code="VEND-04",
            add_claim_payment_for_employee=True,  # It will find payment/claim data
            add_eft=True,
        ),
    )

    test_db_session.commit()

    # Finally call the method after all that setup
    error_reports._send_ctr_payments_errors(test_db_session)

    # Confirm state logs for VENDOR_EFT flow
    state_logs = (
        test_db_session.query(StateLog)
        .join(LkState, StateLog.end_state_id == LkState.state_id)
        .filter(LkState.flow_id == Flow.VENDOR_EFT.flow_id)
        .all()
    )
    assert len(state_logs) == 2
    for state_log in state_logs:
        assert state_log.end_state_id == State.EFT_PENDING.state_id


# API-1489 disabled time-based reports, so commenting this out for now
# @freeze_time("2020-04-01 12:00:00")
# def test_send_ctr_payments_errors_time_based_reports(
#     test_db_session, initialize_factories_session, mock_ses, set_exporter_env_vars
# ):
#     s3_prefix = payments_config.get_s3_config().pfml_error_reports_path
#     # Note, for the sake of this test, all state logs are too old/stuck
#     # The utilities used in this test create the records on 2020-01-01, so we've set "now" to 2020-04-01

#     # Gax error report stuck setup
#     setup_state_log_in_end_state(
#         state_log_util.AssociatedClass.PAYMENT,
#         end_state=State.GAX_ERROR_REPORT_SENT,
#         test_db_session=test_db_session,
#         additional_params=AdditionalParams(
#             fineos_customer_num="000000000",
#             fineos_absence_id="NTN-00-ABS-00",
#             ctr_vendor_customer_code="VEND-00",
#         ),
#     )

#     # Gax stuck setup
#     setup_state_log_in_end_state(
#         state_log_util.AssociatedClass.PAYMENT,
#         end_state=State.GAX_SENT,
#         test_db_session=test_db_session,
#         additional_params=AdditionalParams(
#             fineos_customer_num="000000001",
#             fineos_absence_id="NTN-01-ABS-01",
#             ctr_vendor_customer_code="VEND-01",
#         ),
#     )

#     # CONFIRM_VENDOR_STATUS_IN_MMARS stuck setup
#     setup_state_log_in_end_state(
#         state_log_util.AssociatedClass.PAYMENT,
#         end_state=State.CONFIRM_VENDOR_STATUS_IN_MMARS,
#         test_db_session=test_db_session,
#         additional_params=AdditionalParams(
#             fineos_customer_num="000000002",
#             fineos_absence_id="NTN-02-ABS-02",
#             ctr_vendor_customer_code="VEND-02",
#         ),
#     )

#     # VCM report sent setup
#     setup_state_log_in_end_state(
#         state_log_util.AssociatedClass.EMPLOYEE,
#         end_state=State.VCM_REPORT_SENT,
#         test_db_session=test_db_session,
#         additional_params=AdditionalParams(
#             fineos_customer_num="000000003",
#             fineos_absence_id="NTN-03-ABS-03",
#             ctr_vendor_customer_code="VEND-03",
#             add_claim_payment_for_employee=False,  # No payment or claim data will be found
#         ),
#     )

#     setup_state_log_in_end_state(
#         state_log_util.AssociatedClass.EMPLOYEE,
#         end_state=State.VCM_REPORT_SENT,
#         test_db_session=test_db_session,
#         additional_params=AdditionalParams(
#             fineos_customer_num="000000004",
#             fineos_absence_id="NTN-04-ABS-04",
#             ctr_vendor_customer_code="VEND-04",
#             add_claim_payment_for_employee=True,  # It will find payment/claim data
#         ),
#     )

#     # VCC sent setup
#     setup_state_log_in_end_state(
#         state_log_util.AssociatedClass.EMPLOYEE,
#         end_state=State.VCC_SENT,
#         test_db_session=test_db_session,
#         additional_params=AdditionalParams(
#             fineos_customer_num="000000005",
#             fineos_absence_id="NTN-05-ABS-05",
#             ctr_vendor_customer_code="VEND-05",
#             add_claim_payment_for_employee=False,  # No payment or claim data will be found
#         ),
#     )

#     setup_state_log_in_end_state(
#         state_log_util.AssociatedClass.EMPLOYEE,
#         end_state=State.VCC_SENT,
#         test_db_session=test_db_session,
#         additional_params=AdditionalParams(
#             fineos_customer_num="000000006",
#             fineos_absence_id="NTN-06-ABS-06",
#             ctr_vendor_customer_code="VEND-06",
#             add_claim_payment_for_employee=True,  # It will find payment/claim data
#         ),
#     )

#     # VCC error report sent setup
#     setup_state_log_in_end_state(
#         state_log_util.AssociatedClass.EMPLOYEE,
#         end_state=State.VCC_ERROR_REPORT_SENT,
#         test_db_session=test_db_session,
#         additional_params=AdditionalParams(
#             fineos_customer_num="000000007",
#             fineos_absence_id="NTN-07-ABS-07",
#             ctr_vendor_customer_code="VEND-07",
#             add_claim_payment_for_employee=False,  # No payment or claim data will be found
#         ),
#     )

#     setup_state_log_in_end_state(
#         state_log_util.AssociatedClass.EMPLOYEE,
#         end_state=State.VCC_ERROR_REPORT_SENT,
#         test_db_session=test_db_session,
#         additional_params=AdditionalParams(
#             fineos_customer_num="000000008",
#             fineos_absence_id="NTN-08-ABS-08",
#             ctr_vendor_customer_code="VEND-08",
#             add_claim_payment_for_employee=True,  # It will find payment/claim data
#         ),
#     )

#     # EFT pending report sent
#     setup_state_log_in_end_state(
#         state_log_util.AssociatedClass.EMPLOYEE,
#         end_state=State.EFT_PENDING,
#         test_db_session=test_db_session,
#         additional_params=AdditionalParams(
#             fineos_customer_num="000000009",
#             fineos_absence_id="NTN-09-ABS-09",
#             ctr_vendor_customer_code="VEND-09",
#             add_claim_payment_for_employee=False,  # No payment or claim data will be found
#         ),
#     )

#     setup_state_log_in_end_state(
#         state_log_util.AssociatedClass.EMPLOYEE,
#         end_state=State.EFT_PENDING,
#         test_db_session=test_db_session,
#         additional_params=AdditionalParams(
#             fineos_customer_num="000000010",
#             fineos_absence_id="NTN-10-ABS-10",
#             ctr_vendor_customer_code="VEND-10",
#             add_claim_payment_for_employee=True,  # It will find payment/claim data
#         ),
#     )
#     test_db_session.commit()

#     # Finally call the method after all that setup
#     error_reports._send_ctr_payments_errors(test_db_session)

#     file_names = file_util.list_files(s3_prefix, recursive=True)
#     assert len(file_names) == 7  # 7 total reports
#     file_names.sort()
#     validate_ctr_files("2020-04-01-08-00-00", file_names)

#     eft_audit_records = parse_csv(s3_prefix, file_names[0])
#     assert len(eft_audit_records) == 2
#     assert eft_audit_records[0] == {
#         error_reporting.DESCRIPTION_COLUMN: "Process has been stuck for 15 days in [EFT pending] without a resolution.",
#         error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000009",
#         error_reporting.FINEOS_ABSENCE_ID_COLUMN: "",  # Not found because no payment/claims attached
#         error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "VEND-09",
#         error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",  # Never set for time based reports
#         error_reporting.PAYMENT_DATE_COLUMN: "",  # Not found because no payment/claims attached
#     }
#     assert eft_audit_records[1] == {
#         error_reporting.DESCRIPTION_COLUMN: "Process has been stuck for 15 days in [EFT pending] without a resolution.",
#         error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000010",
#         error_reporting.FINEOS_ABSENCE_ID_COLUMN: "NTN-10-ABS-10",
#         error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "VEND-10",
#         error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",  # Never set for time based reports
#         error_reporting.PAYMENT_DATE_COLUMN: "01/07/2020",
#     }

#     payment_audit_records = parse_csv(s3_prefix, file_names[5])
#     assert len(payment_audit_records) == 3
#     assert payment_audit_records[0] == {
#         error_reporting.DESCRIPTION_COLUMN: "Process has been stuck for 5 days in [GAX error report sent] without a resolution.",
#         error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000000",
#         error_reporting.FINEOS_ABSENCE_ID_COLUMN: "NTN-00-ABS-00",
#         error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "VEND-00",
#         error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",  # Never set for time based reports
#         error_reporting.PAYMENT_DATE_COLUMN: "01/07/2020",
#     }
#     assert payment_audit_records[1] == {
#         error_reporting.DESCRIPTION_COLUMN: "Process has been stuck for 5 days in [GAX sent] without a resolution.",
#         error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000001",
#         error_reporting.FINEOS_ABSENCE_ID_COLUMN: "NTN-01-ABS-01",
#         error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "VEND-01",
#         error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",  # Never set for time based reports
#         error_reporting.PAYMENT_DATE_COLUMN: "01/07/2020",
#     }
#     assert payment_audit_records[2] == {
#         error_reporting.DESCRIPTION_COLUMN: "Process has been stuck for 15 days in [Confirm vendor status in MMARS] without a resolution.",
#         error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000002",
#         error_reporting.FINEOS_ABSENCE_ID_COLUMN: "NTN-02-ABS-02",
#         error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "VEND-02",
#         error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",  # Never set for time based reports
#         error_reporting.PAYMENT_DATE_COLUMN: "01/07/2020",
#     }

#     vendor_audit_records = parse_csv(s3_prefix, file_names[6])
#     assert len(vendor_audit_records) == 6
#     assert vendor_audit_records[0] == {
#         error_reporting.DESCRIPTION_COLUMN: "Process has been stuck for 15 days in [VCM report sent] without a resolution.",
#         error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000003",
#         error_reporting.FINEOS_ABSENCE_ID_COLUMN: "",  # Not found because no payment/claims attached
#         error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "VEND-03",
#         error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",  # Never set for time based reports
#         error_reporting.PAYMENT_DATE_COLUMN: "",  # Not found because no payment/claims attached
#     }
#     assert vendor_audit_records[1] == {
#         error_reporting.DESCRIPTION_COLUMN: "Process has been stuck for 15 days in [VCM report sent] without a resolution.",
#         error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000004",
#         error_reporting.FINEOS_ABSENCE_ID_COLUMN: "NTN-04-ABS-04",
#         error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "VEND-04",
#         error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",  # Never set for time based reports
#         error_reporting.PAYMENT_DATE_COLUMN: "01/07/2020",
#     }
#     assert vendor_audit_records[2] == {
#         error_reporting.DESCRIPTION_COLUMN: "Process has been stuck for 5 days in [VCC sent] without a resolution.",
#         error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000005",
#         error_reporting.FINEOS_ABSENCE_ID_COLUMN: "",  # Not found because no payment/claims attached
#         error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "VEND-05",
#         error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",  # Never set for time based reports
#         error_reporting.PAYMENT_DATE_COLUMN: "",  # Not found because no payment/claims attached
#     }
#     assert vendor_audit_records[3] == {
#         error_reporting.DESCRIPTION_COLUMN: "Process has been stuck for 5 days in [VCC sent] without a resolution.",
#         error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000006",
#         error_reporting.FINEOS_ABSENCE_ID_COLUMN: "NTN-06-ABS-06",
#         error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "VEND-06",
#         error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",  # Never set for time based reports
#         error_reporting.PAYMENT_DATE_COLUMN: "01/07/2020",
#     }
#     assert vendor_audit_records[4] == {
#         error_reporting.DESCRIPTION_COLUMN: "Process has been stuck for 5 days in [VCC error report sent] without a resolution.",
#         error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000007",
#         error_reporting.FINEOS_ABSENCE_ID_COLUMN: "",  # Not found because no payment/claims attached
#         error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "VEND-07",
#         error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",  # Never set for time based reports
#         error_reporting.PAYMENT_DATE_COLUMN: "",  # Not found because no payment/claims attached
#     }
#     assert vendor_audit_records[5] == {
#         error_reporting.DESCRIPTION_COLUMN: "Process has been stuck for 5 days in [VCC error report sent] without a resolution.",
#         error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: "000000008",
#         error_reporting.FINEOS_ABSENCE_ID_COLUMN: "NTN-08-ABS-08",
#         error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: "VEND-08",
#         error_reporting.MMARS_DOCUMENT_ID_COLUMN: "",  # Never set for time based reports
#         error_reporting.PAYMENT_DATE_COLUMN: "01/07/2020",
#     }

#     # Show that we can do a rollback

#     # 39 total state logs
#     # 11 calls to setup_state_log_in_end_state (created employee or payment state logs)
#     # 11 prior states created in setup_state_log_in_end_state
#     #   4 additional created when we add_claim_payment_for_employee=True and created an additional payment state log
#     # the 11 records created to move the payment/employee state logs to the next state.
#     #   2 additional records for the VCM_REPORT_SENT records that were moved to the next state as part of the simple reports
#     state_logs = test_db_session.query(StateLog).all()
#     assert len(state_logs) == 39
#     test_db_session.rollback()
#     # the 11 created as part of processing no longer exist
#     rolled_back_state_logs = test_db_session.query(StateLog).all()
#     assert len(rolled_back_state_logs) == 26
