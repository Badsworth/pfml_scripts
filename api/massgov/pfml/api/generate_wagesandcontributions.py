#!/usr/bin/env python3
#
# Generate fake wage_and_contributions record, if one does not exist for the provided employer_fein and employee_ssn combo.
#
# Run via `make generate-wage`.
#

import argparse
import datetime
import random
from decimal import Decimal
from uuid import UUID

from factory.faker import faker

import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    Employee,
    Employer,
    TaxIdentifier,
    WagesAndContributions,
)
from massgov.pfml.types import Fein, TaxId

logger = massgov.pfml.util.logging.get_logger("massgov.pfml.api.generate_wage")
parser = argparse.ArgumentParser(description="Generate fake WagesAndContributions data")
parser.add_argument("--employer_fein", type=str, help="EIN of employer")
parser.add_argument("--employee_ssn", type=str, help="SSN of employee")

_faker = faker.Faker()


def get_or_create_employer(employer_fein: Fein, db_session: db.Session) -> Employer:

    employer = (
        db_session.query(Employer).filter(Employer.employer_fein == employer_fein).one_or_none()
    )

    if employer:
        logger.info(f"Found employer {employer.employer_id}")
    else:
        employer = Employer(employer_fein=employer_fein, employer_dba="Acme Co")

    return employer


def get_or_create_tax_identifier(employee_ssn: TaxId, db_session: db.Session) -> TaxIdentifier:

    tax_identifier = (
        db_session.query(TaxIdentifier)
        .filter(TaxIdentifier.tax_identifier == employee_ssn)
        .one_or_none()
    )

    if tax_identifier:
        logger.info(f"Found tax_identifier {tax_identifier.tax_identifier_id}")
    else:
        tax_identifier = TaxIdentifier(tax_identifier=employee_ssn)

    db_session.add(tax_identifier)
    db_session.commit()  # generate the tax_identifier_id if not already generated

    return tax_identifier


def get_or_create_employee(tax_identifier_id: UUID, db_session: db.Session) -> Employee:

    employee = (
        db_session.query(Employee)
        .filter(Employee.tax_identifier_id == tax_identifier_id)
        .one_or_none()
    )

    if employee:
        logger.info(f"Found employee {employee.employee_id}")
    else:
        employee = Employee(
            email_address=_faker.email(),
            first_name=_faker.first_name(),
            last_name=_faker.last_name(),
            tax_identifier_id=tax_identifier_id,
        )

    db_session.add(employee)

    return employee


def get_or_create_wages_and_contributions(
    employee: Employee, employer: Employer, db_session: db.Session
) -> None:

    wages_and_contributions = (
        db_session.query(WagesAndContributions)
        .filter(
            WagesAndContributions.employer_id == employer.employer_id,
            WagesAndContributions.employee_id == employee.employee_id,
        )
        .first()
    )

    if wages_and_contributions:
        logger.info("User is set up")
    else:
        wages_and_contributions = WagesAndContributions(
            employer_id=employer.employer_id,
            employee_id=employee.employee_id,
            account_key="44100000157",
            filing_period=datetime.datetime.now().date(),
            is_independent_contractor=False,
            is_opted_in=True,
            employer_med_contribution=Decimal(round(random.uniform(0, 50000), 2)),
            employer_fam_contribution=Decimal(round(random.uniform(0, 50000), 2)),
            employee_fam_contribution=Decimal(round(random.uniform(0, 50000), 2)),
            employee_med_contribution=Decimal(round(random.uniform(0, 50000), 2)),
            employee_qtr_wages=Decimal(round(random.uniform(0, 50000), 2)),
            employee_ytd_wages=Decimal(round(random.uniform(0, 50000), 2)),
        )

        db_session.add(wages_and_contributions)

    return


def generate(employer_fein: Fein, employee_ssn: TaxId, db_session: db.Session) -> None:
    """
        Generates a WagesAndContributions record for the provided employeer_fein and employee_ssn combo
        If Employer, Employee, or TaxIdentifier records do not exist, generates a record using faker
        Also sets Employer's fineos_employer_id to 1 to bypass validation
    """
    employer = get_or_create_employer(employer_fein, db_session)
    employer.fineos_employer_id = 1
    db_session.add(employer)

    tax_identifier = get_or_create_tax_identifier(employee_ssn, db_session)

    employee = get_or_create_employee(tax_identifier.tax_identifier_id, db_session)

    get_or_create_wages_and_contributions(employee, employer, db_session)

    db_session.commit()


def main():
    """WagesAndContributions generator"""
    massgov.pfml.util.logging.init(__name__)

    args = parser.parse_args()

    employer_fein = args.employer_fein
    employee_ssn = args.employee_ssn

    if not employer_fein:
        raise ValueError("employer_fein required")
    if not employee_ssn:
        raise ValueError("employee_ssn required")

    db_session = db.init()

    generate(employer_fein, employee_ssn, db_session)


if __name__ == "__main__":
    main()
