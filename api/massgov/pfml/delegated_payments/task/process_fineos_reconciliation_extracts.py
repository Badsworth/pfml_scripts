import argparse
import sys
from typing import List

import massgov.pfml.db as db
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.delegated_payments.fineos_extract_step import (
    PAYMENT_RECONCILIATION_EXTRACT_CONFIG,
    FineosExtractStep,
)
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_report_step import ReportStep
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_reports import (
    PROCESS_FINEOS_RECONCILIATION_REPORTS,
)
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.datetime import get_now_us_eastern

logger = logging.get_logger(__name__)


ALL = "ALL"
EXTRACT = "extract"
REPORT = "report"
ALLOWED_VALUES = [ALL, EXTRACT, REPORT]


class Configuration:
    do_extract: bool
    make_reports: bool

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(
            description="Process FINEOS monthly payment and create a reconciliation report"
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
            self.do_extract = True
            self.make_reports = True
        else:
            self.do_extract = EXTRACT in steps
            self.make_reports = REPORT in steps


def make_db_session() -> db.Session:
    return db.init(sync_lookups=True)


@background_task("pub-payments-process-snapshot")
def main():
    """Entry point for PUB Payment Processing"""
    config = Configuration(sys.argv[1:])

    with db.session_scope(make_db_session(), close=True) as db_session, db.session_scope(
        make_db_session(), close=True
    ) as log_entry_db_session:
        _process_fineos_payment_reconciliation_extracts(db_session, log_entry_db_session, config)


def _process_fineos_payment_reconciliation_extracts(
    db_session: db.Session, log_entry_db_session: db.Session, config: Configuration
) -> None:
    """Process FINEOS Reconciliation Report Extracts"""
    logger.info("Start - FINEOS Reconciliation Report Extracts ECS Task")
    start_time = get_now_us_eastern()

    if config.do_extract:
        FineosExtractStep(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            extract_config=PAYMENT_RECONCILIATION_EXTRACT_CONFIG,
        ).run()

    if config.make_reports:
        ReportStep(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            report_names=PROCESS_FINEOS_RECONCILIATION_REPORTS,
        ).run()

    payments_util.create_success_file(start_time, "pub-payments-process-snapshot")
    logger.info("End - FINEOS Reconciliation Report Extracts ECS Task")
