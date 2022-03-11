import decimal
import os
from unittest import mock

import faker
import pytest

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.factories import Pfml1099Factory
from massgov.pfml.delegated_payments.irs_1099.generate_1099_irs_filing import (
    Generate1099IRSfilingStep,
)
from massgov.pfml.util.datetime import get_now_us_eastern

fake = faker.Faker()


@pytest.fixture
def generate_1099_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    return Generate1099IRSfilingStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


@pytest.fixture
def create_pfml_1099():
    pfml_list = []
    for _i in range(20):
        pfml_list.append(Pfml1099Factory.build())
    return pfml_list


def test_create_irs_file(
    generate_1099_step: Generate1099IRSfilingStep, tmp_path, monkeypatch, local_test_db_session
):
    # set environment variables
    archive_folder_path = str(tmp_path / "reports")
    outbound_folder_path = str(tmp_path / "outbound")
    monkeypatch.setenv("pfml_error_reports_archive_path", archive_folder_path)
    monkeypatch.setenv("dfml_report_outbound_path", outbound_folder_path)
    # generate the 1099.txt file
    entries = "T2021 04600228408025         COMMONWEALTH OF MASSACHUSETTS                                                   COMMONWEALTH OF MASSACHUSETTS                                                   ONE ASHBURTON PL ROOM 901               BOSTON                                  MA021080000               00000017JESSICA A COGSWELL                      6179732323     jessica.cogswell@mass.gov                                                                                                                    00000001          I                                                                                                                                                                                                                                        "
    generate_1099_step._create_irs_file(entries)

    # check that ach archive file was generated
    now = get_now_us_eastern()
    date_folder = now.strftime("%Y-%m-%d")
    formatted_now = now.strftime("%Y-%m-%d-%H-%M-%S")
    file_name = f"{formatted_now}-1099.txt"
    expected_file_folder = os.path.join(
        archive_folder_path, payments_util.Constants.S3_OUTBOUND_SENT_DIR, date_folder
    )
    if len(file_util.list_files(expected_file_folder)) > 0:
        assert file_name in file_util.list_files(expected_file_folder)


def test_format_amount_fields(generate_1099_step: Generate1099IRSfilingStep):
    expected_result = ["10000", "25055", "900000", "45080", "60008"]
    input_amt = ("100.00", "250.55", "9000", "450.8", "600.08")
    outcome = []

    for _i in range(len(input_amt)):
        outcome.append(generate_1099_step._format_amount_fields(input_amt[_i]))

    assert outcome[0] == "10000"
    assert expected_result == outcome


def test_name_ctl(generate_1099_step: Generate1099IRSfilingStep):
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
    print(len(input_names))
    for _i in range(len(input_names)):
        result_names.append(generate_1099_step._get_name_ctl(input_names[_i]))
    assert expected_result == result_names


def test_zip_code(generate_1099_step: Generate1099IRSfilingStep):
    zip_codes = ["02412", "02412-3456", "024123456", "0241234567"]
    expected_result = ["02412", "024123456", "024123456", "024123456"]
    results = []
    for _i in range(len(zip_codes)):
        results.append(generate_1099_step._get_zip(zip_codes[_i]))

    assert results == expected_result


def test_get_full_name(generate_1099_step: Generate1099IRSfilingStep):
    name_upper = "FernandoDSouzaConstantineJohnVanderbiltF".upper()
    name_upper2 = "itzerland".upper()
    full_name = generate_1099_step._get_full_name("Johnny", "Depp", "PAYEE_NM1")
    assert full_name == "DEPPJOHNNY"
    full_name = generate_1099_step._get_full_name("Johnny", "Depp", "PAYEE_NM2")
    assert full_name == ""

    full_name = generate_1099_step._get_full_name(
        "JohnVanderbiltFitzerland", "FernandoDSouzaConstantine", "PAYEE_NM1"
    )
    assert full_name == name_upper
    full_name = generate_1099_step._get_full_name(
        "JohnVanderbiltFitzerland", "FernandoDSouzaConstantine", "PAYEE_NM2"
    )
    assert full_name == name_upper2


def test_create_t_template(generate_1099_step: Generate1099IRSfilingStep):
    t_template = generate_1099_step._create_t_template()
    assert t_template.find("TX_NAME") != -1


