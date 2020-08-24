#!/usr/bin/env python3
#
# Generate fake DOR data.
#

import argparse
import datetime as dt
import decimal
import os
import random
import sys
from datetime import datetime, timedelta

import faker

# Running this module as a python command from the top level /api directory seems
# to reset the path on load causing issues with local module imports.
# Workaround is to force set the path to run directory (top level api folder)
# See lambdas/dor/README.md for running details.
sys.path.insert(0, ".")  # noqa: E402

import massgov.pfml.util.logging as logging  # noqa: E402 isort:skip
from massgov.pfml.util.datetime.quarter import Quarter  # noqa: E402 isort:skip

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

EMPLOYER_COUNT_RANDOM_POOL = (1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 4)


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


def boolean_to_str(b):
    return "T" if b else "F"


# generator

file_extension = format_datetime(datetime.now())
employer_file_name = "DORDFMLEMP_" + file_extension
employee_file_name = "DORDFML_" + file_extension

EMPLOYER_TO_EMPLOYEE_RATIO = 15

NO_EXEMPTION_DATE = dt.date(9999, 12, 31)

# == entry point functions for command line ==


def main():
    """DOR Mock File Generator"""
    logging.init(__name__)

    args = parser.parse_args()
    employer_count = args.count

    output_folder = args.folder
    os.makedirs(output_folder, exist_ok=True)
    employer_file = open("{}/{}".format(output_folder, employer_file_name), "w")
    employee_file = open("{}/{}".format(output_folder, employee_file_name), "w")

    process(employer_count, employer_file, employee_file)

    employer_file.close()
    employee_file.close()


# == main processor ==


def process(
    employer_count,
    employer_file,
    employee_file,
    employer_count_random_pool=EMPLOYER_COUNT_RANDOM_POOL,
):
    # minimum of 4 employers
    employee_count = employer_count * EMPLOYER_TO_EMPLOYEE_RATIO
    if employer_count < 4:
        employer_count = 4

    employer_account_keys = process_employer_file(employer_count, employer_file, employee_file)
    process_employee_file(
        employee_count, employer_account_keys, employee_file, employer_count_random_pool
    )

    logger.info(
        "DONE: Please check files in generated_files folder: %s and %s",
        employer_file_name,
        employee_file_name,
    )


# == Employer ==


def process_employer_file(employer_count, employers_file, employees_file):
    """Generate employers, print rows to file"""
    employer_account_keys = []

    def on_employer(employer, employer_wage_rows):
        populate_employee_row(employer, employers_file)
        for employer_wage_row in employer_wage_rows:
            populate_employer_wage_row(employer_wage_row, employees_file)
        employer_account_keys.append(employer["account_key"])

    generate_employers(employer_count, on_employer)

    return employer_account_keys


def populate_employee_row(row, employers_file):
    line = "{}{:255}{}{:255}{:30}{}{}{:255}{}{}{}{}{}\n".format(
        row["account_key"],
        row["employer_name"],
        row["fein"],
        row["employer_address_street"],
        row["employer_address_city"],
        row["employer_address_state"],
        row["employer_address_zip"],
        row["employer_dba"],
        boolean_to_str(row["family_exemption"]),
        boolean_to_str(row["medical_exemption"]),
        format_date(row["exemption_commence_date"]),
        format_date(row["exemption_cease_date"]),
        format_datetime(row["updated_date"]),
    )
    employers_file.write(line)


def populate_employer_wage_row(employer_wage_row, employer_wage_row_file):
    line = "{}{}{!s}{:255}{}{}{}{}\n".format(
        "A",
        employer_wage_row["account_key"],
        employer_wage_row["filing_period"],
        employer_wage_row["employer_name"],
        employer_wage_row["employer_fein"],
        boolean_to_str(employer_wage_row["amended_flag"]),
        format_date(employer_wage_row["received_date"]),
        format_datetime(employer_wage_row["updated_date"]),
    )
    employer_wage_row_file.write(line)


def generate_employers(employer_count, on_employer):
    """Generate employer rows"""
    # TODO use better id generators to match DOR format when available
    account_key_base = 1

    count = 0

    logger.info("Generating employer information - count: %i", employer_count)

    for _i in range(employer_count):

        if count > 0 and (count % 1000) == 0:
            logger.info("Generating employers, current count: %i", count)

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
        family_exemption = random.choice((True, False))
        medical_exemption = random.choice((True, False))

        exemption_commence_date = NO_EXEMPTION_DATE
        exemption_cease_date = NO_EXEMPTION_DATE
        has_exemption = random.choice((True, False))
        if has_exemption:
            commence_days_before = random.randrange(1, 365)  # up to one year
            exemption_commence_date = get_date_days_before(datetime.today(), commence_days_before)
            exemption_cease_date = get_date_days_after(
                exemption_commence_date, 365
            )  # lasts for a year

        updated_date = get_date_days_before(datetime.today(), random.randrange(1, 90))

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

        employer_wage_rows = []

        for quarter in QUARTERS:
            # is the quarter information amended
            amended_flag = random.choice((True, False))

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
            employer_wage_rows.append(employer_row)

        on_employer(employer, employer_wage_rows)

        count += 1

    logger.info("Generated employers total: %i", count)


