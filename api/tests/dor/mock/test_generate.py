import io
import tempfile
from datetime import date, datetime
from decimal import Decimal

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
    employers = generate.generate_employers(1)
    assert len(employers) == 1

    employer = employers[0]
    validate_employer_object(employer)


def test_generate_employee_employer_quarterly_wage_rows():
    employers = generate.generate_employers(1)
    employer = employers[0]

    (
        employer_wage_rows,
        employee_wage_rows,
    ) = generate.generate_employee_employer_quarterly_wage_rows(1, employers, [1])

    assert len(employer_wage_rows) == 4
    assert len(employee_wage_rows) == 4

    for i in range(4):
        employer_wage = employer_wage_rows[i]
        validate_employer_wage(employer_wage, employer, QUARTERS[i])

    for i in range(4):
        employee_wage = employee_wage_rows[i]
        validate_employee_wage(employee_wage, employer, QUARTERS[i])
        assert (
            employee_wage["employee_ytd_wages"]
            == employee_wage["employee_qtr_wages"] * employee_wage["filing_period"].quarter
        )


def test_file_populate(tmpdir):
    # employer info
    employers = generate.generate_employers(1)

    employers_file = io.StringIO()
    generate.populate_employer_file(employers, employers_file)

    employers_file.seek(0)
    employer_lines = employers_file.readlines()
    assert len(employer_lines) == 1

    employer_line = employer_lines[0].rstrip()
    employer_file_format = FileFormat(EMPLOYER_FILE_FORMAT)
    assert len(employer_line) == employer_file_format.get_line_length()

    parsed_employer_line = employer_file_format.parse_line(employer_line)
    validate_employer_object(parsed_employer_line)

    # employer and employee wage info
    (
        employer_wage_rows,
        employee_wage_rows,
    ) = generate.generate_employee_employer_quarterly_wage_rows(1, employers, [1])

    employees_file = io.StringIO()
    generate.populate_employee_file(
        employer_wage_rows, employee_wage_rows, employers, employees_file
    )

    employees_file.seek(0)
    employee_lines = employees_file.readlines()
    assert len(employee_lines) == 8

    employer_wage_line = employee_lines[0].rstrip()
    employer_quarter_info_file_format = FileFormat(EMPLOYER_QUARTER_INFO_FORMAT)
    assert len(employer_wage_line) == employer_quarter_info_file_format.get_line_length()

    parsed_employer_wage_line = employer_quarter_info_file_format.parse_line(employer_wage_line)
    validate_employer_wage(parsed_employer_wage_line, employers[0], QUARTERS[0].as_date())

    employee_wage_line = employee_lines[4].rstrip()
    employee_wage_file_format = FileFormat(EMPLOYEE_FORMAT)
    assert len(employee_wage_line) == employee_wage_file_format.get_line_length()

    parsed_employee_wage_line = employee_wage_file_format.parse_line(employee_wage_line)
    validate_employee_wage(parsed_employee_wage_line, employers[0], QUARTERS[0].as_date())


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


def validate_employee_wage(employee_wage, employer, quarter):
    assert employee_wage["account_key"] == employer["account_key"]
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
