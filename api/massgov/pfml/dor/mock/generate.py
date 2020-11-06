#!/usr/bin/env python3
#
# Generate fake DOR data.
#
# Run via `make dor-generate`.
#

import argparse
import datetime as dt
import decimal
import os
import random
import string
from datetime import datetime, timedelta

import faker

import massgov.pfml.util.logging
from massgov.pfml.util.datetime.quarter import Quarter

logger = massgov.pfml.util.logging.get_logger("massgov.pfml.dor.mock.generate")

fake = faker.Faker()

# To make the output of this script identical each time it runs, we use this date as the base of
# various generated dates.
SIMULATED_TODAY = datetime(2020, 12, 1, 23, 0, 0)

TWOPLACES = decimal.Decimal(10) ** -2

parser = argparse.ArgumentParser(description="Generate fake DOR data")
parser.add_argument(
    "--count", type=int, default=100, help="Number of employers to generate data for"
)
parser.add_argument(
    "--folder", type=str, default="generated_files", help="Output folder for generated files"
)

EMPLOYER_COUNT_RANDOM_POOL = (1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 4)
WAGE_CHANGE_RANDOM_POOL = (0, 0, 0, 0, 1000, 2500, 4400, 7800, -1200, -3500)


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
    massgov.pfml.util.logging.init(__name__)

    args = parser.parse_args()
    employer_count = args.count

    output_folder = args.folder
    os.makedirs(output_folder, exist_ok=True)
    employer_file = open("{}/{}".format(output_folder, employer_file_name), "w")
    employee_file = open("{}/{}".format(output_folder, employee_file_name), "w")

    generate(employer_count, employer_file, employee_file)

    employer_file.close()
    employee_file.close()


# == main processor ==


def generate(
    employer_count,
    employer_file,
    employee_file,
    employer_count_random_pool=EMPLOYER_COUNT_RANDOM_POOL,
):
    if employer_count <= 0 or employer_count % 100 != 0:
        raise RuntimeError("employer_count must be a multiple of 100")

    # Generate in chunks of 100 employers, followed by their employees. This ensures that whatever
    # count we generate, employer M never changes and employee N never changes (including which
    # employers each employee works for).
    #
    # (If we generated all employers then all employees, the possible employer_account_keys for an
    # employee would change depending on the employer_count.)
    for chunk in range(0, employer_count, 100):
        employer_account_keys = generate_employer_file(chunk + 1, 100, employer_file, employee_file)
        generate_employee_file(
            chunk * EMPLOYER_TO_EMPLOYEE_RATIO + 1,
            100 * EMPLOYER_TO_EMPLOYEE_RATIO,
            employer_account_keys,
            employee_file,
            employer_count_random_pool,
        )

    logger.info(
        "DONE: Please check files in generated_files folder: %s and %s",
        employer_file_name,
        employee_file_name,
    )


# == Employer ==


def generate_employer_file(base_id, employer_count, employers_file, employees_file):
    """Generate employers, print rows to file"""
    employer_account_keys = []

    for employer, employer_wage_rows in generate_employers(base_id, employer_count):
        write_employee_row(employer, employers_file)
        for employer_wage_row in employer_wage_rows:
            write_employer_wage_row(employer_wage_row, employees_file)
        employer_account_keys.append(employer["account_key"])

    return employer_account_keys


def write_employee_row(row, employers_file):
    line = "{}{:255}{:14}{:255}{:30}{}{}{}{:255}{}{}{}{}{}\n".format(
        row["account_key"],
        row["employer_name"],
        row["fein"],
        row["employer_address_street"],
        row["employer_address_city"],
        row["employer_address_state"],
        row["employer_address_zip"],
        row["employer_address_country"],
        row["employer_dba"],
        boolean_to_str(row["family_exemption"]),
        boolean_to_str(row["medical_exemption"]),
        format_date(row["exemption_commence_date"]),
        format_date(row["exemption_cease_date"]),
        format_datetime(row["updated_date"]),
    )
    employers_file.write(line)


