from datetime import date, timedelta
from decimal import Decimal

import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
from massgov.pfml.db.models.absences import AbsencePeriodType, AbsenceStatus
from massgov.pfml.db.models.employees import PaymentTransactionType, State
from massgov.pfml.db.models.factories import (
    AbsencePeriodFactory,
    BenefitYearFactory,
    ClaimFactory,
    DiaReductionPaymentFactory,
    DuaReductionPaymentFactory,
    EmployeeFactory,
    EmployerFactory,
)
from massgov.pfml.db.models.payments import PaymentAuditReportDetails, PaymentAuditReportType
from massgov.pfml.db.models.state import Flow
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_step import (
    PaymentPostProcessingStep,
)

from . import _create_payment_container

###
# Note that the maximum weekly benefit cap for these tests is set to $850.00 in:
# api/massgov/pfml/db/models/applications.py::sync_state_metrics
###


@pytest.fixture
def payment_post_processing_step(
    initialize_factories_session,
    test_db_session,
):
    return PaymentPostProcessingStep(
        db_session=test_db_session, log_entry_db_session=test_db_session
    )


def test_payment_date_mismatch_post_processing(payment_post_processing_step, test_db_session):
    absence_period_start_date = date(2020, 1, 5)
    absence_period_end_date = date(2020, 1, 30)
    period_start_date = date(2020, 2, 1)
    fineos_leave_request_id = 1234

    employee = EmployeeFactory.create()
    employer = EmployerFactory.create()
    claim = ClaimFactory.create(
        employee=employee,
        employer=employer,
        absence_period_start_date=absence_period_start_date,
        absence_period_end_date=absence_period_end_date,
    )
    AbsencePeriodFactory.create(
        claim=claim,
        absence_period_start_date=absence_period_start_date,
        absence_period_end_date=absence_period_end_date,
        fineos_leave_request_id=fineos_leave_request_id,
    )
    payment_container = _create_payment_container(
        employee,
        Decimal("600.00"),
        test_db_session,
        start_date=period_start_date,
        periods=1,
        length_of_period=7,
        is_adhoc_payment=False,
        claim=claim,
    )
    payment_container.payment.fineos_leave_request_id = fineos_leave_request_id

    payment_post_processing_step.run()

    payment = payment_container.payment
    payment_flow_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, test_db_session
    )
    assert (
        payment_flow_log.end_state_id
        == State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_id
    )

    audit_report_details: PaymentAuditReportDetails = (
        test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .one_or_none()
    )
    assert (
        audit_report_details.audit_report_type_id
        == PaymentAuditReportType.PAYMENT_DATE_MISMATCH.payment_audit_report_type_id
    )
    assert (
        audit_report_details.details["message"]
        == "Payment for 2020-02-01 -> 2020-02-07 outside all leave dates. Had absence periods for 2020-01-05 -> 2020-01-30."
    )


def test_total_leave_duration_post_processing(payment_post_processing_step, test_db_session):
    employee = EmployeeFactory.create()
    employer = EmployerFactory.create()
    claim = ClaimFactory.create()
    absence_period_start_date = date(2021, 1, 5)
    fineos_leave_request_id = 1234
    absence_period_end_date = absence_period_start_date + timedelta(weeks=26)
    BenefitYearFactory.create(
        employee=employee, start_date=date(2021, 1, 3), end_date=date(2022, 1, 1)
    )
    claim = ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        absence_period_start_date=absence_period_start_date,
        absence_period_end_date=absence_period_end_date,
        employee=employee,
        employer=employer,
    )
    AbsencePeriodFactory.create(
        claim=claim,
        absence_period_start_date=absence_period_start_date,
        absence_period_end_date=absence_period_end_date,
        absence_period_type_id=AbsencePeriodType.CONTINUOUS.absence_period_type_id,
        fineos_leave_request_id=fineos_leave_request_id,
    )

    payment_container = _create_payment_container(
        employee,
        Decimal("600.00"),
        test_db_session,
        start_date=absence_period_start_date,
        periods=1,
        length_of_period=7,
        claim=claim,
    )
    payment_container.payment.fineos_leave_request_id = fineos_leave_request_id

    payment_post_processing_step.run()

    payment = payment_container.payment
    # Check that it is staged for audit
    payment_flow_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, test_db_session
    )
    assert (
        payment_flow_log.end_state_id
        == State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_id
    )

    audit_report_details = (
        test_db_session.query(PaymentAuditReportDetails)
        .filter(
            PaymentAuditReportDetails.payment_id == payment.payment_id,
            PaymentAuditReportDetails.audit_report_type_id
            == PaymentAuditReportType.EXCEEDS_26_WEEKS_TOTAL_LEAVE.payment_audit_report_type_id,
        )
        .one()
    )

    assert audit_report_details.details["message"] == "\n".join(
        [
            "Benefit Year Start: 2021-01-03, Benefit Year End: 2022-01-01",
            f"- Employer ID: {employer.fineos_employer_id}, Leave Duration: 183",
        ]
    )


