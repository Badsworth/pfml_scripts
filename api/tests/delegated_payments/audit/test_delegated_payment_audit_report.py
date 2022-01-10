import csv
import os
import tempfile
from datetime import date, datetime
from decimal import Decimal
from typing import List

import pytest
from freezegun import freeze_time

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    Payment,
    PaymentTransactionType,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.db.models.factories import ClaimFactory, LinkSplitPaymentFactory, PaymentFactory
from massgov.pfml.db.models.payments import (
    FineosWritebackDetails,
    FineosWritebackTransactionStatus,
    PaymentAuditReportDetails,
    PaymentAuditReportType,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_csv import (
    PAYMENT_AUDIT_CSV_HEADERS,
    PaymentAuditCSV,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_report import (
    PaymentAuditReportStep,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_util import (
    PaymentAuditData,
    bool_to_str,
    get_leave_type,
    get_payment_audit_report_details,
    get_payment_preference,
    stage_payment_audit_report_details,
    write_audit_report,
)
from massgov.pfml.delegated_payments.audit.mock.delegated_payment_audit_generator import (
    AUDIT_SCENARIO_DESCRIPTORS,
    DEFAULT_AUDIT_SCENARIO_DATA_SET,
    AuditScenarioData,
    generate_audit_report_dataset,
)
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory
from massgov.pfml.delegated_payments.pub.pub_check import _format_check_memo
from massgov.pfml.util.datetime import get_now_us_eastern, get_period_in_weeks


@pytest.fixture
def payment_audit_report_step(initialize_factories_session, test_db_session, test_db_other_session):
    return PaymentAuditReportStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


@freeze_time("2021-01-15 12:00:00", tz_offset=5)  # payments_util.get_now returns EST time
def test_generate_audit_report_rollback(
    initialize_factories_session, test_db_session, test_db_other_session, monkeypatch
):
    # This validates our rollback works properly.
    # This will fail after moving one set of state logs
    # but before the second set of state log updates

    def mock(self):
        # To mimic a random flush event, have it flush before raising an exception
        self.db_session.flush()
        raise Exception("Test exception")

    monkeypatch.setattr(PaymentAuditReportStep, "set_sampled_payments_to_sent_state", mock)

    payment_audit_report_step = PaymentAuditReportStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )

    # setup folder path configs
    monkeypatch.setenv("PFML_ERROR_REPORTS_ARCHIVE_PATH", str(tempfile.mkdtemp()))
    monkeypatch.setenv("DFML_REPORT_OUTBOUND_PATH", str(tempfile.mkdtemp()))

    # generate the audit report data set
    generate_audit_report_dataset(DEFAULT_AUDIT_SCENARIO_DATA_SET, test_db_session)
    test_db_session.commit()  # Commit here so it'll rollback to this

    state_log_counts_before = state_log_util.get_state_counts(test_db_session)

    # generate audit report
    with pytest.raises(Exception, match="Test exception"):
        payment_audit_report_step.run()

    state_log_counts_after = state_log_util.get_state_counts(test_db_session)
    assert state_log_counts_before == state_log_counts_after


def test_stage_payment_audit_report_details(test_db_session, initialize_factories_session):
    payment = PaymentFactory.create()
    stage_payment_audit_report_details(
        payment,
        PaymentAuditReportType.DOR_FINEOS_NAME_MISMATCH,
        "Test Message",
        None,
        test_db_session,
    )

    audit_report_details = test_db_session.query(PaymentAuditReportDetails).one_or_none()
    assert audit_report_details
    assert audit_report_details.payment_id == payment.payment_id
    assert (
        audit_report_details.audit_report_type_id
        == PaymentAuditReportType.DOR_FINEOS_NAME_MISMATCH.payment_audit_report_type_id
    )
    assert audit_report_details.details
    assert audit_report_details.details["message"] == "Test Message"
    assert audit_report_details.created_at is not None
    assert audit_report_details.updated_at is not None
    assert audit_report_details.added_to_audit_report_at is None


def test_get_payment_audit_report_details(test_db_session, initialize_factories_session):
    payment = PaymentFactory.create()
    stage_payment_audit_report_details(
        payment,
        PaymentAuditReportType.DUA_ADDITIONAL_INCOME,
        "DUA Reduction Test Message",
        None,
        test_db_session,
    )
    stage_payment_audit_report_details(
        payment,
        PaymentAuditReportType.DIA_ADDITIONAL_INCOME,
        "DIA Reduction Test Message",
        None,
        test_db_session,
    )
    stage_payment_audit_report_details(
        payment,
        PaymentAuditReportType.DOR_FINEOS_NAME_MISMATCH,
        "Name mismatch Test Message",
        None,
        test_db_session,
    )
    stage_payment_audit_report_details(
        payment,
        PaymentAuditReportType.LEAVE_PLAN_IN_REVIEW,
        "Leave Plan In Review Test Message",  # Not used
        None,
        test_db_session,
    )

    audit_report_time = get_now_us_eastern()

    audit_report_details = get_payment_audit_report_details(
        payment, audit_report_time, test_db_session
    )

    assert audit_report_details
    assert audit_report_details.dua_additional_income_details == "DUA Reduction Test Message"
    assert audit_report_details.dia_additional_income_details == "DIA Reduction Test Message"
    assert audit_report_details.dor_fineos_name_mismatch_details == "Name mismatch Test Message"
    assert audit_report_details.skipped_by_program_integrity
    assert (
        audit_report_details.rejected_notes
        == f"{PaymentAuditReportType.DUA_ADDITIONAL_INCOME.payment_audit_report_type_description}, {PaymentAuditReportType.DIA_ADDITIONAL_INCOME.payment_audit_report_type_description}, {PaymentAuditReportType.DOR_FINEOS_NAME_MISMATCH.payment_audit_report_type_description}, {PaymentAuditReportType.LEAVE_PLAN_IN_REVIEW.payment_audit_report_type_description} (Skipped)"
    )

    # test that the audit report time was set
    audit_report_details = test_db_session.query(PaymentAuditReportDetails).all()
    assert len(audit_report_details) == 4
    for audit_report_detail in audit_report_details:
        assert audit_report_detail.added_to_audit_report_at == audit_report_time


def test_is_first_time_payment(
    initialize_factories_session, test_db_session, test_db_other_session
):
    payment_audit_report_step = PaymentAuditReportStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )

    claim = ClaimFactory.create()
    payment = DelegatedPaymentFactory(
        test_db_session, claim=claim,
    ).get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING
    )

    assert payment_audit_report_step.previously_audit_sent_count(payment) == 0

    DelegatedPaymentFactory(test_db_session, claim=claim,).get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT
    )

    assert payment_audit_report_step.previously_audit_sent_count(payment) == 0

    previous_rejected_payment_factory = DelegatedPaymentFactory(test_db_session, claim=claim,)
    previous_rejected_payment_factory.get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT
    )
    previous_rejected_payment_factory.get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT
    )

    assert payment_audit_report_step.previously_audit_sent_count(payment) == 1

    previous_bank_error_payment_factory = DelegatedPaymentFactory(test_db_session, claim=claim,)
    previous_bank_error_payment_factory.get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT
    )
    previous_bank_error_payment_factory.get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_ERROR_FROM_BANK
    )

    assert payment_audit_report_step.previously_audit_sent_count(payment) == 2


