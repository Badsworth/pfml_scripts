import abc
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Generator, List, Optional, Union
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

import massgov.pfml.db as db
import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Claim,
    Employee,
    LatestStateLog,
    LkFlow,
    LkState,
    Payment,
    ReferenceFile,
    StateLog,
)
from massgov.pfml.delegated_payments.delegated_payments_util import (
    ValidationContainer as DelegatedValidationContainer,
)

logger = logging.get_logger(__name__)

# The types this state log supports querying for
AssociatedModel = Union[Claim, Employee, Payment, ReferenceFile]


class AssociatedClass(Enum):
    EMPLOYEE = "employee"
    CLAIM = "claim"
    PAYMENT = "payment"
    REFERENCE_FILE = "reference_file"

    @staticmethod
    def get_associated_type(associated_model: AssociatedModel) -> "AssociatedClass":
        if isinstance(associated_model, Payment):
            return AssociatedClass.PAYMENT
        elif isinstance(associated_model, Employee):
            return AssociatedClass.EMPLOYEE
        elif isinstance(associated_model, Claim):
            return AssociatedClass.CLAIM
        elif isinstance(associated_model, ReferenceFile):
            return AssociatedClass.REFERENCE_FILE

    @staticmethod
    def get_associated_model(state_log: StateLog) -> Optional[AssociatedModel]:
        if state_log.associated_type == AssociatedClass.EMPLOYEE.value:
            return state_log.employee
        elif state_log.associated_type == AssociatedClass.CLAIM.value:
            return state_log.claim
        elif state_log.associated_type == AssociatedClass.PAYMENT.value:
            return state_log.payment
        elif state_log.associated_type == AssociatedClass.REFERENCE_FILE.value:
            return state_log.reference_file
        return None


class QueryParamHelper(abc.ABC, metaclass=abc.ABCMeta):
    """
    Abstract base class for organizing and constructing common query params.

    """

    associated_model: AssociatedModel

    def __init__(self, associated_model: AssociatedModel) -> None:
        _raise_exception_if_associated_model_has_no_id(associated_model)
        self.associated_model = associated_model

    def get_associated_class(self) -> AssociatedClass:
        return AssociatedClass.get_associated_type(self.associated_model)

    @abc.abstractmethod
    def get_associated_model_id(self) -> UUID:
        pass

    @abc.abstractmethod
    def get_latest_filter_params(self) -> List[Any]:
        pass

    @abc.abstractmethod
    def get_all_state_logs_for_model_filter_params(self) -> List[Any]:
        pass

    @abc.abstractmethod
    def get_log_message(self) -> str:
        pass

    @abc.abstractmethod
    def attach_model_to_state_log(self, state_log: StateLog) -> None:
        pass


class EmployeeQueryParamHelper(QueryParamHelper):
    associated_model: Employee

    def get_associated_model_id(self) -> UUID:
        return self.associated_model.employee_id

    def get_latest_filter_params(self) -> List[Any]:
        return [LatestStateLog.employee_id == self.associated_model.employee_id]

    def get_all_state_logs_for_model_filter_params(self) -> List[Any]:
        return [StateLog.employee_id == self.associated_model.employee_id]

    def get_log_message(self) -> str:
        return f"Query - employee id: {self.get_associated_model_id()}"

    def attach_model_to_state_log(self, state_log: StateLog) -> None:
        state_log.employee = self.associated_model


class PaymentQueryParamHelper(QueryParamHelper):
    associated_model: Payment

    def get_associated_model_id(self) -> UUID:
        return self.associated_model.payment_id

    def get_latest_filter_params(self) -> List[Any]:
        return [LatestStateLog.payment_id == self.associated_model.payment_id]

    def get_all_state_logs_for_model_filter_params(self) -> List[Any]:
        return [StateLog.payment_id == self.associated_model.payment_id]

    def get_log_message(self) -> str:
        return f"Query - payment id: {self.get_associated_model_id()}"

    def attach_model_to_state_log(self, state_log: StateLog) -> None:
        state_log.payment = self.associated_model


