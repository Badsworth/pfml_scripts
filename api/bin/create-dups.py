#!/usr/bin/env python3
#
# Generate a verified leave admin user and generate claims for the organization
#
# Run via `make create-leave-admin-and-claims`.
# View options: `make create-leave-admin-and-claims args="--help"`
#
import random
from datetime import datetime

import click
import pytz
from factory.faker import faker

import massgov.pfml.db
from massgov.pfml.db.models.employees import Role, UserLeaveAdministrator
from massgov.pfml.db.models.factories import (
    ApplicationFactory,
    DocumentFactory,
    EmployerFactory,
    ManagedRequirementFactory,
    UserFactory,
    UserLeaveAdministratorFactory,
)

fake = faker.Faker()
db_session = massgov.pfml.db.init(sync_lookups=True)


@click.command()
def main() -> None:
    emails_to_duplicate = [
        "test@email.com",
        "test2@email.com",
        "test3@email.com",
        "test4@email.com",
    ]

    created_at = datetime(2021, 9, 1, 1, 1, 1, tzinfo=pytz.UTC)
    for email in emails_to_duplicate:
        # Add data to a single user

        user_1_a = UserFactory.create(email_address=email, roles=[Role.USER], created_at=created_at)

        for _ in range(22):
            employer = EmployerFactory.create()
            UserLeaveAdministratorFactory(
                user=user_1_a, employer=employer,
            )

            app = ApplicationFactory.create(user=user_1_a)
            for _2 in range(6):
                DocumentFactory.create(user_id=user_1_a.user_id, application_id=app.application_id)

            ManagedRequirementFactory.create(respondent_user=user_1_a)

        # Create duplicate data for that user
        for _ in range(10):
            user = UserFactory.create(
                email_address=email, roles=[Role.USER, Role.EMPLOYER, Role.FINEOS]
            )
            employer = EmployerFactory.create()

            UserLeaveAdministratorFactory(
                user=user, employer=employer,
            )
            for _ in range(6):
                app = ApplicationFactory.create(user=user)
                for _2 in range(4):
                    DocumentFactory.create(user_id=user.user_id, application_id=app.application_id)

                ManagedRequirementFactory.create(respondent_user=user)

    db_session.commit()


if __name__ == "__main__":
    main()
