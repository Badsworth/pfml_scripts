import csv
import io
import pathlib
import zipfile
from typing import Dict, List

import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util

expected_file_names = [
    "vpei.csv.zip",
    "vpeipaymentdetails.csv.zip",
    "vpeiclaimdetails.csv.zip",
    "LeavePlan_info.csv.zip",
    "VBI_PERSON_SOM_ALL.csv.zip",
]


def copy_fineos_data_to_archival_bucket() -> Dict[str, str]:
    s3_config = payments_util.get_s3_config()
    return file_util.copy_s3_files(
        s3_config.fineos_data_export_path, s3_config.pfml_fineos_inbound_path, expected_file_names
    )


def download_and_parse_data(s3_path: str, download_directory: pathlib.Path) -> List[Dict[str, str]]:
    file_name = s3_path.split("/")[-1]
    download_location = download_directory / file_name
    file_util.download_from_s3(s3_path, str(download_location))

    extract_data = []

    with zipfile.ZipFile(download_location) as zipf:
        # Open the file within the ZIP file (named the same, without .zip)
        with zipf.open(file_name[:-4]) as extract_file:
            # Need to wrap the file to convert it from bytes to string
            text_wrapper = io.TextIOWrapper(extract_file, encoding="UTF-8")
            dict_reader = csv.DictReader(text_wrapper, delimiter=",")
            # Each data object represents a row from the CSV as a dictionary
            # The keys are column headers
            # The rows are the corresponding value in the row
            extract_data = list(dict_reader)

    return extract_data
