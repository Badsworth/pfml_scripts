#!/usr/bin/env python3
#
# Generate fake DOR data.
#

import argparse
import datetime as dt
import decimal
import math
import os
import random
import sys
from datetime import datetime, timedelta

import faker
import pydash

# Running this module as a python command from the top level /api directory seems
# to reset the path on load causing issues with local module imports.
# Workaround is to force set the path to run directory (top level api folder)
# See import_infra/dor/README.md for running details.
sys.path.insert(0, ".")  # noqa: E402

import massgov.pfml.util.logging as logging  # isort:skip
from massgov.pfml.util.datetime.quarter import Quarter  # isort:skip

logging.init(__package__)
logger = logging.get_logger("massgov.pfml.dor.mock.generate")

random.seed(1111)

fake = faker.Faker()
fake.seed_instance(2222)

TWOPLACES = decimal.Decimal(10) ** -2

parser = argparse.ArgumentParser(description="Generate fake DOR data")
parser.add_argument(
    "--count", type=int, default=100, help="Number of individuals to generate data for"
)
parser.add_argument(
    "--folder", type=str, default="generated_files", help="Output folder for generated files"
)


# helpers
def get_date_days_before(original_date, days_to_subtract):
    d = original_date - timedelta(days=days_to_subtract)
    return d


def get_date_days_after(original_date, days_to_add):
    d = original_date + timedelta(days=days_to_add)
    return d


def format_date(d):
    return d.strftime("%Y%m%d")


def format_datetime(d):
    return d.strftime("%Y%m%d%H%M%S")


# generator

file_extension = format_datetime(datetime.now())
employer_file_name = "DORDFMLEMP_" + file_extension
employee_file_name = "DORDFML_" + file_extension

EMPLOYER_TO_EMPLOYEE_MULTIPLIER = 5

NO_EXEMPTION_DATE = dt.date(9999, 12, 31)


def main():
    args = parser.parse_args()
    employee_count = args.count

    output_folder = args.folder
    os.makedirs(output_folder, exist_ok=True)
    employers_file = open("{}/{}".format(output_folder, employer_file_name), "w")
    employees_file = open("{}/{}".format(output_folder, employee_file_name), "w")

    # minimum of 4 employers
    employer_count = math.ceil(employee_count / EMPLOYER_TO_EMPLOYEE_MULTIPLIER)
    if employer_count < 4:
        employer_count = 4

    employers = populate_employer_file(employer_count, employers_file)
    populate_employee_file(employee_count, employers, employees_file)

    logger.info(
        "DONE: Please check files in generated_files folder: %s and %s",
        employer_file_name,
        employee_file_name,
    )


def populate_employer_file(employer_count, employers_file):
    """Generate employers, print rows to file"""
    employers = generate_employers(employer_count)
    for row in employers:
        line = "{}{:255}{}{:255}{:30}{}{}{:255}{}{}{}{}{}\n".format(
            row["account_key"],
            row["employer_name"],
            row["fein"],
            row["employer_address_street"],
            row["employer_address_city"],
            row["employer_address_state"],
            row["employer_address_zip"],
            row["employer_dba"],
            row["family_exemption"],
            row["medical_exemption"],
            format_date(row["exemption_commence_date"]),
            format_date(row["exemption_cease_date"]),
            format_datetime(row["updated_date"]),
        )
        employers_file.write(line)
    employers_file.close()

    return employers


def generate_employers(employer_count):
    """Generate employer rows"""
    employers = []

    # TODO use better id generators to match DOR format when available
    account_key_base = 1

    count = 0

    logger.info("Generating employer information ...")

    for _i in range(employer_count):
        # employer details
        account_key = str(account_key_base).rjust(11, "0")
        account_key_base += 1

        fein = fake.ssn(taxpayer_identification_number_type="EIN").replace("-", "")
        employer_name = fake.company()
        employer_address_street = fake.street_address()
        employer_address_city = fake.city()
        employer_address_state = fake.state_abbr()
        employer_address_zip = fake.zipcode_plus4().replace("-", "")
        employer_dba = employer_name
        if random.random() < 0.2:
            employer_dba = fake.company()
        family_exemption = random.choice("FT")
        medical_exemption = random.choice("FT")

        exemption_commence_date = NO_EXEMPTION_DATE
        exemption_cease_date = NO_EXEMPTION_DATE
        has_exemption = random.choice("FT")
        if has_exemption == "1":
            commence_days_before = random.randrange(1, 365)  # up to one year
            exemption_commence_date = get_date_days_before(datetime.today(), commence_days_before)
            exemption_cease_date = get_date_days_after(
                exemption_commence_date, 365
            )  # lasts for a year

        updated_date = get_date_days_before(datetime.today(), random.randrange(1, 90))

        if count > 0 and (count % 1000) == 0:
            logger.info("Generating employers, current count: %i", count)

        # Generate an employer row for each quarter
        # TODO randomize subset of quarters
        employer = {
            "account_key": account_key,
            "employer_name": employer_name,
            "fein": fein,
            "employer_address_street": employer_address_street,
            "employer_address_city": employer_address_city,
            "employer_address_state": employer_address_state,
            "employer_address_zip": employer_address_zip,
            "employer_dba": employer_dba,
            "family_exemption": family_exemption,
            "medical_exemption": medical_exemption,
            "exemption_commence_date": exemption_commence_date,
            "exemption_cease_date": exemption_cease_date,
            "updated_date": updated_date,
        }

        employers.append(employer)

        count += 1

    logger.info("Generated employers total: %i, Rows toal: %i", count, len(employers))

    return employers


