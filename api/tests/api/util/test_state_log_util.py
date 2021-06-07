import logging  # noqa: B1
from datetime import datetime, timezone

import pytest
from freezegun import freeze_time

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.payments_util as payments_util
from massgov.pfml.db.models.employees import (
    Claim,
    Employee,
    Flow,
    LatestStateLog,
    Payment,
    ReferenceFile,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployeeFactory,
    PaymentFactory,
    ReferenceFileFactory,
)
from tests.helpers.state_log import default_outcome, setup_state_log

# every test in here requires real resources
pytestmark = pytest.mark.integration

### Setup methods for various state log scenarios ###


# A single state log that has a start and end state
def single_ended_employee(test_db_session):
    return setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_states=[State.DIA_CLAIMANT_LIST_SUBMITTED],
        test_db_session=test_db_session,
    )


# A single state log that has a start and end state
def single_ended_payment(test_db_session):
    return setup_state_log(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_states=[State.PAYMENTS_STORED_IN_DB],
        test_db_session=test_db_session,
    )


# 3 changing State Logs, ends with a DUA_REPORT_FOR_DFML_SUBMITTED
def simple_employee_with_end_state(test_db_session):
    return setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_states=[State.ADD_TO_GAX, State.GAX_SENT, State.CONFIRM_PAYMENT,],
        test_db_session=test_db_session,
    )


# Stuck state log - same start/end repeats 3x
def employee_stuck_state_log(test_db_session):
    return setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_states=[State.CONFIRM_PAYMENT, State.CONFIRM_PAYMENT, State.CONFIRM_PAYMENT,],
        test_db_session=test_db_session,
    )


# Utility method
def build_state_log(associated_class, end_state, test_db_session):
    if associated_class == state_log_util.AssociatedClass.PAYMENT:
        associated_model = PaymentFactory.create()
    elif associated_class == state_log_util.AssociatedClass.EMPLOYEE:
        associated_model = EmployeeFactory.create()
    else:
        associated_model = ReferenceFileFactory.create()

    state_log_util.create_finished_state_log(
        end_state=end_state,
        outcome=state_log_util.build_outcome("Success"),
        associated_model=associated_model,
        db_session=test_db_session,
    )

    return associated_model


### /end Setup methods for various state log scenarios ###


@freeze_time("2020-01-01 12:00:00")
def test_create_finished_state_log(initialize_factories_session, test_db_session):
    # An Employee
    employee = EmployeeFactory.create()
    employee_state_log = state_log_util.create_finished_state_log(
        associated_model=employee,
        end_state=State.DUA_REPORT_FOR_DFML_SUBMITTED,
        outcome=default_outcome(),
        db_session=test_db_session,
    )

    assert employee_state_log.end_state_id == State.DUA_REPORT_FOR_DFML_SUBMITTED.state_id
    assert employee_state_log.started_at.isoformat() == "2020-01-01T12:00:00+00:00"
    assert employee_state_log.ended_at.isoformat() == "2020-01-01T12:00:00+00:00"
    assert employee_state_log.outcome == {"message": "success"}
    assert employee_state_log.associated_type == state_log_util.AssociatedClass.EMPLOYEE.value
    assert employee_state_log.employee_id == employee.employee_id
    assert employee_state_log.payment is None
    assert employee_state_log.claim_id is None
    assert employee_state_log.reference_file_id is None

    # A payment
    payment = PaymentFactory.create()
    payment_state_log = state_log_util.create_finished_state_log(
        associated_model=payment,
        end_state=State.DUA_REPORT_FOR_DFML_SUBMITTED,
        outcome=default_outcome(),
        db_session=test_db_session,
    )

    assert payment_state_log.end_state_id == State.DUA_REPORT_FOR_DFML_SUBMITTED.state_id
    assert payment_state_log.started_at.isoformat() == "2020-01-01T12:00:00+00:00"
    assert payment_state_log.ended_at.isoformat() == "2020-01-01T12:00:00+00:00"
    assert payment_state_log.outcome == {"message": "success"}
    assert payment_state_log.associated_type == state_log_util.AssociatedClass.PAYMENT.value
    assert payment_state_log.employee_id is None
    assert payment_state_log.payment_id == payment.payment_id
    assert payment_state_log.claim_id is None
    assert payment_state_log.reference_file_id is None

    # A claim
    claim = ClaimFactory()
    claim_state_log = state_log_util.create_finished_state_log(
        associated_model=claim,
        end_state=State.DELEGATED_CLAIM_EXTRACTED_FROM_FINEOS,
        outcome=default_outcome(),
        db_session=test_db_session,
    )

    assert claim_state_log.end_state_id == State.DELEGATED_CLAIM_EXTRACTED_FROM_FINEOS.state_id
    assert claim_state_log.started_at.isoformat() == "2020-01-01T12:00:00+00:00"
    assert claim_state_log.ended_at.isoformat() == "2020-01-01T12:00:00+00:00"
    assert claim_state_log.outcome == {"message": "success"}
    assert claim_state_log.associated_type == state_log_util.AssociatedClass.CLAIM.value
    assert claim_state_log.employee_id is None
    assert claim_state_log.payment_id is None
    assert claim_state_log.claim_id == claim.claim_id
    assert claim_state_log.reference_file_id is None

    # A reference file
    reference_file = ReferenceFileFactory.create()
    reference_file_state_log = state_log_util.create_finished_state_log(
        associated_model=reference_file,
        end_state=State.DUA_REPORT_FOR_DFML_SUBMITTED,
        outcome=default_outcome(),
        db_session=test_db_session,
        start_time=datetime(2019, 1, 1),
    )

    assert reference_file_state_log.end_state_id == State.DUA_REPORT_FOR_DFML_SUBMITTED.state_id
    assert reference_file_state_log.started_at.isoformat() == "2019-01-01T00:00:00"
    assert reference_file_state_log.ended_at.isoformat() == "2020-01-01T12:00:00+00:00"
    assert reference_file_state_log.outcome == {"message": "success"}
    assert (
        reference_file_state_log.associated_type
        == state_log_util.AssociatedClass.REFERENCE_FILE.value
    )
    assert reference_file_state_log.employee_id is None
    assert reference_file_state_log.payment_id is None
    assert reference_file_state_log.claim_id is None
    assert reference_file_state_log.reference_file_id == reference_file.reference_file_id


