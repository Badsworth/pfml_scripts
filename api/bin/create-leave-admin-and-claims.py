#!/usr/bin/env python3
#
# Generate a verified leave admin user and generate claims for the organization
#
# Run via `make create-leave-admin-and-claims`.
#
import pprint

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


def print_record(name, record):
    print(f"\n{name}")
    pprint.pp({k: v for k, v in record.__dict__.items() if not k.startswith("_sa")})


def main():
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
    for _ in range(10):
        claim = ClaimFactory.create(
            employer_id=employer.employer_id,
            fineos_absence_id=f"NTN-{fake.unique.random_int()}-ABS-01",
        )
        ManagedRequirementFactory.create(claim=claim)

    db_session.add(verification)
    db_session.add(user_leave_admin)
    db_session.commit()

    print_record("Employer", employer)
    print_record("User", user)
    print(f"\nYou can create a JWT for this user by running `make jwt auth_id={user.sub_id}`")


if __name__ == "__main__":
    main()