def test_previously_errored_payment_count(
    initialize_factories_session, test_db_session, test_db_other_session
):
    payment_audit_report_step = PaymentAuditReportStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )

    period_start_date = date(2021, 1, 16)
    period_end_date = date(2021, 1, 28)

    other_period_start_date = date(2021, 1, 1)
    other_period_end_date = date(2021, 1, 15)

    # state the payment for audit
    claim = ClaimFactory.create()

    payment = DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
    ).get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING
    )

    assert payment_audit_report_step.previously_errored_payment_count(payment) == 0

    # confirm that errors for payments in other periods for the same claim are not counted
    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        period_start_date=other_period_start_date,
        period_end_date=other_period_end_date,
    ).get_or_create_payment_with_state(State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT)

    assert payment_audit_report_step.previously_errored_payment_count(payment) == 0

    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        period_start_date=other_period_start_date,
        period_end_date=other_period_end_date,
    ).get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE
    )

    assert payment_audit_report_step.previously_errored_payment_count(payment) == 0

    # check errored payments in the same payment period are counted

    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
    ).get_or_create_payment_with_state(State.PAYMENT_FAILED_ADDRESS_VALIDATION)

    assert payment_audit_report_step.previously_errored_payment_count(payment) == 1

    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
    ).get_or_create_payment_with_state(State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT)

    assert payment_audit_report_step.previously_errored_payment_count(payment) == 2

    same_period_erroed_payment_restarted = DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
    ).get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE
    )

    assert payment_audit_report_step.previously_errored_payment_count(payment) == 3

    # each restart will be counted
    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        fineos_pei_c_value=same_period_erroed_payment_restarted.fineos_pei_c_value,
        fineos_pei_i_value=same_period_erroed_payment_restarted.fineos_pei_c_value,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
    ).get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE
    )

    assert payment_audit_report_step.previously_errored_payment_count(payment) == 4


