import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.data_mart as data_mart
import massgov.pfml.payments.data_mart_states_processing.vcc_sent as vcc_sent
from massgov.pfml.db.models.employees import State, StateLog
from tests.helpers.data_mart import run_test_process_success_no_pending_payment
from tests.helpers.state_log import setup_state_log

# tests in here require real resources
pytestmark = pytest.mark.integration


def create_vcc_sent_state_log(test_db_session):
    state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_states=[State.VCC_SENT],
        test_db_session=test_db_session,
    )

    return state_log_setup.state_logs[0]


def test_process_vcc_sent_no_vendor(
    test_db_session, mocker, initialize_factories_session, mock_data_mart_client,
):
    state_log = create_vcc_sent_state_log(test_db_session)
    employee = state_log.employee

    mock_data_mart_client.get_vendor_info.return_value = None

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 1

    # run process
    vcc_sent.process(test_db_session, mock_data_mart_client)

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 2

    new_state_log = state_log_util.get_latest_state_log_in_end_state(
        associated_model=employee, end_state=State.VCC_SENT, db_session=test_db_session,
    )

    assert new_state_log
    assert new_state_log.state_log_id != state_log.state_log_id


def test_process_vcc_sent_mismatched_data(
    test_db_session, mocker, initialize_factories_session, mock_data_mart_client,
):
    state_log = create_vcc_sent_state_log(test_db_session)
    employee = state_log.employee

    mock_data_mart_client.get_vendor_info.return_value = data_mart.VendorInfoResult(
        vendor_customer_code="FOO", vendor_active_status=data_mart.VendorActiveStatus.INACTIVE
    )

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 1

    # run process
    vcc_sent.process(test_db_session, mock_data_mart_client)

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 2

    new_state_log = state_log_util.get_latest_state_log_in_end_state(
        associated_model=employee, end_state=State.VCC_SENT, db_session=test_db_session,
    )

    assert new_state_log
    assert new_state_log.state_log_id != state_log.state_log_id


def test_process_vcc_sent_success(
    local_test_db_session, mocker, local_initialize_factories_session, mock_data_mart_client,
):
    state_log = create_vcc_sent_state_log(local_test_db_session)
    run_test_process_success_no_pending_payment(
        local_test_db_session, mock_data_mart_client, mocker, state_log, vcc_sent.process
    )
