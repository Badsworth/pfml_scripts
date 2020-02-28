#!/usr/bin/env python3
#
# Generate fake DOR data.
#

import argparse
import decimal
import logging
import random
import faker

FORMAT = "%(levelname)s %(asctime)s [%(funcName)s] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)
random.seed(1111)
fake = faker.Faker()
fake.seed_instance(2222)
TWOPLACES = decimal.Decimal(10) ** -2

parser = argparse.ArgumentParser(description="Generate fake DOR data")
parser.add_argument("--count", type=int, default=100,
                    help="Number of individuals to generate data for")


def main():
    args = parser.parse_args()
    generate_and_print(args.count)


def generate_and_print(total):
    """Generate and print data for the given number of individuals."""
    person_count = 0
    row_count = 0
    for i in range(total):
        rows = generate_rows()
        for row in rows:
            print("\t".join(map(str, row)))
        person_count += 1
        row_count += len(rows)
        if (person_count % 10000) == 0 or person_count == total:
            logging.info("generated fake individuals %i/%i (%.1f%%), rows %i",
                         person_count, total, 100.0 * person_count / total,
                         row_count)


def generate_rows():
    """Generate a batch of rows for a single person."""
    rows = []

    ssn = fake.invalid_ssn()
    first_name = fake.first_name()
    last_name = fake.last_name()

    employer_count = random.choice((1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 4, 5, 6))
    for employer_index in range(employer_count):
        independent_contractor = random.choice("YN")
        opt_in = random.choice("YN")
        fein = fake.ssn(taxpayer_identification_number_type="EIN")
        company_name = fake.company()
        dba = company_name
        if random.random() < 0.2:
            dba = fake.company()

        start_quarter = random.choice(QUARTERS)
        quarters = start_quarter.series(random.randint(1, 5))
        ytd_wages = 0
        qtr_wages = decimal.Decimal(random.randrange(6000000)) / 100
        contribution = Contribution(qtr_wages)
        fixed_wages = random.choice((True, False))
        for quarter in quarters:
            if quarter.quarter == 1:
                ytd_wages = 0
            if not fixed_wages:
                qtr_wages = decimal.Decimal(random.randrange(5000000)) / 100
                contribution = Contribution(qtr_wages)
            ytd_wages += qtr_wages
            row = (quarter, ssn,
                   first_name, last_name,
                   independent_contractor,
                   opt_in,
                   fein, dba,
                   ytd_wages, qtr_wages,
                   contribution.employer_medical,
                   contribution.employee_medical,
                   contribution.employer_family,
                   contribution.employee_family)
            rows.append(row)

    return rows


class Contribution:
    def __init__(this, qtr_wages):
        this.employer_medical = (decimal.Decimal(0.0062 * 0.6) * qtr_wages).quantize(TWOPLACES)
        this.employee_medical = (decimal.Decimal(0.0062 * 0.4) * qtr_wages).quantize(TWOPLACES)
        this.employer_family = (decimal.Decimal(0.0013 * 0.0) * qtr_wages).quantize(TWOPLACES)
        this.employee_family = (decimal.Decimal(0.0013 * 1.0) * qtr_wages).quantize(TWOPLACES)


class Quarter:
    """Representation of a year / quarter (e.g. 2020-Q1)."""
    def __init__(this, year, quarter):
        if quarter not in (1, 2, 3, 4):
            raise ValueError("Invalid quarter, must be 1-4")
        this.year = year
        this.quarter = quarter

    def series(this, count):
        seq = []
        year = this.year
        quarter = this.quarter
        for i in range(count):
            seq.append(Quarter(year, quarter))
            quarter = quarter + 1
            if quarter == 5:
                year = year + 1
                quarter = 1
        return seq

    def __repr__(this):
        return "Quarter(%i, %i)" % (this.year, this.quarter)

    def __str__(this):
        return "%iQ%i" % (this.year, this.quarter)


QUARTERS = Quarter(2019, 4).series(4)


if __name__ == "__main__":
    main()