class ClaimQueryParamHelper(QueryParamHelper):
    associated_model: Claim

    def get_associated_model_id(self) -> UUID:
        return self.associated_model.claim_id

    def get_latest_filter_params(self) -> List[Any]:
        return [LatestStateLog.claim_id == self.associated_model.claim_id]

    def get_all_state_logs_for_model_filter_params(self) -> List[Any]:
        return [StateLog.claim_id == self.associated_model.claim_id]

    def get_log_message(self) -> str:
        return f"Query - claim id: {self.get_associated_model_id()}"

    def attach_model_to_state_log(self, state_log: StateLog) -> None:
        state_log.claim = self.associated_model


class ReferenceFileQueryParamHelper(QueryParamHelper):
    associated_model: ReferenceFile

    def get_associated_model_id(self) -> UUID:
        return self.associated_model.reference_file_id

    def get_latest_filter_params(self) -> List[Any]:
        return [LatestStateLog.reference_file_id == self.associated_model.reference_file_id]

    def get_all_state_logs_for_model_filter_params(self) -> List[Any]:
        return [StateLog.reference_file_id == self.associated_model.reference_file_id]

    def get_log_message(self) -> str:
        return f"Query - reference_file_id: {self.get_associated_model_id()}"

    def attach_model_to_state_log(self, state_log: StateLog) -> None:
        state_log.reference_file = self.associated_model


def build_query_param_helper(associated_model: AssociatedModel) -> QueryParamHelper:
    if isinstance(associated_model, Employee):
        return EmployeeQueryParamHelper(associated_model)

    elif isinstance(associated_model, Claim):
        return ClaimQueryParamHelper(associated_model)

    elif isinstance(associated_model, Payment):
        return PaymentQueryParamHelper(associated_model)

    elif isinstance(associated_model, ReferenceFile):
        return ReferenceFileQueryParamHelper(associated_model)


def get_now() -> datetime:
    return datetime_util.utcnow()


def create_finished_state_log(
    associated_model: AssociatedModel,
    end_state: LkState,
    outcome: Dict[str, Any],
    db_session: db.Session,
    start_time: Optional[datetime] = None,
    import_log_id: Optional[int] = None,
) -> StateLog:
    # Let the user pass in a start time so start/end aren't the same
    start_state_time = start_time if start_time else get_now()
    associated_class = AssociatedClass.get_associated_type(associated_model)

    return _create_state_log(
        end_state=end_state,
        associated_model=associated_model,
        associated_class=associated_class,
        outcome=outcome,
        start_time=start_state_time,
        db_session=db_session,
        import_log_id=import_log_id,
    )


