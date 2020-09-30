# See details in https://lwd.atlassian.net/wiki/spaces/API/pages/229539929/DOR+Import#Import-Process

from datetime import datetime
from decimal import Decimal

from massgov.pfml.util.files.file_format import FieldFormat, FileFormat


def parse_date(date_str):
    dt = datetime.strptime(date_str, "%Y%m%d")
    return dt.date()


def parse_datetime(datetime_str):
    return datetime.strptime(datetime_str, "%Y%m%d%H%M%S")


def parse_boolean(boolean_str):
    # expected format is "T" or "F"
    return boolean_str == "T"


def parse_dollar_amount(dollar_amount_str):
    return Decimal(dollar_amount_str)


EMPLOYER_FILE_FORMAT = FileFormat(
    (
        FieldFormat("account_key", 11),
        FieldFormat("employer_name", 255),
        FieldFormat("fein", 9),
        FieldFormat("employer_address_street", 255),
        FieldFormat("employer_address_city", 30),
        FieldFormat("employer_address_state", 2),
        FieldFormat("employer_address_zip", 9),
        FieldFormat("employer_dba", 255),
        FieldFormat("family_exemption", 1, parse_boolean),
        FieldFormat("medical_exemption", 1, parse_boolean),
        FieldFormat("exemption_commence_date", 8, parse_date),
        FieldFormat("exemption_cease_date", 8, parse_date),
        FieldFormat("updated_date", 14, parse_datetime),
    )
)

EMPLOYER_QUARTER_INFO_FORMAT = FileFormat(
    (
        FieldFormat("record_type", 1),
        FieldFormat("account_key", 11),
        FieldFormat("filing_period", 8, parse_date),
        FieldFormat("employer_name", 255),
        FieldFormat("employer_fein", 9),
        FieldFormat("amended_flag", 1, parse_boolean),
        FieldFormat("received_date", 8, parse_date),
        FieldFormat("updated_date", 14, parse_datetime),
    )
)

EMPLOYEE_FORMAT = FileFormat(
    (
        FieldFormat("record_type", 1),
        FieldFormat("account_key", 11),
        FieldFormat("filing_period", 8, parse_date),
        FieldFormat("employee_first_name", 255),
        FieldFormat("employee_last_name", 255),
        FieldFormat("employee_ssn", 9),
        FieldFormat("independent_contractor", 1, parse_boolean),
        FieldFormat("opt_in", 1, parse_boolean),
        FieldFormat("employee_ytd_wages", 20, parse_dollar_amount),
        FieldFormat("employee_qtr_wages", 20, parse_dollar_amount),
        FieldFormat("employee_medical", 20, parse_dollar_amount),
        FieldFormat("employer_medical", 20, parse_dollar_amount),
        FieldFormat("employee_family", 20, parse_dollar_amount),
        FieldFormat("employer_family", 20, parse_dollar_amount),
    )
)
