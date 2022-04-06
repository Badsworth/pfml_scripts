import datetime
import json
import os
import sys
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

import massgov
import massgov.pfml.util.batch.log
import massgov.pfml.util.files as file_utils
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.csv import CSVSourceWrapper
from massgov.pfml.util.datetime import utcnow
from massgov.pfml.util.logging import log_every

logger = logging.get_logger(__name__)
SUBMISSION_FILE_NAME = "DORDUADFML_SUBMISSION"


@dataclass
class PendingFilingSubmissionReport:
    start: str = utcnow().isoformat()
    total_employers_received_count: int = 0
    total_employers_written_count: int = 0
    end: Optional[str] = None
    process_duration_in_seconds: float = 0


@background_task("dor_create_pending_filing_submission")
def handler():
    """ECS handler function."""
    handler_with_return()
    return 0


def make_db_session():
    return db.init(sync_lookups=True)


def handler_with_return():
    """ECS handler function."""
    logger.info("Starting to create pending filing submission file.")

    db_session_raw = make_db_session()

    try:
        with massgov.pfml.util.batch.log.log_entry(
            db_session_raw, "", "DOR Pending Filing Submission", ""
        ) as log_entry:
            report = process_pending_filing_employers()
            log_entry.report = json.dumps(asdict(report), indent=2)
    except Exception:
        logger.exception("Error creating pending filing submission file.")
        sys.exit(1)

    logger.info(
        "Finished creating pending filing submission file.", extra={"report": asdict(report)}
    )

    return report


def get_file_to_process() -> Optional[str]:
    folder_path = os.environ["INPUT_FOLDER_PATH"]
    files_for_import = file_utils.list_files(f"{str(folder_path)}/received")

    update_files = []
    for update_file in files_for_import:
        if update_file.startswith("CompaniesReturningToStatePlan"):
            update_files.append(update_file)

    if len(update_files) == 0:
        logger.error(f"No list of employers file found in S3 folder {folder_path}.")
        return None

    if len(update_files) > 1:
        logger.error(f"More than one list of employers file found in S3 folder {folder_path}.")
        return None

    file_path = f"{folder_path}/received/{update_files[0]}"
    return file_path


def setup_output_file(start_time):
    folder_path = os.environ["OUTPUT_FOLDER_PATH"]
    output_file_name = f"{SUBMISSION_FILE_NAME}_{start_time.strftime('%Y%m%d%H%M%S')}"
    output_path = "{}/{}/{}".format(folder_path, "send", output_file_name)
    return file_utils.write_file(output_path, "w", use_s3_multipart_upload=False)


def process_pending_filing_employers() -> PendingFilingSubmissionReport:
    start_time = utcnow()
    report = PendingFilingSubmissionReport(start=start_time.isoformat())

    file_path = get_file_to_process()

    if file_path is None:
        end_time = utcnow()
        report.end = end_time.isoformat()
        report.process_duration_in_seconds = (end_time - start_time).total_seconds()
        return report
    else:
        logger.info(
            f"Processing list of employers returning to State plan with filename: {file_path}"
        )

    csv_input = CSVSourceWrapper(file_path)

    output_file = setup_output_file(start_time)

    line_count = 0
    for row in log_every(logger, csv_input, count=10, item_name="CSV row"):
        line_count += 1

        report.total_employers_received_count += 1
        try:
            process_csv_row(row, output_file, report)
        except Exception as e:
            logger.exception(
                f"Unhandled issue processing CSV row in file: {file_path} at "
                f"line {line_count}. Continuing processing. {e.args}"
            )

    output_file.close()
    end_time = utcnow()
    report.end = end_time.isoformat()
    report.process_duration_in_seconds = (end_time - start_time).total_seconds()

    return report


def process_csv_row(
    row: Dict[Any, Any], output_file: Any, report: PendingFilingSubmissionReport
) -> None:
    employer_fein = row.get("FEIN")
    if not employer_fein or employer_fein == "":
        raise ValueError("Employer FEIN missing and is required to process row.")
    if len(employer_fein) != 9:
        raise ValueError("Employer FEIN is invalid. Length is not 9 digits")
    if not employer_fein.isdigit():
        raise ValueError("Employer FEIN is invalid. Contains non-numeric values.")

    first_requested_quarter = row.get("'First Requested Quarter'")
    if not first_requested_quarter or first_requested_quarter == "":
        raise ValueError("First Requested Quarter missing.")
    try:
        requested_quarter_date = datetime.datetime.strptime(first_requested_quarter, "%m/%d/%Y")
    except Exception:
        raise ValueError(
            "First requested quarter date is an invalid date, or is not in the expected format 'MM/DD/YYYY'."
        )
    formatted_requested_quarter = requested_quarter_date.strftime("%Y%m%d")
    write_to_submission_file(employer_fein, formatted_requested_quarter, output_file)

    report.total_employers_written_count += 1


def write_to_submission_file(
    employer_fein: str, first_requested_quarter: str, output_file: Any
) -> None:
    logger.info(f"Received {employer_fein}, {first_requested_quarter}")

    line = "{:10}{:14}{:8}\n".format("FEIN      ", f"{employer_fein}     ", first_requested_quarter)
    output_file.write(line)
    logger.info(f"Wrote line {line}")
