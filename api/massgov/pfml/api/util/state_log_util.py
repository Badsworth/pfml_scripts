from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Generator, List, Optional, Union

from sqlalchemy.orm.exc import MultipleResultsFound

import massgov.pfml.db as db
import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Employee,
    LatestStateLog,
    LkFlow,
    LkState,
    Payment,
    ReferenceFile,
    StateLog,
)
from massgov.pfml.payments.payments_util import ValidationContainer

logger = logging.get_logger(__name__)

# The types this state log supports querying for
AssociatedModel = Union[Employee, Payment, ReferenceFile]


class AssociatedClass(Enum):
    EMPLOYEE = "employee"
    PAYMENT = "payment"
    REFERENCE_FILE = "reference_file"

    @staticmethod
    def get_associated_type(associated_model: AssociatedModel) -> "AssociatedClass":
        if isinstance(associated_model, Payment):
            return AssociatedClass.PAYMENT
        elif isinstance(associated_model, Employee):
            return AssociatedClass.EMPLOYEE
        elif isinstance(associated_model, ReferenceFile):
            return AssociatedClass.REFERENCE_FILE

    @staticmethod
    def get_associated_model(state_log: StateLog) -> Optional[AssociatedModel]:
        if state_log.associated_type == AssociatedClass.EMPLOYEE.value:
            return state_log.employee
        elif state_log.associated_type == AssociatedClass.PAYMENT.value:
            return state_log.payment
        elif state_log.associated_type == AssociatedClass.REFERENCE_FILE.value:
            return state_log.reference_file
        return None


def get_now() -> datetime:
    return datetime_util.utcnow()


def create_finished_state_log(
    associated_model: AssociatedModel,
    start_state: LkState,
    end_state: LkState,
    outcome: Dict[str, str],
    db_session: db.Session,
    start_time: Optional[datetime] = None,
) -> StateLog:
    # Let the user pass in a start time so start/end aren't the same
    start_state_time = start_time if start_time else get_now()
    associated_class = AssociatedClass.get_associated_type(associated_model)

    return _create_state_log(
        start_state=start_state,
        end_state=end_state,
        associated_model=associated_model,
        associated_class=associated_class,
        outcome=outcome,
        start_time=start_state_time,
        db_session=db_session,
    )


def _create_state_log(
    associated_model: Optional[AssociatedModel],
    associated_class: AssociatedClass,
    start_state: LkState,
    end_state: LkState,
    outcome: Dict[str, str],
    db_session: db.Session,
    start_time: datetime,
    prev_state_log: Optional[StateLog] = None,
) -> StateLog:
    now = get_now()
    state_log = StateLog(
        start_state_id=start_state.state_id,
        end_state_id=end_state.state_id,
        outcome=outcome,
        started_at=start_time,
        associated_type=associated_class.value,
        ended_at=now,
    )

    latest_query_params = None
    if associated_model:
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
        # We also want the latest state log to be in the same flow and flow is attached to the states
        latest_query_params.append(LkState.flow_id == end_state.flow_id)

    db_session.add(state_log)
    _create_or_update_latest_state_log(state_log, latest_query_params, prev_state_log, db_session)

    return state_log


def _create_or_update_latest_state_log(
    state_log: StateLog,
    latest_query_params: List,
    prev_state_log: Optional[StateLog],
    db_session: db.Session,
) -> None:
    # Grab the latest state log and if it exists
    # add a pointer back to the most recent state log

    latest_state_log = None
    # In some cases, we know this is the first one (eg. from create_state_log_without_associated_model)
    if latest_query_params and not prev_state_log:
        try:
            latest_state_log = (
                db_session.query(LatestStateLog)
                .join(StateLog)
                .join(LkState, StateLog.end_state_id == LkState.state_id)
                .filter(*latest_query_params)
                .one_or_none()
            )
        except MultipleResultsFound:
            logger.warning(
                "Unexpected error with one_or_none()",
                extra={
                    "state_log_id": state_log.state_log_id,
                    "payment_id": state_log.payment_id,
                    "employee_id": state_log.employee_id,
                    "reference_file_id": state_log.reference_file_id,
                },
            )
            raise
    elif prev_state_log:
        # If we have a previous state log
        # Get the latest state log that points to it
        latest_state_log = (
            db_session.query(LatestStateLog)
            .filter(LatestStateLog.state_log_id == prev_state_log.state_log_id)
            .one_or_none()
        )

    if latest_state_log:
        state_log.prev_state_log_id = latest_state_log.state_log_id

    # If no existing latest state log entry exists, add it
    else:
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


