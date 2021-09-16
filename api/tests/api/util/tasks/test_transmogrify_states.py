import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
from massgov.pfml.db.models.employees import State
from massgov.pfml.db.models.factories import EmployeeFactory
from massgov.pfml.util.tasks.transmogrify_states import Configuration, _transmogrify_states


def setup_state_logs(test_db_session):
    employee1 = EmployeeFactory.create()
    employee_state_log1 = state_log_util.create_finished_state_log(
        associated_model=employee1,
        end_state=State.ADD_TO_VCM_REPORT,
        outcome=state_log_util.build_outcome("success"),
        db_session=test_db_session,
    )

    employee2 = EmployeeFactory.create()
    employee_state_log2 = state_log_util.create_finished_state_log(
        associated_model=employee2,
        end_state=State.ADD_TO_VCM_REPORT,
        outcome=state_log_util.build_outcome("success"),
        db_session=test_db_session,
    )

    employee3 = EmployeeFactory.create()
    employee_state_log3 = state_log_util.create_finished_state_log(
        associated_model=employee3,
        end_state=State.ADD_TO_VCM_REPORT,
        outcome=state_log_util.build_outcome("success"),
        db_session=test_db_session,
    )

    employee4 = EmployeeFactory.create()
    state_log_util.create_finished_state_log(
        associated_model=employee4,
        end_state=State.MMARS_STATUS_CONFIRMED,  # a different state that should be successfully ignored
        outcome=state_log_util.build_outcome("success"),
        db_session=test_db_session,
    )

    test_db_session.commit()

    # Don't return state+employee 4 as it shouldn't be changed anyways
    return [employee_state_log1, employee_state_log2, employee_state_log3]


def test_transmogrify_states(initialize_factories_session, test_db_session):
    existing_state_logs = setup_state_logs(test_db_session)
    employee_ids = [state_log.employee.employee_id for state_log in existing_state_logs]

    # We will be testing the case of moving from ADD_TO_VCM_REPORT to VCM_REPORT_SENT
    config = Configuration(
        [
            "--current-state",
            str(State.ADD_TO_VCM_REPORT.state_id),
            "--new-state",
            str(State.VCM_REPORT_SENT.state_id),
            "--outcome",
            "Test outcome",
            "--commit",
        ]
    )
    _transmogrify_states(test_db_session, config)

    state_logs = state_log_util.get_all_latest_state_logs_regardless_of_associated_class(
        State.VCM_REPORT_SENT, test_db_session
    )
    assert len(state_logs) == 3
    for state_log in state_logs:
        assert state_log.employee_id and state_log.employee_id in employee_ids
        assert state_log.outcome == {"message": "Test outcome"}
        assert state_log.end_state_id == State.VCM_REPORT_SENT.state_id


def test_transmogrify_states_dryrun(initialize_factories_session, test_db_session):
    existing_state_logs = setup_state_logs(test_db_session)
    state_log_ids = [state_log.state_log_id for state_log in existing_state_logs]

    # We will be testing the case of moving from ADD_TO_VCM_REPORT to VCM_REPORT_SENT
    config = Configuration(
        [
            "--current-state",
            str(State.ADD_TO_VCM_REPORT.state_id),
            "--new-state",
            str(State.VCM_REPORT_SENT.state_id),
            "--outcome",
            "Test outcome",
        ]
    )
    _transmogrify_states(test_db_session, config)

    # Nothing should be in the new state due to the dry run
    state_logs = state_log_util.get_all_latest_state_logs_regardless_of_associated_class(
        State.VCM_REPORT_SENT, test_db_session
    )
    assert len(state_logs) == 0

    # But the latest query should give the state logs we initially created
    state_logs = state_log_util.get_all_latest_state_logs_regardless_of_associated_class(
        State.ADD_TO_VCM_REPORT, test_db_session
    )
    assert len(state_logs) == 3
    for state_log in state_logs:
        assert state_log.state_log_id in state_log_ids


def test_transmogrify_states_invalid_input_scenarios(initialize_factories_session, test_db_session):
    # Current state ID does not correspond to any real state
    config = Configuration(
        [
            "--current-state",
            "-100",
            "--new-state",
            str(State.VCM_REPORT_SENT.state_id),
            "--outcome",
            "Test outcome",
        ]
    )
    with pytest.raises(
        ValueError, match="Current state ID -100 does not correspond to any known state."
    ):
        _transmogrify_states(test_db_session, config)

    # New state ID does not correspond to any real state
    config = Configuration(
        [
            "--current-state",
            str(State.ADD_TO_VCM_REPORT.state_id),
            "--new-state",
            "0",
            "--outcome",
            "Test outcome",
        ]
    )
    with pytest.raises(ValueError, match="New state ID 0 does not correspond to any known state."):
        _transmogrify_states(test_db_session, config)

    # Cannot move a state to the state it already is
    config = Configuration(
        [
            "--current-state",
            str(State.ADD_TO_VCM_REPORT.state_id),
            "--new-state",
            str(State.ADD_TO_VCM_REPORT.state_id),
            "--outcome",
            "Test outcome",
        ]
    )
    with pytest.raises(
        ValueError,
        match="Cannot change state to identical state: current-state cannot match new-state.",
    ):
        _transmogrify_states(test_db_session, config)

    # Cannot move to a a state with a different flow
    # ADD_TO_VCM_REPORT is in flow VENDOR_CHECK
    # PAYMENTS_RETRIEVED is in flow UNUSED
    config = Configuration(
        [
            "--current-state",
            str(State.ADD_TO_VCM_REPORT.state_id),
            "--new-state",
            str(State.PAYMENTS_RETRIEVED.state_id),
            "--outcome",
            "Test outcome",
        ]
    )
    with pytest.raises(
        ValueError,
        match="Cannot update state as states are in different flows. Current state flow ID: 7. New state flow ID: 9.",
    ):
        _transmogrify_states(test_db_session, config)
