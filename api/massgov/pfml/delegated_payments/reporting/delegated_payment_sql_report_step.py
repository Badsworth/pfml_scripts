import os
import pathlib
import tempfile
from typing import Iterable, List, Optional

import massgov.pfml.db as db
import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.execute_sql import execute_sql_statement_file_path
from massgov.pfml.db.models.employees import ReferenceFile, ReferenceFileType
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_reports import (
    Report,
    ReportName,
    get_report_by_name,
)
from massgov.pfml.delegated_payments.step import Step

logger = logging.get_logger(__name__)


class ReportStep(Step):
    report_names: Iterable[ReportName]

    def __init__(
        self,
        db_session: db.Session,
        log_entry_db_session: db.Session,
        report_names: Iterable[ReportName],
    ) -> None:
        super().__init__(db_session=db_session, log_entry_db_session=log_entry_db_session)
        self.report_names = report_names

    def run_step(self) -> None:
        report_names_str = ", ".join([r.value for r in self.report_names])
        expected_reports_count = len(list(self.report_names))

        try:
            logger.info("Start generating %i reports: %s", expected_reports_count, report_names_str)

            s3_config = payments_config.get_s3_config()
            outbound_path = s3_config.pfml_error_reports_path
            archive_path = s3_config.pfml_error_reports_archive_path

            generated_reports: List[str] = []

            for report_name in self.report_names:
                report: Optional[Report] = get_report_by_name(report_name)

                if report is None:
                    self.increment("report_error_count")
                    logger.error("Could not find configuration for report: %s", report_name.value)
                    continue

                try:
                    self.generate_report(
                        outbound_path,
                        archive_path,
                        report.folder_name.value,
                        report.report_name.value,
                        report.sql_command,
                    )
                    generated_reports.append(report.report_name.value)
                    self.increment("report_generated_count")
                except Exception:
                    self.increment("report_error_count")
                    logger.exception("Error generating report: %s", report_name.value)
                    self.db_session.rollback()

            logger.info("Done generating %i reports: %s", len(generated_reports), generated_reports)

            if expected_reports_count != len(generated_reports):
                raise Exception(
                    f"Expected reports do not match generated reports - expected: {expected_reports_count}, generated: {len(generated_reports)}"
                )

        except Exception:
            logger.exception("Error generating reports: %s", report_names_str)

            # We do not want to run any subsequent steps if this fails
            raise

    def generate_report(
        self,
        outbound_path: str,
        archive_path: str,
        folder_name: str,
        report_name: str,
        sql_command: str,
    ) -> None:
        logger.info("Generating report: %s", report_name)

        now = payments_util.get_now()
        date_folder = now.strftime("%Y-%m-%d")
        timestamp_prefix = now.strftime("%Y-%m-%d-%H-%M-%S")
        file_name = f"{timestamp_prefix}-{report_name}.csv"

        temp_directory = pathlib.Path(tempfile.mkdtemp())
        report_file_path = os.path.join(str(temp_directory), file_name)

        execute_sql_statement_file_path(self.db_session, sql_command, report_file_path)

        file_path = os.path.join(outbound_path, folder_name, file_name)
        archive_file_path = os.path.join(archive_path, folder_name, date_folder, file_name)

        if file_util.is_s3_path(file_path):
            file_util.upload_to_s3(report_file_path, file_path)
        else:
            file_util.copy_file(report_file_path, file_path)

        if file_util.is_s3_path(archive_file_path):
            file_util.upload_to_s3(report_file_path, archive_file_path)
        else:
            file_util.copy_file(report_file_path, archive_file_path)

        # create a reference file for the archive report file
        reference_file = ReferenceFile(
            file_location=str(archive_file_path),
            reference_file_type_id=ReferenceFileType.DELEGATED_PAYMENT_REPORT_FILE.reference_file_type_id,
        )
        self.db_session.add(reference_file)

        logger.info(
            "Done generating report: %s, path: %s, archive path: %s",
            report_name,
            file_path,
            archive_file_path,
        )