def test_create_finished_state_log_same_flow(initialize_factories_session, test_db_session):
    # Every end state in this test is in the PAYMENT flow
    payment = PaymentFactory.create()
    payment_state_log_prev = state_log_util.create_finished_state_log(
        associated_model=payment,
        end_state=State.CONFIRM_VENDOR_STATUS_IN_MMARS,
        outcome={"message": "A"},
        db_session=test_db_session,
    )

    payment_state_log = state_log_util.create_finished_state_log(
        associated_model=payment,
        end_state=State.ADD_TO_GAX,  # Still a PAYMENT flow state
        outcome={"message": "B"},
        db_session=test_db_session,
    )

    assert payment_state_log.prev_state_log_id == payment_state_log_prev.state_log_id

    # Create yet another state log and make sure they're all chained together properly.
    another_payment_state_log = state_log_util.create_finished_state_log(
        associated_model=payment,
        end_state=State.GAX_SENT,  # Still a PAYMENT flow state
        outcome={"message": "C"},
        db_session=test_db_session,
    )
    test_db_session.commit()
    assert another_payment_state_log.prev_state_log_id == payment_state_log.state_log_id

    # And if you try to grab the latest specifically, you'll get the last one here
    queried_state_log = state_log_util.get_latest_state_log_in_end_state(
        associated_model=payment, end_state=State.GAX_SENT, db_session=test_db_session
    )
    assert queried_state_log.state_log_id == another_payment_state_log.state_log_id

    # We've seen weird behaviour with the foreign key back to itself for prev_state_log
    # To verify it is working right, we make sure the DB is in the right place as well.
    all_state_logs = test_db_session.query(StateLog).all()
    assert len(all_state_logs) == 3
    state_log_a, state_log_b, state_log_c = None, None, None
    for state_log in all_state_logs:
        if state_log.outcome["message"] == "A":
            state_log_a = state_log
        elif state_log.outcome["message"] == "B":
            state_log_b = state_log
        elif state_log.outcome["message"] == "C":
            state_log_c = state_log
        else:
            raise Exception("This should not happen - the test is broken")

    state_log_a.prev_state_log_id is None
    state_log_b.prev_state_log_id == state_log_a.state_log_id
    state_log_c.prev_state_log_id == state_log_b.state_log_id


