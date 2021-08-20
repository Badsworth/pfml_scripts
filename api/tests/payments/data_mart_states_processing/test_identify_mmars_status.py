import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.data_mart as data_mart
import massgov.pfml.payments.data_mart_states_processing.identify_mmars_status as identify_mmars_status
import massgov.pfml.payments.payments_util as payments_util
from massgov.pfml.db.models.employees import State, StateLog
from massgov.pfml.types import TaxId
from tests.helpers.data_mart import run_test_process_success_no_pending_payment
from tests.helpers.state_log import setup_state_log

# tests in here require real resources
pytestmark = pytest.mark.integration


def create_identify_mmars_status_state_log(test_db_session):
    state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_states=[State.IDENTIFY_MMARS_STATUS],
        test_db_session=test_db_session,
    )

    return state_log_setup.state_logs[0]


def test_process_identify_mmars_status_no_vendor(
    test_db_session, mocker, initialize_factories_session, mock_data_mart_client,
):
    state_log = create_identify_mmars_status_state_log(test_db_session)
    employee = state_log.employee

    mock_data_mart_client.get_vendor_info.return_value = None

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 1

    # run process
    identify_mmars_status.process(test_db_session, mock_data_mart_client)

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 2

    new_state_log = state_log_util.get_latest_state_log_in_end_state(
        associated_model=employee, end_state=State.ADD_TO_VCC, db_session=test_db_session,
    )

    assert new_state_log
    assert new_state_log.state_log_id != state_log.state_log_id


def test_process_identify_mmars_status_add_to_vcm(
    test_db_session, mocker, initialize_factories_session, mock_data_mart_client
):
    state_log = create_identify_mmars_status_state_log(test_db_session)
    employee = state_log.employee

    mock_data_mart_client.get_vendor_info.return_value = data_mart.VendorInfoResult(
        vendor_customer_code="FOO", vendor_active_status=data_mart.VendorActiveStatus.INACTIVE
    )

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 1

    # run process
    identify_mmars_status.process(test_db_session, mock_data_mart_client)

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 2

    new_state_log = state_log_util.get_latest_state_log_in_end_state(
        associated_model=employee, end_state=State.ADD_TO_VCM_REPORT, db_session=test_db_session,
    )

    assert new_state_log
    assert new_state_log.state_log_id != state_log.state_log_id
    assert new_state_log.outcome == state_log_util.build_outcome(
        "Queried Data Mart: Vendor does not match",
        payments_util.ValidationContainer(
            "QueryDataMartForIssuesAndUpdates",
            validation_issues=[
                payments_util.ValidationIssue(
                    payments_util.ValidationReason.UNUSABLE_STATE,
                    "vendor_active_status is INACTIVE",
                ),
                payments_util.ValidationIssue(
                    payments_util.ValidationReason.MISSING_FIELD, "Vendor address does not exist",
                ),
            ],
        ),
    )


def test_process_identify_mmars_status_unexpected_internal_exception_for_state_log(
    local_test_db_session, local_initialize_factories_session, mocker, mock_data_mart_client
):
    state_logs = [create_identify_mmars_status_state_log(local_test_db_session) for _ in range(2)]

    def mock_get_vendor_info(vendor_tin):
        if TaxId(vendor_tin) == state_logs[0].employee.tax_identifier.tax_identifier:
            raise Exception
        else:
            return None

    mock_data_mart_client.get_vendor_info = mocker.Mock(wraps=mock_get_vendor_info)

    state_log_count_before = local_test_db_session.query(StateLog).count()
    assert state_log_count_before == 2

    # run process
    identify_mmars_status.process(local_test_db_session, mock_data_mart_client)

    # we do not want to test things that are not committed, so close the session
    # so the asserts below are against only the data that exists in the DB
    local_test_db_session.close()

    state_log_count_after = local_test_db_session.query(StateLog).count()
    assert state_log_count_after == 4

    # first employee should be in same state as start due to exception
    new_state_log_for_failed = state_log_util.get_latest_state_log_in_end_state(
        associated_model=state_logs[0].employee,
        end_state=State.IDENTIFY_MMARS_STATUS,
        db_session=local_test_db_session,
    )

    assert new_state_log_for_failed
    assert new_state_log_for_failed.state_log_id != state_logs[0].state_log_id
    assert new_state_log_for_failed.end_state_id == State.IDENTIFY_MMARS_STATUS.state_id
    assert new_state_log_for_failed.outcome["message"] == "Hit exception: Exception"

    # second employee should be in next state
    new_state_log_for_success = state_log_util.get_latest_state_log_in_end_state(
        associated_model=state_logs[1].employee,
        end_state=State.ADD_TO_VCC,
        db_session=local_test_db_session,
    )

    assert new_state_log_for_success
    assert new_state_log_for_success.state_log_id != state_logs[1].state_log_id
    assert new_state_log_for_success.end_state_id == State.ADD_TO_VCC.state_id


def test_process_identify_mmars_status_success(
    local_test_db_session, mocker, local_initialize_factories_session, mock_data_mart_client,
):
    state_log = create_identify_mmars_status_state_log(local_test_db_session)
    run_test_process_success_no_pending_payment(
        local_test_db_session,
        mock_data_mart_client,
        mocker,
        state_log,
        identify_mmars_status.process,
    )
