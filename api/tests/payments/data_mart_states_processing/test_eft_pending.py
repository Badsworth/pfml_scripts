import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.data_mart as data_mart
import massgov.pfml.payments.data_mart_states_processing.eft_pending as eft_pending
from massgov.pfml.db.models.employees import State, StateLog
from tests.helpers.state_log import setup_state_log

# tests in here require real resources
pytestmark = pytest.mark.integration


def create_eft_pending_state_log(test_db_session):
    state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_states=[State.EFT_PENDING],
        test_db_session=test_db_session,
    )

    return state_log_setup.state_logs[0]


@pytest.mark.parametrize(
    "vendor_info_response",
    [
        None,
        data_mart.VendorInfoResult(eft_status=data_mart.EFTStatus.PRENOTE_REQUESTED),
        data_mart.VendorInfoResult(eft_status=data_mart.EFTStatus.PRENOTE_PENDING),
    ],
)
def test_process_eft_pending_waits(
    test_db_session,
    mocker,
    initialize_factories_session,
    mock_data_mart_client,
    vendor_info_response,
):
    state_log = create_eft_pending_state_log(test_db_session)
    employee = state_log.employee

    mock_data_mart_client.get_vendor_info.return_value = vendor_info_response

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 1

    # run process
    eft_pending.process(test_db_session, mock_data_mart_client)

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 2

    new_state_log = state_log_util.get_latest_state_log_in_end_state(
        associated_model=employee, end_state=State.EFT_PENDING, db_session=test_db_session,
    )

    assert new_state_log
    assert new_state_log.state_log_id != state_log.state_log_id


@pytest.mark.parametrize(
    "vendor_info_response",
    [
        data_mart.VendorInfoResult(eft_status=data_mart.EFTStatus.NOT_APPLICABLE),
        data_mart.VendorInfoResult(eft_status=data_mart.EFTStatus.NOT_ELIGIBILE_FOR_EFT),
        data_mart.VendorInfoResult(eft_status=data_mart.EFTStatus.EFT_HOLD),
        data_mart.VendorInfoResult(eft_status=data_mart.EFTStatus.PRENOTE_REJECTED),
    ],
)
def test_process_eft_pending_error_report(
    test_db_session,
    mocker,
    initialize_factories_session,
    mock_data_mart_client,
    vendor_info_response,
):
    state_log = create_eft_pending_state_log(test_db_session)
    employee = state_log.employee

    mock_data_mart_client.get_vendor_info.return_value = vendor_info_response

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 1

    # run process
    eft_pending.process(test_db_session, mock_data_mart_client)

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 2

    new_state_log = state_log_util.get_latest_state_log_in_end_state(
        associated_model=employee,
        end_state=State.ADD_TO_EFT_ERROR_REPORT,
        db_session=test_db_session,
    )

    assert new_state_log
    assert new_state_log.state_log_id != state_log.state_log_id


def test_process_eft_pending_eligible_status_but_false_generate(
    test_db_session, mocker, initialize_factories_session, mock_data_mart_client,
):
    state_log = create_eft_pending_state_log(test_db_session)
    employee = state_log.employee

    mock_data_mart_client.get_vendor_info.return_value = data_mart.VendorInfoResult(
        eft_status=data_mart.EFTStatus.ELIGIBILE_FOR_EFT, generate_eft_payment=False
    )

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 1

    # run process
    eft_pending.process(test_db_session, mock_data_mart_client)

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 2

    new_state_log = state_log_util.get_latest_state_log_in_end_state(
        associated_model=employee,
        end_state=State.ADD_TO_EFT_ERROR_REPORT,
        db_session=test_db_session,
    )

    assert new_state_log
    assert new_state_log.state_log_id != state_log.state_log_id


def test_process_eft_pending_eligible(
    test_db_session, mocker, initialize_factories_session, mock_data_mart_client,
):
    state_log = create_eft_pending_state_log(test_db_session)
    employee = state_log.employee

    mock_data_mart_client.get_vendor_info.return_value = data_mart.VendorInfoResult(
        eft_status=data_mart.EFTStatus.ELIGIBILE_FOR_EFT, generate_eft_payment=True
    )

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 1

    # run process
    eft_pending.process(test_db_session, mock_data_mart_client)

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 2

    new_state_log = state_log_util.get_latest_state_log_in_end_state(
        associated_model=employee, end_state=State.EFT_ELIGIBLE, db_session=test_db_session,
    )

    assert new_state_log
    assert new_state_log.state_log_id != state_log.state_log_id