def test_load_t_rec_data(generate_1099_step: Generate1099IRSfilingStep):
    t_template = generate_1099_step._create_t_template()
    t_entries = generate_1099_step._load_t_rec_data(t_template)
    assert len(t_entries) == 750


def test_create_a_template(generate_1099_step: Generate1099IRSfilingStep):
    a_template = generate_1099_step._create_a_template()
    assert a_template.find("PYR_TIN") != -1


def test_load_a_rec_data(generate_1099_step: Generate1099IRSfilingStep):
    a_template = generate_1099_step._create_a_template()
    a_entries = generate_1099_step._load_a_rec_data(a_template)
    assert len(a_entries) == 750


def test_create_k_template(generate_1099_step: Generate1099IRSfilingStep):
    k_template = generate_1099_step._create_k_template()
    k_entries = generate_1099_step._load_k_rec_data(k_template, 10000, 0, 0)
    assert len(k_entries) == 750


def test_create_f_template(generate_1099_step: Generate1099IRSfilingStep):
    f_template = generate_1099_step._create_f_template()
    f_entries = generate_1099_step._load_f_rec_data(f_template)
    assert len(f_entries) == 750


def test_create_c_template(generate_1099_step: Generate1099IRSfilingStep):
    c_template = generate_1099_step._create_c_template()
    c_entries = generate_1099_step._load_c_rec_data(c_template, 10000)
    assert len(c_entries) == 750


def test_create_b_template(generate_1099_step: Generate1099IRSfilingStep, create_pfml_1099):

    b_template = generate_1099_step._create_b_template()
    assert b_template.find("AMT_CD_1") != -1
    b_entries = generate_1099_step._load_b_rec_data(b_template, create_pfml_1099)
    for b_records in b_entries:
        print(b_records)
        assert len(b_records) == 750


def test_get_correction_ind(generate_1099_step: Generate1099IRSfilingStep):
    correction = generate_1099_step._get_correction_ind(True)
    assert correction == "G"
    original = generate_1099_step._get_correction_ind(False)
    assert original == ""


def test_get_totals(generate_1099_step: Generate1099IRSfilingStep, create_pfml_1099):

    expected_st = decimal.Decimal(0.0)
    expected_fed = decimal.Decimal(0.0)
    expected_ctl = decimal.Decimal(0.0)
    for _i in range(len(create_pfml_1099)):
        expected_ctl += create_pfml_1099[_i].gross_payments
        expected_st += create_pfml_1099[_i].state_tax_withholdings
        expected_fed += create_pfml_1099[_i].federal_tax_withholdings
    expected_ctl = generate_1099_step._format_amount_fields(expected_ctl)
    expected_st = generate_1099_step._format_amount_fields(expected_st)
    expected_fed = generate_1099_step._format_amount_fields(expected_fed)
    ctl_total, st_tax, fed_tax = generate_1099_step._get_totals(create_pfml_1099)
    assert ctl_total == expected_ctl
    assert expected_st == st_tax
    assert expected_fed == fed_tax


def test_generate_1099_irs_filing(
    local_test_db_session, generate_1099_step: Generate1099IRSfilingStep, create_pfml_1099
):

    mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_1099_records_to_file",
        return_value=create_pfml_1099,
    )
    generate_1099_step.run_step()


def test_test_file_generation(
    generate_1099_step: Generate1099IRSfilingStep, monkeypatch, create_pfml_1099
):
    monkeypatch.setenv("TEST_FILE_GENERATION_1099", "1")
    # generate the b records of 1099.txt file
    create_pfml_1099 = create_pfml_1099[:11]
    b_template = generate_1099_step._create_b_template()
    b_entries = generate_1099_step._load_b_rec_data(b_template, create_pfml_1099)
    assert len(b_entries) == 11


def test_remove_special_chars(generate_1099_step: Generate1099IRSfilingStep):
    name_string = "FernandoD'SouzaConstantine JohnVanderbilt.!12F"
    final_string = "FernandoDSouzaConstantine JohnVanderbilt12F"
    result_string = generate_1099_step._remove_special_chars(name_string)
    assert final_string == result_string
