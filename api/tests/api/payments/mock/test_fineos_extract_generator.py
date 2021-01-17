import os
import tempfile
from typing import List

import massgov.pfml.payments.mock.fineos_extract_generator as fineos_extract_generator
import massgov.pfml.util.files as file_util
from massgov.pfml.payments.mock.payments_test_scenario_generator import (
    ScenarioDataConfig,
    ScenarioNameWithCount,
)


def test_generate_to_fs(test_db_session, mock_s3_bucket, initialize_factories_session):
    folder_path = tempfile.mkdtemp().__str__()
    generate_and_validate(test_db_session, folder_path)


def test_generate_to_s3(test_db_session, mock_s3_bucket, initialize_factories_session):
    s3_folder_path = f"s3://{mock_s3_bucket}/test_folder"
    generate_and_validate(test_db_session, s3_folder_path)


def generate_and_validate(db_session, folder_path):
    config = ScenarioDataConfig(scenario_config=fineos_extract_generator.DEFAULT_SCENARIOS_CONFIG)
    fineos_extract_generator.generate(config, folder_path)

    files = file_util.list_files(folder_path)
    assert len(files) == 6

    count = get_total_log_count(fineos_extract_generator.DEFAULT_SCENARIOS_CONFIG)
    for file in files:
        file_content = file_util.read_file(os.path.join(folder_path, file))
        assert file_content.strip()
        assert file_content.count("\n") == count + 1  # account for header column


def get_total_log_count(scenario_config: List[ScenarioNameWithCount]):
    count = 0
    for sc in scenario_config:
        count += sc.count
    return count
