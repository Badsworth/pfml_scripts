#!/usr/bin/env python3
#
# Generate fake DOR data.
#

import argparse
import decimal
import logging
import math
import random

import faker

import pydash

FORMAT = "%(levelname)s %(asctime)s [%(funcName)s] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)
random.seed(1111)
fake = faker.Faker()
fake.seed_instance(2222)
TWOPLACES = decimal.Decimal(10) ** -2

parser = argparse.ArgumentParser(description="Generate fake DOR data")
parser.add_argument(
    "--count", type=int, default=100, help="Number of individuals to generate data for"
)

employers_file = open("employers.txt", "w")
employees_file = open("employees.txt", "w")

EMPLOYEE_TO_EMPLOYER_MULTIPILER = 5


def main():
    args = parser.parse_args()
    employee_count = args.count

    # minimum of 4 employers
    employer_count = math.ceil(employee_count / EMPLOYEE_TO_EMPLOYER_MULTIPILER)
    if employer_count < 4:
        employer_count = 4

    employers = generate_and_print_employer_rows(employer_count)
    generate_and_print_employee_rows(employee_count, employers)

    logging.info("DONE: Please check employees.txt and employers.txt files in this folder.")


def generate_and_print_employer_rows(employer_count):
    """Generate employers, print rows to file"""
    employers_rows = generate_employers(employer_count)
    for row in employers_rows:
        line = "{} {!s} {} {:255} {:255} {:255} {} {} {} {}\n".format(
            row["record_type"],
            row["quarter"],
            row["fein"],
            row["employer_name"],
            row["employer_address"],
            row["employer_dba"],
            row["account_key"],
            row["return_key"],
            row["family_exemption"],
            row["medical_exemtion"],
        )
        employers_file.write(line)
    employers_file.close()

    return employers_rows


def generate_employers(employer_count):
    """Generate employer rows"""
    employers = []

    record_type = "A"

    # TODO use better id generators to match DOR format when available
    account_key_base = 1
    return_key_base = 101

    count = 0

    logging.info("Generating employer rows ...")

    for _i in range(employer_count):
        # employer details
        fein = fake.ssn(taxpayer_identification_number_type="EIN")
        employer_name = fake.company()
        employer_address = fake.address().replace("\n", ", ")
        employer_dba = employer_name
        if random.random() < 0.2:
            employer_dba = fake.company()
        family_exemption = random.choice("01")
        medical_exemtion = random.choice("01")

        account_key = str(account_key_base).rjust(11, "0")
        account_key_base += 1

        if count > 0 and (count % 1000) == 0:
            logging.info("Generating employers, current count: %i", count)

        # Generate an employer row for each quarter
        # TODO randomize subset of quarters
        for quarter in QUARTERS:
            return_key = str(return_key_base).rjust(11, "0")
            return_key_base += 1

            employer = {
                "record_type": record_type,
                "quarter": quarter,
                "fein": fein,
                "employer_name": employer_name,
                "employer_address": employer_address,
                "employer_dba": employer_dba,
                "account_key": account_key,
                "return_key": return_key,
                "family_exemption": family_exemption,
                "medical_exemtion": medical_exemtion,
            }

            employers.append(employer)

        count += 1

    logging.info("Generated employers total: %i, Rows toal: %i", count, len(employers))

    return employers


def generate_and_print_employee_rows(employee_count, employers):
    """Generate employees rows, print rows to file"""
    rows = generate_employees(employee_count, employers)
    for row in rows:
        line = "{} {} {} {} {:255} {:255} {} {} {:20.2f} {:20.2f} {:20.2f} {:20.2f} {:20.2f} {:20.2f}\n".format(
            row["record_type"],
            row["amended_flag"],
            row["return_key"],
            row["ssn"],
            row["first_name"],
            row["last_name"],
            row["independent_contractor"],
            row["opt_in"],
            row["ytd_wages"],
            row["qtr_wages"],
            row["employer_medical"],
            row["employee_medical"],
            row["employee_family"],
            row["employer_family"],
        )
        employees_file.write(line)
    employees_file.close()