def test_previously_rejected_payment_count(
    initialize_factories_session, test_db_session, test_db_other_session
):
    payment_audit_report_step = PaymentAuditReportStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )

    period_start_date = date(2021, 1, 16)
    period_end_date = date(2021, 1, 28)

    other_period_start_date = date(2021, 1, 1)
    other_period_end_date = date(2021, 1, 15)

    # state the payment for audit
    claim = ClaimFactory.create()

    payment = DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
    ).get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING
    )

    assert payment_audit_report_step.previously_rejected_payment_count(payment) == 0

    # confirm that rejects for payments in other periods for the same claim are not counted
    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        period_start_date=other_period_start_date,
        period_end_date=other_period_end_date,
    ).get_or_create_payment_with_state(State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT)

    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        period_start_date=other_period_start_date,
        period_end_date=other_period_end_date,
    ).get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE
    )

    assert payment_audit_report_step.previously_rejected_payment_count(payment) == 0

    # check errored payments in the same payment period are counted
    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
    ).get_or_create_payment_with_state(State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT)

    assert payment_audit_report_step.previously_rejected_payment_count(payment) == 1

    # skips are counted separately
    same_period_rejected_payment_restarted = DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
    ).get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE
    )

    assert payment_audit_report_step.previously_rejected_payment_count(payment) == 1
    assert payment_audit_report_step.previously_skipped_payment_count(payment) == 1

    # each restart will be counted
    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        fineos_pei_c_value=same_period_rejected_payment_restarted.fineos_pei_c_value,
        fineos_pei_i_value=same_period_rejected_payment_restarted.fineos_pei_c_value,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
    ).get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE
    )

    assert payment_audit_report_step.previously_skipped_payment_count(payment) == 2


def test_previously_paid_payments(test_db_session, initialize_factories_session):
    claim = ClaimFactory()
    date_start = date(2021, 1, 1)
    date_end = date(2021, 1, 16)
    initial_payment = PaymentFactory(
        period_start_date=date_start, period_end_date=date_end, claim=claim
    )
    second_payment = PaymentFactory(
        period_start_date=date_start, period_end_date=date_end, claim=claim
    )
    third_payment = PaymentFactory(
        period_start_date=date_start, period_end_date=date_end, claim=claim
    )

    # Second payment will be returned because it has a PAID writeback detail
    second_payment_wb_detail = FineosWritebackDetails(
        payment=second_payment,
        transaction_status_id=FineosWritebackTransactionStatus.PAID.transaction_status_id,
    )
    # Third payment will NOT be returned because of it's error status
    # Which happens chronologically after it's paid status
    third_payment_wb_detail1 = FineosWritebackDetails(
        payment=third_payment,
        transaction_status_id=FineosWritebackTransactionStatus.PAID.transaction_status_id,
    )

    third_payment_wb_detail2 = FineosWritebackDetails(
        payment=third_payment,
        transaction_status_id=FineosWritebackTransactionStatus.BANK_PROCESSING_ERROR.transaction_status_id,
    )

    test_db_session.add_all(
        [second_payment_wb_detail, third_payment_wb_detail1, third_payment_wb_detail2]
    )
    test_db_session.commit()

    payment_audit_report_step = PaymentAuditReportStep(
        db_session=test_db_session, log_entry_db_session=test_db_session
    )

    previous_payments = payment_audit_report_step.previously_paid_payments(initial_payment)

    assert len(previous_payments) == 1
    assert previous_payments[0][0] == second_payment
    assert previous_payments[0][1] == second_payment_wb_detail


