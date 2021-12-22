import argparse
import sys
from typing import List

import massgov.pfml.db as db
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.delegated_payments.convert_mmars_data_step import ConvertMmarsDataStep
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.datetime import get_now_us_eastern

logger = logging.get_logger(__name__)

ALL = "ALL"
PROCESS_MMARS_PAYMENTS = "process-mmars-payments"
ALLOWED_VALUES = [ALL, PROCESS_MMARS_PAYMENTS]


class Configuration:
    process_mmars_payments: bool

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(
            description="Process MMARS payments and convert into a payment records"
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
            self.process_mmars_payments = True
        else:
            self.process_mmars_payments = PROCESS_MMARS_PAYMENTS in steps


def make_db_session() -> db.Session:
    return db.init(sync_lookups=True)


@background_task("pub-payments-process-mmars-payments")
def main():
    """Entry point for processing MMARS payments"""
    config = Configuration(sys.argv[1:])

    with db.session_scope(make_db_session(), close=True) as db_session, db.session_scope(
        make_db_session(), close=True
    ) as log_entry_db_session:
        _process_mmars_payments(db_session, log_entry_db_session, config)


def _process_mmars_payments(
    db_session: db.Session, log_entry_db_session: db.Session, config: Configuration
) -> None:
    """Process MMARS Payments"""
    logger.info("Start - Process MMARS payments")
    start_time = get_now_us_eastern()

    if config.process_mmars_payments:
        ConvertMmarsDataStep(db_session=db_session, log_entry_db_session=log_entry_db_session).run()

    payments_util.create_success_file(start_time, "pub-payments-process-mmars-payments")
    logger.info("End - Process MMARS payments")
