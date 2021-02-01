import os

import massgov.pfml.payments.config as payments_config
import massgov.pfml.payments.mock.fineos_extract_generator as fineos_extract_generator
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import Employee, Employer, Payment, ReferenceFileType
from massgov.pfml.payments.mock.payments_test_scenario_generator import (
    ScenarioDataConfig,
    ScenarioName,
    ScenarioNameWithCount,
)
from massgov.pfml.payments.process_payments import Configuration, _fineos_process

# == E2E Tests ==

test_scenario_config = [
    ScenarioNameWithCount(ScenarioName.SCENARIO_A, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_B, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_C, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_D, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_E, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_F, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_G, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_H, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_I, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_J, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_K, 1),
    ScenarioNameWithCount(ScenarioName.SCENARIO_L, 1),
]


def test_fineos_process(
    test_db_session,
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    initialize_factories_session,
    monkeypatch,
):
    monkeypatch.setenv("FINEOS_VENDOR_MAX_HISTORY_DATE", "2019-12-31")
    monkeypatch.setenv("FINEOS_PAYMENT_MAX_HISTORY_DATE", "2019-12-31")

    # Setup the data
    s3_config = payments_config.get_s3_config()
    fineos_data_export_path = s3_config.fineos_data_export_path

    config = ScenarioDataConfig(scenario_config=test_scenario_config)
    fineos_extract_generator.generate(config, fineos_data_export_path)

    mock_fineos_export_files = file_util.list_files(fineos_data_export_path)
    assert len(mock_fineos_export_files) == 6

    # Run the process
    _fineos_process(test_db_session, Configuration(["--steps", "ALL"]))

    # fetch relevant db models
    employees = test_db_session.query(Employee).all()
    employers = test_db_session.query(Employer).all()
    payments = test_db_session.query(Payment).all()

    # top level assersions
    assert len(employees) == 12
    assert len(employers) == 12
    assert len(payments) == 5  # account for extra claim for scenario A

    date_group_str = payments_util.get_date_group_str_from_path(mock_fineos_export_files[0])
    processed_payment_folder_path = os.path.join(
        payments_config.get_s3_config().pfml_fineos_inbound_path,
        payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
        payments_util.get_date_group_folder_name(date_group_str, ReferenceFileType.PAYMENT_EXTRACT),
    )
    processed_payment_files = file_util.list_files_without_folder(processed_payment_folder_path)
    assert len(processed_payment_files) == 3

    processed_vendor_folder_path = os.path.join(
        payments_config.get_s3_config().pfml_fineos_inbound_path,
        payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
        payments_util.get_date_group_folder_name(
            date_group_str, ReferenceFileType.VENDOR_CLAIM_EXTRACT
        ),
    )
    processed_vendor_files = file_util.list_files_without_folder(processed_vendor_folder_path)
    assert len(processed_vendor_files) == 3
