import io
import tempfile
from datetime import date, datetime
from decimal import Decimal

import pytest

import massgov.pfml.dor.mock.generate as generate
from massgov.pfml.dor.importer.dor_file_formats import (
    EMPLOYEE_FORMAT,
    EMPLOYER_FILE_FORMAT,
    EMPLOYER_QUARTER_INFO_FORMAT,
)
from massgov.pfml.util.datetime.quarter import Quarter
from massgov.pfml.util.files.file_format import FileFormat

QUARTERS = tuple(Quarter(2019, 2).series(4))


def test_generate_employers():
    employer_info_list = []
    employer_wage_info_list = []

    def on_employer(employer_info, employer_wage_data):
        employer_info_list.append(employer_info)
        employer_wage_info_list.extend(employer_wage_data)

    count = 200
    generate.generate_employers(count, on_employer)
    assert len(employer_info_list) == count
    assert len(employer_wage_info_list) == count * 4  # one line for each quarter

    validate_employer_object(employer_info_list[0])
    validate_employer_wage(employer_wage_info_list[0], employer_info_list[0], QUARTERS[0])


def test_employer_file_populate():
    count = 200
    employers_file = io.StringIO()
    employer_wage_file = io.StringIO()
    employer_account_keys = generate.process_employer_file(
        count, employers_file, employer_wage_file
    )

    assert len(employer_account_keys) == count

    # employee info
    employers_file.seek(0)
    employer_lines = employers_file.readlines()
    assert len(employer_lines) == count

    employer_line = employer_lines[0].rstrip()
    employer_file_format = FileFormat(EMPLOYER_FILE_FORMAT)
    assert len(employer_line) == employer_file_format.get_line_length()

    parsed_employer_obj = employer_file_format.parse_line(employer_line)
    validate_employer_object(parsed_employer_obj)

    # employee wage info
    employer_wage_file.seek(0)
    employer_wage_lines = employer_wage_file.readlines()
    assert len(employer_wage_lines) == count * 4  # one line for each quarter

    employer_wage_line = employer_wage_lines[0].rstrip()
    employer_quarter_info_file_format = FileFormat(EMPLOYER_QUARTER_INFO_FORMAT)
    assert len(employer_wage_line) == employer_quarter_info_file_format.get_line_length()

    parsed_employer_wage_obj = employer_quarter_info_file_format.parse_line(employer_wage_line)
    validate_employer_wage(parsed_employer_wage_obj, parsed_employer_obj, QUARTERS[0].as_date())


def test_generate_employee_employer_quarterly_wage_rows():
    account_key = "00000000001"

    employees_wage_infos = []

    def on_employee(employee_wage_info):
        employees_wage_infos.append(employee_wage_info)

    count = 200
    generate.generate_employee_employer_quarterly_wage_rows(count, [account_key], on_employee, [1])
    assert len(employees_wage_infos) == count * 4  # one line for each quarter

    for i in range(4):
        employee_wage = employees_wage_infos[i]
        validate_employee_wage(employee_wage, account_key, QUARTERS[i])
        assert (
            employee_wage["employee_ytd_wages"]
            == employee_wage["employee_qtr_wages"] * employee_wage["filing_period"].quarter
        )


def test_employee_file_populate():
    count = 200
    employee_wage_file = io.StringIO()

    account_key = "00000000001"
    employer_account_keys = [account_key]
    generate.process_employee_file(count, employer_account_keys, employee_wage_file, [1])

    # employee info
    employee_wage_file.seek(0)
    employee_wage_lines = employee_wage_file.readlines()
    assert len(employee_wage_lines) == count * 4  # one line for each quarter

    employee_wage_line = employee_wage_lines[0].rstrip()
    employer_file_format = FileFormat(EMPLOYEE_FORMAT)
    assert len(employee_wage_line) == employer_file_format.get_line_length()

    parsed_employee_wage_obj = employer_file_format.parse_line(employee_wage_line)
    validate_employee_wage(parsed_employee_wage_obj, account_key, QUARTERS[0].as_date())


@pytest.mark.timeout(5)
def test_full_generate():
    employer_count = 200
    employee_count = employer_count * generate.EMPLOYER_TO_EMPLOYEE_RATIO

    employer_file = io.StringIO()
    employer_employee_wage_file = io.StringIO()

    generate.process(employer_count, employer_file, employer_employee_wage_file, [1])

    employer_file.seek(0)
    employer_file_lines = employer_file.readlines()
    assert len(employer_file_lines) == employer_count

    employer_employee_wage_file.seek(0)
    employer_employee_wage_file_lines = employer_employee_wage_file.readlines()
    assert len(employer_employee_wage_file_lines) == (employer_count * 4) + (
        employee_count * 4
    )  # one line for each quarter


# validation utils


def validate_employer_object(employer):
    assert len(employer["account_key"]) == 11
    assert len(employer["employer_name"]) > 0
    assert len(employer["fein"]) == 9
    int(employer["fein"])

    assert len(employer["employer_address_street"]) > 11
    assert len(employer["employer_address_city"]) > 0
    assert len(employer["employer_address_zip"]) == 9
    int(employer["employer_address_zip"])

    assert len(employer["employer_dba"]) > 0
    assert employer["family_exemption"] in (True, False)
    assert employer["medical_exemption"] in (True, False)

    assert isinstance(employer["exemption_commence_date"], date)
    assert isinstance(employer["exemption_cease_date"], date)
    assert isinstance(employer["updated_date"], datetime)


def validate_employer_wage(employer_wage, employer, quarter):
    assert employer_wage["account_key"] == employer["account_key"]
    assert employer_wage["filing_period"] == quarter
    assert employer_wage["employer_name"] == employer["employer_name"]
    assert employer_wage["employer_fein"] == employer["fein"]
    assert employer_wage["amended_flag"] in (True, False)

    assert isinstance(employer_wage["received_date"], date)
    assert isinstance(employer_wage["updated_date"], datetime)


def validate_employee_wage(employee_wage, account_key, quarter):
    assert employee_wage["account_key"] == account_key
    assert employee_wage["filing_period"] == quarter
    assert len(employee_wage["employee_first_name"]) > 0
    assert len(employee_wage["employee_last_name"]) > 0
    assert len(employee_wage["employee_ssn"]) == 9
    int(employee_wage["employee_ssn"])

    assert employee_wage["independent_contractor"] in (True, False)
    assert employee_wage["opt_in"] in (True, False)

    Decimal(employee_wage["employee_ytd_wages"])
    Decimal(employee_wage["employee_qtr_wages"])

    Decimal(employee_wage["employer_medical"])
    Decimal(employee_wage["employer_family"])
    Decimal(employee_wage["employee_medical"])
    Decimal(employee_wage["employee_family"])


# helpers


def get_line_length(format):
    length = 0
    for column_format in format:
        length = length + column_format.length
    return length


def get_temp_file_path():
    handle, path = tempfile.mkstemp()
    return path