def test_build_payment_audit_data_set_with_previously_paid_payments(
    test_db_session, payment_audit_report_step, initialize_factories_session
):
    claim = ClaimFactory()
    date_start = date(2021, 1, 1)
    date_end = date(2021, 1, 16)
    initial_payment = PaymentFactory(
        period_start_date=date_start, period_end_date=date_end, claim=claim
    )
    second_payment = PaymentFactory(
        period_start_date=date_start, period_end_date=date_end, claim=claim
    )
    third_payment = PaymentFactory(
        period_start_date=date_start, period_end_date=date_end, claim=claim
    )
    # Fourth payment will have no writeback detail and will be shown in the new columns
    fourth_payment = PaymentFactory(
        period_start_date=date_start, period_end_date=date_end, claim=claim
    )

    # Second payment will be returned because it has a PAID writeback detail
    second_payment_wb_detail = FineosWritebackDetails(
        payment=second_payment,
        transaction_status_id=FineosWritebackTransactionStatus.PAID.transaction_status_id,
        writeback_sent_at=datetime.now(),
    )
    # Third payment will NOT be returned because of it's error status
    # Which happens chronologically after it's paid status
    third_payment_wb_detail1 = FineosWritebackDetails(
        payment=third_payment,
        transaction_status_id=FineosWritebackTransactionStatus.PAID.transaction_status_id,
    )

    third_payment_wb_detail2 = FineosWritebackDetails(
        payment=third_payment,
        transaction_status_id=FineosWritebackTransactionStatus.BANK_PROCESSING_ERROR.transaction_status_id,
    )

    test_db_session.add_all(
        [second_payment_wb_detail, third_payment_wb_detail1, third_payment_wb_detail2]
    )
    test_db_session.commit()

    payment_audit_report_step = PaymentAuditReportStep(
        db_session=test_db_session, log_entry_db_session=test_db_session
    )

    audit_data = payment_audit_report_step.build_payment_audit_data_set([initial_payment])

    assert len(audit_data) == 1
    assert audit_data[0].previously_paid_payment_count == 2

    paid_payments_column_string = (
        f"Payment C={second_payment.fineos_pei_c_value}, "
        f"I={second_payment.fineos_pei_i_value}: amount={second_payment.amount}, "
        f"transaction_status={FineosWritebackTransactionStatus.PAID.transaction_status_description}, "
        f"writeback_sent_at={second_payment_wb_detail.writeback_sent_at}\n"
        f"Payment C={fourth_payment.fineos_pei_c_value}, "
        f"I={fourth_payment.fineos_pei_i_value}: amount={fourth_payment.amount}, "
        f"transaction_status=N/A, "
        f"writeback_sent_at=N/A\n"
    )
    assert audit_data[0].previously_paid_payments_string == paid_payments_column_string


def test_write_audit_report(tmp_path, test_db_session, initialize_factories_session):
    payment_audit_scenario_data_set: List[AuditScenarioData] = generate_audit_report_dataset(
        DEFAULT_AUDIT_SCENARIO_DATA_SET, test_db_session
    )

    payment_audit_data_set: List[PaymentAuditData] = []
    for payment_audit_scenario_data in payment_audit_scenario_data_set:
        payment_audit_data_set.append(payment_audit_scenario_data.payment_audit_data)

    write_audit_report(payment_audit_data_set, tmp_path, test_db_session, "Payment-Audit-Report")

    # Report is created
    expected_output_folder = os.path.join(
        str(tmp_path),
        payments_util.Constants.S3_OUTBOUND_SENT_DIR,
        get_now_us_eastern().strftime("%Y-%m-%d"),
    )
    files = file_util.list_files(expected_output_folder)
    assert len(files) == 1

    # Correct number of rows
    csv_path = os.path.join(expected_output_folder, files[0])

    # Validate rows
    parsed_csv = csv.DictReader(open(csv_path))

    index = 0
    for row in parsed_csv:
        audit_scenario_data = payment_audit_scenario_data_set[index]
        validate_payment_audit_csv_row_by_payment_audit_data(row, audit_scenario_data)

        index += 1

    expected_count = len(payment_audit_data_set)
    assert (
        index == expected_count  # account for header row
    ), f"Unexpected number of lines in audit report found: {index}, expected: {expected_count}"


