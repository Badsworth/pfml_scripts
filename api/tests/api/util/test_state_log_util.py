from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Union

from freezegun import freeze_time

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.payments_util as payments_util
from massgov.pfml.db.models.employees import Employee, LatestStateLog, Payment, State, StateLog
from massgov.pfml.db.models.factories import EmployeeFactory, PaymentFactory, ReferenceFileFactory

### Setup methods for various state log scenarios ###


# A single state log that has a start_state but no end_state
def single_unended_employee(test_db_session):
    return setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        start_states=[State.CLAIMANT_LIST_CREATED],
        end_states=[None],
        test_db_session=test_db_session,
    )


# A single state log that has a start and end state
def single_ended_employee(test_db_session):
    return setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        start_states=[State.CLAIMANT_LIST_CREATED],
        end_states=[State.CLAIMANT_LIST_SUBMITTED],
        test_db_session=test_db_session,
    )


# A single state log that has a start_state but not end state
def single_unended_payment(test_db_session):
    return setup_state_log(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        start_states=[State.PAYMENTS_RETRIEVED],
        end_states=[None],
        test_db_session=test_db_session,
    )


# A single state log that has a start and end state
def single_ended_payment(test_db_session):
    return setup_state_log(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        start_states=[State.PAYMENTS_RETRIEVED],
        end_states=[State.PAYMENTS_STORED_IN_DB],
        test_db_session=test_db_session,
    )


# A single state log that has a start_state but not end state
def single_unended_reference_file(test_db_session):
    return setup_state_log(
        associated_class=state_log_util.AssociatedClass.REFERENCE_FILE,
        start_states=[State.DFML_REPORT_CREATED],
        end_states=[None],
        test_db_session=test_db_session,
    )


# 3 changing State Logs, ends with a DFML_REPORT_SUBMITTED
def simple_employee_with_end_state(test_db_session):
    return setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        start_states=[
            State.CLAIMANT_LIST_CREATED,
            State.CLAIMANT_LIST_SUBMITTED,
            State.DFML_REPORT_CREATED,
        ],
        end_states=[
            State.CLAIMANT_LIST_SUBMITTED,
            State.DFML_REPORT_CREATED,
            State.DFML_REPORT_SUBMITTED,
        ],
        test_db_session=test_db_session,
    )


# 2 state logs, ends with an in-progress state log
def simple_payment_without_end_state(test_db_session):
    return setup_state_log(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        start_states=[State.CLAIMANT_LIST_SUBMITTED, State.DFML_REPORT_CREATED],
        end_states=[State.DFML_REPORT_CREATED, None],
        test_db_session=test_db_session,
    )


# Stuck state log - same start/end repeats 3x
def employee_stuck_state_log(test_db_session):
    return setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        start_states=[
            State.DFML_REPORT_CREATED,
            State.DFML_REPORT_CREATED,
            State.DFML_REPORT_CREATED,
        ],
        end_states=[
            State.DFML_REPORT_SUBMITTED,
            State.DFML_REPORT_SUBMITTED,
            State.DFML_REPORT_SUBMITTED,
        ],
        test_db_session=test_db_session,
    )


### /end Setup methods for various state log scenarios ###

# Container class for returning the created values for tests
@dataclass
class StateLogSetupResult:
    state_logs: List[StateLog]
    associated_model: Union[Employee, Payment]


# Utility method for creating state logs
def setup_state_log(associated_class, start_states, end_states, test_db_session):
    if associated_class == state_log_util.AssociatedClass.EMPLOYEE:
        associated_model = EmployeeFactory.create()
    if associated_class == state_log_util.AssociatedClass.PAYMENT:
        associated_model = PaymentFactory.create()
    if associated_class == state_log_util.AssociatedClass.REFERENCE_FILE:
        associated_model = ReferenceFileFactory.create()

    state_logs = []

    for index, start_state in enumerate(start_states):
        end_state = end_states[index]

        with freeze_time(f"2020-01-0{index + 1} 00:00:00"):
            state_log = state_log_util.create_state_log(
                start_state=start_state,
                associated_model=associated_model,
                db_session=test_db_session,
            )
            if end_state:
                state_log_util.finish_state_log(
                    state_log=state_log,
                    end_state=end_state,
                    outcome=state_log_util.build_outcome("success"),
                    db_session=test_db_session,
                )

            state_logs.append(state_log)

    test_db_session.flush()
    test_db_session.commit()
    return StateLogSetupResult(state_logs=state_logs, associated_model=associated_model)


