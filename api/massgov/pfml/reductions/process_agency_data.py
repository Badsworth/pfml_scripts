import argparse
import sys
from typing import List, Optional

import massgov.pfml.db as db
import massgov.pfml.reductions.dia as dia
import massgov.pfml.reductions.dua as dua
import massgov.pfml.reductions.reports.dia_payments.create as dia_payments_reports_create
import massgov.pfml.reductions.reports.dia_payments.send as dia_payments_reports_send
import massgov.pfml.reductions.reports.dua_payments_reports as dua_reports
import massgov.pfml.util.logging as logging
from massgov.pfml.reductions.common import AgencyLoadResult
from massgov.pfml.util.batch.log import LogEntry
from massgov.pfml.util.bg import background_task

logger = logging.get_logger(__name__)

ALL = "ALL"
DIA_DOWNLOAD = "dia-download-and-import-data"
DIA_REPORT_GENERATE = "dia-report-generate-and-send"
DIA_DOWNLOAD_AND_REPORT_GENERATE = "dia-download-and-report-generate-and-send"
DUA_DOWNLOAD = "dua-download-and-import-data"
DUA_REPORT_GENERATE = "dua-report-generate-and-send"
DUA_DOWNLOAD_AND_REPORT_GENERATE = "dua-download-and-report-generate-and-send"
ALLOWED_VALUES = [
    ALL,
    DIA_DOWNLOAD,
    DIA_REPORT_GENERATE,
    DIA_DOWNLOAD_AND_REPORT_GENERATE,
    DUA_DOWNLOAD,
    DUA_REPORT_GENERATE,
    DUA_DOWNLOAD_AND_REPORT_GENERATE,
]


class Configuration:
    dia_download_import: bool
    dia_generate_report: bool
    dia_download_import_and_generate_report: bool

    dua_download_import: bool
    dua_generate_report: bool
    dua_download_import_and_generate_report: bool

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(
            description="Retrieve and process payment files from agencies and/or generate report files for agencies"
        )
        parser.add_argument(
            "--steps",
            nargs="+",
            choices=ALLOWED_VALUES,
            default=[ALL],
            help="Indicate which steps to run",
        )

        args = parser.parse_args(input_args)
        steps = set(args.steps)

        if ALL in steps:
            self.dia_download_import = False
            self.dia_generate_report = False
            self.dia_download_import_and_generate_report = True

            self.dua_download_import = False
            self.dua_generate_report = False
            self.dua_download_import_and_generate_report = True
        else:
            self.dia_download_import = DIA_DOWNLOAD in steps
            self.dia_generate_report = DIA_REPORT_GENERATE in steps
            self.dia_download_import_and_generate_report = DIA_DOWNLOAD_AND_REPORT_GENERATE in steps

            self.dua_download_import = DUA_DOWNLOAD in steps
            self.dua_generate_report = DUA_REPORT_GENERATE in steps
            self.dua_download_import_and_generate_report = DUA_DOWNLOAD_AND_REPORT_GENERATE in steps


@background_task("reductions-process-agency-data")
def main():
    config = Configuration(sys.argv[1:])

    dia_load_results: Optional[AgencyLoadResult] = None
    dua_load_results: Optional[AgencyLoadResult] = None

    with db.session_scope(db.init(), close=True) as db_session:
        if config.dia_download_import or config.dia_download_import_and_generate_report:
            logger.info("Running DIA steps to check for and load payments")
            with LogEntry(db_session, "DIA retrieve_payment_lists_from_agencies") as log_entry:
                dia.download_payment_list_from_moveit(db_session, log_entry)
                dia_load_results = dia.load_new_dia_payments(db_session, log_entry)

        if config.dia_generate_report or (
            config.dia_download_import_and_generate_report
            and dia_load_results
            and dia_load_results.found_pending_files
        ):
            logger.info("Running DIA steps to generate report")
            with LogEntry(db_session, "DIA send_wage_replacement_payments_to_dfml") as log_entry:
                dia_payments_reports_create.create_report_new_dia_payments_to_dfml(
                    db_session, log_entry
                )
                dia_payments_reports_send.send_dia_reductions_report(db_session)

        if config.dua_download_import or config.dua_download_import_and_generate_report:
            logger.info("Running DUA steps to check for and load payments")
            with LogEntry(db_session, "DUA retrieve_payment_lists_from_agencies") as log_entry:
                dua.download_payment_list_from_moveit(db_session, log_entry)
                dua_load_results = dua.load_new_dua_payments(db_session, log_entry)

        if config.dua_generate_report or (
            dua_load_results is not None
            and config.dua_download_import_and_generate_report
            and dua_load_results.found_pending_files
        ):
            logger.info("Running DUA steps to generate report")
            with LogEntry(db_session, "DUA send_wage_replacement_payments_to_dfml") as log_entry:
                dua.create_report_new_dua_payments_to_dfml(db_session, log_entry)
                dua_reports.send_dua_reductions_report(db_session)