def test_create_finished_state_log_different_flow(initialize_factories_session, test_db_session):
    # In this test, the same associated_model (a payment) will be used, but
    # the end state will be associated with a different flow each time meaning
    # none of the state logs will be associated with each other
    payment = PaymentFactory.create()

    state_log_1 = state_log_util.create_finished_state_log(
        associated_model=payment,
        end_state=State.ADD_TO_GAX,  # A PAYMENT flow state
        outcome=default_outcome(),
        db_session=test_db_session,
    )

    state_log_2 = state_log_util.create_finished_state_log(
        associated_model=payment,
        end_state=State.EFT_DETECTED_IN_VENDOR_EXPORT,  # A VENDOR_EFT flow state
        outcome=default_outcome(),
        db_session=test_db_session,
    )

    state_log_3 = state_log_util.create_finished_state_log(
        associated_model=payment,
        end_state=State.VCC_SENT,  # A VENDOR_CHECK flow state
        outcome=default_outcome(),
        db_session=test_db_session,
    )
    test_db_session.commit()

    assert state_log_1.prev_state_log is None
    assert state_log_2.prev_state_log is None
    assert state_log_3.prev_state_log is None

    latest_state_logs = test_db_session.query(LatestStateLog).all()
    assert len(latest_state_logs) == 3

    test_db_session.refresh(payment)
    assert len(payment.state_logs) == 3


@freeze_time("2020-01-01 12:00:00")
def test_create_state_log_without_associated_model(initialize_factories_session, test_db_session):
    unattached_state_log = state_log_util.create_state_log_without_associated_model(
        end_state=State.PAYMENTS_RETRIEVED,
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        outcome=default_outcome(),
        db_session=test_db_session,
    )

    assert unattached_state_log.end_state_id == State.PAYMENTS_RETRIEVED.state_id
    assert unattached_state_log.started_at.isoformat() == "2020-01-01T12:00:00+00:00"
    assert unattached_state_log.ended_at.isoformat() == "2020-01-01T12:00:00+00:00"
    assert unattached_state_log.outcome == {"message": "success"}
    assert unattached_state_log.payment is None
    assert unattached_state_log.reference_file is None
    assert unattached_state_log.associated_type == state_log_util.AssociatedClass.EMPLOYEE.value
    assert unattached_state_log.employee is None

    latest_state_logs = test_db_session.query(LatestStateLog).all()

    assert len(latest_state_logs) == 1
    assert latest_state_logs[0].state_log_id == unattached_state_log.state_log_id

    # Note that this will always create a new latest state log as we
    # have no object to index on in the latest state log table
    # to find it. This is fine and expected
    state_log_util.create_state_log_without_associated_model(
        end_state=State.PAYMENTS_RETRIEVED,
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        outcome=default_outcome(),
        db_session=test_db_session,
    )  # Exact same params as before - but can't be connected
    test_db_session.commit()
    latest_state_logs = test_db_session.query(LatestStateLog).all()
    assert len(latest_state_logs) == 2

    # However, if we create ANOTHER state log and specify we want to attach it
    # it won't create a new previous state log entry and will properly
    # link them
    state_log_util.create_state_log_without_associated_model(
        end_state=State.PAYMENTS_RETRIEVED,
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        outcome=default_outcome(),
        prev_state_log=unattached_state_log,
        db_session=test_db_session,
    )
    test_db_session.commit()
    latest_state_logs = test_db_session.query(LatestStateLog).all()
    assert len(latest_state_logs) == 2

    # The first state log we created should not
    # be returned when querying for latest state log
    # as it has been succeeded
    state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.PAYMENTS_RETRIEVED,
        db_session=test_db_session,
    )
    assert len(state_logs) == 2
    state_log_ids = [state_log.state_log_id for state_log in state_logs]
    assert unattached_state_log.state_log_id not in state_log_ids


def test_get_latest_state_log_in_end_state(initialize_factories_session, test_db_session):
    # This employee has 3 linked state logs that ends with a CONFIRM_PAYMENT
    test_setup = simple_employee_with_end_state(test_db_session)
    state_log = state_log_util.get_latest_state_log_in_end_state(
        test_setup.associated_model, State.CONFIRM_PAYMENT, test_db_session,
    )
    assert test_setup.state_logs[2].state_log_id == state_log.state_log_id


