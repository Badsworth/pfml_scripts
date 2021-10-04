from datetime import date
from decimal import Decimal

import pytest

from massgov.pfml.db.models.factories import (
    ClaimFactory,
    DiaReductionPaymentFactory,
    DuaReductionPaymentFactory,
    EmployeeFactory,
    PaymentFactory,
)
from massgov.pfml.db.models.payments import PaymentAuditReportDetails
from massgov.pfml.delegated_payments.postprocessing.dua_dia_reductions_processor import (
    DuaDiaReductionsProcessor,
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
def dua_dia_reductions_processor(payment_post_processing_step):
    return DuaDiaReductionsProcessor(payment_post_processing_step)


# TODO Use delagated payment factory PUB-277
def test_processor_mixed(dua_dia_reductions_processor, local_test_db_session):
    fineos_customer_number_1 = "1"
    fineos_customer_number_2 = "2"

    employee = EmployeeFactory.create(fineos_customer_number=fineos_customer_number_1)
    claim = ClaimFactory.create(employee=employee)
    payment = PaymentFactory.create(
        claim=claim, period_start_date=date(2021, 9, 20), period_end_date=date(2021, 9, 26)
    )

    message = dua_dia_reductions_processor.process(payment)

    assert message is None

    # DUA reduction with a request_week_begin_date that overlaps with payment period
    DuaReductionPaymentFactory.create(
        fineos_customer_number=fineos_customer_number_1,
        payment_date=date(2021, 9, 29),
        request_week_begin_date=date(2021, 9, 22),
        payment_amount_cents=12765,
        gross_payment_amount_cents=34550,
        benefit_year_begin_date=date(2021, 1, 1),
        benefit_year_end_date=date(2021, 12, 31),
    )
    # DUA reduction with a derived end date (request_week_begin_date + 6) that overlaps with payment period
    DuaReductionPaymentFactory.create(
        fineos_customer_number=fineos_customer_number_1,
        payment_date=date(2021, 9, 22),
        request_week_begin_date=date(2021, 9, 15),
        payment_amount_cents=3447,
        gross_payment_amount_cents=745550,
        benefit_year_begin_date=date(2021, 1, 1),
        benefit_year_end_date=date(2021, 12, 31),
        fraud_indicator="Y",
    )
    # same user outside of the overlap period
    DuaReductionPaymentFactory.create(
        fineos_customer_number=fineos_customer_number_1, request_week_begin_date=date(2021, 9, 13)
    )
    DuaReductionPaymentFactory.create(
        fineos_customer_number=fineos_customer_number_1, request_week_begin_date=date(2021, 9, 27)
    )
    # different user, within payment period
    DuaReductionPaymentFactory.create(
        fineos_customer_number=fineos_customer_number_2, payment_date=date(2021, 9, 22)
    )

    # DIA entries
    DiaReductionPaymentFactory.create(
        fineos_customer_number=fineos_customer_number_1,
        award_created_date=date(2021, 1, 15),
        start_date=date(2021, 1, 15),
        award_amount=Decimal("1200.00"),
        weekly_amount=Decimal("400.00"),
        eve_created_date=date(2021, 1, 11),
    )
    DiaReductionPaymentFactory.create(
        fineos_customer_number=fineos_customer_number_1,
        award_created_date=date(2020, 9, 15),
        start_date=date(2020, 9, 15),
        award_amount=Decimal("1000.00"),
        weekly_amount=Decimal("200.00"),
        eve_created_date=date(2020, 8, 28),
    )

    dua_dia_reductions_processor.process(payment)

    audit_report = (
        local_test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .one_or_none()
    )
    message = audit_report.details["message"]
    assert message == "\n".join(
        [
            "DUA Reductions:",
            "- Payment Date: 2021-09-22, Amount: 34.47, Gross Payment Amount: 7455.50, Request Week Begin Date: 2021-09-15, Calculated Request Week End Date: 2021-09-21, Benefit Year Begin Date: 2021-01-01, Benefit Year End Date: 2021-12-31, Fraud Indicator: Y",
            "- Payment Date: 2021-09-29, Amount: 127.65, Gross Payment Amount: 345.50, Request Week Begin Date: 2021-09-22, Calculated Request Week End Date: 2021-09-28, Benefit Year Begin Date: 2021-01-01, Benefit Year End Date: 2021-12-31, Fraud Indicator: N/A",
            "",
            "DIA Reductions:",
            "- Award Date: 2020-09-15, Start Date: 2020-09-15, Amount: 1000.00, Weekly Amount: 200.00, Event Created Date: 2020-08-28",
            "- Award Date: 2021-01-15, Start Date: 2021-01-15, Amount: 1200.00, Weekly Amount: 400.00, Event Created Date: 2021-01-11",
        ]
    )


# TODO Use delagated payment factory PUB-277
def test_multiple_payments(dua_dia_reductions_processor, local_test_db_session):
    fineos_customer_number_1 = "1"
    fineos_customer_number_2 = "2"

    employee = EmployeeFactory.create(fineos_customer_number=fineos_customer_number_1)
    claim = ClaimFactory.create(employee=employee)
    payment_1 = PaymentFactory.create(
        claim=claim, period_start_date=date(2021, 1, 16), period_end_date=date(2021, 1, 28)
    )

    payment_2 = PaymentFactory.create(
        claim=claim, period_start_date=date(2021, 2, 1), period_end_date=date(2021, 2, 8)
    )

    DuaReductionPaymentFactory.create(
        fineos_customer_number=fineos_customer_number_1, request_week_begin_date=date(2021, 2, 5)
    )

    DuaReductionPaymentFactory.create(
        fineos_customer_number=fineos_customer_number_1, request_week_begin_date=date(2021, 1, 24)
    )

    DiaReductionPaymentFactory.create(fineos_customer_number=fineos_customer_number_1)

    employee = EmployeeFactory.create(fineos_customer_number=fineos_customer_number_2)
    claim = ClaimFactory.create(employee=employee)
    payment_3 = PaymentFactory.create(
        claim=claim, period_start_date=date(2021, 1, 16), period_end_date=date(2021, 1, 28)
    )

    DuaReductionPaymentFactory.create(
        fineos_customer_number=fineos_customer_number_2, request_week_begin_date=date(2021, 1, 20)
    )

    DiaReductionPaymentFactory.create(fineos_customer_number=fineos_customer_number_2)

    dua_dia_reductions_processor.process(payment_1)
    dua_dia_reductions_processor.process(payment_2)
    dua_dia_reductions_processor.process(payment_3)

    assert (
        local_test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment_1.payment_id)
        .one_or_none()
    )
    assert (
        local_test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment_2.payment_id)
        .one_or_none()
    )
    assert (
        local_test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment_3.payment_id)
        .one_or_none()
    )
