from decimal import Decimal

import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
from massgov.pfml.db.models.factories import EmployeeFactory
from massgov.pfml.db.models.payments import (
    FineosWritebackDetails,
    FineosWritebackTransactionStatus,
    PaymentLog,
)
from massgov.pfml.db.models.state import Flow, State
from massgov.pfml.delegated_payments.weekly_max.max_weekly_benefit_amount_validation_step import (
    MaxWeeklyBenefitAmountValidationStep,
)
from tests.delegated_payments.postprocessing import _create_payment_container

###
# Note that the maximum weekly benefit cap for these tests is set to $850.00 in:
# api/massgov/pfml/db/models/applications.py::sync_state_metrics
###


@pytest.fixture
def max_weekly_benefit_amount_validation_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    return MaxWeeklyBenefitAmountValidationStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


def test_run_step_payment_over_cap(
    max_weekly_benefit_amount_validation_step, local_test_db_session, monkeypatch
):

    employee = EmployeeFactory.create(fineos_customer_number="2")
    payment_container = _create_payment_container(
        employee,
        Decimal("600.00"),
        local_test_db_session,
        is_ready_for_max_weekly_benefit_validation=True,
    )
    _create_payment_container(
        employee, Decimal("500.00"), local_test_db_session, has_processed_state=True
    )

    local_test_db_session.commit()

    max_weekly_benefit_amount_validation_step.run()

    payment = payment_container.payment
    # Despite failing the validation, it'll move onto the next step,
    # but with some additional audit details.
    payment_flow_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert (
        payment_flow_log.end_state_id
        == State.PAYMENT_FAILED_MAX_WEEKLY_BENEFIT_AMOUNT_VALIDATION.state_id
    )
    assert payment_flow_log.outcome
    assert payment_flow_log.outcome["maximum_weekly_details"]

    writeback_detail = (
        local_test_db_session.query(FineosWritebackDetails)
        .filter(FineosWritebackDetails.payment_id == payment.payment_id)
        .one_or_none()
    )
    assert writeback_detail
    assert (
        writeback_detail.transaction_status_id
        == FineosWritebackTransactionStatus.WEEKLY_BENEFITS_AMOUNT_EXCEEDS_850.transaction_status_id
    )
    writeback_flow_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PEI_WRITEBACK, local_test_db_session
    )
    assert writeback_flow_log.end_state_id == State.DELEGATED_ADD_TO_FINEOS_WRITEBACK.state_id

    payment_log = (
        local_test_db_session.query(PaymentLog)
        .filter(PaymentLog.payment_id == payment.payment_id)
        .one_or_none()
    )
    assert payment_log and payment_log.details
    assert "maximum_weekly_benefits" in payment_log.details
