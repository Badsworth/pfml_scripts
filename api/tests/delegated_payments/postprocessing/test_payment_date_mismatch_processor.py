from datetime import date, timedelta

import pytest

from massgov.pfml.db.models.employees import Payment
from massgov.pfml.db.models.factories import (
    AbsencePeriodFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
)
from massgov.pfml.db.models.payments import PaymentAuditReportDetails
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory
from massgov.pfml.delegated_payments.postprocessing.payment_date_mismatch_processor import (
    PaymentDateMismatchProcessor,
)
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_step import (
    PaymentPostProcessingStep,
)


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


@pytest.fixture
def payment_date_mismatch_processor(payment_post_processing_step):
    return PaymentDateMismatchProcessor(payment_post_processing_step)


@pytest.fixture
def payment_missing_absence_periods(local_test_db_session, local_initialize_factories_session):
    absence_period_start_date = date(2020, 1, 5)
    absence_period_end_date = date(2020, 1, 30)
    period_start_date = date(2020, 1, 6)
    period_end_date = period_start_date + timedelta(days=7)
    fineos_leave_request_id = 1234

    payment_factory = DelegatedPaymentFactory(
        local_test_db_session,
        absence_period_start_date=absence_period_start_date,
        absence_period_end_date=absence_period_end_date,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
        fineos_leave_request_id=fineos_leave_request_id,
    )
    payment = payment_factory.get_or_create_payment()
    payment.fineos_leave_request_id = fineos_leave_request_id
    return payment


@pytest.fixture
def payment_period_outside_of_absence_period(
    local_test_db_session, local_initialize_factories_session
):
    # Payment absence period does not contain the payment period
    absence_period_start_date = date(2020, 1, 5)
    absence_period_end_date = date(2020, 1, 30)
    period_start_date = date(2020, 2, 1)
    period_end_date = period_start_date + timedelta(days=7)
    fineos_leave_request_id = 5678

    payment_factory = DelegatedPaymentFactory(
        local_test_db_session,
        absence_period_start_date=absence_period_start_date,
        absence_period_end_date=absence_period_end_date,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
        fineos_leave_request_id=fineos_leave_request_id,
    )
    claim = payment_factory.get_or_create_claim()
    AbsencePeriodFactory.create(
        claim=claim,
        absence_period_start_date=absence_period_start_date,
        absence_period_end_date=absence_period_end_date,
        fineos_leave_request_id=fineos_leave_request_id,
    )
    payment = payment_factory.get_or_create_payment()
    payment.fineos_leave_request_id = fineos_leave_request_id
    return payment


@pytest.fixture
def payment_period_outside_of_multiple_absence_periods(
    local_test_db_session, local_initialize_factories_session
):
    # Multiple absence periods that do not contain the payment period
    absence_period_start_date = date(2020, 1, 5)
    absence_period_end_date = date(2020, 1, 30)
    period_start_date = date(2020, 2, 1)
    period_end_date = period_start_date + timedelta(days=7)
    fineos_leave_request_id = 91011

    payment_factory = DelegatedPaymentFactory(
        local_test_db_session,
        absence_period_start_date=absence_period_start_date,
        absence_period_end_date=absence_period_end_date,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
        fineos_leave_request_id=fineos_leave_request_id,
    )
    claim = payment_factory.get_or_create_claim()
    AbsencePeriodFactory.create(
        claim=claim,
        absence_period_start_date=date(2020, 1, 5),
        absence_period_end_date=date(2020, 1, 10),
        fineos_leave_request_id=fineos_leave_request_id,
    )
    AbsencePeriodFactory.create(
        claim=claim,
        absence_period_start_date=date(2020, 1, 12),
        absence_period_end_date=date(2020, 1, 16),
        fineos_leave_request_id=fineos_leave_request_id,
    )
    AbsencePeriodFactory.create(
        claim=claim,
        absence_period_start_date=date(2020, 1, 17),
        absence_period_end_date=date(2020, 1, 24),
        fineos_leave_request_id=fineos_leave_request_id,
    )
    payment = payment_factory.get_or_create_payment()
    payment.fineos_leave_request_id = fineos_leave_request_id
    return payment


@pytest.fixture
def payment_period_overlaps_absence_periods(
    local_test_db_session, local_initialize_factories_session
):
    # Multiple absence periods overlap on the front or back of the period
    absence_period_start_date = date(2020, 1, 5)
    absence_period_end_date = date(2020, 1, 30)
    period_start_date = date(2020, 2, 1)
    period_end_date = period_start_date + timedelta(days=7)
    fineos_leave_request_id = 91011

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
        absence_period_start_date=period_start_date - timedelta(days=7),
        absence_period_end_date=period_start_date,
        fineos_leave_request_id=fineos_leave_request_id,
    )
    AbsencePeriodFactory.create(
        claim=claim,
        absence_period_start_date=period_end_date,
        absence_period_end_date=period_end_date + timedelta(days=7),
        fineos_leave_request_id=fineos_leave_request_id,
    )

    payment_factory = DelegatedPaymentFactory(
        local_test_db_session,
        employee=employee,
        employer=employer,
        claim=claim,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
    )
    payment = payment_factory.get_or_create_payment()
    payment.fineos_leave_request_id = fineos_leave_request_id
    return payment


