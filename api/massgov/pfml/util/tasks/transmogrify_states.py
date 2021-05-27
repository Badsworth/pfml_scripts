"""
====================================================================================
CAUTION - WARNING - DANGER - CAUTION - WARNING - DANGER - CAUTION - WARNING - DANGER
====================================================================================
CAUTION - WARNING - DANGER - CAUTION - WARNING - DANGER - CAUTION - WARNING - DANGER
====================================================================================
CAUTION - WARNING - DANGER - CAUTION - WARNING - DANGER - CAUTION - WARNING - DANGER
====================================================================================

Using this utility in production is IMMENSELY risky and should ONLY be used in absolute emergencies.

This utility changes EVERYTHING in a given state to another state which profoundly affects
our processing logic. This should ONLY be used if you understand the exact behavior of the
state log and what the results of this operation will be.

While there is some validation to prevent you from doing certain obviously bad changes,
it is highly recommended that you have at least one other developer vet and verify
what you are about to do before using this tool.

As a precaution, this tool explicitly does not commit changes UNLESS you pass in
the `--commit` flag and will by default be run in a dry run mode.

====================================================================================
CAUTION - WARNING - DANGER - CAUTION - WARNING - DANGER - CAUTION - WARNING - DANGER
====================================================================================
CAUTION - WARNING - DANGER - CAUTION - WARNING - DANGER - CAUTION - WARNING - DANGER
====================================================================================
CAUTION - WARNING - DANGER - CAUTION - WARNING - DANGER - CAUTION - WARNING - DANGER
====================================================================================
"""

import argparse
import sys
from typing import List

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import LkState, StateLog
from massgov.pfml.util.logging import audit

logger = logging.get_logger(__name__)


class Configuration:
    current_state_id: int
    new_state_id: int

    outcome: str

    do_commit: bool

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(
            description="Move all records from a current state to a new one"
        )
        parser.add_argument("--current-state", type=int, required=True, help="The current state ID")
        parser.add_argument("--new-state", type=int, required=True, help="The new state ID")
        parser.add_argument(
            "--outcome", type=str, required=True, help="The outcome to write to the DB"
        )
        parser.add_argument(
            "--commit",
            help="Setting this argument will disable dry run (default mode).",
            action="store_true",
        )
        args = parser.parse_args(input_args)

        self.current_state_id = args.current_state
        self.new_state_id = args.new_state
        self.outcome = args.outcome
        self.do_commit = args.commit


def make_db_session() -> db.Session:
    return db.init(sync_lookups=True)


def transmogrify_states():
    """Entry point for changing all state logs in a given state to another new state
       Note this is deliberately named "transmogrify" instead of state to illicit a reaction
       that this is not just a simple/routine script to be run (see above description)
    """
    audit.init_security_logging()
    logging.init(__name__)

    config = Configuration(sys.argv[1:])

    with db.session_scope(make_db_session(), close=True) as db_session:
        _transmogrify_states(db_session, config)


def _transmogrify_states(db_session: db.Session, config: Configuration) -> None:
    # Need to query the DB to get the state objects
    current_state = (
        db_session.query(LkState).filter(LkState.state_id == config.current_state_id).one_or_none()
    )
    new_state = (
        db_session.query(LkState).filter(LkState.state_id == config.new_state_id).one_or_none()
    )

    if current_state is None:
        raise ValueError(
            f"Current state ID {config.current_state_id} does not correspond to any known state."
        )
    if new_state is None:
        raise ValueError(
            f"New state ID {config.new_state_id} does not correspond to any known state."
        )

    if current_state.state_id == new_state.state_id:
        raise ValueError(
            "Cannot change state to identical state: current-state cannot match new-state."
        )

    if current_state.flow_id != new_state.flow_id:
        raise ValueError(
            f"Cannot update state as states are in different flows. Current state flow ID: {current_state.flow_id}. New state flow ID: {new_state.flow_id}."
        )

    state_logs: List[
        StateLog
    ] = state_log_util.get_all_latest_state_logs_regardless_of_associated_class(
        current_state, db_session
    )
    if not state_logs:
        logger.warning(
            f"No state logs were found in state [{current_state.state_description}] - Exiting."
        )
        return

    logger.info(
        f"{len(state_logs)} state logs were found in state [{current_state.state_description}] and will be moved to [{new_state.state_description}]"
    )

    if not config.do_commit:
        logger.info("This is a dry run, no state logs were updated.")
        return

    for state_log in state_logs:
        associated_model = state_log_util.AssociatedClass.get_associated_model(state_log)

        if associated_model is None:
            logger.error(
                "A state log exists without an associated model. This shouldn't be possible.",
                extra={"state_log_id": state_log.state_log_id},
            )
            continue

        logger.debug(
            "Updating state log %s from current state (id: %s, description: %s) to new state (id: %s, description %s)",
            state_log.state_log_id,
            current_state.state_id,
            current_state.state_description,
            new_state.state_id,
            new_state.state_description,
        )
        state_log_util.create_finished_state_log(
            associated_model=associated_model,
            end_state=new_state,
            outcome=state_log_util.build_outcome(config.outcome),
            db_session=db_session,
        )

    db_session.commit()
    logger.info("Successfully ran and updated state logs.")
