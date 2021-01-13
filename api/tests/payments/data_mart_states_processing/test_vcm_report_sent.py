import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.data_mart as data_mart
import massgov.pfml.payments.data_mart_states_processing.vcm_report_sent as vcm_report_sent
from massgov.pfml.db.models.employees import State, StateLog
from tests.helpers.data_mart import run_test_process_success_no_pending_payment
from tests.helpers.state_log import setup_state_log

# tests in here require real resources
pytestmark = pytest.mark.integration


def create_vcm_report_sent_state_log(test_db_session):
    state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        start_states=[State.ADD_TO_VCM_REPORT],
        end_states=[State.VCM_REPORT_SENT],
        test_db_session=test_db_session,
    )

    return state_log_setup.state_logs[0]


def test_process_vcm_report_sent_no_vendor(
    test_db_session, mocker, initialize_factories_session, mock_data_mart_engine,
):
    state_log = create_vcm_report_sent_state_log(test_db_session)
    employee = state_log.employee

    mocker.patch.object(data_mart, "get_vendor_info", return_value=None)

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 1

    # run process
    vcm_report_sent.process(test_db_session, mock_data_mart_engine)

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 2

    new_state_log = state_log_util.get_latest_state_log_in_end_state(
        associated_model=employee, end_state=State.VCM_REPORT_SENT, db_session=test_db_session,
    )

    assert new_state_log
    assert new_state_log.state_log_id != state_log.state_log_id
    assert new_state_log.start_state_id == State.VCM_REPORT_SENT.state_id

    assert new_state_log.outcome == {"message": "Hit exception: ValueError"}


def test_process_vcm_report_sent_mismatched_data(
    test_db_session, mocker, initialize_factories_session, mock_data_mart_engine,
):
    state_log = create_vcm_report_sent_state_log(test_db_session)
    employee = state_log.employee

    mocker.patch.object(
        data_mart,
        "get_vendor_info",
        return_value=data_mart.VendorInfoResult(
            vendor_customer_code="FOO", vendor_active_status=data_mart.VendorActiveStatus.INACTIVE
        ),
    )

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 1

    # run process
    vcm_report_sent.process(test_db_session, mock_data_mart_engine)

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 2

    new_state_log = state_log_util.get_latest_state_log_in_end_state(
        associated_model=employee, end_state=State.VCM_REPORT_SENT, db_session=test_db_session,
    )

    assert new_state_log
    assert new_state_log.state_log_id != state_log.state_log_id
    assert new_state_log.start_state_id == State.VCM_REPORT_SENT.state_id


def test_process_vcm_report_sent_success(
    test_db_session, mocker, initialize_factories_session, mock_data_mart_engine,
):
    state_log = create_vcm_report_sent_state_log(test_db_session)
    run_test_process_success_no_pending_payment(
        test_db_session, mock_data_mart_engine, mocker, state_log, vcm_report_sent.process
    )
