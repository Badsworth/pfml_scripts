import os
import tempfile
from typing import List

import pytest

import massgov.pfml.payments.mock.fineos_extract_generator as fineos_extract_generator
import massgov.pfml.util.files as file_util
from massgov.pfml.payments.mock.fineos_extract_generator import (
    EMPLOYEE_FEED_FILE_NAME,
    LEAVE_PLAN_FILE_NAME,
    PEI_CLAIM_DETAILS_FILE_NAME,
    PEI_FILE_NAME,
    PEI_PAYMENT_DETAILS_FILE_NAME,
    REQUESTED_ABSENCES_FILE_NAME,
)
from massgov.pfml.payments.mock.payments_test_scenario_generator import (
    EmployeePaymentScenarioDescriptor,
    ScenarioData,
    ScenarioDataConfig,
)

# every test in here requires real resources
pytestmark = pytest.mark.integration


def test_generate_to_fs(test_db_session, mock_s3_bucket, initialize_factories_session):
    folder_path = tempfile.mkdtemp().__str__()
    generate_and_validate(test_db_session, folder_path)


def test_generate_to_s3(test_db_session, mock_s3_bucket, initialize_factories_session):
    s3_folder_path = f"s3://{mock_s3_bucket}/test_folder"
    generate_and_validate(test_db_session, s3_folder_path)


def generate_and_validate(db_session, folder_path):
    config = ScenarioDataConfig(scenario_config=fineos_extract_generator.DEFAULT_SCENARIOS_CONFIG)
    scenario_dataset: List[ScenarioData] = fineos_extract_generator.generate(config, folder_path)

    files = file_util.list_files(folder_path)
    assert len(files) == 6

    line_counts = {}
    line_counts[REQUESTED_ABSENCES_FILE_NAME] = 0
    line_counts[EMPLOYEE_FEED_FILE_NAME] = 0
    line_counts[LEAVE_PLAN_FILE_NAME] = 0  # this file is no longer used, TODO remove
    line_counts[PEI_FILE_NAME] = 0
    line_counts[PEI_PAYMENT_DETAILS_FILE_NAME] = 0
    line_counts[PEI_CLAIM_DETAILS_FILE_NAME] = 0

    # build the expected count map
    for scenario_data in scenario_dataset:
        scenario_descriptor: EmployeePaymentScenarioDescriptor = scenario_data.scenario_descriptor

        line_counts[REQUESTED_ABSENCES_FILE_NAME] += scenario_descriptor.absence_claims_count

        if not scenario_descriptor.missing_from_employee_feed:
            line_counts[EMPLOYEE_FEED_FILE_NAME] += 1

        if scenario_descriptor.has_payment_extract:
            line_counts[PEI_FILE_NAME] += scenario_descriptor.absence_claims_count
            line_counts[PEI_PAYMENT_DETAILS_FILE_NAME] += scenario_descriptor.absence_claims_count
            line_counts[PEI_CLAIM_DETAILS_FILE_NAME] += scenario_descriptor.absence_claims_count

    for filename in files:
        for expected_filename, expected_count in line_counts.items():
            if filename.endswith(expected_filename):
                file_content = file_util.read_file(os.path.join(folder_path, filename))
                file_content.strip()
                file_line_count = file_content.count("\n")
                # account for header row
                assert (
                    file_line_count == expected_count + 1
                ), f"Unexpected number of lines in extract file  - file name: {expected_filename}, found: {file_line_count}, expected: {expected_count + 1}"
