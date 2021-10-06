from datetime import date
from decimal import Decimal

import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
from massgov.pfml.db.models.employees import DiaReductionPayment, DuaReductionPayment, Flow, State
from massgov.pfml.db.models.factories import (
    DiaReductionPaymentFactory,
    DuaReductionPaymentFactory,
    EmployeeFactory,
)
from massgov.pfml.db.models.payments import (
    PaymentAuditReportDetails,
    PaymentAuditReportType,
    PaymentLog,
)
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_step import (
    PaymentPostProcessingStep,
)

from . import _create_payment_container

###
# Note that the maximum weekly benefit cap for these tests is set to $850.00 in:
# api/massgov/pfml/db/models/payments.py::sync_maximum_weekly_benefit_amount
###


@pytest.fixture
def payment_post_processing_step(
    local_initialize_factories_session,
    local_test_db_session,
    local_test_db_other_session,
    monkeypatch,
):
    return PaymentPostProcessingStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


def test_run_step_payment_over_cap(
    payment_post_processing_step, local_test_db_session, monkeypatch
):

    employee = EmployeeFactory.create(fineos_customer_number="2")
    payment_container = _create_payment_container(
        employee, Decimal("600.00"), local_test_db_session
    )
    _create_payment_container(
        employee, Decimal("500.00"), local_test_db_session, has_processed_state=True
    )

    local_test_db_session.commit()
    local_test_db_session.query(DuaReductionPayment).all()
    local_test_db_session.query(DiaReductionPayment).all()

    payment_post_processing_step.run()

    payment = payment_container.payment
    # Despite failing the validation, it'll move onto the next step,
    # but with some additional audit details.
    payment_flow_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert (
        payment_flow_log.end_state_id
        == State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_id
    )
    audit_report_details = (
        local_test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .all()
    )

    local_test_db_session.query(DuaReductionPayment).all()
    local_test_db_session.query(DiaReductionPayment).all()

    audit_report_details = (
        local_test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .one_or_none()
    )
    assert audit_report_details.details["message"]

    payment_log = (
        local_test_db_session.query(PaymentLog)
        .filter(PaymentLog.payment_id == payment.payment_id)
        .one_or_none()
    )
    assert payment_log and payment_log.details
    assert "maximum_weekly_benefits" in payment_log.details


def test_name_mismatch_post_processing(payment_post_processing_step, local_test_db_session):
    employee = EmployeeFactory.create(first_name="Jane", last_name="Smith")
    payment_container = _create_payment_container(
        employee, Decimal("600.00"), local_test_db_session, start_date=date(2020, 12, 16)
    )
    payment_container.payment.fineos_employee_first_name = "Sam"
    payment_container.payment.fineos_employee_last_name = "Jones"

    payment_post_processing_step.run()

    payment = payment_container.payment
    # Check that it is staged for audit
    payment_flow_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert (
        payment_flow_log.end_state_id
        == State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_id
    )

    audit_report_details = (
        local_test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .one_or_none()
    )
    assert audit_report_details.details["message"] == "\n".join(
        ["DOR Name: Jane Smith", "FINEOS Name: Sam Jones",]
    )


def test_dua_dia_reductions_post_processing(payment_post_processing_step, local_test_db_session):
    fineos_customer_number = "1"

    employee = EmployeeFactory.create(fineos_customer_number=fineos_customer_number)
    payment_container = _create_payment_container(
        employee, Decimal("600.00"), local_test_db_session, start_date=date(2021, 9, 20)
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
        payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert (
        payment_flow_log.end_state_id
        == State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_id
    )

    audit_report_details = (
        local_test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .one_or_none()
    )
    assert audit_report_details.details["message"] == "\n".join(
        [
            "DUA Reductions:",
            "- Payment Date: 2021-09-29, Amount: 127.65, Gross Payment Amount: 345.50, Request Week Begin Date: 2021-09-22, Calculated Request Week End Date: 2021-09-28, Benefit Year Begin Date: 2021-01-01, Benefit Year End Date: 2021-12-31, Fraud Indicator: N/A",
            "",
            "DIA Reductions:",
            "- Award Date: 2021-01-15, Start Date: 2021-01-15, Amount: 1200.00, Weekly Amount: 400.00, Event Created Date: 2021-01-11",
        ]
    )


def test_mixed_post_processing_scenarios(
    payment_post_processing_step, local_test_db_session, monkeypatch
):
    monkeypatch.setenv("USE_NEW_MAXIMUM_WEEKLY_LOGIC", "1")

    fineos_customer_number = "1"

    employee = EmployeeFactory.create(fineos_customer_number=fineos_customer_number)
    payment_container = _create_payment_container(
        employee, Decimal("600.00"), local_test_db_session, start_date=date(2021, 1, 16)
    )
    # this force a payment over the weekly cap
    _create_payment_container(
        employee,
        Decimal("500.00"),
        local_test_db_session,
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
        payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert (
        payment_flow_log.end_state_id
        == State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_id
    )

    audit_report_details = (
        local_test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .all()
    )
    assert len(audit_report_details) == 2

    audit_report_type_ids = [
        audit_report_detail.audit_report_type.payment_audit_report_type_id
        for audit_report_detail in audit_report_details
    ]
    assert (
        PaymentAuditReportType.DUA_DIA_REDUCTION.payment_audit_report_type_id
        in audit_report_type_ids
    )
    assert (
        PaymentAuditReportType.MAX_WEEKLY_BENEFITS.payment_audit_report_type_id
        in audit_report_type_ids
    )
