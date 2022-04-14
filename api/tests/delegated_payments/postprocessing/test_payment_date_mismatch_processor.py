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
    initialize_factories_session,
    test_db_session,
):
    return PaymentPostProcessingStep(
        db_session=test_db_session, log_entry_db_session=test_db_session
    )


@pytest.fixture
def payment_date_mismatch_processor(payment_post_processing_step):
    return PaymentDateMismatchProcessor(payment_post_processing_step)


@pytest.fixture
def payment_missing_absence_periods(test_db_session, initialize_factories_session):
    absence_period_start_date = date(2020, 1, 5)
    absence_period_end_date = date(2020, 1, 30)
    period_start_date = date(2020, 1, 6)
    period_end_date = period_start_date + timedelta(days=7)
    fineos_leave_request_id = 1234

    payment_factory = DelegatedPaymentFactory(
        test_db_session,
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
def payment_period_outside_of_absence_period(test_db_session, initialize_factories_session):
    # Payment absence period does not contain the payment period
    absence_period_start_date = date(2020, 1, 5)
    absence_period_end_date = date(2020, 1, 30)
    period_start_date = date(2020, 2, 1)
    period_end_date = period_start_date + timedelta(days=7)
    fineos_leave_request_id = 5678

    payment_factory = DelegatedPaymentFactory(
        test_db_session,
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
    test_db_session, initialize_factories_session
):
    # Multiple absence periods that do not contain the payment period
    absence_period_start_date = date(2020, 1, 5)
    absence_period_end_date = date(2020, 1, 30)
    period_start_date = date(2020, 2, 1)
    period_end_date = period_start_date + timedelta(days=7)
    fineos_leave_request_id = 91011

    payment_factory = DelegatedPaymentFactory(
        test_db_session,
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
def payment_period_overlaps_absence_periods(test_db_session, initialize_factories_session):
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
        test_db_session,
        employee=employee,
        employer=employer,
        claim=claim,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
    )
    payment = payment_factory.get_or_create_payment()
    payment.fineos_leave_request_id = fineos_leave_request_id
    return payment


@pytest.fixture
def payment_period_overlaps_absence_periods_but_is_valid(
    test_db_session, initialize_factories_session
):
    # Payment from 2/1 -> 2/8
    period_start_date = date(2020, 2, 1)
    period_end_date = period_start_date + timedelta(days=7)

    claim = ClaimFactory.create()
    employee = claim.employee
    fineos_leave_request_id = 91011

    # Absence Periods from
    # 1/15 -> 2/3
    # 2/6 -> 2/11
    AbsencePeriodFactory.create(
        claim=claim,
        absence_period_start_date=date(2020, 1, 15),
        absence_period_end_date=date(2020, 2, 3),
        fineos_leave_request_id=fineos_leave_request_id,
    )
    AbsencePeriodFactory.create(
        claim=claim,
        absence_period_start_date=date(2020, 2, 6),
        absence_period_end_date=date(2020, 2, 11),
        fineos_leave_request_id=fineos_leave_request_id,
    )

    payment_factory = DelegatedPaymentFactory(
        test_db_session,
        employee=employee,
        claim=claim,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
    )
    payment = payment_factory.get_or_create_payment()
    payment.fineos_leave_request_id = fineos_leave_request_id
    return payment


def test_processor_happy_path(
    payment_date_mismatch_processor: PaymentDateMismatchProcessor,
    test_db_session,
    initialize_factories_session,
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
        test_db_session,
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
        test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .one_or_none()
    )
    assert audit_report is None


def test_processor_no_absence_periods_should_flag_payment(
    payment_date_mismatch_processor: PaymentDateMismatchProcessor,
    test_db_session,
    initialize_factories_session,
    payment_missing_absence_periods: Payment,
):

    payment_date_mismatch_processor.process(payment_missing_absence_periods)

    audit_report = (
        test_db_session.query(PaymentAuditReportDetails)
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
    test_db_session,
    initialize_factories_session,
    payment_period_outside_of_absence_period: Payment,
):
    payment_date_mismatch_processor.process(payment_period_outside_of_absence_period)

    audit_report = (
        test_db_session.query(PaymentAuditReportDetails)
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
    test_db_session,
    initialize_factories_session,
    payment_period_outside_of_multiple_absence_periods: Payment,
):

    payment_date_mismatch_processor.process(payment_period_outside_of_multiple_absence_periods)

    audit_report = (
        test_db_session.query(PaymentAuditReportDetails)
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
    test_db_session,
    initialize_factories_session,
    payment_period_overlaps_absence_periods: Payment,
):

    payment_date_mismatch_processor.process(payment_period_overlaps_absence_periods)

    audit_report = (
        test_db_session.query(PaymentAuditReportDetails)
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


def test_processor_multiple_overlapping_absence_periods_but_payment_is_valid(
    payment_date_mismatch_processor: PaymentDateMismatchProcessor,
    test_db_session,
    initialize_factories_session,
    payment_period_overlaps_absence_periods_but_is_valid: Payment,
):
    payment_date_mismatch_processor.process(payment_period_overlaps_absence_periods_but_is_valid)

    audit_report = (
        test_db_session.query(PaymentAuditReportDetails)
        .filter(
            PaymentAuditReportDetails.payment_id
            == payment_period_overlaps_absence_periods_but_is_valid.payment_id
        )
        .one_or_none()
    )
    assert audit_report is None


def test_processor_adhoc_payments_should_not_flag(
    payment_date_mismatch_processor: PaymentDateMismatchProcessor,
    test_db_session,
    initialize_factories_session,
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
            test_db_session.query(PaymentAuditReportDetails)
            .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
            .one_or_none()
        ) is None, f"Unexpected AuditReport for payments_with_date_mismatches[{p}]"


def test_group_absence_periods(
    payment_date_mismatch_processor, test_db_session, initialize_factories_session
):
    payment = DelegatedPaymentFactory(test_db_session).get_or_create_payment()

    # Create a few absence periods
    all_jan_period = AbsencePeriodFactory.create(
        absence_period_start_date=date(2022, 1, 1),
        absence_period_end_date=date(2022, 1, 31),
    )
    another_all_jan_period = AbsencePeriodFactory.create(
        absence_period_start_date=date(2022, 1, 1),
        absence_period_end_date=date(2022, 1, 31),
    )
    all_feb_period = AbsencePeriodFactory.create(
        absence_period_start_date=date(2022, 2, 1),
        absence_period_end_date=date(2022, 2, 28),
    )
    some_feb_period = AbsencePeriodFactory.create(
        absence_period_start_date=date(2022, 2, 3),
        absence_period_end_date=date(2022, 2, 25),
    )
    all_march_period = AbsencePeriodFactory.create(
        absence_period_start_date=date(2022, 3, 1),
        absence_period_end_date=date(2022, 3, 31),
    )
    small_apr_period = AbsencePeriodFactory.create(
        absence_period_start_date=date(2022, 4, 15),
        absence_period_end_date=date(2022, 4, 21),
    )
    all_may_period = AbsencePeriodFactory.create(
        absence_period_start_date=date(2022, 5, 1),
        absence_period_end_date=date(2022, 5, 31),
    )

    # No absence periods gives an empty list
    groups = payment_date_mismatch_processor.group_absence_periods(payment, [])
    assert len(groups) == 0

    # Single absence period ends up in a group alone
    groups = payment_date_mismatch_processor.group_absence_periods(payment, [all_jan_period])
    assert len(groups) == 1
    assert len(groups[0].absence_periods) == 1
    assert groups[0].start_date == all_jan_period.absence_period_start_date
    assert groups[0].end_date == all_jan_period.absence_period_end_date

    # Three back-to-back periods grouped
    groups = payment_date_mismatch_processor.group_absence_periods(
        payment, [all_jan_period, all_feb_period, all_march_period]
    )
    assert len(groups) == 1
    assert len(groups[0].absence_periods) == 3
    assert groups[0].start_date == all_jan_period.absence_period_start_date
    assert groups[0].end_date == all_march_period.absence_period_end_date

    # Three back to back with a duplicate grouped
    groups = payment_date_mismatch_processor.group_absence_periods(
        payment, [all_jan_period, all_feb_period, all_march_period, another_all_jan_period]
    )
    assert len(groups) == 1
    assert len(groups[0].absence_periods) == 4
    assert groups[0].start_date == all_jan_period.absence_period_start_date
    assert groups[0].end_date == all_march_period.absence_period_end_date

    # The february period doesn't quite touch, but is close enough
    # to cause them to still group as one whole unit
    groups = payment_date_mismatch_processor.group_absence_periods(
        payment, [all_jan_period, some_feb_period, all_march_period]
    )
    assert len(groups) == 1
    assert len(groups[0].absence_periods) == 3
    assert groups[0].start_date == all_jan_period.absence_period_start_date
    assert groups[0].end_date == all_march_period.absence_period_end_date

    # Two distinctly separate date ranges as Feb isn't present
    groups = payment_date_mismatch_processor.group_absence_periods(
        payment, [all_jan_period, all_march_period]
    )
    assert len(groups) == 2
    assert len(groups[0].absence_periods) == 1
    assert groups[0].start_date == all_jan_period.absence_period_start_date
    assert groups[0].end_date == all_jan_period.absence_period_end_date

    assert len(groups[1].absence_periods) == 1
    assert groups[1].start_date == all_march_period.absence_period_start_date
    assert groups[1].end_date == all_march_period.absence_period_end_date

    # Four distinct groups
    groups = payment_date_mismatch_processor.group_absence_periods(
        payment, [all_jan_period, all_march_period, small_apr_period, all_may_period]
    )
    assert len(groups) == 4
    assert len(groups[0].absence_periods) == 1
    assert groups[0].start_date == all_jan_period.absence_period_start_date
    assert groups[0].end_date == all_jan_period.absence_period_end_date

    assert len(groups[1].absence_periods) == 1
    assert groups[1].start_date == all_march_period.absence_period_start_date
    assert groups[1].end_date == all_march_period.absence_period_end_date

    assert len(groups[2].absence_periods) == 1
    assert groups[2].start_date == small_apr_period.absence_period_start_date
    assert groups[2].end_date == small_apr_period.absence_period_end_date

    assert len(groups[3].absence_periods) == 1
    assert groups[3].start_date == all_may_period.absence_period_start_date
    assert groups[3].end_date == all_may_period.absence_period_end_date


def test_group_absence_periods_missing_values(
    payment_date_mismatch_processor, test_db_session, initialize_factories_session
):
    payment = DelegatedPaymentFactory(test_db_session).get_or_create_payment()

    # Create a few absence periods
    missing_start_date_period = AbsencePeriodFactory.create(
        absence_period_start_date=None,
        absence_period_end_date=date(2022, 1, 31),
    )
    missing_end_date_period = AbsencePeriodFactory.create(
        absence_period_start_date=date(2022, 1, 31),
        absence_period_end_date=None,
    )

    groups = payment_date_mismatch_processor.group_absence_periods(
        payment, [missing_start_date_period, missing_end_date_period]
    )
    assert len(groups) == 0
