from decimal import Decimal

import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
from massgov.pfml.db.models.employees import Flow, State
from massgov.pfml.db.models.factories import EmployeeFactory
from massgov.pfml.db.models.payments import PaymentAuditReportDetails, PaymentLog
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

    employee = EmployeeFactory.create()
    payment_container = _create_payment_container(
        employee, Decimal("600.00"), local_test_db_session
    )
    _create_payment_container(
        employee, Decimal("500.00"), local_test_db_session, has_processed_state=True
    )

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
