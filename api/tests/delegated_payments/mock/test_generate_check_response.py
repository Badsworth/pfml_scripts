import pytest

from massgov.pfml.db.models.employees import PaymentCheck
from massgov.pfml.db.models.factories import PaymentFactory, PubEftFactory
from massgov.pfml.delegated_payments.mock.generate_check_response import (
    generate_outstanding_ftp_data,
    generate_paid_ftp_data,
)
from massgov.pfml.delegated_payments.mock.scenarios import ScenarioDescriptor, ScenarioName
from massgov.pfml.delegated_payments.pub.pub_check import _format_employee_name_for_ez_check


@pytest.fixture()
def generate_payments(initialize_factories_session):
    check = PaymentCheck(check_number=500)
    pub_eft = PubEftFactory.create()
    payment = PaymentFactory.create(pub_eft=pub_eft)
    payment.check = check
    return [payment]


def test_generate_paid_ftp_data(generate_payments):
    payments = generate_payments
    paid_ftp_scenario_descriptor = ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_CHECK_RESPONSE_PAID_FTP
    )
    paid_ftp_data = generate_paid_ftp_data(paid_ftp_scenario_descriptor, payments)[0]
    payment = payments[0]
    assert paid_ftp_data.check_number == payment.check.check_number
    assert paid_ftp_data.posted_amount == payment.amount
    assert paid_ftp_data.posted_date == payment.payment_date.strftime("%m/%d/%Y")
    assert paid_ftp_data.payee_name == _format_employee_name_for_ez_check(payment.claim.employee)


def test_generate_outstanding_ftp_data(generate_payments):
    payments = generate_payments
    outstanding_ftp_scenario_descriptor = ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_CHECK_RESPONSE_OUTSTANDING_FTP
    )
    outstanding_ftp_data = generate_outstanding_ftp_data(
        outstanding_ftp_scenario_descriptor, payments
    )[0]
    payment = payments[0]
    assert outstanding_ftp_data.check_number == payment.check.check_number
    assert outstanding_ftp_data.issued_amount == payment.amount
    assert outstanding_ftp_data.issued_date == payment.payment_date.strftime("%m/%d/%Y")
    assert outstanding_ftp_data.payee_name == _format_employee_name_for_ez_check(
        payment.claim.employee
    )
