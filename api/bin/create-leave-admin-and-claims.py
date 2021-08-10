#!/usr/bin/env python3
#
# Generate a verified leave admin user and generate claims for the organization
#
# Run via `make create-leave-admin-and-claims`.
# View options: `make create-leave-admin-and-claims args="--help"`
#
import random

import click
from factory.faker import faker

import massgov.pfml.db
from massgov.pfml.db.models.employees import Role, UserLeaveAdministrator
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployerOnlyDORDataFactory,
    ManagedRequirementFactory,
    UserFactory,
)
from massgov.pfml.db.models.verifications import Verification, VerificationType

fake = faker.Faker()
db_session = massgov.pfml.db.init(sync_lookups=True)


@click.command()
@click.option("--total_claims", default=10, help="Number of claims to create.")
def main(total_claims: int) -> None:
    user = UserFactory.create(consented_to_data_sharing=True, roles=[Role.EMPLOYER])
    employer = EmployerOnlyDORDataFactory.create()
    verification = Verification(verification_type_id=VerificationType.MANUAL.verification_type_id)
    user_leave_admin = UserLeaveAdministrator(
        user_id=user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id=fake.uuid4(),
        verification=verification,
    )

    # Create some claims so we have data to read and write to
    for _ in range(total_claims):
        claim = ClaimFactory.create(
            employer_id=employer.employer_id,
            fineos_absence_id=f"NTN-{fake.unique.random_int()}-ABS-01",
            fineos_absence_status_id=random.randint(1, 7),
        )
        managed_requirement = ManagedRequirementFactory.create(
            claim=claim,
            fineos_managed_requirement_id=fake.unique.random_int(),
            follow_up_date=fake.date_time_between(start_date="-1d", end_date="+11d"),
            managed_requirement_status_id=random.randint(1, 3),
        )
        click.secho(
            f"Created Claim {claim.claim_id}, and ManagedRequirement {managed_requirement.managed_requirement_id}",
            fg="cyan",
        )

    db_session.add(verification)
    db_session.add(user_leave_admin)
    db_session.commit()

    click.secho(f"Created Employer {employer.employer_id}", fg="cyan")
    click.secho(f"Created User {user.user_id}", fg="cyan")

    click.secho(
        f"You can create a JWT for this user by running `make jwt auth_id={user.sub_id}`",
        fg="green",
    )


if __name__ == "__main__":
    main()
