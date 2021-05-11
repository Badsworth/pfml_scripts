import datetime
import logging  # noqa: B1
import os

import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.config as payments_config
import massgov.pfml.payments.gax as gax
import massgov.pfml.payments.mock.ctr_outbound_file_generator as ctr_outbound_file_generator
import massgov.pfml.payments.mock.fineos_extract_generator as fineos_extract_generator
import massgov.pfml.payments.mock.payments_test_scenario_generator as scenario_generator
import massgov.pfml.payments.moveit as moveit
import massgov.pfml.payments.vcc as vcc
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import State
from massgov.pfml.payments.process_ctr_payments import Configuration, _ctr_process

# every test in here requires real resources
pytestmark = pytest.mark.integration

# # == E2E Tests ==


# def test_ctr_process(
#     test_db_session,
#     mock_fineos_s3_bucket,
#     mock_sftp_client,
#     set_exporter_env_vars,
#     initialize_factories_session,
# ):

#     # TODO setup data and files

#     # Run the process
#     # _ctr_process(test_db_session)

#     # TODO test generated files
#     # TODO test state log


def test_ctr_process_errors(
    test_db_session,
    mock_fineos_s3_bucket,
    mock_ses,
    set_exporter_env_vars,
    monkeypatch,
    initialize_factories_session,
    caplog,
    mocker,
):
    # This tests that if anything errors
    # prior to the GAX/VCC logic, it will
    # skip the GAX/VCC logic, but still make an error report.

    caplog.set_level(logging.INFO)  # noqa: B1

    def generic_erroring_method(db_session):
        raise Exception("It errors")

    # Make the moveit logic error
    monkeypatch.setattr(moveit, "pickup_files_from_moveit", generic_erroring_method)

    # Add spies on the VCC/GAX code
    gax_spy = mocker.spy(gax, "build_gax_files_for_s3")
    vcc_spy = mocker.spy(vcc, "build_vcc_files_for_s3")
    moveit_send_spy = mocker.spy(moveit, "send_files_to_moveit")

    _ctr_process(test_db_session, Configuration(["--steps", "ALL"]))

    log_messages = set(record.msg for record in caplog.records)

    # Make sure it errored properly
    assert "One of the setup steps failed - skipping GAX/VCC logic" in log_messages

    # Make sure the VCC/GAX logic was not called
    assert gax_spy.call_count == 0
    assert vcc_spy.call_count == 0
    assert moveit_send_spy.call_count == 0

    # Make sure the error reports were still created
    error_reports = file_util.list_files(
        payments_config.get_s3_config().pfml_error_reports_path, recursive=True
    )
    assert len(error_reports) == 4
    # Going to very quickly check that they're all empty except for a header
    for error_report in error_reports:
        lines = file_util.read_file_lines(
            os.path.join(payments_config.get_s3_config().pfml_error_reports_path, error_report)
        )
        assert len(list(lines)) == 1  # Just a header


def test_ctr_process_outbound_vendor_return(
    initialize_factories_session, mock_s3_bucket, set_exporter_env_vars, test_db_session, tmp_path
):
    scenario_list = [
        scenario_generator.ScenarioNameWithCount(scenario_generator.ScenarioName.SCENARIO_A, 1),
        scenario_generator.ScenarioNameWithCount(scenario_generator.ScenarioName.SCENARIO_B, 1),
    ]
    scenario_config = scenario_generator.ScenarioDataConfig(
        scenario_list, ssn_id_base=526000029, fein_id_base=626000029
    )
    scenario_data_list = fineos_extract_generator.generate(scenario_config, tmp_path)

    for scenario_data in scenario_data_list:
        state_log_util.create_finished_state_log(
            end_state=State.VCC_SENT,
            associated_model=scenario_data.employee,
            outcome="Initial state",
            db_session=test_db_session,
        )

        # Assert ctr_address_pair exists, but only the FINEOS half.
        assert scenario_data.employee.ctr_address_pair is not None
        assert scenario_data.employee.ctr_address_pair.fineos_address is not None
        assert scenario_data.employee.ctr_address_pair.ctr_address is None

    ctr_outbound_file_generator.generate_outbound_vendor_return(
        scenario_data_list,
        f"s3://{mock_s3_bucket}/ctr/inbound/received",
        datetime.datetime.now().isoformat(),
    )
    ctr_process_config = Configuration(["--steps", "outbound-vendor-return"])
    _ctr_process(test_db_session, ctr_process_config)

    for scenario_data in scenario_data_list:
        # Assert ctr_address_pair exists, but only the FINEOS half.
        assert scenario_data.employee.ctr_address_pair is not None
        assert scenario_data.employee.ctr_address_pair.fineos_address is not None
        assert scenario_data.employee.ctr_address_pair.ctr_address is not None
