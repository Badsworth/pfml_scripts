from dataclasses import asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import massgov.pfml.db as db
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.datetime as datetime_util
from massgov.pfml.db.models.employees import (
    Employee,
    LatestStateLog,
    LkState,
    Payment,
    ReferenceFile,
    StateLog,
)

# The types this state log supports querying for
AssociatedModel = Union[Employee, Payment, ReferenceFile]


class AssociatedClass(Enum):
    EMPLOYEE = "employee"
    PAYMENT = "payment"
    REFERENCE_FILE = "reference_file"

    @staticmethod
    def get_associated_type(associated_model: AssociatedModel) -> str:
        if isinstance(associated_model, Payment):
            return AssociatedClass.PAYMENT.value
        elif isinstance(associated_model, Employee):
            return AssociatedClass.EMPLOYEE.value
        elif isinstance(associated_model, ReferenceFile):
            return AssociatedClass.REFERENCE_FILE.value


def get_now() -> datetime:
    return datetime_util.utcnow()


def _create_or_update_latest_state_log(
    state_log: StateLog, latest_query_params: Optional[List], db_session: db.Session
) -> None:
    # Grab the latest state log and if it exists
    # add a pointer back to the previous most recent state log

    latest_state_log = None
    # In some cases, we know this is the first one (eg. from create_state_log_without_associated_model)
    if latest_query_params is not None:
        latest_state_log = (
            db_session.query(LatestStateLog).filter(*latest_query_params).one_or_none()
        )

    if latest_state_log:
        state_log.prev_state_log = latest_state_log.state_log

    # If no existing latest state log entry exists, add it
    if not latest_state_log:
        latest_state_log = LatestStateLog()
        # all values in this statement should only be set
        # when the latest state log is initialized.

        # Only one of the below models will not be None, but
        # they default to None anyways
        latest_state_log.employee = state_log.employee
        latest_state_log.payment = state_log.payment
        latest_state_log.reference_file = state_log.reference_file

    latest_state_log.state_log = state_log

    db_session.add(latest_state_log)


def create_state_log(
    start_state: LkState,
    associated_model: AssociatedModel,
    db_session: db.Session,
    commit: bool = True,
) -> StateLog:
    now = get_now()

    state_log = StateLog(start_state_id=start_state.state_id, started_at=now)
    latest_query_params = []

    # Depending on whether it's a payment/employee/reference_file, need to setup
    # the object and query params differently
    if isinstance(associated_model, Payment):
        state_log.payment = associated_model
        latest_query_params.append(LatestStateLog.payment_id == associated_model.payment_id)
    elif isinstance(associated_model, Employee):
        state_log.employee = associated_model
        latest_query_params.append(LatestStateLog.employee_id == associated_model.employee_id)
    elif isinstance(associated_model, ReferenceFile):
        state_log.reference_file = associated_model
        latest_query_params.append(
            LatestStateLog.reference_file_id == associated_model.reference_file_id
        )
    state_log.associated_type = AssociatedClass.get_associated_type(associated_model)
    db_session.add(state_log)

    _create_or_update_latest_state_log(state_log, latest_query_params, db_session)

    if commit:
        db_session.commit()
    return state_log


def create_state_log_without_associated_model(
    start_state: LkState,
    associated_class: AssociatedClass,
    db_session: db.Session,
    commit: bool = True,
) -> StateLog:
    now = get_now()

    state_log = StateLog(
        start_state_id=start_state.state_id, started_at=now, associated_type=associated_class.value
    )
    db_session.add(state_log)

    _create_or_update_latest_state_log(state_log, None, db_session)

    if commit:
        db_session.commit()
    return state_log


def finish_state_log(
    state_log: StateLog,
    end_state: LkState,
    outcome: Dict[str, str],
    db_session: db.Session,
    commit: bool = True,
) -> StateLog:
    now = get_now()

    state_log.ended_at = now
    state_log.end_state_id = end_state.state_id
    state_log.outcome = outcome

    if commit:
        db_session.commit()
    return state_log


