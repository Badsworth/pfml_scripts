import os
import tempfile

import massgov.pfml.payments.mock.fineos_extract_generator as fineos_extract_generator
import massgov.pfml.util.files as file_util
from massgov.pfml.payments.mock.payments_test_scenario_generator import (
    SCENARIO_DESCRIPTORS,
    ScenarioDataConfig,
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
    assert len(files) == len(list(fineos_extract_generator.FINEOS_EXPORT_FILES.keys()))

    for filename in files:
        if filename.endswith(fineos_extract_generator.LEAVE_PLAN_FILE_NAME):
            continue  # this file is no longer used

        count = get_total_log_count(filename)
        file_content = file_util.read_file(os.path.join(folder_path, filename))
        assert file_content.strip()
        assert file_content.count("\n") == count + 1  # account for header row


def get_total_log_count(filename: str):
    # Scenarios that have the missing_from_employee_feed attribute will be missing from the
    # employee feed FINEOS extract.
    data_lines_in_employee_feed = 0
    for scenario_descriptor in SCENARIO_DESCRIPTORS.values():
        if not scenario_descriptor.missing_from_employee_feed:
            data_lines_in_employee_feed = data_lines_in_employee_feed + 1

    # Scenarios will only be included in the payment extract files if they have the
    # has_payment_extract attribute.
    data_lines_in_payment_extract = 0
    for scenario_descriptor in SCENARIO_DESCRIPTORS.values():
        if scenario_descriptor.has_payment_extract:
            data_lines_in_payment_extract = data_lines_in_payment_extract + 1

    row_count_for_file = {
        fineos_extract_generator.EMPLOYEE_FEED_FILE_NAME: data_lines_in_employee_feed,
        fineos_extract_generator.PEI_FILE_NAME: data_lines_in_payment_extract,
        fineos_extract_generator.PEI_CLAIM_DETAILS_FILE_NAME: data_lines_in_payment_extract,
        fineos_extract_generator.PEI_PAYMENT_DETAILS_FILE_NAME: data_lines_in_payment_extract,
    }

    for filename_ending, count in row_count_for_file.items():
        if filename.endswith(filename_ending):
            return count

    # If we have not defined any special case for this filename then we assume that all scenarios
    # should be included in the extract file.
    all_scenario_count = 0
    for sc in fineos_extract_generator.DEFAULT_SCENARIOS_CONFIG:
        all_scenario_count += sc.count

    return all_scenario_count