def _create_state_log(
    associated_model: Optional[AssociatedModel],
    associated_class: AssociatedClass,
    end_state: LkState,
    outcome: Dict[str, str],
    db_session: db.Session,
    start_time: datetime,
    prev_state_log: Optional[StateLog] = None,
    import_log_id: Optional[int] = None,
) -> StateLog:

    now = get_now()
    state_log = StateLog(
        end_state_id=end_state.state_id,
        outcome=outcome,
        started_at=start_time,
        associated_type=associated_class.value,
        ended_at=now,
        import_log_id=import_log_id,
    )

    messages = []
    try:
        latest_query_params = []
        if associated_model:
            query_param_helper = build_query_param_helper(associated_model)

            latest_query_params = query_param_helper.get_latest_filter_params()

            query_param_helper.attach_model_to_state_log(state_log)
            messages.append(query_param_helper.get_log_message())

            # We also want the latest state log to be in the same flow and flow is attached to the states
            latest_query_params.append(LkState.flow_id == end_state.flow_id)
            messages.append(f"Query - flow id: {end_state.flow_id}")

        logger.debug(
            "create state log for %s - end state: %s (%s), query: %s",
            associated_class.value,
            end_state.state_description,
            end_state.state_id,
            ", ".join(messages),
            extra={"outcome": outcome},
        )

        db_session.add(state_log)
        _create_or_update_latest_state_log(
            state_log, latest_query_params, prev_state_log, db_session
        )
    except Exception:
        logger.exception(
            "Error trying to create or update latest state log - %s", ", ".join(messages)
        )
        raise

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
        except SQLAlchemyError as e:
            logger.exception(
                "Unexpected error %s with one_or_none() when querying for latest state log",
                type(e),
                extra={
                    "state_log_id": state_log.state_log_id or "Empty",
                    "claim_id": state_log.claim_id or "Empty",
                    "payment_id": state_log.payment_id or "Empty",
                    "employee_id": state_log.employee_id or "Empty",
                    "reference_file_id": state_log.reference_file_id or "Empty",
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
        latest_state_log.claim = state_log.claim
        latest_state_log.employee = state_log.employee
        latest_state_log.payment = state_log.payment
        latest_state_log.reference_file = state_log.reference_file

    latest_state_log.state_log = state_log

    db_session.add(latest_state_log)


def create_state_log_without_associated_model(
    end_state: LkState,
    associated_class: AssociatedClass,
    outcome: Dict[str, str],
    db_session: db.Session,
    start_time: Optional[datetime] = None,
    prev_state_log: Optional[StateLog] = None,
) -> StateLog:
    start_state_time = start_time if start_time else get_now()

    return _create_state_log(
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
    # Get params needed for latest state log query
    query_param_helper = build_query_param_helper(associated_model)
    filter_params = query_param_helper.get_latest_filter_params()

    # Add the flow
    filter_params.append(LkState.flow_id == flow.flow_id)

    latest_state_log: Optional[StateLog] = (
        db_session.query(StateLog)
        .join(LatestStateLog)
        .join(LkState, StateLog.end_state_id == LkState.state_id)
        .filter(*filter_params)
        .one_or_none()
    )
    logger.debug(
        "Latest state log flow query result - associated class: %s, associated model id: %s, flow state: %s (%s), id: %s",
        AssociatedClass.get_associated_type(associated_model).value,
        query_param_helper.get_associated_model_id(),
        flow.flow_description,
        flow.flow_id,
        ("None" if not latest_state_log else latest_state_log.state_log_id),
    )

    return latest_state_log


def get_latest_state_log_in_end_state(
    associated_model: AssociatedModel, end_state: LkState, db_session: db.Session,
) -> Optional[StateLog]:
    # Get params needed for latest state log query
    query_param_helper = build_query_param_helper(associated_model)
    filter_params = query_param_helper.get_latest_filter_params()

    # Also filter on the end state ID
    filter_params.append(StateLog.end_state_id == end_state.state_id)

    # Example query (for employee scenario)
    #
    # SELECT * from state_log
    # WHERE state_log.end_state_id={end_state.state_id} AND
    #       latest_state_log.employee_id={associated_model.employee_id}
    # JOIN latest_state_log ON (state_log.state_log_id = latest_state_log.state_log_id)
    latest_state_log: Optional[StateLog] = db_session.query(StateLog).join(LatestStateLog).filter(
        *filter_params
    ).one_or_none()
    logger.debug(
        "Latest state log query result - associated class: %s, associated model id: %s, end state: %s (%s), id: %s",
        AssociatedClass.get_associated_type(associated_model).value,
        query_param_helper.get_associated_model_id(),
        end_state.state_description,
        end_state.state_id,
        ("None" if not latest_state_log else latest_state_log.state_log_id),
    )

    return latest_state_log


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
    latest_state_logs = db_session.query(StateLog).join(LatestStateLog).filter(*filter_params).all()
    logger.debug(
        "Latest state logs query result - associated class: %s, end state: %s (%s), count: %i",
        associated_class.value,
        end_state.state_description,
        end_state.state_id,
        len(latest_state_logs),
    )

    return latest_state_logs


def get_all_latest_state_logs_regardless_of_associated_class(
    end_state: LkState, db_session: db.Session
) -> List[StateLog]:
    # Example query
    #
    # SELECT * from state_log
    # WHERE state_log.end_state_id={end_state.state_id}
    # JOIN latest_state_log ON (state_log.state_log_id = latest_state_log.state_log_id)
    latest_state_logs = (
        db_session.query(StateLog)
        .join(LatestStateLog)
        .filter(StateLog.end_state_id == end_state.state_id)
        .all()
    )
    logger.debug(
        "Latest state logs query result - end state: %s (%s), count: %i",
        end_state.state_description,
        end_state.state_id,
        len(latest_state_logs),
    )

    return latest_state_logs


def has_been_in_end_state(
    associated_model: AssociatedModel, db_session: db.Session, end_state: LkState
) -> bool:
    # Get the query params to filter state logs to the ones specific to this model
    query_param_helper = build_query_param_helper(associated_model)
    filter_params = query_param_helper.get_all_state_logs_for_model_filter_params()

    # Filter to just the state log we want to check
    filter_params.append(StateLog.end_state_id == end_state.state_id)

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


def get_state_counts(db_session: db.Session) -> Dict[str, int]:
    """
    Get a dictionary of state_description -> count for all latest state logs
    Note that this method logs the counts it finds whenever it's called.
    """
    # Query looks like:
    #
    # SELECT lk_state.state_description, lk_state.state_id, COUNT(latest_state_log.latest_state_log_id)
    # FROM latest_state_log
    # JOIN state_log ON latest_state_log.state_log_id = state_log.state_log_id
    # JOIN lk_state ON state_log.end_state_id = lk_state.state_id
    # GROUP BY lk_state.state_id, lk_state.flow_id
    latest_state_log_counts = (
        db_session.query(
            LkState.state_description,
            LkState.state_id,
            func.count(LatestStateLog.latest_state_log_id),
        )
        .join(StateLog, LatestStateLog.state_log_id == StateLog.state_log_id)
        .join(LkState)
        .group_by(LkState.state_id, LkState.flow_id)
        .all()
    )

    logger.info("Fetched state log counts")
    state_counts = {}
    for record in latest_state_log_counts:
        description = record[0]
        state_id = record[1]
        count = record[2]
        logger.info(
            "[%s][%i]: %i",
            description,
            state_id,
            count,
            extra={"state_description": description, "state_id": state_id, "count": count},
        )
        state_counts[description] = count

    return state_counts


def build_outcome(
    message: str,
    validation_container: Optional[DelegatedValidationContainer] = None,
    **extra_attributes: str,
) -> Dict[str, Any]:
    outcome: Dict[str, Any] = {}
    outcome["message"] = message

    # Only add a validation container if it had any issues (otherwise leave that empty)
    if validation_container and validation_container.has_validation_issues():
        outcome["validation_container"] = asdict(validation_container)

    outcome.update(extra_attributes)
    return outcome


@contextmanager
def process_state(
    prior_state: LkState, associated_model: AssociatedModel, db_session: db.Session
) -> Generator[None, None, None]:
    """Log an exception if an error occurs while processing a state
    """

    try:
        yield
    except Exception as e:
        create_finished_state_log(
            end_state=prior_state,  # Create the error, but don't change the state
            associated_model=associated_model,
            outcome=build_outcome(f"Hit exception: {type(e).__name__}"),
            db_session=db_session,
        )
        # then re-raise the exception
        raise


def _raise_exception_if_associated_model_has_no_id(associated_model: AssociatedModel) -> None:
    if isinstance(associated_model, Employee) and associated_model.employee_id is None:
        raise ValueError("Employee model associated with StateLog has no employee_id")
    elif isinstance(associated_model, Claim) and associated_model.claim_id is None:
        raise ValueError("Claim model associated with StateLog has no claim_id")
    elif isinstance(associated_model, Payment) and associated_model.payment_id is None:
        raise ValueError("Payment model associated with StateLog has no payment_id")
    elif isinstance(associated_model, ReferenceFile) and associated_model.reference_file_id is None:
        raise ValueError("ReferenceFile model associated with StateLog has no reference_file_id")