def validate_payment_audit_csv_row_by_payment_audit_data(
    row: PaymentAuditCSV, audit_scenario_data: AuditScenarioData
):
    payment_audit_data: PaymentAuditData = audit_scenario_data.payment_audit_data
    scenario_descriptor = AUDIT_SCENARIO_DESCRIPTORS[audit_scenario_data.scenario_name]
    previous_rejection_count = len(
        list(
            filter(
                lambda s: s == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
                scenario_descriptor.previous_rejection_states,
            )
        )
    )
    previously_skipped_payment_count = len(
        list(
            filter(
                lambda s: s == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE,
                scenario_descriptor.previous_rejection_states,
            )
        )
    )

    error_msg = f"Error validaing payment audit scenario data - scenario name: {audit_scenario_data.scenario_name}"

    validate_payment_audit_csv_row_by_payment(row, payment_audit_data.payment)

    assert (
        row[PAYMENT_AUDIT_CSV_HEADERS.is_first_time_payment]
        == bool_to_str[scenario_descriptor.is_first_time_payment]
    ), error_msg
    assert row[PAYMENT_AUDIT_CSV_HEADERS.previously_errored_payment_count] == str(
        len(scenario_descriptor.previous_error_states)
    ), error_msg
    assert row[PAYMENT_AUDIT_CSV_HEADERS.previously_rejected_payment_count] == str(
        previous_rejection_count
    ), error_msg
    assert row[PAYMENT_AUDIT_CSV_HEADERS.previously_skipped_payment_count] == str(
        previously_skipped_payment_count
    )

    if scenario_descriptor.audit_report_detail_informational:
        assert row[PAYMENT_AUDIT_CSV_HEADERS.dua_additional_income_details]
        assert row[PAYMENT_AUDIT_CSV_HEADERS.dua_additional_income_details] != ""

    assert row[PAYMENT_AUDIT_CSV_HEADERS.dor_fineos_name_mismatch_details] == ""

    assert row[PAYMENT_AUDIT_CSV_HEADERS.rejected_by_program_integrity] == ""

    assert row[PAYMENT_AUDIT_CSV_HEADERS.skipped_by_program_integrity] == "", error_msg

    if scenario_descriptor.audit_report_detail_informational:
        assert row[PAYMENT_AUDIT_CSV_HEADERS.rejected_notes]
        assert row[PAYMENT_AUDIT_CSV_HEADERS.rejected_notes] != ""


def validate_payment_audit_csv_row_by_payment(row: PaymentAuditCSV, payment: Payment):
    assert row[PAYMENT_AUDIT_CSV_HEADERS.pfml_payment_id] == str(payment.payment_id)
    assert row[PAYMENT_AUDIT_CSV_HEADERS.leave_type] == get_leave_type(payment)
    assert (
        row[PAYMENT_AUDIT_CSV_HEADERS.fineos_customer_number]
        == payment.claim.employee.fineos_customer_number
    )
    assert row[PAYMENT_AUDIT_CSV_HEADERS.first_name] == payment.fineos_employee_first_name
    assert row[PAYMENT_AUDIT_CSV_HEADERS.last_name] == payment.fineos_employee_last_name
    assert row[PAYMENT_AUDIT_CSV_HEADERS.dor_first_name] == payment.claim.employee.first_name
    assert row[PAYMENT_AUDIT_CSV_HEADERS.dor_last_name] == payment.claim.employee.last_name

    validate_address_columns(row, payment)

    assert row[PAYMENT_AUDIT_CSV_HEADERS.payment_preference] == get_payment_preference(payment)
    assert row[PAYMENT_AUDIT_CSV_HEADERS.scheduled_payment_date] == payment.payment_date.isoformat()
    assert (
        row[PAYMENT_AUDIT_CSV_HEADERS.payment_period_start_date]
        == payment.period_start_date.isoformat()
    )
    assert (
        row[PAYMENT_AUDIT_CSV_HEADERS.payment_period_end_date]
        == payment.period_end_date.isoformat()
    )
    assert row[PAYMENT_AUDIT_CSV_HEADERS.payment_period_weeks] == str(
        get_period_in_weeks(payment.period_start_date, payment.period_end_date)
    )
    assert row[PAYMENT_AUDIT_CSV_HEADERS.payment_amount] == str(payment.amount)
    assert row[PAYMENT_AUDIT_CSV_HEADERS.absence_case_number] == payment.claim.fineos_absence_id
    assert row[PAYMENT_AUDIT_CSV_HEADERS.c_value] == payment.fineos_pei_c_value
    assert row[PAYMENT_AUDIT_CSV_HEADERS.i_value] == payment.fineos_pei_i_value

    assert row[PAYMENT_AUDIT_CSV_HEADERS.employer_id] == str(
        payment.claim.employer.fineos_employer_id
    )
    assert (
        row[PAYMENT_AUDIT_CSV_HEADERS.absence_case_creation_date]
        == payment.absence_case_creation_date.isoformat()
    )
    assert (
        row[PAYMENT_AUDIT_CSV_HEADERS.absence_start_date]
        == payment.claim.absence_period_start_date.isoformat()
    )
    assert (
        row[PAYMENT_AUDIT_CSV_HEADERS.absence_end_date]
        == payment.claim.absence_period_end_date.isoformat()
    )
    assert (
        row[PAYMENT_AUDIT_CSV_HEADERS.case_status]
        == payment.claim.fineos_absence_status.absence_status_description
    )
    assert row[PAYMENT_AUDIT_CSV_HEADERS.leave_request_decision] == payment.leave_request_decision
    assert row[PAYMENT_AUDIT_CSV_HEADERS.check_description] == _format_check_memo(payment)


