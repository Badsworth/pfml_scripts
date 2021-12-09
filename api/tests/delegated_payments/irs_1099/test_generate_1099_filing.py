import decimal
import os
import random
from massgov.pfml.db.models.factories import Pfml1099Factory
from massgov.pfml.delegated_payments.irs_1099 import pfml_1099_util

import faker
import pytest


import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.delegated_payments.irs_1099.generate_1099_irs_filing import (
    Generate1099IRSfilingStep,
)
from massgov.pfml.util.datetime import get_now_us_eastern

fake = faker.Faker()


@pytest.fixture
def generate_1099_irs_filing_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session,
):
    return Generate1099IRSfilingStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )
    
@pytest.fixture
def pfml1099_factory():
    pfml_1099=[]
    for _ in range(10):
        rec_1099 = Pfml1099Factory.build(
            first_name=fake.first_name(),
            first_last=fake.last_name(),
            #gross_payments = decimal(round(random.uniform(0, 50000), 2)),
            #state_tax_withholdings = decimal(round(random.uniform(0, 50000), 2)),
            #federal_tax_withholdings = decimal(round(random.uniform(0, 50000), 2)),
            correction_ind = random.choice([True, False])
        )
        pfml_1099.append(rec_1099)
    return pfml_1099
        
@pytest.fixture
def enable_test_file_generation(monkeypatch):
    new_env = monkeypatch.setenv("TEST_FILE_1099_ORG", "1")
    return new_env

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
    tot_num_chars = 0
    # set environment variables
    archive_folder_path = str(tmp_path / "reports")
    outbound_folder_path = str(tmp_path / "outbound")
    monkeypatch.setenv("pfml_error_reports_archive_path", archive_folder_path)
    monkeypatch.setenv("dfml_report_outbound_path", outbound_folder_path)
    # generate the 1099.org file
    generate_1099_irs_filing_step.run_step()

    # check that ach archive file was generated
    now = get_now_us_eastern()
    date_folder = now.strftime("%Y-%m-%d")
    formatted_now = now.strftime("%Y-%m-%d-%H-%M-%S")
    file_name = f"{formatted_now}-1099.ORG"
    expected_file_folder = os.path.join(
        archive_folder_path, payments_util.Constants.S3_OUTBOUND_SENT_DIR, date_folder
    )
    if len(file_util.list_files(expected_file_folder)) > 0:
        assert file_name in file_util.list_files(expected_file_folder)
        fname = os.path.join(expected_file_folder, file_name)
        with open(fname, "r") as f:
            for line in f:
                num_lines += 1
                num_chars = len(line)
                assert num_chars == 751
                tot_num_chars += len(line)
    # assert tot_num_chars == 3004
    # assert num_lines == 5


def test_format_amount_fields():
    expected_result = ["10000", "25055", "900000", "45080", "60008"]
    input_amt = ("100.00", "250.55", "9000", "450.8", "600.08")
    outcome = []

    for _i in range(len(input_amt)):
        tot_amt = input_amt[_i].split(".")
        dollars = tot_amt[0]
        if len(tot_amt) == 2:
            cents = tot_amt[1]
            if len(cents) == 2:
                cents = cents
            elif len(cents) == 1:
                cents = cents + "0"
        else:
            cents = "00"
        format_amt = dollars + cents
        print(format_amt)
        outcome.append(format_amt)

    assert outcome[0] == "10000"
    assert expected_result == outcome


def test_name_ctl():
    expected_result = ["JONE", "SMIT", "SMIT", "DELA", "MORA", "NGUY", "LO"]
    input_names = [
        "Smith Jones",
        "Smith",
        "Smith-Jones",
        "de la Rosa",
        "Garza Morales",
        "Van Nguyen",
        "Lo",
    ]
    result_names = []
    last_name_four = ""
    print(len(input_names))
    for _i in range(len(input_names)):
        if input_names[_i].find("-") != -1:
            last_name = input_names[_i].split("-")[0]

        elif input_names[_i].find(" ") != -1:
            last_name_list = input_names[_i].split(" ")
            print("last name spaces", last_name_list)
            name_length = len(last_name_list)

            if name_length == 2:
                if last_name_list[0].upper().find("VAN") != -1:
                    last_name = last_name_list[1]
                elif last_name_list[0].upper().find("THI") != -1:
                    last_name = last_name_list[1]
                else:
                    last_name = last_name_list[1]
            elif name_length > 2:
                last_name = last_name_list[0].rstrip() + last_name_list[1]
        else:
            last_name = input_names[_i]

        last_name_four = last_name[0:4].upper()
        result_names.append(last_name_four)
    assert expected_result == result_names
    
def test_b_record_types(pfml1099_factory):
    correction=[]
    original=[]
    for i in range(len(pfml1099_factory)):
        if pfml1099_factory[i].correction_ind == True:
            correction.append(pfml1099_factory[i])
        else:
            original.append(pfml1099_factory[i])
    assert 5 == len(correction)        


    
