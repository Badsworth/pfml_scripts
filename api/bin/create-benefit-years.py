#!/usr/bin/env python3
#
# Generates benefit years data for a set of employees
#
# Run via `make create-benefit-years`.
# View options: `make create-benefit-years args="--help"`
#
from datetime import datetime, timedelta
from decimal import Decimal

import click
from factory.faker import faker

import massgov.pfml.db
from massgov.pfml.api.eligibility.benefit_year_dates import get_benefit_year_dates
from massgov.pfml.db.models.employees import BenefitYear
from massgov.pfml.db.models.factories import ApplicationFactory, EmployeeFactory, UserFactory

fake = faker.Faker()
db_session = massgov.pfml.db.init(sync_lookups=True)


def create_benefit_year_for_employee(benefit_year_dates, employee, total_wages):
    by = BenefitYear(
        **benefit_year_dates.dict(), employee_id=employee.employee_id, total_wages=total_wages
    )
    db_session.add(by)
    db_session.commit()


@click.command(help="Creates sample benefit year data for local API testing")
@click.option(
    "--number_of_employees",
    default=1,
    help="The number of unique employees that should have benefit years generated for them",
)
@click.option(
    "--claim_start_date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=str(datetime.today().strftime("%Y-%m-%d")),
    help="The date that the claim would start",
)
@click.option(
    "--create_previous_benefit_year",
    type=click.BOOL,
    default=True,
    help="Create a benefit year that predates claim_start_date",
)
def main(
    number_of_employees: int, claim_start_date: datetime, create_previous_benefit_year: bool
) -> None:
    user = UserFactory.create(consented_to_data_sharing=True)
    benefit_year_dates = get_benefit_year_dates(claim_start_date)
    previous_benefit_year_dates = get_benefit_year_dates(
        benefit_year_dates.start_date - timedelta(weeks=52)
    )
    total_wages = Decimal(1000)
    for _i in range(number_of_employees):
        employee = EmployeeFactory.create()
        # An application is required as this is the how we determine which employees
        # a particular user can see benefit years from
        # User -> Application -> TaxIdentifier -> Employee
        ApplicationFactory.create(user=user, tax_identifier=employee.tax_identifier)
        create_benefit_year_for_employee(benefit_year_dates, employee, total_wages)

        if create_previous_benefit_year:
            create_benefit_year_for_employee(previous_benefit_year_dates, employee, total_wages)

        click.secho(f"Created employee {employee.employee_id}", fg="cyan")

    click.secho(
        f"You can create a JWT for this user by running `make jwt auth_id={user.sub_id}`",
        fg="green",
    )


if __name__ == "__main__":
    main()
