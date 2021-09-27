import os
from typing import List
import pytest
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.expression import select, text
from sqlalchemy.sql.functions import count, func
from sqlalchemy.dialects import postgresql
from massgov.pfml import db
from massgov.pfml.db.models.applications import Application

from massgov.pfml.db.models.employees import Role, User, UserLeaveAdministrator, UserRole
from massgov.pfml.db.models.factories import (
    ApplicationFactory,
    DocumentFactory,
    EmployerFactory,
    ManagedRequirementFactory,
    UserFactory,
)


@pytest.fixture
def generate_duplicate_users(initialize_factories_session, test_db_session):

    emails_to_duplicate = [
        "test@email.com",
        "test2@email.com",
        "test3@email.com",
        "test4@email.com",
    ]

    for email in emails_to_duplicate:
        # Add data to a single user
        user_1_a = UserFactory.create(email_address=email, roles=[Role.USER])

        for _ in range(22):
            employer = EmployerFactory.create()
            UserLeaveAdministrator(
                user_id=user_1_a.user_id, employer_id=employer.employer_id,
            )

            app = ApplicationFactory.create(user=user_1_a)
            for _2 in range(6):
                DocumentFactory.create(user_id=user_1_a.user_id, application_id=app.application_id)

            ManagedRequirementFactory.create(respondent_user=user_1_a)

        # Create duplicate data for that user
        for _ in range(10):
            user = UserFactory.create(email_address=email, roles=[Role.USER])
            employer = EmployerFactory.create()

            UserLeaveAdministrator(
                user_id=user.user_id, employer_id=employer.employer_id,
            )
            for _ in range(6):
                app = ApplicationFactory.create(user=user)
                for _2 in range(4):
                    DocumentFactory.create(user_id=user.user_id, application_id=app.application_id)

                ManagedRequirementFactory.create(respondent_user=user)


def open_file(fileName: str):
    pth = os.path.join(os.path.dirname(__file__), fileName)
    print(pth)
    fd = open(pth, "r")
    sql_file = fd.read()
    fd.close()

    return sql_file.strip("\n")


class UserEmailCount(db.RowProxy):
    email_address: User.email_address
    count: int


def test_remove_and_merge_duplicates(
    initialize_factories_session, test_db_session: Session, generate_duplicate_users,
):
    all_users = test_db_session.query(User).count()
    assert all_users == 44

    sql_file = open_file("merge_duplicate_users.sql")

    duplicated_users: List[UserEmailCount] = (
        test_db_session.query(User.email_address, count(User.user_id).label("count"))
        .group_by(User.email_address)
        .having(func.count(User.user_id) > 1)
        .all()
    )

    assert len(duplicated_users) == 4
    assert duplicated_users[0].count == 11
    assert duplicated_users[1].count == 11
    assert duplicated_users[2].count == 11
    assert duplicated_users[3].count == 11

    test_db_session.execute(sql_file)

    duplicated_users_remaining: List[UserEmailCount] = (
        test_db_session.query(User.email_address, count(User.user_id).label("count"))
        .group_by(User.email_address)
        .having(func.count(User.user_id) > 1)
        .all()
    )

    assert len(duplicated_users_remaining) == 0

    all_users = test_db_session.query(User).count()
    assert all_users == 4