@freeze_time("2020-01-01 12:00:00")
def test_create_state_log_employee(initialize_factories_session, test_db_session):
    employee = EmployeeFactory.create()

    employee_state_log = state_log_util.create_state_log(
        start_state=State.VERIFY_VENDOR_STATUS,
        associated_model=employee,
        db_session=test_db_session,
    )

    assert employee_state_log.start_state_id == State.VERIFY_VENDOR_STATUS.state_id
    assert employee_state_log.end_state_id is None
    assert employee_state_log.started_at.isoformat() == "2020-01-01T12:00:00+00:00"
    assert employee_state_log.ended_at is None
    assert employee_state_log.outcome is None
    assert employee_state_log.payment is None
    assert employee_state_log.reference_file_id is None
    assert employee_state_log.employee_id == employee.employee_id

    latest_state_log = (
        test_db_session.query(LatestStateLog)
        .filter(LatestStateLog.employee_id == employee.employee_id)
        .first()
    )
    assert latest_state_log
    assert latest_state_log.state_log_id == employee_state_log.state_log_id

    # Add another state_log to make sure the latest state log ID updates properly
    employee_state_log2 = state_log_util.create_state_log(
        start_state=State.CLAIMANT_LIST_CREATED,
        associated_model=employee,
        db_session=test_db_session,
    )

    # Verify the latest state log ID was properly updated
    test_db_session.refresh(latest_state_log)
    assert latest_state_log.state_log_id == employee_state_log2.state_log_id


@freeze_time("2020-01-01 12:00:00")
def test_create_state_log_payment(initialize_factories_session, test_db_session):
    payment = PaymentFactory.create()
    payment_state_log = state_log_util.create_state_log(
        start_state=State.PAYMENTS_RETRIEVED, associated_model=payment, db_session=test_db_session,
    )

    assert payment_state_log.start_state_id == State.PAYMENTS_RETRIEVED.state_id
    assert payment_state_log.end_state_id is None
    assert payment_state_log.started_at.isoformat() == "2020-01-01T12:00:00+00:00"
    assert payment_state_log.ended_at is None
    assert payment_state_log.outcome is None
    assert payment_state_log.payment_id == payment.payment_id
    assert payment_state_log.reference_file_id is None
    assert payment_state_log.employee is None

    latest_state_log = (
        test_db_session.query(LatestStateLog)
        .filter(LatestStateLog.payment_id == payment.payment_id)
        .first()
    )
    assert latest_state_log
    assert latest_state_log.state_log_id == payment_state_log.state_log_id

    # Add another state_log to make sure the latest state log ID updates properly
    payment_state_log2 = state_log_util.create_state_log(
        start_state=State.PAYMENTS_STORED_IN_DB,
        associated_model=payment,
        db_session=test_db_session,
    )

    # Verify the latest state log ID was properly updated
    test_db_session.refresh(latest_state_log)
    assert latest_state_log.state_log_id == payment_state_log2.state_log_id


@freeze_time("2020-01-01 12:00:00")
def test_create_state_log_reference_file(initialize_factories_session, test_db_session):
    reference_file = ReferenceFileFactory.create()

    reference_file_state_log = state_log_util.create_state_log(
        start_state=State.DFML_REPORT_CREATED,
        associated_model=reference_file,
        db_session=test_db_session,
    )

    assert reference_file_state_log.start_state_id == State.DFML_REPORT_CREATED.state_id
    assert reference_file_state_log.end_state_id is None
    assert reference_file_state_log.started_at.isoformat() == "2020-01-01T12:00:00+00:00"
    assert reference_file_state_log.ended_at is None
    assert reference_file_state_log.outcome is None
    assert reference_file_state_log.payment is None
    assert reference_file_state_log.reference_file_id == reference_file.reference_file_id
    assert reference_file_state_log.employee_id is None

    latest_state_log = (
        test_db_session.query(LatestStateLog)
        .filter(LatestStateLog.reference_file_id == reference_file.reference_file_id)
        .first()
    )
    assert latest_state_log
    assert latest_state_log.state_log_id == reference_file_state_log.state_log_id

    # Add another state_log to make sure the latest state log ID updates properly
    reference_file_state_log2 = state_log_util.create_state_log(
        start_state=State.DFML_REPORT_SUBMITTED,
        associated_model=reference_file,
        db_session=test_db_session,
    )

    # Verify the latest state log ID was properly updated
    test_db_session.refresh(latest_state_log)
    assert latest_state_log.state_log_id == reference_file_state_log2.state_log_id