def validate_address_columns(row: PaymentAuditCSV, payment: Payment):
    def validate_address_columns_helper(
        address_line_one, address_line_two, city, state, zip_code, is_address_verified,
    ):
        assert row[PAYMENT_AUDIT_CSV_HEADERS.address_line_1] == address_line_one
        assert row[PAYMENT_AUDIT_CSV_HEADERS.address_line_2] == address_line_two
        assert row[PAYMENT_AUDIT_CSV_HEADERS.city] == city
        assert row[PAYMENT_AUDIT_CSV_HEADERS.state] == state
        assert row[PAYMENT_AUDIT_CSV_HEADERS.zip] == zip_code
        assert row[PAYMENT_AUDIT_CSV_HEADERS.is_address_verified] == is_address_verified

    address_pair = payment.experian_address_pair

    if address_pair is None:
        validate_address_columns_helper(
            address_line_one="",
            address_line_two="",
            city="",
            state="",
            zip_code="",
            is_address_verified="N",
        )
    else:
        address = (
            address_pair.experian_address
            if address_pair.experian_address is not None
            else address_pair.fineos_address
        )
        is_address_verified = "Y" if address_pair.experian_address is not None else "N"

        validate_address_columns_helper(
            address_line_one=address.address_line_one,
            address_line_two="" if address.address_line_two is None else address.address_line_two,
            city=address.city,
            state=address.geo_state.geo_state_description,
            zip_code=address.zip_code,
            is_address_verified=is_address_verified,
        )


@freeze_time("2021-01-15 12:00:00", tz_offset=5)  # payments_util.get_now returns EST time
def test_generate_audit_report(test_db_session, payment_audit_report_step, monkeypatch):
    # setup folder path configs
    archive_folder_path = str(tempfile.mkdtemp())
    outgoing_folder_path = str(tempfile.mkdtemp())

    monkeypatch.setenv("PFML_ERROR_REPORTS_ARCHIVE_PATH", archive_folder_path)
    monkeypatch.setenv("DFML_REPORT_OUTBOUND_PATH", outgoing_folder_path)

    date_folder = "2021-01-15"
    timestamp_file_prefix = "2021-01-15-12-00-00"

    # generate the audit report data set
    payment_audit_scenario_data_set = generate_audit_report_dataset(
        DEFAULT_AUDIT_SCENARIO_DATA_SET, test_db_session
    )
    payment_audit_scenario_data_set_by_payment_id = {
        str(audit_scenario_data.payment_audit_data.payment.payment_id): audit_scenario_data
        for audit_scenario_data in payment_audit_scenario_data_set
    }

    # generate audit report
    payment_audit_report_step.run()

    # check that sampled states have transitioned
    sampled_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        state_log_util.AssociatedClass.PAYMENT,
        State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
        test_db_session,
    )
    assert len(sampled_state_logs) == len(DEFAULT_AUDIT_SCENARIO_DATA_SET)

    # check that audit report file was generated in outbound folder with correct number of rows
    expected_audit_report_archive_folder_path = os.path.join(
        archive_folder_path, payments_util.Constants.S3_OUTBOUND_SENT_DIR, date_folder
    )
    payment_audit_report_file_name = f"{timestamp_file_prefix}-Payment-Audit-Report.csv"
    assert_files(expected_audit_report_archive_folder_path, [payment_audit_report_file_name])

    audit_report_file_path = os.path.join(
        expected_audit_report_archive_folder_path, payment_audit_report_file_name
    )

    # Validate column values
    parsed_csv = csv.DictReader(open(audit_report_file_path))
    parsed_csv_by_payment_id = {
        row[PAYMENT_AUDIT_CSV_HEADERS.pfml_payment_id]: row for row in parsed_csv
    }

    assert len(parsed_csv_by_payment_id) == len(
        sampled_state_logs
    ), f"Unexpected number of lines in payment rejects report - found: {parsed_csv}, expected: {len(sampled_state_logs)}"

    for payment_id, row in parsed_csv_by_payment_id.items():
        audit_scenario_data = payment_audit_scenario_data_set_by_payment_id.get(payment_id, None)
        assert audit_scenario_data is not None

        validate_payment_audit_csv_row_by_payment_audit_data(row, audit_scenario_data)

    # check reference file created for archive folder file
    assert (
        test_db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.file_location
            == str(
                os.path.join(
                    expected_audit_report_archive_folder_path, payment_audit_report_file_name
                )
            ),
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.DELEGATED_PAYMENT_AUDIT_REPORT.reference_file_type_id,
        )
        .one_or_none()
        is not None
    )

    # check that audit report file was generated in outgoing folder without any timestamps in path/name
    assert_files(outgoing_folder_path, ["Payment-Audit-Report.csv"])


