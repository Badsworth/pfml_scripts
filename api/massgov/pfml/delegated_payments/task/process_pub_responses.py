import argparse
import sys
from typing import List

import massgov.pfml.db as db
import massgov.pfml.delegated_payments.pub.response_file_handler as response_file_handler
import massgov.pfml.util.logging as logging
import massgov.pfml.util.logging.audit as audit
from massgov.pfml.delegated_payments import delegated_config
from massgov.pfml.delegated_payments.delegated_fineos_pei_writeback import FineosPeiWritebackStep
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_report_step import ReportStep
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_reports import (
    PROCESS_PUB_RESPONSES_REPORTS,
)

logger = logging.get_logger("massgov.pfml.delegated_payments.task.process_pub_responses")


ALL = "ALL"
PICKUP_FILES = "pickup"
PROCESS_RESPONSES = "process"
REPORT = "report"
WRITEBACK = "writeback"
ALLOWED_VALUES = [
    ALL,
    PICKUP_FILES,
    PROCESS_RESPONSES,
    REPORT,
    WRITEBACK,
]


class Configuration:
    pickup_files: bool
    process_responses: bool
    make_reports: bool

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
            self.make_reports = True
            self.send_fineos_writeback = True
        else:
            self.pickup_files = PICKUP_FILES in steps
            self.process_responses = PROCESS_RESPONSES in steps
            self.make_reports = REPORT in steps
            self.send_fineos_writeback = WRITEBACK in steps


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

    s3_config = delegated_config.get_s3_config()

    if config.pickup_files:
        response_file_handler.CopyReturnFilesToS3Step(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.process_responses:
        process_return_files_step = response_file_handler.ProcessReturnFileStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session, s3_config=s3_config,
        )
        while process_return_files_step.have_more_files_to_process():
            process_return_files_step.run()

    if config.send_fineos_writeback:
        FineosPeiWritebackStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.make_reports:
        ReportStep(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            report_names=PROCESS_PUB_RESPONSES_REPORTS,
        ).run()

    logger.info("Done - PUB Responses ECS Task")


if __name__ == "__main__":
    main()
