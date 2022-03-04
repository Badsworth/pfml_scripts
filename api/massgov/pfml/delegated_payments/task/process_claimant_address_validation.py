import argparse
import sys
from typing import List

import massgov.pfml.db as db
import massgov.pfml.util.logging as logging
from massgov.pfml.delegated_payments.claimant_address_validation import (
    ClaimantAddressValidationStep,
)
from massgov.pfml.util.bg import background_task

logger = logging.get_logger(__name__)


ALL = "ALL"
VALIDATE_ADDRESSES = "validate-addresses"
# REPORT = "report"
ALLOWED_VALUES = [ALL, VALIDATE_ADDRESSES]


class Configuration:
    validate_addresses: bool

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(description="Validate address for 1099G form generation")
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
            self.validate_addresses = True


def make_db_session() -> db.Session:
    return db.init(sync_lookups=True)


@background_task("pub-claimant-address-validation")
def main():
    """Entry point for Address Validation Processing"""
    config = Configuration(sys.argv[1:])

    with db.session_scope(make_db_session(), close=True) as db_session, db.session_scope(
        make_db_session(), close=True
    ) as log_entry_db_session:
        _process_address_validations(db_session, log_entry_db_session, config)


def _process_address_validations(
    db_session: db.Session, log_entry_db_session: db.Session, config: Configuration
) -> None:
    """Process Address Validations"""
    logger.info("Start - Address Validation ECS Task")

    if config.validate_addresses:
        ClaimantAddressValidationStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    logger.info("Done - Claimant Address Validations ECS Task")
