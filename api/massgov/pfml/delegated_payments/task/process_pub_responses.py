import argparse
import sys
from typing import List

import massgov.pfml.db as db
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.delegated_payments.delegated_fineos_pei_writeback import FineosPeiWritebackStep
from massgov.pfml.delegated_payments.pickup_response_files_step import PickupResponseFilesStep
from massgov.pfml.delegated_payments.pub.process_check_return_step import ProcessCheckReturnFileStep
from massgov.pfml.delegated_payments.pub.process_nacha_return_step import ProcessNachaReturnFileStep
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_report_step import ReportStep
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_reports import (
    PROCESS_PUB_RESPONSES_REPORTS,
)
from massgov.pfml.util.bg import background_task

logger = logging.get_logger("massgov.pfml.delegated_payments.task.process_pub_responses")

# The maximum number of files we'll attempt to process for each PUB file type
# This exists in case we are endlessly processing files, and failing to move them
MAX_FILE_COUNT = 25

ALL = "ALL"
PICKUP_FILES = "pickup"
PROCESS_NACHA_RESPONSES = "process-nacha"
PROCESS_CHECK_RESPONSES = "process-checks"
WRITEBACK = "writeback"
REPORT = "report"
ALLOWED_VALUES = [
    ALL,
    PICKUP_FILES,
    PROCESS_NACHA_RESPONSES,
    PROCESS_CHECK_RESPONSES,
    WRITEBACK,
    REPORT,
]


class Configuration:
    pickup_files: bool
    process_nacha_responses: bool
    process_check_responses: bool
    send_fineos_writeback: bool
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
            self.process_nacha_responses = True
            self.process_check_responses = True
            self.send_fineos_writeback = True
            self.make_reports = True
        else:
            self.pickup_files = PICKUP_FILES in steps
            self.process_nacha_responses = PROCESS_NACHA_RESPONSES in steps
            self.process_check_responses = PROCESS_CHECK_RESPONSES in steps
            self.send_fineos_writeback = WRITEBACK in steps
            self.make_reports = REPORT in steps


def make_db_session() -> db.Session:
    return db.init(sync_lookups=True)


@background_task("pub-payments-process-pub-returns")
def main():
    """Entry point for PUB Response Processing"""
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
    start_time = payments_util.get_now()

    if config.pickup_files:
        PickupResponseFilesStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.process_nacha_responses:
        process_nacha_return_files_step = ProcessNachaReturnFileStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session,
        )
        iteration_count = 0
        while process_nacha_return_files_step.have_more_files_to_process():
            process_nacha_return_files_step.run()
            iteration_count += 1
            if iteration_count > MAX_FILE_COUNT:
                raise Exception(
                    "Found more than 25 files in %s directory, this may indicate that the process was failing to move the files"
                    % process_nacha_return_files_step.received_path
                )

    if config.process_check_responses:
        process_check_return_file_step = ProcessCheckReturnFileStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session,
        )
        iteration_count = 0
        while process_check_return_file_step.have_more_files_to_process():
            process_check_return_file_step.run()
            iteration_count += 1
            if iteration_count > MAX_FILE_COUNT:
                raise Exception(
                    "Found more than 25 files in %s directory, this may indicate that the process was failing to move the files"
                    % process_check_return_file_step.received_path
                )

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

    payments_util.create_success_file(start_time, "pub-payments-process-pub-returns")
    logger.info("Done - PUB Responses ECS Task")


if __name__ == "__main__":
    main()