def test_name_mismatch_post_processing(payment_post_processing_step, test_db_session):
    employee = EmployeeFactory.create(first_name="Jane", last_name="Smith")
    payment_container = _create_payment_container(
        employee, Decimal("600.00"), test_db_session, start_date=date(2020, 12, 16)
    )
    payment_container.payment.fineos_employee_first_name = "Sam"
    payment_container.payment.fineos_employee_last_name = "Jones"

    payment_post_processing_step.run()

    payment = payment_container.payment
    # Check that it is staged for audit
    payment_flow_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, test_db_session
    )
    assert (
        payment_flow_log.end_state_id
        == State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_id
    )

    audit_report_details = (
        test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .filter(
            PaymentAuditReportDetails.audit_report_type_id
            == PaymentAuditReportType.DOR_FINEOS_NAME_MISMATCH.payment_audit_report_type_id
        )
        .one_or_none()
    )
    assert audit_report_details.details["message"] == "\n".join(
        ["DOR Name: Jane Smith", "FINEOS Name: Sam Jones"]
    )


def test_dua_dia_reductions_post_processing(payment_post_processing_step, test_db_session):
    fineos_customer_number = "1"

    employee = EmployeeFactory.create(fineos_customer_number=fineos_customer_number)
    payment_container = _create_payment_container(
        employee, Decimal("600.00"), test_db_session, start_date=date(2021, 9, 20)
    )

    DuaReductionPaymentFactory.create(
        fineos_customer_number=fineos_customer_number,
        payment_date=date(2021, 9, 29),
        request_week_begin_date=date(2021, 9, 22),
        payment_amount_cents=12765,
        gross_payment_amount_cents=34550,
        benefit_year_begin_date=date(2021, 1, 1),
        benefit_year_end_date=date(2021, 12, 31),
    )
    DiaReductionPaymentFactory.create(
        fineos_customer_number=fineos_customer_number,
        award_created_date=date(2021, 1, 15),
        start_date=date(2021, 1, 15),
        award_amount=Decimal("1200.00"),
        weekly_amount=Decimal("400.00"),
        eve_created_date=date(2021, 1, 11),
    )

    payment_post_processing_step.run()

    payment = payment_container.payment
    # Check that it is staged for audit
    payment_flow_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, test_db_session
    )
    assert (
        payment_flow_log.end_state_id
        == State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_id
    )

    dua_audit_report_details = (
        test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .filter(
            PaymentAuditReportDetails.audit_report_type_id
            == PaymentAuditReportType.DUA_ADDITIONAL_INCOME.payment_audit_report_type_id
        )
        .one_or_none()
    )
    assert dua_audit_report_details.details["message"] == "\n".join(
        [
            "DUA Reductions:",
            "- Payment Date: 2021-09-29, Amount: 127.65, Gross Payment Amount: 345.50, Request Week Begin Date: 2021-09-22, Calculated Request Week End Date: 2021-09-28, Benefit Year Begin Date: 2021-01-01, Benefit Year End Date: 2021-12-31, Fraud Indicator: N/A",
        ]
    )

    dia_audit_report_details = (
        test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .filter(
            PaymentAuditReportDetails.audit_report_type_id
            == PaymentAuditReportType.DIA_ADDITIONAL_INCOME.payment_audit_report_type_id
        )
        .one_or_none()
    )
    assert dia_audit_report_details.details["message"] == "\n".join(
        [
            "DIA Reductions:",
            "- Award Date: 2021-01-15, Start Date: 2021-01-15, Amount: 1200.00, Weekly Amount: 400.00, Event Created Date: 2021-01-11",
        ]
    )