def write_employer_wage_row(employer_wage_row, employer_wage_row_file):
    line = "{}{}{!s}{:255}{:14}{}{}{}\n".format(
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


def generate_employers(base_id, employer_count):
    """Generate employer rows"""
    # TODO use better id generators to match DOR format when available
    count = 0

    logger.info("Generating employer information - count: %i", employer_count)

    for index in range(employer_count):
        if count > 0 and (count % 1000) == 0:
            logger.info("Generating employers, current count: %i", count)

        yield generate_single_employer(base_id + index)

        count += 1

    logger.info("Generated employers total: %i", count)


def generate_single_employer(employer_generate_id):
    """Generate a single employer.

    This is intended to always generate the same fake values for a given employer_generate_id.
    """
    fake.seed_instance(employer_generate_id)
    random.seed(employer_generate_id)

    # employer details
    account_key = str(employer_generate_id).rjust(11, "0")
    fein = str(100000000 + employer_generate_id)

    employer_name = fake.company()

    (
        employer_address_country,
        employer_address_state,
        employer_address_city,
        employer_address_street,
        employer_address_zip,
    ) = generate_fake_address()

    employer_dba = employer_name
    if random.random() < 0.2:
        employer_dba = fake.company()

    family_exemption = fake.boolean()
    medical_exemption = fake.boolean()
    exemption_commence_date = NO_EXEMPTION_DATE
    exemption_cease_date = NO_EXEMPTION_DATE
    has_exemption = fake.boolean()
    if has_exemption:
        commence_days_before = random.randrange(1, 365)  # up to one year
        exemption_commence_date = get_date_days_before(SIMULATED_TODAY, commence_days_before)
        exemption_cease_date = get_date_days_after(exemption_commence_date, 365)  # lasts for a year

    updated_date = get_date_days_before(SIMULATED_TODAY, random.randrange(1, 90))

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
        "employer_address_country": employer_address_country,
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
        amended_flag = fake.boolean()

        received_date = get_date_days_after(quarter.as_date(), random.randrange(1, 90))
        updated_date = get_date_days_before(SIMULATED_TODAY, random.randrange(1, 90))

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

    return employer, employer_wage_rows


def generate_fake_address():
    """Generate a fake address."""
    street = fake.street_address()
    city = fake.city()
    if random.random() < 0.05:
        # Small chance of a non-USA address.
        country = fake.country_code(representation="alpha-3")
        state = fake.lexify("??", letters=string.ascii_uppercase)
        postal_code = fake.bothify("??## #?? ", letters=string.ascii_uppercase)
    else:
        country = "USA"
        state = fake.state_abbr()
        postal_code = fake.zipcode_plus4().replace("-", "")

    return country, state, city, street, postal_code


# == Employee ==


def generate_employee_file(
    base_id,
    employee_count,
    employer_account_keys,
    employees_file,
    employer_count_random_pool=EMPLOYER_COUNT_RANDOM_POOL,
):
    """Generate employees rows, print rows to file"""
    for employee in generate_employee_employer_quarterly_wage_rows(
        base_id, employee_count, employer_account_keys, employer_count_random_pool
    ):
        write_employee_line(employee, employees_file)


def write_employee_line(employee_wage_info, employees_file):
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
    base_id,
    employee_count,
    employer_account_keys,
    employer_count_random_pool=EMPLOYER_COUNT_RANDOM_POOL,
):
    """Generate employee and employer quarterly wage information rows"""

    logger.info("Generating employee rows ...")

    count = 0

    # for the number of employees we want to generate
    for index in range(employee_count):
        yield from generate_single_employee(
            base_id + index, employer_account_keys, employer_count_random_pool
        )

        count += 1
        if count > 0 and (count % 1000) == 0:
            logger.info("Generating employee rows, current employee count: %i", count)

    logger.info("Generated employees info - Employee count: %i", count)


def generate_single_employee(
    employee_generate_id, employer_account_keys, employer_count_random_pool
):
    """Generate a single employee.

    This is intended to always generate the same fake values for a given employee_generate_id.
    """
    fake.seed_instance(employee_generate_id)
    random.seed(employee_generate_id)

    ssn = str(250000000 + employee_generate_id)

    first_name = fake.first_name()
    last_name = fake.last_name()

    # randomly pick employers by random count
    employer_count = random.choice(employer_count_random_pool)
    employer_account_keys_for_employee = random.sample(employer_account_keys, employer_count)

    # for each employer account key randomly chosen for an employee
    for account_key in employer_account_keys_for_employee:

        # information about the employees classification with this employer
        independent_contractor = fake.boolean()
        opt_in = fake.boolean()

        # initial quarterly wage
        qtr_wages = decimal.Decimal(random.randrange(6000000)) / 100

        # which quarters to generate?
        start_quarter = random.choice(QUARTERS)
        quarters = start_quarter.series(random.randint(1, 8))

        # generate information for the selected quarters:
        ytd_wages = decimal.Decimal(0)
        for quarter in quarters:
            # generate the employee details and quarter wage information row
            if quarter.quarter == 1:
                ytd_wages = decimal.Decimal(0)
            ytd_wages += qtr_wages
            contribution = Contribution(qtr_wages)

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

            yield employee

            qtr_wages += random.choice(WAGE_CHANGE_RANDOM_POOL)
            if qtr_wages <= 0:
                qtr_wages = decimal.Decimal(1)


class Contribution:
    def __init__(self, qtr_wages):
        self.employer_medical = (decimal.Decimal(0.0062 * 0.6) * qtr_wages).quantize(TWOPLACES)
        self.employee_medical = (decimal.Decimal(0.0062 * 0.4) * qtr_wages).quantize(TWOPLACES)
        self.employer_family = (decimal.Decimal(0.0013 * 0.0) * qtr_wages).quantize(TWOPLACES)
        self.employee_family = (decimal.Decimal(0.0013 * 1.0) * qtr_wages).quantize(TWOPLACES)


QUARTERS = tuple(Quarter(2019, 2).series(4))

if __name__ == "__main__":
    main()