def get_latest_state_log_in_end_state(
    associated_model: AssociatedModel, end_state: LkState, db_session: db.Session,
) -> StateLog:
    filter_params = [StateLog.end_state_id == end_state.state_id]

    if isinstance(associated_model, Employee):
        filter_params.append(LatestStateLog.employee_id == associated_model.employee_id)
    elif isinstance(associated_model, Payment):
        filter_params.append(LatestStateLog.payment_id == associated_model.payment_id)
    elif isinstance(associated_model, ReferenceFile):
        filter_params.append(LatestStateLog.reference_file_id == associated_model.reference_file_id)

    # Example query (for employee scenario)
    #
    # SELECT * from state_log
    # WHERE state_log.end_state_id={end_state.state_id} AND
    #       latest_state_log.employee_id={associated_model.employee_id}
    # JOIN latest_state_log ON (state_log.state_log_id = latest_state_log.state_log_id)
    return db_session.query(StateLog).join(LatestStateLog).filter(*filter_params).one_or_none()


def get_all_latest_state_logs_in_end_state(
    associated_class: AssociatedClass, end_state: LkState, db_session: db.Session
) -> List[StateLog]:
    filter_params = [
        StateLog.end_state_id == end_state.state_id,
        StateLog.associated_type == associated_class.value,
    ]

    # Example query (for employee scenario)
    #
    # SELECT * from state_log
    # WHERE state_log.end_state_id={end_state.state_id} AND
    #       latest_state_log.associated_class = "employee"
    # JOIN latest_state_log ON (state_log.state_log_id = latest_state_log.state_log_id)
    return db_session.query(StateLog).join(LatestStateLog).filter(*filter_params).all()


def get_state_logs_stuck_in_state(
    associated_class: AssociatedClass,
    end_state: LkState,
    days_stuck: int,
    db_session: db.Session,
    now: Optional[datetime] = None,
) -> List[StateLog]:
    state_logs = get_all_latest_state_logs_in_end_state(
        associated_class=associated_class, end_state=end_state, db_session=db_session
    )

    stuck_state_logs = []
    for state_log in state_logs:
        # Get how long a state log has been in its current state
        # Note this iterates backwards to find the earliest state with
        # the same end_state and uses that state_logs ended_at time
        time_elapsed = get_time_in_current_state(state_log, now)

        # Note, timedelta.days will give a count of WHOLE days that have passed
        # eg. if it is equal to 47 hours, that will return 1 day (not 2)
        if time_elapsed and time_elapsed.days >= days_stuck:
            stuck_state_logs.append(state_log)

    return stuck_state_logs


def get_time_in_current_state(
    state_log: StateLog, now: Optional[datetime] = None
) -> Optional[timedelta]:
    curr_state_log = state_log
    state_log_iter = state_log.prev_state_log

    while state_log_iter:
        # We want to iterate back until the end state is something else
        # or we just get to the earliest state
        if state_log_iter.end_state_id != state_log.end_state_id:
            break
        curr_state_log = state_log_iter
        state_log_iter = state_log_iter.prev_state_log

    return _get_time_since_ended(curr_state_log, now)


def _get_time_since_ended(
    state_log: StateLog, now: Optional[datetime] = None
) -> Optional[timedelta]:
    # Allow for passing in now so if you're checking
    # multiple state_log objects, you can compare against
    # the same time (and not have a slight drift in times).
    if not state_log.ended_at:
        return None  # TODO How do we want to handle this scenario?

    if now:
        current_time = now
    else:
        current_time = get_now()

    elapsed_time = current_time - state_log.ended_at
    return elapsed_time


def build_outcome(
    message: str, validation_container: Optional[payments_util.ValidationContainer] = None
) -> Dict[str, Any]:
    outcome: Dict[str, Any] = {}
    outcome["message"] = message

    # Only add a validation container if it had any issues (otherwise leave that empty)
    if validation_container and validation_container.has_validation_issues():
        outcome["validation_container"] = asdict(validation_container)
    return outcome
