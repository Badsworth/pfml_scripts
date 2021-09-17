import abc
import csv
import os
import pathlib
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List, Optional, Sequence

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.util.aws.ses import EmailRecipient, send_email

logger = logging.get_logger(__name__)


@dataclass
class AbstractRecord(abc.ABC, metaclass=abc.ABCMeta):
    pass


@dataclass
class EmailConfig:
    """ Represents configuration for sending a report via email. """

    sender: str
    recipient: EmailRecipient  # The EmailRecipient object can contain multiple TO addresses
    subject: str
    body_text: str
    bounce_forwarding_email_address_arn: str


@dataclass
class FileConfig:
    """ Represents configuration for sending a report to a file store (local disk and S3 supported). """

    file_prefix: str


# Report doesn't need to be abstract, it just needs
# configuration based on the type of records in it and
# where to store the outputs (s3/email/etc.). That
# is best served by factories.
class Report:
    """ A class representing a report that is made up of records"""

    report_name: str
    header_record: AbstractRecord

    records: List[AbstractRecord]

    def __init__(self, report_name: str, header_record: AbstractRecord) -> None:
        self.report_name = report_name
        self.header_record = header_record
        self.records = []

    def add_record(self, record: AbstractRecord) -> None:
        self.records.append(record)

    def add_records(self, records: Sequence[AbstractRecord]) -> None:
        # Note that sequence is used for typing workaround (It's a list)
        # See: https://mypy.readthedocs.io/en/latest/common_issues.html#variance
        self.records.extend(records)

    def create_report(self, temp_directory: pathlib.Path, now: datetime) -> pathlib.Path:
        report_file_path = (
            temp_directory / f"{now.strftime('%Y-%m-%d-%H-%M-%S')}-{self.report_name}.csv"
        )
        logger.info("Creating report %s", report_file_path)
        # Note, from the docs:
        # "the value None is written as the empty string" - which is fine for us
        # https://docs.python.org/3/library/csv.html#csv.DictWriter
        with open(report_file_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=list(asdict(self.header_record).keys()), quoting=csv.QUOTE_ALL
            )
            writer.writerow(asdict(self.header_record))  # Add the static header
            for record in self.records:
                writer.writerow(asdict(record))

        return report_file_path


class ReportGroup:
    """ A container class for a group of reports that all go to the
        same location (eg. all emailed together)
    """

    reports: List[Report]

    email_config: Optional[EmailConfig]
    file_config: Optional[FileConfig]

    def __init__(
        self, email_config: Optional[EmailConfig] = None, file_config: Optional[FileConfig] = None
    ) -> None:
        self.email_config = email_config
        self.file_config = file_config
        self.reports = []

    def add_report(self, report: Report) -> None:
        self.reports.append(report)

    def send_reports_by_email(self, report_file_paths: List[pathlib.Path]) -> None:
        if not self.email_config:
            return

        report_names = [report.name for report in report_file_paths]
        logger.info("Emailing reports %s", report_names)

        try:
            send_email(
                recipient=self.email_config.recipient,
                subject=self.email_config.subject,
                body_text=self.email_config.body_text,
                sender=self.email_config.sender,
                bounce_forwarding_email_address_arn=self.email_config.bounce_forwarding_email_address_arn,
                attachments=report_file_paths,
            )
            logger.info("Successfully emailed report %s", report_names)
        except Exception:
            logger.exception("Failed to send email for report %s", report_names)

    def send_reports_to_storage(self, report_file_paths: List[pathlib.Path]) -> List[str]:
        if not self.file_config:
            return []

        output_paths = []

        for report_file_path in report_file_paths:
            output_path = os.path.join(
                self.file_config.file_prefix,
                payments_util.get_now().strftime("%Y-%m-%d"),
                report_file_path.name,
            )
            extra = {"report_file_path": str(report_file_path), "output_path": output_path}
            logger.info(
                "Attempting to save report %s to %s",
                report_file_path.name,
                output_path,
                extra=extra,
            )

            if file_util.is_s3_path(output_path):
                try:
                    file_util.upload_to_s3(str(report_file_path), output_path)
                    logger.info("Successfully uploaded report %s to S3", output_path, extra=extra)
                    output_paths.append(output_path)
                except Exception:
                    logger.exception("Failed to upload report %s to S3", output_path, extra=extra)
            else:
                try:
                    file_util.copy_file(str(report_file_path), output_path)
                    logger.info("Successfully copied report to %s", output_path, extra=extra)
                    output_paths.append(output_path)
                except Exception:
                    logger.exception("Failed to copy report to %s", output_path, extra=extra)

        return output_paths

    def create_and_send_reports(self) -> List[str]:
        report_files = []

        temp_directory = pathlib.Path(tempfile.mkdtemp())
        now = payments_util.get_now()

        for report in self.reports:
            report_file = report.create_report(temp_directory, now)
            report_files.append(report_file)

        self.send_reports_by_email(report_files)
        return self.send_reports_to_storage(report_files)
