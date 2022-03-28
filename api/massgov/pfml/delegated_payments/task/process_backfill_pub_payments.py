import argparse
import sys
from typing import Dict, List

import massgov.pfml.db as db
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import ReferenceFileType
from massgov.pfml.delegated_payments.backfill.backfill_fineos_extract_step import (
    BackfillFineosExtractStep,
)
from massgov.pfml.delegated_payments.backfill.backfill_pay_period_lines_step import (
    BackfillPayPeriodLinesStep,
)
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.datetime import get_now_us_eastern

logger = logging.get_logger(__name__)

RUN_PEI_LINE_ITEM_BACKFILL = "run-pei-line-item-backfill"
RUN_PAY_PERIOD_LINES_BACKFILL = "run-pay-period-lines-backfill"

ALLOWED_VALUES = [RUN_PEI_LINE_ITEM_BACKFILL, RUN_PAY_PERIOD_LINES_BACKFILL]


class Configuration:

    step_config: Dict[str, bool]

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(description="Run a backfill of payment data")
        parser.add_argument(
            "--steps",
            nargs="+",
            choices=ALLOWED_VALUES,
            help="Indicate which steps of the process to run",
        )

        args = parser.parse_args(input_args)
        steps = set(args.steps)

        # Create a mapping from all allowed keys -> False
        step_config = dict.fromkeys(ALLOWED_VALUES, False)

        # For each configured step, turn
        # it on if configured
        for step in steps:
            step_config[step] = True

        self.step_config = step_config

    def is_enabled(self, step_str: str) -> bool:
        return self.step_config.get(step_str, False)


def make_db_session() -> db.Session:
    return db.init(sync_lookups=True)


@background_task("pub-payments-backfill-data")
def main():
    config = Configuration(sys.argv[1:])

    with db.session_scope(make_db_session(), close=True) as db_session, db.session_scope(
        make_db_session(), close=True
    ) as log_entry_db_session:
        _process_backfill_pub_payments(db_session, log_entry_db_session, config)


def _process_backfill_pub_payments(
    db_session: db.Session, log_entry_db_session: db.Session, config: Configuration
) -> None:
    """Process FINEOS Payments Backfill"""
    logger.info("Start - Backfill Payment ECS Task")
    start_time = get_now_us_eastern()

    if config.is_enabled(RUN_PEI_LINE_ITEM_BACKFILL):
        BackfillFineosExtractStep(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            reference_file_type=ReferenceFileType.FINEOS_PAYMENT_EXTRACT,
            fineos_extract=payments_util.FineosExtractConstants.PAYMENT_LINE,
        ).run()

    if config.is_enabled(RUN_PAY_PERIOD_LINES_BACKFILL):
        BackfillPayPeriodLinesStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    payments_util.create_success_file(start_time, "pub-payments-backfill-data")
    logger.info("End - Backfill Payment ECS Task")