def test_processor_happy_path(
    payment_date_mismatch_processor: PaymentDateMismatchProcessor,
    local_test_db_session,
    local_initialize_factories_session,
):

    absence_period_start_date = date(2020, 1, 5)
    absence_period_end_date = date(2020, 1, 30)
    period_start_date = date(2020, 1, 6)
    period_end_date = period_start_date + timedelta(days=7)
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
    payment_factory = DelegatedPaymentFactory(
        local_test_db_session,
        employee=employee,
        employer=employer,
        claim=claim,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
    )
    payment = payment_factory.get_or_create_payment()
    payment.fineos_leave_request_id = fineos_leave_request_id

    payment_date_mismatch_processor.process(payment)

    audit_report = (
        local_test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .one_or_none()
    )
    assert audit_report is None


def test_processor_no_absence_periods_should_flag_payment(
    payment_date_mismatch_processor: PaymentDateMismatchProcessor,
    local_test_db_session,
    local_initialize_factories_session,
    payment_missing_absence_periods: Payment,
):

    payment_date_mismatch_processor.process(payment_missing_absence_periods)

    audit_report = (
        local_test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment_missing_absence_periods.payment_id)
        .one_or_none()
    )
    message = audit_report.details["message"]
    assert (
        message
        == "Payment for 2020-01-06 -> 2020-01-13 outside all leave dates. Had no absence periods."
    )


def test_processor_invalid_absence_periods_should_flag_payment(
    payment_date_mismatch_processor: PaymentDateMismatchProcessor,
    local_test_db_session,
    local_initialize_factories_session,
    payment_period_outside_of_absence_period: Payment,
):
    payment_date_mismatch_processor.process(payment_period_outside_of_absence_period)

    audit_report = (
        local_test_db_session.query(PaymentAuditReportDetails)
        .filter(
            PaymentAuditReportDetails.payment_id
            == payment_period_outside_of_absence_period.payment_id
        )
        .one_or_none()
    )
    message = audit_report.details["message"]
    assert (
        message
        == "Payment for 2020-02-01 -> 2020-02-08 outside all leave dates. Had absence periods for 2020-01-05 -> 2020-01-30."
    )


def test_processor_multiple_invalid_absence_periods_should_flag_payment(
    payment_date_mismatch_processor: PaymentDateMismatchProcessor,
    local_test_db_session,
    local_initialize_factories_session,
    payment_period_outside_of_multiple_absence_periods: Payment,
):

    payment_date_mismatch_processor.process(payment_period_outside_of_multiple_absence_periods)

    audit_report = (
        local_test_db_session.query(PaymentAuditReportDetails)
        .filter(
            PaymentAuditReportDetails.payment_id
            == payment_period_outside_of_multiple_absence_periods.payment_id
        )
        .one_or_none()
    )
    message = audit_report.details["message"]
    assert (
        message
        == "Payment for 2020-02-01 -> 2020-02-08 outside all leave dates. Had absence periods for 2020-01-05 -> 2020-01-10, 2020-01-12 -> 2020-01-16, 2020-01-17 -> 2020-01-24."
    )


def test_processor_multiple_overlapping_absence_periods_should_flag_payment(
    payment_date_mismatch_processor: PaymentDateMismatchProcessor,
    local_test_db_session,
    local_initialize_factories_session,
    payment_period_overlaps_absence_periods: Payment,
):

    payment_date_mismatch_processor.process(payment_period_overlaps_absence_periods)

    audit_report = (
        local_test_db_session.query(PaymentAuditReportDetails)
        .filter(
            PaymentAuditReportDetails.payment_id
            == payment_period_overlaps_absence_periods.payment_id
        )
        .one_or_none()
    )
    message = audit_report.details["message"]
    assert (
        message
        == "Payment for 2020-02-01 -> 2020-02-08 outside all leave dates. Had absence periods for 2020-01-25 -> 2020-02-01, 2020-02-08 -> 2020-02-15."
    )


def test_processor_adhoc_payments_should_not_flag(
    payment_date_mismatch_processor: PaymentDateMismatchProcessor,
    local_test_db_session,
    local_initialize_factories_session,
    payment_missing_absence_periods: Payment,
    payment_period_outside_of_absence_period: Payment,
    payment_period_outside_of_multiple_absence_periods: Payment,
    payment_period_overlaps_absence_periods: Payment,
):
    payments_with_date_mismatches = [
        payment_missing_absence_periods,
        payment_period_outside_of_absence_period,
        payment_period_outside_of_multiple_absence_periods,
        payment_period_overlaps_absence_periods,
    ]

    for p, payment in enumerate(payments_with_date_mismatches):
        payment.is_adhoc_payment = True

        payment_date_mismatch_processor.process(payment)

        assert (
            local_test_db_session.query(PaymentAuditReportDetails)
            .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
            .one_or_none()
        ) is None, f"Unexpected AuditReport for payments_with_date_mismatches[{p}]"
