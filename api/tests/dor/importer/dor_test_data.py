import copy
from datetime import date, datetime
from decimal import Decimal

import pytz

from massgov.pfml.types import Fein

employer_quarter_line = "A0000000000120190930Anderson, Barber and Johnson                                                                                                                                                                                                                                   244674065     F2020040120200522110527"
employee_quarter_line = "B0000000000120190930john                                                                                                                                                                                                                                                           Doe                                                                                                                                                                                                                                                            123456789TF            45000.00            15000.00               55.80              37.29                15.00                7.00"
employer_info_line = "00000000001Anderson, Barber and Johnson                                                                                                                                                                                                                                   244674065     64034 Angela Mews                                                                                                                                                                                                                                              North Kaylabury               MA935463801USAAnderson, Barber and Johnson                                                                                                                                                                                                                                   TF202001012020123120200522110527"

new_employer = {
    "account_key": "00000000001",
    "employer_name": "Anderson, Barber and Johnson",
    "employer_dba": "Anderson, Barber and Johnson",
    "fein": "244674065",
    "employer_address_street": "64034 Angela Mews",
    "employer_address_city": "North Kaylabury",
    "employer_address_state": "MA",
    "employer_address_zip": "935463801",
    "employer_address_country": "USA",
    "family_exemption": True,
    "medical_exemption": False,
    "exemption_commence_date": date(2020, 1, 1),
    "exemption_cease_date": date(2020, 12, 31),
    "updated_date": pytz.UTC.localize(datetime(2020, 5, 22, 11, 5, 27)),
}

updated_employer_except_update_date = copy.deepcopy(new_employer)
updated_employer_except_update_date["employer_dba"] = "ABJ"
updated_employer_except_update_date["employer_address_street"] = "1234 Main Street"
updated_employer_except_update_date["employer_address_zip"] = "935513845"
updated_employer_except_update_date["family_exemption"] = False
updated_employer_except_update_date["medical_exemption"] = True
updated_employer_except_update_date["exemption_commence_date"] = date(2021, 1, 1)
updated_employer_except_update_date["exemption_cease_date"] = date(2021, 12, 31)

updated_employer = copy.deepcopy(updated_employer_except_update_date)
updated_employer["updated_date"] = pytz.UTC.localize(datetime(2020, 5, 23, 11, 5, 27))

employer_international_address = copy.deepcopy(new_employer)
employer_international_address["fein"] = Fein("999999999")
employer_international_address["account_key"] = "00000000002"
employer_international_address["employer_address_state"] = "DX"
employer_international_address["employer_address_country"] = "CAN"

employer_invalid_country = copy.deepcopy(new_employer)
employer_invalid_country["fein"] = Fein("999999991")
employer_invalid_country["account_key"] = "00000000003"
employer_invalid_country["employer_address_state"] = "MA"
employer_invalid_country["employer_address_country"] = "UXU"

new_employee_wage_data = {
    "record_type": "B",
    "account_key": "00000000001",
    "filing_period": date(2019, 9, 30),
    "employee_first_name": "john",
    "employee_last_name": "Doe",
    "employee_ssn": "123456789",
    "independent_contractor": True,
    "opt_in": False,
    "employee_ytd_wages": Decimal("45000.00"),
    "employee_qtr_wages": Decimal("15000.00"),
    "employee_medical": Decimal("55.80"),
    "employer_medical": Decimal("37.29"),
    "employee_family": Decimal("15.00"),
    "employer_family": Decimal("7.00"),
}

updated_employee_wage_data = copy.deepcopy(new_employee_wage_data)
updated_employee_wage_data["employee_first_name"] = "John"
updated_employee_wage_data["employee_last_name"] = "Doe Jr."
updated_employee_wage_data["independent_contractor"] = False
updated_employee_wage_data["opt_in"] = True
updated_employee_wage_data["employee_ytd_wages"] = Decimal("48000.00")
updated_employee_wage_data["employee_qtr_wages"] = Decimal("16000.00")
updated_employee_wage_data["employee_medical"] = Decimal("56.20")
updated_employee_wage_data["employer_medical"] = Decimal("38.40")
updated_employee_wage_data["employee_family"] = Decimal("15.70")
updated_employee_wage_data["employer_family"] = Decimal("7.50")

employer_quarter_info = {
    "record_type": "A",
    "account_key": new_employer["account_key"],
    "filing_period": new_employee_wage_data["filing_period"],
    "employer_name": new_employer["employer_name"],
    "employer_fein": new_employer["fein"],
    "amended_flag": False,
    "received_date": date(2020, 4, 1),
    "updated_date": pytz.UTC.localize(datetime(2020, 5, 22, 11, 5, 27)),
}

employer_quarter_info_amended = copy.deepcopy(employer_quarter_info)
employer_quarter_info_amended["amended_flag"] = True


def get_new_employer():
    return new_employer


def get_updated_employer_except_update_date():
    return updated_employer_except_update_date


def get_updated_employer():
    return updated_employer


def get_employer_international_address():
    return employer_international_address


def get_employer_invalid_country():
    return employer_invalid_country


def get_new_employee_wage_data():
    return new_employee_wage_data


def get_updated_employee_wage_data():
    return updated_employee_wage_data


def get_employer_quarter_info():
    return employer_quarter_info


def get_employer_quarter_info_amended():
    return employer_quarter_info_amended


def get_employer_quarter_line():
    return employer_quarter_line


def get_employee_quarter_line():
    return employee_quarter_line


def get_employer_info_line():
    return employer_info_line
