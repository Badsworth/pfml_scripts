import argparse
import sys
from typing import List

import massgov.pfml.db as db
import massgov.pfml.util.logging as logging
from massgov.pfml.delegated_payments.pub.transaction_file_creator import TransactionFileCreator

logger = logging.get_logger(__name__)


ALL = "ALL"
PROCESS_CHECKS = "checks"
PROCESS_PRENOTES = "prenotes"
PROCESS_ACH = "ach"
SEND_FILES = "send"
ALLOWED_VALUES = [
    ALL,
    PROCESS_CHECKS,
    PROCESS_PRENOTES,
    PROCESS_ACH,
    SEND_FILES,
]


class Configuration:
    process_checks: bool
    process_prenotes: bool
    process_ach: bool
    send_files: bool

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(
            description="Create and send PUB transactions for ACH pre-notes, check, and ACH payments"
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
            self.process_checks = True
            self.process_prenotes = True
            self.process_ach = True
            self.send_files = True
        else:
            self.process_checks = PROCESS_CHECKS in steps
            self.process_prenotes = PROCESS_PRENOTES in steps
            self.process_ach = PROCESS_ACH in steps
            self.send_files = SEND_FILES in steps


def make_db_session() -> db.Session:
    return db.init(sync_lookups=True)


def main():
    """Entry point for PUB Payment Processing"""
    logging.audit.init_security_logging()
    logging.init(__name__)

    config = Configuration(sys.argv[1:])

    with db.session_scope(make_db_session(), close=True) as db_session:
        _process_pub_payments(db_session, config)


def _process_pub_payments(db_session: db.Session, config: Configuration) -> None:
    """Process PUB Payments"""
    logger.info("Start - PUB Payments ECS Task")

    transaction_file_creator = TransactionFileCreator(db_session)

    if config.process_checks:
        transaction_file_creator.create_check_file()

    if config.process_prenotes:
        transaction_file_creator.add_prenotes()

    if config.process_ach:
        transaction_file_creator.add_ach_payments()

    if config.send_files:
        transaction_file_creator.send_payment_files()

    logger.info("Done - PUB Payments ECS Task")