def create_state_log_without_associated_model(
    start_state: LkState,
    end_state: LkState,
    associated_class: AssociatedClass,
    outcome: Dict[str, str],
    db_session: db.Session,
    start_time: Optional[datetime] = None,
    prev_state_log: Optional[StateLog] = None,
) -> StateLog:
    start_state_time = start_time if start_time else get_now()

    return _create_state_log(
        start_state=start_state,
        end_state=end_state,
        associated_model=None,
        associated_class=associated_class,
        outcome=outcome,
        start_time=start_state_time,
        db_session=db_session,
        prev_state_log=prev_state_log,
    )


def get_latest_state_log_in_flow(
    associated_model: AssociatedModel, flow: LkFlow, db_session: db.Session
) -> Optional[StateLog]:
    filter_params = [LkState.flow_id == flow.flow_id]

    if isinstance(associated_model, Employee):
        filter_params.append(LatestStateLog.employee_id == associated_model.employee_id)
    elif isinstance(associated_model, Payment):
        filter_params.append(LatestStateLog.payment_id == associated_model.payment_id)
    elif isinstance(associated_model, ReferenceFile):
        filter_params.append(LatestStateLog.reference_file_id == associated_model.reference_file_id)

    return (
        db_session.query(StateLog)
        .join(LatestStateLog)
        .join(LkState, StateLog.end_state_id == LkState.state_id)
        .filter(*filter_params)
        .one_or_none()
    )


def get_latest_state_log_in_end_state(
    associated_model: AssociatedModel, end_state: LkState, db_session: db.Session,
) -> Optional[StateLog]:
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


def get_all_latest_state_logs_regardless_of_associated_class(
    end_state: LkState, db_session: db.Session
) -> List[StateLog]:
    # Example query
    #
    # SELECT * from state_log
    # WHERE state_log.end_state_id={end_state.state_id}
    # JOIN latest_state_log ON (state_log.state_log_id = latest_state_log.state_log_id)
    return (
        db_session.query(StateLog)
        .join(LatestStateLog)
        .filter(StateLog.end_state_id == end_state.state_id)
        .all()
    )


def has_been_in_end_state(
    associated_model: AssociatedModel, db_session: db.Session, end_state: LkState
) -> bool:
    filter_params = [StateLog.end_state_id == end_state.state_id]

    if isinstance(associated_model, Employee):
        filter_params.append(StateLog.employee_id == associated_model.employee_id)
    elif isinstance(associated_model, Payment):
        filter_params.append(StateLog.payment_id == associated_model.payment_id)
    elif isinstance(associated_model, ReferenceFile):
        filter_params.append(StateLog.reference_file_id == associated_model.reference_file_id)

    # Query is effectively (for an employee):
    # SELECT count(*) FROM state_log
    # WHERE state_log.end_state_id == {end_state.state_id} AND
    #       state_log.employee_id == {employee.employee_id}
    count = db_session.query(StateLog).filter(*filter_params).count()
    return count > 0


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
    message: str, validation_container: Optional[ValidationContainer] = None
) -> Dict[str, Any]:
    outcome: Dict[str, Any] = {}
    outcome["message"] = message

    # Only add a validation container if it had any issues (otherwise leave that empty)
    if validation_container and validation_container.has_validation_issues():
        outcome["validation_container"] = asdict(validation_container)
    return outcome


@contextmanager
def process_state(
    start_state: LkState, associated_model: AssociatedModel, db_session: db.Session
) -> Generator[None, None, None]:
    """Log an exception if an error occurs while processing a state
    """

    try:
        yield
    except Exception as e:
        create_finished_state_log(
            start_state=start_state,
            end_state=start_state,  # Create the error, but don't change the state
            associated_model=associated_model,
            outcome=build_outcome(f"Hit exception: {type(e).__name__}"),
            db_session=db_session,
        )
        # then re-raise the exception
        raise
