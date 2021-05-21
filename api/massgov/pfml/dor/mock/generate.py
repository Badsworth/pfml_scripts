#!/usr/bin/env python3
#
# Generate fake DOR data.
#
# Run via `make dor-generate`.
#

import argparse
import datetime as dt
import decimal
import math
import os
import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import faker

import massgov.pfml.util.files
import massgov.pfml.util.logging
from massgov.pfml.util.datetime.quarter import Quarter
from massgov.pfml.util.sentry import initialize_sentry

logger = massgov.pfml.util.logging.get_logger("massgov.pfml.dor.mock.generate")

fake = faker.Faker()

# To make the output of this script identical each time it runs, we use this date as the base of
# various generated dates.
SIMULATED_TODAY = datetime(2020, 12, 1, 23, 0, 0)

TWOPLACES = decimal.Decimal(10) ** -2


def fein_or_ssn(arg):
    value = int(arg)
    if value < 100000000:
        raise argparse.ArgumentTypeError("must be at least 100000000")
    return value


parser = argparse.ArgumentParser(description="Generate fake DOR data")
parser.add_argument(
    "--count", type=int, default=100, help="Number of employers to generate data for"
)
parser.add_argument(
    "--folder", type=str, default="generated_files", help="Output folder for generated files"
)
parser.add_argument("--update", action="store_true", help="Generate daily update files")
parser.add_argument("--fein", type=fein_or_ssn, default=100000000, help="Base FEIN for employers")
parser.add_argument("--ssn", type=fein_or_ssn, default=250000000, help="Base SSN for employees")

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
    initialize_sentry()
    massgov.pfml.util.logging.init(__name__)

    args = parser.parse_args()
    employer_count = args.count
    update_mode = args.update

    output_folder = args.folder
    if not output_folder.startswith("s3:"):
        os.makedirs(output_folder, exist_ok=True)

    logger.info(
        "args: count %i, fein base %s %s, ssn base %s %s",
        args.count,
        str(args.fein)[:2],
        str(args.fein)[2:],
        str(args.ssn)[:3],
        str(args.ssn)[3:],
    )

    employer_path = "{}/{}".format(output_folder, employer_file_name)
    employee_path = "{}/{}".format(output_folder, employee_file_name)

    employer_file = massgov.pfml.util.files.open_stream(employer_path, "w")
    employee_file = massgov.pfml.util.files.open_stream(employee_path, "w")

    generate(employer_count, employer_file, employee_file, update_mode, args.fein, args.ssn)

    employer_file.close()
    employee_file.close()

    logger.info(
        "DONE: output files %s, %s", employer_path, employee_path,
    )


# == main processor ==


def generate(
    employer_count,
    employer_file,
    employee_file,
    update_mode=False,
    fein_base=100000000,
    ssn_base=250000000,
):
    if employer_count <= 0 or employer_count % 100 != 0:
        raise RuntimeError("employer_count must be a multiple of 100")

    # Generate in chunks of 100 employers, followed by their employees. This ensures that whatever
    # count we generate, employer M never changes and employee N never changes (including which
    # employers each employee works for).
    #
    # (If we generated all employers then all employees, the possible employer_account_keys for an
    # employee would change depending on the employer_count.)
    employee_generate_id = 1
    for chunk in range(0, employer_count, 100):
        # Generate employers
        employers = tuple(generate_employers(chunk + 1, 100, update_mode, fein_base))

        total_employees = sum(employer["number_of_employees"] for employer in employers)

        # Assign employees to employers according to number of employees
        employee_ids = tuple(range(employee_generate_id, employee_generate_id + total_employees))
        random.seed(chunk)
        employee_employers: Dict[int, List[Dict[str, Any]]] = {}
        for employer in employers:
            employer_employee_ids = random.sample(employee_ids, employer["number_of_employees"])
            for employee_id in employer_employee_ids:
                if employee_id not in employee_employers:
                    employee_employers[employee_id] = []
                employee_employers[employee_id].append(employer)

        # Generate employee rows
        employee_wage_rows: List[Dict[str, Any]] = []
        for employee_id, employers_for_employee in employee_employers.items():
            employee_wage_rows += tuple(
                generate_single_employee(employee_id, employers_for_employee, update_mode, ssn_base)
            )

        logger.info(
            "chunk %i: %i employers, %i employees", chunk, len(employers), len(employee_employers)
        )

        # Write files
        write_employer_file(employers, employer_file)

        for employer in employers:
            for employer_wage_row in generate_employer_wage_rows(employer):
                write_employer_wage_row(employer_wage_row, employee_file)
        for row in employee_wage_rows:
            write_employee_line(row, employee_file)

        employee_generate_id += total_employees


def write_employer_file(employers, employers_file):
    """Write employer rows to file"""
    for employer in employers:
        write_employer_row(employer, employers_file)