@freeze_time("2020-01-01 12:00:00")
def test_finish_state_log(initialize_factories_session, test_db_session):
    # An Employee
    test_setup_employee = single_unended_employee(test_db_session)
    employee_state_log = state_log_util.finish_state_log(
        test_setup_employee.state_logs[0],
        end_state=State.DFML_REPORT_SUBMITTED,
        outcome=state_log_util.build_outcome("success"),
        db_session=test_db_session,
    )

    assert employee_state_log.end_state_id == State.DFML_REPORT_SUBMITTED.state_id
    assert employee_state_log.ended_at.isoformat() == "2020-01-01T12:00:00+00:00"
    assert employee_state_log.outcome == {"message": "success"}

    # A payment
    test_setup_payment = single_unended_payment(test_db_session)
    payment_state_log = state_log_util.finish_state_log(
        test_setup_payment.state_logs[0],
        end_state=State.DFML_REPORT_SUBMITTED,
        outcome=state_log_util.build_outcome("success"),
        db_session=test_db_session,
    )

    assert payment_state_log.end_state_id == State.DFML_REPORT_SUBMITTED.state_id
    assert payment_state_log.ended_at.isoformat() == "2020-01-01T12:00:00+00:00"
    assert payment_state_log.outcome == {"message": "success"}

    # A reference file
    test_setup_reference_file = single_unended_reference_file(test_db_session)
    reference_file_state_log = state_log_util.finish_state_log(
        test_setup_reference_file.state_logs[0],
        end_state=State.DFML_REPORT_SUBMITTED,
        outcome=state_log_util.build_outcome("success"),
        db_session=test_db_session,
    )

    assert reference_file_state_log.end_state_id == State.DFML_REPORT_SUBMITTED.state_id
    assert reference_file_state_log.ended_at.isoformat() == "2020-01-01T12:00:00+00:00"
    assert reference_file_state_log.outcome == {"message": "success"}


def test_get_latest_state_log_in_end_state(initialize_factories_session, test_db_session):
    # A happy path where the last state log entry has an end state
    test_setup = simple_employee_with_end_state(test_db_session)
    state_log = state_log_util.get_latest_state_log_in_end_state(
        test_setup.associated_model, State.DFML_REPORT_SUBMITTED, test_db_session,
    )
    assert test_setup.state_logs[2].state_log_id == state_log.state_log_id

    # The 2nd state starts DFML_REPORT_CREATED and doesn't yet have an end state
    # Meaning it is still running and we shouldn't return a state log for this
    test_setup2 = simple_payment_without_end_state(test_db_session)
    state_log2 = state_log_util.get_latest_state_log_in_end_state(
        test_setup2.associated_model, State.DFML_REPORT_CREATED, test_db_session
    )
    assert state_log2 is None


def test_get_all_latest_state_logs_in_end_state(initialize_factories_session, test_db_session):
    # 3 State Logs, ends with a DFML_REPORT_SUBMITTED
    test_setup = simple_employee_with_end_state(test_db_session)

    # 2 State Logs, ends with DFML_REPORT_SUBMITTED
    test_setup2 = setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        start_states=[State.CLAIMANT_LIST_SUBMITTED, State.DFML_REPORT_CREATED],
        end_states=[State.DFML_REPORT_CREATED, State.DFML_REPORT_SUBMITTED],
        test_db_session=test_db_session,
    )

    # 2 State Logs, contains, but does not end with DFML_REPORT_SUBMITTED
    # Will not be present in results
    setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        start_states=[State.DFML_REPORT_CREATED, State.DFML_REPORT_SUBMITTED],
        end_states=[State.DFML_REPORT_SUBMITTED, State.VERIFY_VENDOR_STATUS],
        test_db_session=test_db_session,
    )

    # 2 State Logs, the last one that has an end state is DFML_REPORT_SUBMITTED,
    # but because another exists (and is now latest), will not be present
    setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        start_states=[State.DFML_REPORT_CREATED, State.DFML_REPORT_SUBMITTED],
        end_states=[State.DFML_REPORT_SUBMITTED, None],
        test_db_session=test_db_session,
    )

    submitted_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE, State.DFML_REPORT_SUBMITTED, test_db_session,
    )
    assert len(submitted_state_logs) == 2
    submitted_state_log_ids = [state_log.state_log_id for state_log in submitted_state_logs]
    assert test_setup.state_logs[2].state_log_id in submitted_state_log_ids
    assert test_setup2.state_logs[1].state_log_id in submitted_state_log_ids

    # Also verify that it does not return anything for non-latest state logs
    created_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE, State.DFML_REPORT_CREATED, test_db_session,
    )
    assert created_state_logs == []


