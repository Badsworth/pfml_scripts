#
# DOR Importer - functions related to S3 or file paths and names.
#

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Tuple

import massgov.pfml.util.files
import massgov.pfml.util.logging

EMPLOYER_FILE_PREFIX = "DORDFMLEMP_"
EMPLOYEE_FILE_PREFIX = "DORDFML_"
PENDING_FILING_FILE_PREFIX = "DORDUADFML_SUBMISSION"
EXEMPT_EMPLOYER_FILE_PREFIX = "DORDUADFML"


logger = massgov.pfml.util.logging.get_logger(__name__)


@dataclass
class ImportBatch:
    upload_date: str
    employer_file: str
    employee_file: str


def get_pending_filing_files_to_process(path: str) -> List[str]:
    return get_files_to_process_by_regex(path, PENDING_FILING_FILE_PREFIX)


def get_exempt_employer_files_to_process(path: str) -> List[str]:
    return get_files_to_process_by_regex(path, EXEMPT_EMPLOYER_FILE_PREFIX)


def get_files_to_process_by_regex(path: str, prefix: str) -> List[str]:
    import_files: List[str] = []

    files_for_import = massgov.pfml.util.files.list_files(str(path))
    files_for_import.sort()

    for filename in files_for_import:
        match = re.match(r"({prefix}.*_)(\d+)".format(prefix=prefix), filename)

        if match is not None:
            if path.endswith("/"):
                import_files.append("{}{}".format(path, filename))
            else:
                import_files.append("{}/{}".format(path, filename))

    return import_files


def get_exemption_file_to_process(path: str) -> str:
    files_for_import = massgov.pfml.util.files.list_files(str(path))
    files_for_import.sort()

    for filename in files_for_import:
        match = re.match(r"CompaniesReturningToStatePlan.*.csv", filename)

        if match is not None:
            return "{}{}".format(path, filename)

    raise ValueError("Exemption file not found")


def get_files_to_process(path: str) -> List[ImportBatch]:
    employer_files, employee_files = get_files_for_import(path)
    import_batches: List[ImportBatch] = []

    for employer_file in employer_files:
        match = re.match(r"(DORDFML.*_)(\d+)", employer_file)

        if match is not None:
            file_date = match[2]

            import_batches.append(
                ImportBatch(
                    upload_date=file_date,
                    employer_file="{}/{}".format(path, employer_file),
                    employee_file="",
                )
            )

    for employee_file in employee_files:
        match = re.match(r"(DORDFML.*_)(\d+)", employee_file)

        if match is not None:
            file_date = match[2]

            import_batches.append(
                ImportBatch(
                    upload_date=file_date,
                    employer_file="",
                    employee_file="{}/{}".format(path, employee_file),
                )
            )

    return import_batches


def get_files_for_import(path: str) -> Tuple[Iterator[Any], Iterator[Any]]:
    files_for_import = massgov.pfml.util.files.list_files(str(path))
    files_for_import.sort()

    def employer_filter(filename: str) -> bool:
        match = re.match(r"(DORDFML.*_)(\d+)", filename)

        if not match:
            return False

        prefix = match[1]
        return prefix == EMPLOYER_FILE_PREFIX

    def employee_filter(filename: str) -> bool:
        match = re.match(r"(DORDFML.*_)(\d+)", filename)

        if not match:
            return False

        prefix = match[1]
        return prefix == EMPLOYEE_FILE_PREFIX

    employer_files = filter(employer_filter, files_for_import)
    employee_files = filter(employee_filter, files_for_import)

    return employer_files, employee_files


def get_files_for_import_grouped_by_date(path: str) -> Dict[str, Dict[str, str]]:
    """Get the paths (s3 keys) of files in the received folder of the bucket"""

    files_by_date: Dict[str, Dict[str, str]] = {}
    files_for_import = massgov.pfml.util.files.list_files(str(path))
    files_for_import.sort()
    for file_key in files_for_import:
        match = re.match(r"(DORDFML.*_)(\d+)", file_key)
        if not match:
            logger.warning("file %s does not match expected format - skipping", file_key)
            continue

        prefix = match[1]
        file_date = match[2]

        if prefix not in (EMPLOYER_FILE_PREFIX, EMPLOYEE_FILE_PREFIX):
            logger.warning("file %s does not have a known prefix - skipping", file_key)
            continue

        if file_date not in files_by_date:
            files_by_date[file_date] = {}
        files_by_date[file_date][prefix] = f"{path}/{file_key}"

    return files_by_date