def test_orphaned_withholding_payments(
    initialize_factories_session, test_db_session, test_db_other_session
):

    payments: List[Payment] = []

    # Create a bunch of payments
    payment_audit_report_step = PaymentAuditReportStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )

    claim = ClaimFactory.create()
    payment = DelegatedPaymentFactory(
        test_db_session, claim=claim,
    ).get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING
    )

    withholding_payment_1 = DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        payment_transaction_type=PaymentTransactionType.FEDERAL_TAX_WITHHOLDING,
    ).get_or_create_payment_with_state(State.FEDERAL_WITHHOLDING_ORPHANED_PENDING_AUDIT)

    withholding_payment_2 = DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        payment_transaction_type=PaymentTransactionType.STATE_TAX_WITHHOLDING,
    ).get_or_create_payment_with_state(State.STATE_WITHHOLDING_ORPHANED_PENDING_AUDIT)

    withholding_payment_3 = DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        payment_transaction_type=PaymentTransactionType.FEDERAL_TAX_WITHHOLDING,
    ).get_or_create_payment_with_state(State.FEDERAL_WITHHOLDING_ORPHANED_PENDING_AUDIT)

    withholding_payment_4 = DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        payment_transaction_type=PaymentTransactionType.STATE_TAX_WITHHOLDING,
    ).get_or_create_payment_with_state(State.STATE_WITHHOLDING_ORPHANED_PENDING_AUDIT)

    payments.append(payment)
    payments.append(withholding_payment_1)
    payments.append(withholding_payment_2)
    payments.append(withholding_payment_3)
    payments.append(withholding_payment_4)

    assert payment_audit_report_step.audit_sent_count(payments) == 0
    payment_audit_report_step.run_step()
    assert payment_audit_report_step.audit_sent_count(payments) == 5


def test_related_withholding_payments(
    initialize_factories_session, test_db_session, test_db_other_session
):

    payments: List[Payment] = []

    # Create a bunch of payments
    payment_audit_report_step = PaymentAuditReportStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )

    claim = ClaimFactory.create()
    payment = DelegatedPaymentFactory(
        test_db_session, claim=claim,
    ).get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING
    )

    withholding_payment_1 = DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        payment_transaction_type=PaymentTransactionType.FEDERAL_TAX_WITHHOLDING,
    ).get_or_create_payment_with_state(State.FEDERAL_WITHHOLDING_RELATED_PENDING_AUDIT)

    withholding_payment_2 = DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        payment_transaction_type=PaymentTransactionType.STATE_TAX_WITHHOLDING,
    ).get_or_create_payment_with_state(State.FEDERAL_WITHHOLDING_RELATED_PENDING_AUDIT)

    withholding_payment_3 = DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        payment_transaction_type=PaymentTransactionType.FEDERAL_TAX_WITHHOLDING,
    ).get_or_create_payment_with_state(State.FEDERAL_WITHHOLDING_RELATED_PENDING_AUDIT)

    withholding_payment_4 = DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        payment_transaction_type=PaymentTransactionType.STATE_TAX_WITHHOLDING,
    ).get_or_create_payment_with_state(State.FEDERAL_WITHHOLDING_RELATED_PENDING_AUDIT)

    # Create the Payment Relationships
    related_1 = LinkSplitPaymentFactory.create(
        payment=payment, related_payment=withholding_payment_1
    )
    related_2 = LinkSplitPaymentFactory.create(
        payment=payment, related_payment=withholding_payment_2
    )
    related_3 = LinkSplitPaymentFactory.create(
        payment=payment, related_payment=withholding_payment_3
    )
    related_4 = LinkSplitPaymentFactory.create(
        payment=payment, related_payment=withholding_payment_4
    )

    assert related_1 is not None
    assert related_2 is not None
    assert related_3 is not None
    assert related_4 is not None

    payments.append(payment)
    payments.append(withholding_payment_1)
    payments.append(withholding_payment_2)
    payments.append(withholding_payment_3)
    payments.append(withholding_payment_4)

    assert payment_audit_report_step.audit_sent_count(payments) == 0
    payment_audit_report_step.run_step()
    assert payment_audit_report_step.audit_sent_count(payments) == 1