def test_get_all_latest_state_logs_in_end_state(initialize_factories_session, test_db_session):
    # 3 State Logs, ends with a CONFIRM_PAYMENT
    test_setup = simple_employee_with_end_state(test_db_session)

    # 2 State Logs, ends with CONFIRM_PAYMENT
    test_setup2 = setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_states=[State.GAX_SENT, State.CONFIRM_PAYMENT],
        test_db_session=test_db_session,
    )

    # 2 State Logs, contains, but does not end with CONFIRM_PAYMENT
    # Will not be present in results
    setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_states=[State.CONFIRM_PAYMENT, State.ADD_TO_GAX],
        test_db_session=test_db_session,
    )

    submitted_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE, State.CONFIRM_PAYMENT, test_db_session,
    )
    assert len(submitted_state_logs) == 2
    submitted_state_log_ids = [state_log.state_log_id for state_log in submitted_state_logs]
    assert test_setup.state_logs[2].state_log_id in submitted_state_log_ids
    assert test_setup2.state_logs[1].state_log_id in submitted_state_log_ids

    # Also verify that it does not return anything for non-latest state logs
    created_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE, State.GAX_SENT, test_db_session,
    )
    assert created_state_logs == []


def test_has_been_in_end_state(test_db_session, initialize_factories_session):
    payment = PaymentFactory.create()

    # Add a few state logs that are not in GAX_SENT
    state_log_util.create_finished_state_log(
        end_state=State.PAYMENT_PROCESS_INITIATED,
        outcome=state_log_util.build_outcome("success"),
        associated_model=payment,
        db_session=test_db_session,
    )
    state_log_util.create_finished_state_log(
        end_state=State.MARK_AS_EXTRACTED_IN_FINEOS,
        outcome=state_log_util.build_outcome("success"),
        associated_model=payment,
        db_session=test_db_session,
    )
    state_log_util.create_finished_state_log(
        end_state=State.ADD_TO_GAX,
        outcome=state_log_util.build_outcome("success"),
        associated_model=payment,
        db_session=test_db_session,
    )

    assert not state_log_util.has_been_in_end_state(payment, test_db_session, State.GAX_SENT)

    # Add another few state logs with GAX_SENT in there
    state_log_util.create_finished_state_log(
        end_state=State.CONFIRM_VENDOR_STATUS_IN_MMARS,
        outcome=state_log_util.build_outcome("success"),
        associated_model=payment,
        db_session=test_db_session,
    )
    state_log_util.create_finished_state_log(
        end_state=State.GAX_SENT,  # This will cause the method to return True
        outcome=state_log_util.build_outcome("success"),
        associated_model=payment,
        db_session=test_db_session,
    )
    state_log_util.create_finished_state_log(
        end_state=State.ADD_TO_GAX_ERROR_REPORT,
        outcome=state_log_util.build_outcome("success"),
        associated_model=payment,
        db_session=test_db_session,
    )

    assert state_log_util.has_been_in_end_state(payment, test_db_session, State.GAX_SENT)


def test_create_or_update_latest_state_log_one_or_none_issue(
    initialize_factories_session, test_db_session, logging_fix, caplog
):
    # This test is setup in a non-real use case for simplicity
    # We call the underlying method directly with a query
    # that will fail the one_or_none query to validate the error
    # is thrown properly

    # First create some prior states as normal
    payment1 = PaymentFactory.create()
    payment2 = PaymentFactory.create()

    state_log_util.create_finished_state_log(
        end_state=State.ADD_TO_GAX,
        outcome=state_log_util.build_outcome("success"),
        associated_model=payment1,
        db_session=test_db_session,
    )

    state_log_util.create_finished_state_log(
        end_state=State.ADD_TO_GAX,
        outcome=state_log_util.build_outcome("success"),
        associated_model=payment2,
        db_session=test_db_session,
    )

    # Call it with query params that will cause both
    # of the created state logs to be returned
    new_state_log = StateLog()
    query_params = [StateLog.associated_type == state_log_util.AssociatedClass.PAYMENT.value]

    caplog.set_level(logging.ERROR)  # noqa: B1
    with pytest.raises(Exception, match="Multiple rows were found for one_or_none()"):
        state_log_util._create_or_update_latest_state_log(
            new_state_log, query_params, None, test_db_session
        )

    assert (
        caplog.records[0].message
        == "Unexpected error <class 'sqlalchemy.orm.exc.MultipleResultsFound'> with one_or_none() when querying for latest state log"
    )


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
    # Has 3 consecutive days in CONFIRM_PAYMENT state
    test_setup1 = employee_stuck_state_log(test_db_session)
    # Just the last state log was in CONFIRM_PAYMENT state
    test_setup2 = simple_employee_with_end_state(test_db_session)

    stuck_state_logs = state_log_util.get_state_logs_stuck_in_state(
        state_log_util.AssociatedClass.EMPLOYEE, State.CONFIRM_PAYMENT, 3, test_db_session, now,
    )
    assert len(stuck_state_logs) == 1
    assert stuck_state_logs[0].state_log_id == test_setup1.state_logs[-1].state_log_id

    # now let's get anything "stuck" for more than 0 days, should return the latest for all
    stuck_state_logs = state_log_util.get_state_logs_stuck_in_state(
        state_log_util.AssociatedClass.EMPLOYEE, State.CONFIRM_PAYMENT, 0, test_db_session, now,
    )
    assert len(stuck_state_logs) == 2
    stuck_state_log_ids = [state_log.state_log_id for state_log in stuck_state_logs]
    assert test_setup1.state_logs[-1].state_log_id in stuck_state_log_ids
    assert test_setup2.state_logs[-1].state_log_id in stuck_state_log_ids