def test_mixed_post_processing_scenarios(
    payment_post_processing_step, test_db_session, monkeypatch
):
    fineos_customer_number = "1"

    employee = EmployeeFactory.create(fineos_customer_number=fineos_customer_number)
    payment_container = _create_payment_container(
        employee, Decimal("600.00"), test_db_session, start_date=date(2021, 1, 16)
    )
    # this force a payment over the weekly cap
    _create_payment_container(
        employee,
        Decimal("500.00"),
        test_db_session,
        start_date=date(2021, 1, 16),
        has_processed_state=True,
    )

    DuaReductionPaymentFactory.create(
        fineos_customer_number=fineos_customer_number,
        request_week_begin_date=date(2021, 1, 21),
        payment_amount_cents=12765,
    )
    DiaReductionPaymentFactory.create(
        fineos_customer_number=fineos_customer_number,
        award_created_date=date(2020, 1, 15),
        award_amount=Decimal("1200.00"),
        weekly_amount=Decimal("400.00"),
    )

    payment_post_processing_step.run()

    payment = payment_container.payment

    # Check that it is staged for audit
    payment_flow_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, test_db_session
    )
    assert (
        payment_flow_log.end_state_id
        == State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_id
    )

    audit_report_details = (
        test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .all()
    )

    assert len(audit_report_details) == 3

    audit_report_type_ids = [
        audit_report_detail.audit_report_type.payment_audit_report_type_id
        for audit_report_detail in audit_report_details
    ]
    assert (
        PaymentAuditReportType.DUA_ADDITIONAL_INCOME.payment_audit_report_type_id
        in audit_report_type_ids
    )
    assert (
        PaymentAuditReportType.DIA_ADDITIONAL_INCOME.payment_audit_report_type_id
        in audit_report_type_ids
    )

    payment_date_mismatch_details = [
        x
        for x in audit_report_details
        if x.audit_report_type_id
        == PaymentAuditReportType.PAYMENT_DATE_MISMATCH.payment_audit_report_type_id
    ]
    assert len(payment_date_mismatch_details) == 1
    assert (
        payment_date_mismatch_details[0].details["message"]
        == "Payment for 2021-01-16 -> 2021-01-22 outside all leave dates. Had absence periods for 2021-01-07 -> None."
    )


def test_employer_reimbursement_payment_post_processing(
    payment_post_processing_step, test_db_session
):
    fineos_customer_number = "1"

    employee = EmployeeFactory.create(
        fineos_customer_number=fineos_customer_number, first_name="Jane", last_name="Smith"
    )
    payment_container = _create_payment_container(
        employee,
        Decimal("600.00"),
        test_db_session,
        start_date=date(2020, 12, 16),
        payment_transaction_type=PaymentTransactionType.EMPLOYER_REIMBURSEMENT,
    )

    payment_container.payment.fineos_employee_first_name = "Sam"
    payment_container.payment.fineos_employee_last_name = "Jones"

    payment_post_processing_step.run()

    payment = payment_container.payment
    # Check that it is staged for audit
    payment_flow_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, test_db_session
    )

    audit_report_details = (
        test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .one()
    )

    # it should not report name mismatch since employer reimbursements will not qualify for name mismatch check
    assert (
        audit_report_details.details["message"]
        == "Payment for 2020-12-16 -> 2020-12-22 outside all leave dates. Had absence periods for 2021-01-07 -> None."
    )

    assert (
        payment_flow_log.end_state_id == State.EMPLOYER_REIMBURSEMENT_READY_FOR_PROCESSING.state_id
    )


def test_waiting_week_post_processing(payment_post_processing_step, test_db_session):
    employee = EmployeeFactory.create(first_name="Jane", last_name="Smith")
    claim = ClaimFactory.create(absence_period_start_date=date(2020, 12, 13))
    payment_container = _create_payment_container(
        employee, Decimal("600.00"), test_db_session, start_date=date(2020, 12, 16), claim=claim
    )

    payment_post_processing_step.run()

    payment = payment_container.payment
    # Check that it is staged for audit
    payment_flow_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, test_db_session
    )
    assert (
        payment_flow_log.end_state_id
        == State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_id
    )

    audit_report_details = (
        test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .filter(
            PaymentAuditReportDetails.audit_report_type_id
            == PaymentAuditReportType.WAITING_WEEK.payment_audit_report_type_id
        )
        .one_or_none()
    )
    assert (
        audit_report_details.details["message"]
        == f"Payment period start date: {payment.period_start_date}.  Claim start date: {claim.absence_period_start_date}. Payment in waiting week status: 1"
    )
