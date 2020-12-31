import pytest

import massgov.pfml.payments.data_mart as data_mart
import massgov.pfml.payments.data_mart_states_processing as data_mart_states_processing


@pytest.fixture
def mock_db_session(mocker):
    return mocker.patch("sqlalchemy.orm.Session", autospec=True)


def test_process_all_states_data_mart_engine_fail_just_returns(mocker, mock_db_session):
    mocker.patch.object(data_mart, "init", side_effect=Exception)

    mock_identify_mmars_status = mocker.patch.object(
        data_mart_states_processing.identify_mmars_status, "process"
    )

    data_mart_states_processing.process_all_states(mock_db_session)

    mock_identify_mmars_status.assert_not_called()


def test_process_all_states_raises_exception_at_end_if_any_state_raised_execption(
    mocker, mock_db_session
):
    mocker.patch.object(data_mart, "init")

    mock_identify_mmars_status = mocker.patch.object(
        data_mart_states_processing.identify_mmars_status, "process", side_effect=Exception
    )

    mock_vcc_sent = mocker.patch.object(
        data_mart_states_processing.vcc_sent, "process", side_effect=Exception
    )

    mock_vcm_report_sent = mocker.patch.object(
        data_mart_states_processing.vcm_report_sent, "process", side_effect=Exception
    )

    mock_vcc_error_report_sent = mocker.patch.object(
        data_mart_states_processing.vcc_error_report_sent, "process", side_effect=Exception
    )

    mock_eft_pending = mocker.patch.object(
        data_mart_states_processing.eft_pending, "process", side_effect=Exception
    )

    with pytest.raises(Exception):
        data_mart_states_processing.process_all_states(mock_db_session)

    mock_identify_mmars_status.assert_called_once()
    mock_vcc_sent.assert_called_once()
    mock_vcm_report_sent.assert_called_once()
    mock_vcc_error_report_sent.assert_called_once()
    mock_eft_pending.assert_called_once()


def test_process_all_states_all_success(mocker, mock_db_session):
    mocker.patch.object(data_mart, "init")

    mock_identify_mmars_status = mocker.patch.object(
        data_mart_states_processing.identify_mmars_status, "process"
    )

    mock_vcc_sent = mocker.patch.object(data_mart_states_processing.vcc_sent, "process")

    mock_vcm_report_sent = mocker.patch.object(
        data_mart_states_processing.vcm_report_sent, "process"
    )

    mock_vcc_error_report_sent = mocker.patch.object(
        data_mart_states_processing.vcc_error_report_sent, "process"
    )

    mock_eft_pending = mocker.patch.object(data_mart_states_processing.eft_pending, "process")

    data_mart_states_processing.process_all_states(mock_db_session)

    mock_identify_mmars_status.assert_called_once()
    mock_vcc_sent.assert_called_once()
    mock_vcm_report_sent.assert_called_once()
    mock_vcc_error_report_sent.assert_called_once()
    mock_eft_pending.assert_called_once()