def test_calculate_withholding_amounts(test_db_session, initialize_factories_session):

    claim = ClaimFactory()
    date_start = date(2021, 1, 1)
    date_end = date(2021, 1, 16)

    # Create a Primary Payment
    payment = PaymentFactory(
        period_start_date=date_start,
        period_end_date=date_end,
        claim=claim,
        amount=Decimal("700.00"),
        fineos_pei_i_value="58000",
        payment_transaction_type_id=PaymentTransactionType.STANDARD.payment_transaction_type_id,
    )

    # Create a bunch of Payments
    payments: List[Payment] = []
    payment_1 = PaymentFactory(
        period_start_date=date_start,
        period_end_date=date_end,
        claim=claim,
        amount=Decimal("100.00"),
        fineos_pei_i_value="58001",
        payment_transaction_type_id=PaymentTransactionType.FEDERAL_TAX_WITHHOLDING.payment_transaction_type_id,
    )
    payment_2 = PaymentFactory(
        period_start_date=date_start,
        period_end_date=date_end,
        claim=claim,
        amount=Decimal("20.00"),
        fineos_pei_i_value="58002",
        payment_transaction_type_id=PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id,
    )
    payment_3 = PaymentFactory(
        period_start_date=date_start,
        period_end_date=date_end,
        claim=claim,
        amount=Decimal("110.00"),
        fineos_pei_i_value="58003",
        payment_transaction_type_id=PaymentTransactionType.FEDERAL_TAX_WITHHOLDING.payment_transaction_type_id,
    )
    payment_4 = PaymentFactory(
        period_start_date=date_start,
        period_end_date=date_end,
        claim=claim,
        amount=Decimal("21.00"),
        fineos_pei_i_value="58004",
        payment_transaction_type_id=PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id,
    )
    payment_5 = PaymentFactory(
        period_start_date=date_start,
        period_end_date=date_end,
        claim=claim,
        amount=Decimal("120.00"),
        fineos_pei_i_value="58005",
        payment_transaction_type_id=PaymentTransactionType.FEDERAL_TAX_WITHHOLDING.payment_transaction_type_id,
    )
    payment_6 = PaymentFactory(
        period_start_date=date_start,
        period_end_date=date_end,
        claim=claim,
        amount=Decimal("22.00"),
        fineos_pei_i_value="58006",
        payment_transaction_type_id=PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id,
    )

    payments.append(payment_1)
    payments.append(payment_2)
    payments.append(payment_3)
    payments.append(payment_4)
    payments.append(payment_5)
    payments.append(payment_6)

    payment_audit_report_step = PaymentAuditReportStep(
        db_session=test_db_session, log_entry_db_session=test_db_session
    )

    # Test Federal Withholding Amount
    federal_tax_amount = payment_audit_report_step.calculate_federal_withholding_amount(
        payment=payment, link_payments=payments
    )
    assert federal_tax_amount == 330.00

    # Test State Withholding Amount
    state_tax_amount = payment_audit_report_step.calculate_state_withholding_amount(
        payment=payment, link_payments=payments
    )
    assert state_tax_amount == 63.00

    # Test Federal Withholding I Values
    federal_tax_values = payment_audit_report_step.get_federal_withholding_i_value(
        link_payments=payments
    )
    assert federal_tax_values == "58001 58003 58005"

    # Test State Withholding I Values
    state_tax_values = payment_audit_report_step.get_state_withholding_i_value(
        link_payments=payments
    )
    assert state_tax_values == "58002 58004 58006"


# Assertion helpers
def assert_files(folder_path, expected_files):
    files_in_folder = file_util.list_files(folder_path)
    for expected_file in expected_files:
        assert expected_file in files_in_folder


# TODO test all exception scenarios
