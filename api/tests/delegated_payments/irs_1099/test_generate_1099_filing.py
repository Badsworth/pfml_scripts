import os

import pytest

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.delegated_payments.irs_1099.generate_1099_irs_filing import (
    Generate1099IRSfilingStep,
)


@pytest.fixture
def generate_1099_irs_filing_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session,
):
    return Generate1099IRSfilingStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


def test_T_Template():
    expected_dict = {
        "T_REC_TYPE": "T",
        "PY_IND": " ",
        "TAX_YEAR": 2021,
        "TX_TIN": "123456789",
        "TX_CTL_NO": 12345,
        "B7": "       ",
        "TST_FILE_IND": " ",
        "FOR_IND": " ",
    }

    t_dict = dict(
        TRECTYPE="T",
        PYIND=" ",
        TAX_YEAR=2021,
        TXTIN=123456789,
        TXCTLNO=12345,
        B7="",
        TSTFILEIND="",
        FORIND="",
    )
    myTemplate = "{TRECTYPE:<1}{TAX_YEAR:<4}{PYIND:<1}{TXTIN:>9}{TXCTLNO:>5}{B7:>7}{TSTFILEIND:>1}{FORIND:>1}"
    result_dict = myTemplate.format_map(t_dict)
    if expected_dict == result_dict:
        assert True


def test_A_Template():
    expected_dict = {
        "A_REC_TYPE": "A",
        "PY_IND": " ",
        "TAX_YEAR": 2021,
        "CSF_IND": " ",
        "B5": "",
        "PYR_TIN": 123456789,
        "PYR_NM_CTL": "MDET",
        "LAST_FILING_IND": " ",
        "TYPE_RET": "F ",
        "AMT_CD": "00000001",
    }

    a_dict = dict(
        A_REC_TYPE="A",
        PY_IND="",
        TAX_YEAR=2021,
        CSF_IND=" ",
        B5="",
        PYR_TIN=123456789,
        PYR_NM_CTL="MDET",
        LAST_FILING_IND="",
        TYPE_RET="F",
        AMT_CD=1,
    )
    myTemplate = "{A_REC_TYPE:<1}{TAX_YEAR:<4}{PY_IND:<1}{CSF_IND:<1}{B5:<5}{PYR_TIN:<9}{PYR_NM_CTL:<4}{LAST_FILING_IND:<1}{TYPE_RET:<2}{AMT_CD:016}"
    result_dict = myTemplate.format_map(a_dict)
    if expected_dict == result_dict:
        assert True


def test_file_creation(
    generate_1099_irs_filing_step: Generate1099IRSfilingStep,
    test_db_session,
    # initialize_factories_session,
    tmp_path,
    monkeypatch,
):
    num_lines = 0
    num_chars = 0
    # set environment variables
    archive_folder_path = str(tmp_path / "reports")
    outbound_folder_path = str(tmp_path / "outbound")
    monkeypatch.setenv("pfml_error_reports_archive_path", archive_folder_path)
    monkeypatch.setenv("dfml_report_outbound_path", outbound_folder_path)
    # generate the 1099.org file
    generate_1099_irs_filing_step.run_step()

    # check that ach archive file was generated
    now = payments_util.get_now()
    date_folder = now.strftime("%Y-%m-%d")
    formatted_now = now.strftime("%Y-%m-%d-%H-%M-%S")
    file_name = f"{formatted_now}-1099.org"
    expected_file_folder = os.path.join(
        archive_folder_path, payments_util.Constants.S3_OUTBOUND_SENT_DIR, date_folder
    )
    assert file_name in file_util.list_files(expected_file_folder)
    fname = os.path.join(expected_file_folder, file_name)
    with open(fname, "r") as f:
        for line in f:
            num_lines += 1
            num_chars += len(line)
    assert num_chars == 1503
    assert num_lines == 2