def test_get_state_counts(initialize_factories_session, test_db_session):
    misc_states = [
        State.DELEGATED_PAYMENT_PROCESSED_ZERO_PAYMENT,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
        State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT,
    ]
    payments = []

    # Start by adding 5 of every state
    for _ in range(5):
        for state in misc_states:
            payment = build_state_log(
                state_log_util.AssociatedClass.PAYMENT, state, test_db_session
            )
            payments.append(payment)

    state_log_counts = state_log_util.get_state_counts(test_db_session)
    for state in misc_states:
        assert state_log_counts[state.state_description] == 5

    # Add 7 of another state
    for _ in range(7):
        payment = build_state_log(
            state_log_util.AssociatedClass.PAYMENT,
            State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
            test_db_session,
        )
        payments.append(payment)

    state_log_counts = state_log_util.get_state_counts(test_db_session)
    # Prior counts unaffected
    for state in misc_states:
        assert state_log_counts[state.state_description] == 5

    assert state_log_counts[State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT.state_description] == 7

    # Now move every payment to a new state
    for payment in payments:
        state_log_util.create_finished_state_log(
            payment,
            State.DELEGATED_PAYMENT_COMPLETE,
            state_log_util.build_outcome("Success"),
            test_db_session,
        )

    # Now everything should be in just a single state
    state_log_counts = state_log_util.get_state_counts(test_db_session)

    assert len(state_log_counts) == 1
    assert state_log_counts[State.DELEGATED_PAYMENT_COMPLETE.state_description] == len(payments)


def test_get_state_counts_different_flows(initialize_factories_session, test_db_session):
    # Each of these states is in a different flow
    misc_states = [State.PEI_WRITEBACK_SENT, State.VERIFY_VENDOR_STATUS, State.ADD_TO_VCM_REPORT]
    payments = []

    # Start by adding 5 of every state
    for _ in range(5):
        for state in misc_states:
            payment = build_state_log(
                state_log_util.AssociatedClass.PAYMENT, state, test_db_session
            )
            payments.append(payment)

    state_log_counts = state_log_util.get_state_counts(test_db_session)
    for state in misc_states:
        assert state_log_counts[state.state_description] == 5

    # Now add all of these payments to a state in a different flow
    # The existing counts should stay as each payment is now associated
    # with two different state log flows
    for payment in payments:
        state_log_util.create_finished_state_log(
            payment,
            State.DELEGATED_PAYMENT_COMPLETE,
            state_log_util.build_outcome("Success"),
            test_db_session,
        )

    state_log_counts = state_log_util.get_state_counts(test_db_session)

    # These are all still here
    for state in misc_states:
        assert state_log_counts[state.state_description] == 5

    # All of the new states are also present
    assert state_log_counts[State.DELEGATED_PAYMENT_COMPLETE.state_description] == len(payments)


def test_build_outcome():
    simple_outcome = default_outcome()
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
        },
    }


def test_process_state(test_db_session, initialize_factories_session):
    state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_states=[State.IDENTIFY_MMARS_STATUS],
        test_db_session=test_db_session,
    )

    prev_state_log = state_log_setup.state_logs[0]
    employee = prev_state_log.employee

    # an exception will set end state to the same start state
    with pytest.raises(Exception):
        with state_log_util.process_state(
            prior_state=State.IDENTIFY_MMARS_STATUS,
            associated_model=employee,
            db_session=test_db_session,
        ):
            raise Exception("An exception message")
    test_db_session.commit()

    state_log = state_log_util.get_latest_state_log_in_end_state(
        employee, State.IDENTIFY_MMARS_STATUS, test_db_session
    )
    assert state_log.end_state.state_id == State.IDENTIFY_MMARS_STATUS.state_id
    assert state_log.outcome["message"] == "Hit exception: Exception"


