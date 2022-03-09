import argparse
import sys
from typing import List

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.payments import (
    FineosExtractVbiLeavePlanRequestedAbsence,
    FineosExtractVPaidLeaveInstruction,
)
from massgov.pfml.delegated_payments.delegated_fineos_iaww_extract import IAWWExtractStep
from massgov.pfml.delegated_payments.fineos_extract_step import (
    IAWW_EXTRACT_CONFIG,
    FineosExtractStep,
)
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.datetime import get_now_us_eastern

logger = logging.get_logger(__name__)

ALL = "ALL"
CONSUME_FINEOS_IAWW = "consume-fineos-iaww"
IAWW_EXTRACT = "iaww-extract"
ALLOWED_VALUES = [ALL, CONSUME_FINEOS_IAWW, IAWW_EXTRACT]


class Configuration:
    consume_fineoss_iaww: bool
    do_iaww_extract: bool

    def __init__(self, input_args: List[str]) -> None:
        parser = argparse.ArgumentParser(description="Process FINEOS IAWW exports")
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
            self.consume_fineoss_iaww = True
            self.do_iaww_extract = True
        else:
            self.consume_fineoss_iaww = CONSUME_FINEOS_IAWW in steps
            self.do_iaww_extract = IAWW_EXTRACT in steps


def make_db_session() -> db.Session:
    return db.init(sync_lookups=True)


@background_task("fineos-import-iaww")
def main():
    """Entry point for processing IAWW from FINEOS extracts"""
    config = Configuration(sys.argv[1:])

    with db.session_scope(make_db_session(), close=True) as db_session, db.session_scope(
        make_db_session(), close=True
    ) as log_entry_db_session:
        _process_iaww_from_fineos(db_session, log_entry_db_session, config)


def _process_iaww_from_fineos(
    db_session: db.Session, log_entry_db_session: db.Session, config: Configuration
) -> None:
    """Extract IAWW data from FINEOS"""
    logger.info("Start - FINEOS IAWW Extract ECS Task")
    start_time = get_now_us_eastern()

    # We can truncate the old data in the tables before we extract the latest data since both
    # of these files are full extracts
    try:
        db_session.query(FineosExtractVPaidLeaveInstruction).delete()
        db_session.query(FineosExtractVbiLeavePlanRequestedAbsence).delete()
        db_session.commit()
    except Exception as ex:
        logger.warning("Unable to truncate IAWW extract tables", exc_info=ex)
        db_session.rollback()

    if config.consume_fineoss_iaww:
        FineosExtractStep(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            extract_config=IAWW_EXTRACT_CONFIG,
        ).run()

    if config.do_iaww_extract:
        IAWWExtractStep(db_session=db_session, log_entry_db_session=log_entry_db_session).run()

    payments_util.create_success_file(start_time, "fineos-import-iaww")
    logger.info("End - FINEOS IAWW Extract ECS Task")
