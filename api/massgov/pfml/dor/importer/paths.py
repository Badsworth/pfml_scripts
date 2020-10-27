#
# DOR Importer - functions related to S3 or file paths and names.
#

import re
from dataclasses import dataclass
from typing import Dict, List

import massgov.pfml.util.files
import massgov.pfml.util.logging

EMPLOYER_FILE_PREFIX = "DORDFMLEMP_"
EMPLOYEE_FILE_PREFIX = "DORDFML_"


logger = massgov.pfml.util.logging.get_logger(__name__)


@dataclass
class ImportBatch:
    upload_date: str
    employer_file: str
    employee_file: str


def get_files_to_process(path: str) -> List[ImportBatch]:
    files_by_date = get_files_for_import_grouped_by_date(path)
    file_date_keys = sorted(files_by_date.keys())

    import_batches: List[ImportBatch] = []

    for file_date_key in file_date_keys:
        files = files_by_date[file_date_key]

        if EMPLOYER_FILE_PREFIX not in files or EMPLOYEE_FILE_PREFIX not in files:
            logger.warning("incomplete files for %s: %s", file_date_key, files)
            continue

        import_batches.append(
            ImportBatch(
                upload_date=file_date_key,
                employer_file=files[EMPLOYER_FILE_PREFIX],
                employee_file=files[EMPLOYEE_FILE_PREFIX],
            )
        )

    return import_batches


def get_files_for_import_grouped_by_date(path: str,) -> Dict[str, Dict[str, str]]:
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