@pytest.mark.parametrize(
    "associated_model, end_state, err_msg",
    (
        (
            Employee(),
            State.ADD_TO_VCC,
            "Employee model associated with StateLog has no employee_id",
        ),
        (
            Payment(),
            State.PAYMENTS_STORED_IN_DB,
            "Payment model associated with StateLog has no payment_id",
        ),
        (
            ReferenceFile(),
            State.DUA_PAYMENT_LIST_SAVED_TO_S3,
            "ReferenceFile model associated with StateLog has no reference_file_id",
        ),
    ),
)
def test_create_finished_state_log_for_associated_model_without_id_fails(
    test_db_session, associated_model, end_state, err_msg
):
    with pytest.raises(ValueError, match=err_msg):
        state_log_util.create_finished_state_log(
            associated_model=associated_model,
            end_state=end_state,
            outcome={},
            db_session=test_db_session,
        )


@pytest.mark.parametrize(
    "associated_model, flow, err_msg",
    (
        (
            Employee(),
            Flow.VENDOR_CHECK,
            "Employee model associated with StateLog has no employee_id",
        ),
        (Payment(), Flow.PAYMENT, "Payment model associated with StateLog has no payment_id",),
        (
            Claim(),
            Flow.DELEGATED_CLAIM_VALIDATION,
            "Claim model associated with StateLog has no claim_id",
        ),
        (
            ReferenceFile(),
            Flow.DUA_PAYMENT_LIST,
            "ReferenceFile model associated with StateLog has no reference_file_id",
        ),
    ),
)
def test_get_latest_state_log_in_flow_for_associated_model_without_id_fails(
    test_db_session, associated_model, flow, err_msg
):
    with pytest.raises(ValueError, match=err_msg):
        state_log_util.get_latest_state_log_in_flow(
            associated_model=associated_model, flow=flow, db_session=test_db_session
        )


@pytest.mark.parametrize(
    "associated_model, end_state, err_msg",
    (
        (
            Employee(),
            State.ADD_TO_VCC,
            "Employee model associated with StateLog has no employee_id",
        ),
        (
            Payment(),
            State.PAYMENTS_STORED_IN_DB,
            "Payment model associated with StateLog has no payment_id",
        ),
        (
            Claim(),
            State.DELEGATED_CLAIM_EXTRACTED_FROM_FINEOS,
            "Claim model associated with StateLog has no claim_id",
        ),
        (
            ReferenceFile(),
            State.DUA_PAYMENT_LIST_SAVED_TO_S3,
            "ReferenceFile model associated with StateLog has no reference_file_id",
        ),
    ),
)
def test_get_latest_state_log_in_end_state_for_associated_model_without_id_fails(
    test_db_session, associated_model, end_state, err_msg
):
    with pytest.raises(ValueError, match=err_msg):
        state_log_util.get_latest_state_log_in_end_state(
            associated_model=associated_model, end_state=end_state, db_session=test_db_session
        )


@pytest.mark.parametrize(
    "associated_model, end_state, err_msg",
    (
        (
            Employee(),
            State.ADD_TO_VCC,
            "Employee model associated with StateLog has no employee_id",
        ),
        (
            Payment(),
            State.PAYMENTS_STORED_IN_DB,
            "Payment model associated with StateLog has no payment_id",
        ),
        (
            Claim(),
            State.DELEGATED_CLAIM_EXTRACTED_FROM_FINEOS,
            "Claim model associated with StateLog has no claim_id",
        ),
        (
            ReferenceFile(),
            State.DUA_PAYMENT_LIST_SAVED_TO_S3,
            "ReferenceFile model associated with StateLog has no reference_file_id",
        ),
    ),
)
def test_has_been_in_end_state_for_associated_model_without_id_fails(
    test_db_session, associated_model, end_state, err_msg
):
    with pytest.raises(ValueError, match=err_msg):
        state_log_util.has_been_in_end_state(
            associated_model=associated_model, end_state=end_state, db_session=test_db_session
        )