def test_get_time_since_ended(initialize_factories_session, test_db_session):
    # Note that setup_state_log will always create records with end time
    # 2020-01-01 00:00:00 (assuming just one state log passed in)
    test_setup1 = single_ended_employee(test_db_session)
    now = datetime(year=2020, month=1, day=2, hour=1, minute=0, tzinfo=timezone.utc)
    time_elapsed1 = state_log_util._get_time_since_ended(test_setup1.state_logs[0], now)

    assert time_elapsed1.days == 1  # Days are truncated
    assert time_elapsed1.total_seconds() == 25 * 60 * 60  # 25 hours in seconds

    # Don't pass in a current value
    test_setup2 = single_ended_payment(test_db_session)
    with freeze_time("2020-01-02 23:00:00"):  # The value it'll get when getting "now"
        time_elapsed2 = state_log_util._get_time_since_ended(test_setup2.state_logs[0])
        assert time_elapsed2.days == 1  # Day only rolls over when a full day accumulates
        assert time_elapsed2.total_seconds() == 47 * 60 * 60  # 47 hours in seconds

    # Create an unfinished state log, which will return None for time elapsed
    test_setup3 = single_unended_reference_file(test_db_session)
    time_elapsed3 = state_log_util._get_time_since_ended(test_setup3.state_logs[0])
    assert time_elapsed3 is None


def test_get_time_in_current_state(initialize_factories_session, test_db_session):
    # For each of these 3 state logs are created with dates
    # 2020-01-01, 2020-01-02, and 2020-01-03 (all at 00:00:00)
    # for each of these examples

    # Now will be 2020-01-04 for all of these
    now = datetime(year=2020, month=1, day=4, hour=0, minute=0, tzinfo=timezone.utc)

    # All state logs have same start/end states, should iterate
    # to first state log (2020-01-01)
    test_setup1 = employee_stuck_state_log(test_db_session)
    time_elapsed = state_log_util.get_time_in_current_state(test_setup1.state_logs[-1], now)
    assert time_elapsed.total_seconds() == 3 * 24 * 60 * 60  # 3 days in seconds

    # State logs are changing state so shouldn't iterate and should just consider latest state log
    test_setup2 = simple_employee_with_end_state(test_db_session)
    time_elapsed = state_log_util.get_time_in_current_state(test_setup2.state_logs[-1], now)
    assert time_elapsed.total_seconds() == 24 * 60 * 60  # 1 day in seconds


def test_get_state_logs_stuck_in_state(initialize_factories_session, test_db_session):
    # For each of these 3 state logs are created with dates
    # 2020-01-01, 2020-01-02, and 2020-01-03 (all at 00:00:00)
    # for each of these examples

    # Now will be 2020-01-04 for all of these
    now = datetime(year=2020, month=1, day=4, hour=0, minute=0, tzinfo=timezone.utc)
    # Has 3 consecutive days in DFML_REPORT_SUBMITTED state
    test_setup1 = employee_stuck_state_log(test_db_session)
    # Just the last state log was in DFML_REPORT_SUBMITTED state
    test_setup2 = simple_employee_with_end_state(test_db_session)

    stuck_state_logs = state_log_util.get_state_logs_stuck_in_state(
        state_log_util.AssociatedClass.EMPLOYEE,
        State.DFML_REPORT_SUBMITTED,
        3,
        test_db_session,
        now,
    )
    assert len(stuck_state_logs) == 1
    assert stuck_state_logs[0].state_log_id == test_setup1.state_logs[-1].state_log_id

    # now let's get anything "stuck" for more than 0 days, should return the latest for all
    stuck_state_logs = state_log_util.get_state_logs_stuck_in_state(
        state_log_util.AssociatedClass.EMPLOYEE,
        State.DFML_REPORT_SUBMITTED,
        0,
        test_db_session,
        now,
    )
    assert len(stuck_state_logs) == 2
    stuck_state_log_ids = [state_log.state_log_id for state_log in stuck_state_logs]
    assert test_setup1.state_logs[-1].state_log_id in stuck_state_log_ids
    assert test_setup2.state_logs[-1].state_log_id in stuck_state_log_ids


def test_build_outcome():
    simple_outcome = state_log_util.build_outcome("success")
    assert simple_outcome == {"message": "success"}

    validation_container = payments_util.ValidationContainer("example_key")
    validation_container.add_validation_issue(
        payments_util.ValidationReason.MISSING_DATASET, "DATASET1"
    )
    validation_container.add_validation_issue(
        payments_util.ValidationReason.MISSING_FIELD, "FIELD1"
    )
    validation_container.add_validation_issue(payments_util.ValidationReason.MISSING_IN_DB, "DB1")
    complex_outcome = state_log_util.build_outcome("complex", validation_container)
    assert complex_outcome == {
        "message": "complex",
        "validation_container": {
            "record_key": "example_key",
            "validation_issues": [
                {"reason": "MissingDataset", "details": "DATASET1"},
                {"reason": "MissingField", "details": "FIELD1"},
                {"reason": "MissingInDB", "details": "DB1"},
            ],
            "errors": [],  # TODO - might not want to add these - Will figure out in API-677
        },
    }