# == Employee ==


def process_employee_file(
    employee_count,
    employer_account_keys,
    employees_file,
    employer_count_random_pool=EMPLOYER_COUNT_RANDOM_POOL,
):
    """Generate employees rows, print rows to file"""

    def on_employee(employee):
        populate_employee_line(employee, employees_file)

    generate_employee_employer_quarterly_wage_rows(
        employee_count, employer_account_keys, on_employee, employer_count_random_pool
    )


def populate_employee_line(employee_wage_info, employees_file):
    line = "{}{}{!s}{:255}{:255}{}{}{}{:20.2f}{:20.2f}{:20.2f}{:20.2f}{:20.2f}{:20.2f}\n".format(
        "B",
        employee_wage_info["account_key"],
        employee_wage_info["filing_period"],
        employee_wage_info["employee_first_name"],
        employee_wage_info["employee_last_name"],
        employee_wage_info["employee_ssn"],
        boolean_to_str(employee_wage_info["independent_contractor"]),
        boolean_to_str(employee_wage_info["opt_in"]),
        employee_wage_info["employee_ytd_wages"],
        employee_wage_info["employee_qtr_wages"],
        employee_wage_info["employee_medical"],
        employee_wage_info["employer_medical"],
        employee_wage_info["employee_family"],
        employee_wage_info["employer_family"],
    )
    employees_file.write(line)


def generate_employee_employer_quarterly_wage_rows(
    employee_count,
    employer_account_keys,
    on_employee,
    employer_count_random_pool=EMPLOYER_COUNT_RANDOM_POOL,
):
    """Generate employee and employer quarterly wage information rows"""

    logger.info("Generating employee rows ...")

    count = 0

    # for the number of employees we want to generate
    for _i in range(employee_count):
        # create employee details
        first_name = fake.first_name()
        last_name = fake.last_name()
        ssn = fake.ssn().replace("-", "")

        # randomly pick employers by random count
        employer_count = random.choice(employer_count_random_pool)
        employer_account_keys_for_employee = random.sample(employer_account_keys, employer_count)

        if count > 0 and (count % 1000) == 0:
            logger.info("Generating employee rows, current employee count: %i", count)

        count += 1

        # for each employer account key randomly chosen for an employee
        for account_key in employer_account_keys_for_employee:

            # information about the employees classification with this employer
            independent_contractor = random.choice((True, False))
            opt_in = random.choice((True, False))

            # random quarter wage information to be used by all quarters
            qtr_wages = decimal.Decimal(random.randrange(6000000)) / 100
            contribution = Contribution(qtr_wages)

            # generate infomration for the last four quarters:
            for quarter in QUARTERS:
                # generate the employee details and quarter wage informatino row
                ytd_wages = quarter.quarter * qtr_wages

                employee = {
                    "account_key": account_key,
                    "filing_period": quarter,
                    "employee_first_name": first_name,
                    "employee_last_name": last_name,
                    "employee_ssn": ssn,
                    "independent_contractor": independent_contractor,
                    "opt_in": opt_in,
                    "employee_ytd_wages": ytd_wages,
                    "employee_qtr_wages": qtr_wages,
                    "employer_medical": contribution.employer_medical,
                    "employer_family": contribution.employer_family,
                    "employee_medical": contribution.employee_medical,
                    "employee_family": contribution.employee_family,
                }

                on_employee(employee)

    logger.info("Generated employees info - Employee count: %i", count)


class Contribution:
    def __init__(self, qtr_wages):
        self.employer_medical = (decimal.Decimal(0.0062 * 0.6) * qtr_wages).quantize(TWOPLACES)
        self.employee_medical = (decimal.Decimal(0.0062 * 0.4) * qtr_wages).quantize(TWOPLACES)
        self.employer_family = (decimal.Decimal(0.0013 * 0.0) * qtr_wages).quantize(TWOPLACES)
        self.employee_family = (decimal.Decimal(0.0013 * 1.0) * qtr_wages).quantize(TWOPLACES)


QUARTERS = tuple(Quarter(2019, 2).series(4))

if __name__ == "__main__":
    main()
