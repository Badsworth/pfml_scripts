import argparse
import sys
from typing import List

import massgov.pfml.db as db
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.delegated_payments.delegated_fineos_pei_writeback import FineosPeiWritebackStep
from massgov.pfml.delegated_payments.pickup_response_files_step import PickupResponseFilesStep
from massgov.pfml.delegated_payments.pub.process_check_return_step import ProcessCheckReturnFileStep
from massgov.pfml.delegated_payments.pub.process_files_in_path_step import ProcessFilesInPathStep
from massgov.pfml.delegated_payments.pub.process_manual_pub_rejection_step import (
    ProcessManualPubRejectionStep,
)
from massgov.pfml.delegated_payments.pub.process_nacha_return_step import ProcessNachaReturnFileStep
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_report_step import ReportStep
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_reports import (
    PROCESS_PUB_RESPONSES_REPORTS,
)
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.datetime import get_now_us_eastern

logger = logging.get_logger("massgov.pfml.delegated_payments.task.process_pub_responses")

# The maximum number of files we'll attempt to process for each PUB file type
# This exists in case we are endlessly processing files, and failing to move them
MAX_FILE_COUNT = 25

ALL = "ALL"
PICKUP_FILES = "pickup"
PROCESS_NACHA_RESPONSES = "process-nacha"
PROCESS_CHECK_RESPONSES = "process-checks"
PROCESS_MANUAL_REJECTS = "process-manual-rejects"
WRITEBACK = "writeback"
REPORT = "report"
ALLOWED_VALUES = [
    ALL,
    PICKUP_FILES,
    PROCESS_NACHA_RESPONSES,
    PROCESS_CHECK_RESPONSES,
    PROCESS_MANUAL_REJECTS,
    WRITEBACK,
    REPORT,
]


class Configuration:
    pickup_files: bool
    process_nacha_responses: bool
    process_check_responses: bool
    process_manual_rejects: bool
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
            self.process_manual_rejects = True
            self.send_fineos_writeback = True
            self.make_reports = True
        else:
            self.pickup_files = PICKUP_FILES in steps
            self.process_nacha_responses = PROCESS_NACHA_RESPONSES in steps
            self.process_check_responses = PROCESS_CHECK_RESPONSES in steps
            self.process_manual_rejects = PROCESS_MANUAL_REJECTS in steps
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
        _check_for_files_not_recieved(db_session)
        _process_pub_responses(db_session, log_entry_db_session, config)


def _process_pub_responses(
    db_session: db.Session, log_entry_db_session: db.Session, config: Configuration
) -> None:
    """Process PUB Responses"""
    logger.info("Start - PUB Responses ECS Task")
    start_time = get_now_us_eastern()

    if config.pickup_files:
        PickupResponseFilesStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.process_nacha_responses:
        process_nacha_return_files_step = ProcessNachaReturnFileStep(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            should_add_to_report_queue=True,
        )
        run_repeated_step(process_nacha_return_files_step)

    if config.process_check_responses:
        process_check_return_file_step = ProcessCheckReturnFileStep(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            should_add_to_report_queue=True,
        )
        run_repeated_step(process_check_return_file_step)

    if config.process_manual_rejects:
        process_manual_pub_reject_step = ProcessManualPubRejectionStep(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            should_add_to_report_queue=True,
        )
        run_repeated_step(process_manual_pub_reject_step)

    if config.send_fineos_writeback:
        FineosPeiWritebackStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.make_reports:
        ReportStep(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            report_names=PROCESS_PUB_RESPONSES_REPORTS,
            sources_to_clear_from_report_queue=[
                ProcessCheckReturnFileStep,
                ProcessNachaReturnFileStep,
                ProcessManualPubRejectionStep,
            ],
        ).run()

    payments_util.create_success_file(start_time, "pub-payments-process-pub-returns")
    logger.info("Done - PUB Responses ECS Task")


def _check_for_files_not_recieved(db_session: db.Session) -> None:
    ProcessNachaReturnFileStep.check_if_processed_within_x_days(
        db_session=db_session,
        metric=ProcessNachaReturnFileStep.Metrics.PROCESSED_ACH_FILE,
        business_days=3,
    )

    ProcessCheckReturnFileStep.check_if_processed_within_x_days(
        db_session=db_session,
        metric=ProcessCheckReturnFileStep.Metrics.PROCESSED_CHECKS_PAID_FILE,
        business_days=3,
    )

    ProcessCheckReturnFileStep.check_if_processed_within_x_days(
        db_session=db_session,
        metric=ProcessCheckReturnFileStep.Metrics.PROCESSED_CHECKS_OUTSTANDING_FILE,
        business_days=3,
    )


def run_repeated_step(step: ProcessFilesInPathStep) -> None:
    iteration_count = 0
    while step.have_more_files_to_process():
        step.run()
        iteration_count += 1
        if iteration_count > MAX_FILE_COUNT:
            raise Exception(
                "Found more than 25 files in %s directory, this may indicate that the process was failing to move the files"
                % step.received_path
            )


if __name__ == "__main__":
    main()