def generate_employees(employee_count, employer_rows):
    """Generate employee rows for each randomly sampled employer row"""
    employee_rows = []

    employer_rows_by_ein = pydash.group_by(employer_rows, "fein")
    employer_eins = employer_rows_by_ein.keys()

    logging.info("Generating employee rows ...")

    count = 0

    for _i in range(employee_count):
        # employee details
        first_name = fake.first_name()
        last_name = fake.last_name()
        ssn = fake.invalid_ssn()

        employer_count = random.choice((1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 4))
        employer_eins_for_employee = random.sample(employer_eins, employer_count)

        if count > 0 and (count % 5000) == 0:
            logging.info("Generating employee rows, current employee count: %i", count)

        count += 1

        for ein in employer_eins_for_employee:

            amended_flag = random.choice("01")
            independent_contractor = random.choice("YN")
            opt_in = random.choice("YN")

            qtr_wages = decimal.Decimal(random.randrange(6000000)) / 100
            contribution = Contribution(qtr_wages)

            logging.debug(
                "Employee: %s %s, Empoyer: %s, Quarter Wages: %s",
                first_name,
                last_name,
                employer_rows_by_ein[ein][0]["employer_name"].strip(),
                qtr_wages,
            )

            for employer_row in employer_rows_by_ein[ein]:
                ytd_wages = employer_row["quarter"].quarter * qtr_wages

                employee = {
                    "record_type": "B",
                    "amended_flag": amended_flag,
                    "return_key": employer_row[
                        "return_key"
                    ],  # unique id for the employer + quarter
                    "ssn": ssn,
                    "first_name": first_name,
                    "last_name": last_name,
                    "independent_contractor": independent_contractor,
                    "opt_in": opt_in,
                    "ytd_wages": ytd_wages,
                    "qtr_wages": qtr_wages,
                    "employer_medical": contribution.employer_medical,
                    "employee_medical": contribution.employee_medical,
                    "employee_family": contribution.employee_family,
                    "employer_family": contribution.employer_family,
                }
                employee_rows.append(employee)

    logging.info("Generated employees total: %i, Rows total: %i", count, len(employee_rows))

    return employee_rows


class Contribution:
    def __init__(self, qtr_wages):
        self.employer_medical = (decimal.Decimal(0.0062 * 0.6) * qtr_wages).quantize(TWOPLACES)
        self.employee_medical = (decimal.Decimal(0.0062 * 0.4) * qtr_wages).quantize(TWOPLACES)
        self.employer_family = (decimal.Decimal(0.0013 * 0.0) * qtr_wages).quantize(TWOPLACES)
        self.employee_family = (decimal.Decimal(0.0013 * 1.0) * qtr_wages).quantize(TWOPLACES)


QUARTER_ENDS = ["0331", "0630", "0930", "1231"]


class Quarter:
    """Representation of a year / quarter (e.g. 2020-Q1)."""

    def __init__(self, year, quarter):
        if quarter not in (1, 2, 3, 4):
            raise ValueError("Invalid quarter, must be 1-4")
        self.year = year
        self.quarter = quarter
        self.end_date = QUARTER_ENDS[quarter - 1]

    def series(self, count):
        seq = []
        year = self.year
        quarter = self.quarter
        for _i in range(count):
            seq.append(Quarter(year, quarter))
            quarter = quarter + 1
            if quarter == 5:
                year = year + 1
                quarter = 1
        return seq

    def __repr__(self):
        return "Quarter(%i, %i)" % (self.year, self.quarter)

    def __str__(self):
        return "%i%s" % (self.year, self.end_date)


QUARTERS = Quarter(2019, 4).series(4)

if __name__ == "__main__":
    main()