def populate_employee_file(employee_count, employers, employees_file):
    """Generate employees rows, print rows to file"""
    employer_rows, employee_rows = generate_employee_employer_quarterly_wage_rows(
        employee_count, employers
    )

    for employer_row in employer_rows:
        line = "{}{}{!s}{:255}{}{}{}{}\n".format(
            "A",
            employer_row["account_key"],
            employer_row["filing_period"],
            employer_row["employer_name"],
            employer_row["employer_fein"],
            employer_row["amended_flag"],
            format_date(employer_row["received_date"]),
            format_datetime(employer_row["updated_date"]),
        )
        employees_file.write(line)

    for employee_row in employee_rows:
        line = "{}{}{!s}{:255}{:255}{}{}{}{:20.2f}{:20.2f}{:20.2f}{:20.2f}{:20.2f}{:20.2f}\n".format(
            "B",
            employee_row["account_key"],
            employee_row["filing_period"],
            employee_row["employee_first_name"],
            employee_row["employee_last_name"],
            employee_row["employee_ssn"],
            employee_row["independent_contractor"],
            employee_row["opt_in"],
            employee_row["employer_ytd_wages"],
            employee_row["employer_qtr_wages"],
            employee_row["employee_medical"],
            employee_row["employer_medical"],
            employee_row["employee_family"],
            employee_row["employer_family"],
        )
        employees_file.write(line)

    employees_file.close()


def generate_employee_employer_quarterly_wage_rows(employee_count, employees):
    """Generate employee and employer quarterly wage information rows"""
    employer_rows = []
    employee_rows = []

    employers_by_ein = pydash.group_by(employees, "fein")
    employer_eins = employers_by_ein.keys()

    logger.info("Generating employee rows ...")

    count = 0

    # for the number of employees we want to generate
    for _i in range(employee_count):
        # create employee details
        first_name = fake.first_name()
        last_name = fake.last_name()
        ssn = fake.invalid_ssn().replace("-", "")

        # randomly pick employers by random count
        employer_count = random.choice((1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 4))
        employer_eins_for_employee = random.sample(employer_eins, employer_count)

        if count > 0 and (count % 5000) == 0:
            logger.info("Generating employee rows, current employee count: %i", count)

        count += 1

        # for each employer randomly chosen for an employee
        for ein in employer_eins_for_employee:

            # fetch the chosen employer information
            employer = employers_by_ein[ein][0]

            # information about the employees classification with this employer
            independent_contractor = random.choice("YN")
            opt_in = random.choice("YN")

            # random quarter wage information to be used by all quarters
            qtr_wages = decimal.Decimal(random.randrange(6000000)) / 100
            contribution = Contribution(qtr_wages)

            # generate infomration for the last four quarters:
            for quarter in QUARTERS:

                # is the quarter information amended
                amended_flag = random.choice("FT")

                received_date = get_date_days_after(quarter.as_date(), random.randrange(1, 90))
                updated_date = get_date_days_before(datetime.today(), random.randrange(1, 90))

                # generate an employer specific quarter row
                employer_row = {
                    "account_key": employer["account_key"],
                    "filing_period": quarter,
                    "employer_name": employer["employer_name"],
                    "employer_fein": employer["fein"],
                    "amended_flag": amended_flag,
                    "received_date": received_date,
                    "updated_date": updated_date,
                }
                employer_rows.append(employer_row)

                # generate the employee details and quarter wage informatino row
                ytd_wages = quarter.quarter * qtr_wages

                employee = {
                    "account_key": employer["account_key"],
                    "filing_period": quarter,
                    "employee_first_name": first_name,
                    "employee_last_name": last_name,
                    "employee_ssn": ssn,
                    "independent_contractor": independent_contractor,
                    "opt_in": opt_in,
                    "employer_ytd_wages": ytd_wages,
                    "employer_qtr_wages": qtr_wages,
                    "employer_medical": contribution.employer_medical,
                    "employer_family": contribution.employer_family,
                    "employee_medical": contribution.employee_medical,
                    "employee_family": contribution.employee_family,
                }
                employee_rows.append(employee)

    logger.info(
        "Generated employees info - Employee count: %i, Employee Rows: %i, Employer Rows: %i",
        count,
        len(employee_rows),
        len(employer_rows),
    )

    return employer_rows, employee_rows


class Contribution:
    def __init__(self, qtr_wages):
        self.employer_medical = (decimal.Decimal(0.0062 * 0.6) * qtr_wages).quantize(TWOPLACES)
        self.employee_medical = (decimal.Decimal(0.0062 * 0.4) * qtr_wages).quantize(TWOPLACES)
        self.employer_family = (decimal.Decimal(0.0013 * 0.0) * qtr_wages).quantize(TWOPLACES)
        self.employee_family = (decimal.Decimal(0.0013 * 1.0) * qtr_wages).quantize(TWOPLACES)


QUARTERS = tuple(Quarter(2019, 2).series(4))

if __name__ == "__main__":
    main()
