import argparse
import sys
from typing import List

import massgov.pfml.db as db
import massgov.pfml.delegated_payments.pub.response_file_handler as response_file_handler
import massgov.pfml.util.logging as logging
import massgov.pfml.util.logging.audit as audit

logger = logging.get_logger(__name__)


ALL = "ALL"
PICKUP_FILES = "pickup"
PROCESS_RESPONSES = "process"
ALLOWED_VALUES = [
    ALL,
    PICKUP_FILES,
    PROCESS_RESPONSES,
]


class Configuration:
    pickup_files: bool
    process_responses: bool

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(
            description="Pick up and process PUB status response files"
        )
        parser.add_argument(
            "--steps",
            nargs="+",
            choices=ALLOWED_VALUES,
            default=[ALL],
            help="Indicate which steps of the process to run",
        )

        args = parser.parse_args(input_args)
        steps = set(args.steps)

        if ALL in steps:
            self.pickup_files = True
            self.process_responses = True
        else:
            self.pickup_files = PICKUP_FILES in steps
            self.process_responses = PROCESS_RESPONSES in steps


def make_db_session() -> db.Session:
    return db.init(sync_lookups=True)


def main():
    """Entry point for PUB Response Processing"""
    audit.init_security_logging()
    logging.init(__name__)

    config = Configuration(sys.argv[1:])

    with db.session_scope(make_db_session(), close=True) as db_session, db.session_scope(
        make_db_session(), close=True
    ) as log_entry_db_session:
        _process_pub_responses(db_session, log_entry_db_session, config)


def _process_pub_responses(
    db_session: db.Session, log_entry_db_session: db.Session, config: Configuration
) -> None:
    """Process PUB Responses"""
    logger.info("Start - PUB Responses ECS Task")

    if config.pickup_files:
        response_file_handler.copy_response_files_to_s3(db_session)

    if config.process_responses:
        response_file_handler.process_pending_response_files(db_session)

    logger.info("Done - PUB Responses ECS Task")
