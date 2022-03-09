# See details in https://lwd.atlassian.net/wiki/spaces/API/pages/229539929/DOR+Import#Import-Process
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Tuple

import pytz

from massgov.pfml.util.files.file_format import FieldFormat, FileFormat


def parse_date(date_str: str) -> date:
    dt = datetime.strptime(date_str, "%Y%m%d")
    return dt.date()


def parse_datetime(datetime_str: str) -> datetime:
    return pytz.UTC.localize(datetime.strptime(datetime_str, "%Y%m%d%H%M%S"))


def parse_boolean(boolean_str: str) -> bool:
    # expected format is "T" or "F"
    return boolean_str == "T"


def parse_dollar_amount(dollar_amount_str: str) -> Decimal:
    return Decimal(dollar_amount_str)


def parse_optional_dollar_amount(dollar_amount_str: str) -> Decimal:
    if len(dollar_amount_str) == 0:
        return Decimal(0)

    return Decimal(dollar_amount_str)


EMPLOYER_FILE_FORMAT = FileFormat(
    (
        FieldFormat("account_key", 11),
        FieldFormat("employer_name", 255),
        FieldFormat("fein", 14),
        FieldFormat("employer_address_street", 255),
        FieldFormat("employer_address_city", 30),
        FieldFormat("employer_address_state", 2),
        FieldFormat("employer_address_zip", 9),
        FieldFormat("employer_address_country", 3),
        FieldFormat("employer_dba", 255),
        FieldFormat("family_exemption", 1, parse_boolean),
        FieldFormat("medical_exemption", 1, parse_boolean),
        FieldFormat("exemption_commence_date", 8, parse_date),
        FieldFormat("exemption_cease_date", 8, parse_date),
        FieldFormat("updated_date", 14, parse_datetime),
    )
)

# numbers correspond to format cols above
EMPLOYER_FILE_ROW_LENGTH = 11 + 255 + 14 + 255 + 30 + 2 + 9 + 255 + 1 + 1 + 8 + 8 + 14 + 3

EMPLOYER_QUARTER_INFO_FORMAT = FileFormat(
    (
        FieldFormat("record_type", 1),
        FieldFormat("account_key", 11),
        FieldFormat("filing_period", 8, parse_date),
        FieldFormat("employer_name", 255),
        FieldFormat("employer_fein", 14),
        FieldFormat("amended_flag", 1, parse_boolean),
        FieldFormat("pfm_account_id", 14),
        FieldFormat("total_pfml_contribution", 20, parse_dollar_amount),
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

EMPLOYEE_FILE_ROW_LENGTH = 1 + 11 + 8 + 255 + 255 + 9 + 1 + 1 + 20 + 20 + 20 + 20 + 20 + 20

EMPLOYER_PENDING_FILING_RESPONSE_FILE_FORMAT_A = FileFormat(
    (
        FieldFormat("fstrRecordType", 1),
        FieldFormat("fstrEmployerIDType", 10),
        FieldFormat("fstrEmployerID", 14),
        FieldFormat("fdtmQuarterYear", 8),
        FieldFormat("fstrEmployerName", 255),
        FieldFormat("fcurEmployeeWages", 20, parse_optional_dollar_amount),
    )
)

EMPLOYER_PENDING_FILING_RESPONSE_FILE_A_ROW_LENGTH = 1 + 10 + 14 + 8 + 255 + 20

EMPLOYER_PENDING_FILING_RESPONSE_FILE_FORMAT_B = FileFormat(
    (
        FieldFormat("fstrRecordType", 1),
        FieldFormat("fstrIDType", 10),
        FieldFormat("fstrID", 9),
        FieldFormat("fstrFirstName", 255),
        FieldFormat("fstrLastName", 255),
        FieldFormat("fcurQuarterWages", 20, parse_optional_dollar_amount),
    )
)

EMPLOYER_PENDING_FILING_RESPONSE_FILE_B_ROW_LENGTH = 1 + 10 + 9 + 255 + 255 + 20

# alias types
WageKey = Tuple[uuid.UUID, uuid.UUID, date]
EmployerQuarterlyKey = Tuple[uuid.UUID, date]
ParsedEmployeeLine = Dict[str, Any]
ParsedEmployerLine = Dict[str, Any]
ParsedEmployerQuarterLine = Dict[str, Any]
ParsedEmployeeWageLine = Dict[str, Any]
