import logging  # noqa: B1
import os

import pytest

import massgov.pfml.payments.config as payments_config
import massgov.pfml.payments.gax as gax
import massgov.pfml.payments.moveit as moveit
import massgov.pfml.payments.vcc as vcc
import massgov.pfml.util.files as file_util
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