def write_employer_row(row, employers_file):
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
    line = "{}{}{!s}{:255}{:14}{}{:14}{:20.2f}{}{}\n".format(
        "A",
        employer_wage_row["account_key"],
        employer_wage_row["filing_period"],
        employer_wage_row["employer_name"],
        employer_wage_row["employer_fein"],
        boolean_to_str(employer_wage_row["amended_flag"]),
        employer_wage_row["pfm_account_id"],
        employer_wage_row["total_pfml_contribution"],
        format_date(employer_wage_row["received_date"]),
        format_datetime(employer_wage_row["updated_date"]),
    )
    employer_wage_row_file.write(line)


def generate_employers(base_id, employer_count, update_mode=False, fein_base=100000000):
    """Generate employer rows"""
    for index in range(employer_count):
        yield generate_single_employer(base_id + index, update_mode, fein_base)


def generate_single_employer(employer_generate_id, update_mode=False, fein_base=100000000):
    """Generate a single employer.

    This is intended to always generate the same fake values for a given employer_generate_id.
    """
    fake.seed_instance(employer_generate_id)
    random.seed(employer_generate_id)

    # employer details
    fein = str(fein_base + employer_generate_id)
    account_key = fein.rjust(11, "4")

    # occasionally generates a duplicate, but that's realistic as it happens in the real data
    employer_name = fake.company()

    if employer_generate_id % 500 == 0:
        employer_name += " “Company”"  # add some Unicode characters

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

    # random.seed(create_seed)  # keep number of employees the same
    number_of_employees = math.floor(random.paretovariate(1))

    if update_mode:
        if random.random() < 0.1:
            employer_name = fake.company()

        employer_dba = employer_name
        if random.random() < 0.3:
            employer_dba = fake.company()

            (
                employer_address_country,
                employer_address_state,
                employer_address_city,
                employer_address_street,
                employer_address_zip,
            ) = generate_fake_address()

            updated_date = get_date_days_after(updated_date, 1)

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
        "number_of_employees": number_of_employees,
    }

    return employer


def generate_employer_wage_rows(employer):
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
            "pfm_account_id": employer["fein"],
            "total_pfml_contribution": decimal.Decimal(random.randrange(6000000)) / 100,
            "received_date": received_date,
            "updated_date": updated_date,
        }
        employer_wage_rows.append(employer_row)

    return employer_wage_rows


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


def generate_single_employee(
    employee_generate_id, employers, update_mode=False, ssn_base=250000000
):
    """Generate a single employee.

    This is intended to always generate the same fake values for a given employee_generate_id.
    """
    fake.seed_instance(employee_generate_id)
    random.seed(employee_generate_id)

    ssn = str(ssn_base + employee_generate_id)

    first_name = fake.first_name()
    last_name = fake.last_name()

    if update_mode and random.random() < 0.5:
        last_name = fake.last_name()

    # for each employer randomly chosen for this employee
    for employer in employers:
        account_key = employer["account_key"]

        # information about the employees classification with this employer
        independent_contractor = fake.boolean()
        opt_in = fake.boolean()

        wage_change_random_pool: Tuple[int, ...] = WAGE_CHANGE_RANDOM_POOL
        quarters: Tuple[Quarter, ...] = ()

        if (employee_generate_id % 100) <= 5:
            # Special scenario 1: one quarter, wage $4000 to $5000
            # Financial eligibility: when 2 employers, fails 30x rule
            qtr_wages = decimal.Decimal(4000 + random.randrange(1000))  # initial quarterly wage
            quarters = (Quarter(2020, 4),)

        elif (employee_generate_id % 100) <= 10:
            # Special scenario 2: two quarters, wages $5000 and $10000
            # Financial eligibility: fails 30x rule
            qtr_wages = decimal.Decimal(5000)  # initial quarterly wage
            quarters = (
                Quarter(2020, 4),
                Quarter(2021, 1),
            )
            wage_change_random_pool = (10000 - 5000,)

        elif (employee_generate_id % 100) <= 13:
            # Special scenario 3: two quarters, wages $2000 and $2000
            # Financial eligibility: when 1 employer, not eligible / when 2 employers, eligible
            qtr_wages = decimal.Decimal(2000)  # initial quarterly wage
            quarters = (
                Quarter(2020, 4),
                Quarter(2021, 1),
            )
            wage_change_random_pool = (0,)

        elif (employee_generate_id % 100) <= 15:
            # Special scenario 4: two quarters, wages $5000 and $21000
            # Financial eligibility: eligible in 2021, but not in 2022 (due to 2021 max benefit)
            qtr_wages = decimal.Decimal(5000)  # initial quarterly wage
            quarters = (
                Quarter(2021, 3),
                Quarter(2021, 4),
            )
            wage_change_random_pool = (21000 - 5000,)

        else:
            # General random scenario
            qtr_wages = decimal.Decimal(random.randrange(6000000)) / 100  # initial quarterly wage

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

            if not update_mode or (random.random() < 0.1):
                yield employee

            qtr_wages += random.choice(wage_change_random_pool)
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
