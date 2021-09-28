from datetime import datetime
import os
from typing import Dict, List, Type
import pytest
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.elements import and_
from sqlalchemy.sql.expression import select, text
from sqlalchemy.sql.functions import count, func
from sqlalchemy.dialects import postgresql
from massgov.pfml import db
from massgov.pfml.db.models.applications import Application, Document

from massgov.pfml.db.models.employees import (
    ManagedRequirement,
    Role,
    User,
    UserLeaveAdministrator,
    UserRole,
)
from massgov.pfml.db.models.factories import (
    ApplicationFactory,
    DocumentFactory,
    EmployerFactory,
    ManagedRequirementFactory,
    UserFactory,
    UserLeaveAdministratorFactory,
)


@pytest.fixture
def generate_duplicate_users(initialize_factories_session, test_db_session):

    emails_to_duplicate = [
        "test@email.com",
        "test2@email.com",
        "test3@email.com",
        "test4@email.com",
    ]

    created_at = datetime.utcnow()
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
    oldest_created_at: datetime


def test_remove_and_merge_duplicates(
    initialize_factories_session, test_db_session: Session, generate_duplicate_users,
):
    all_users = test_db_session.query(User).all()

    assert len(all_users) == 44

    sql_file = open_file("merge_duplicate_users.sql")

    duplicated_users_counts: List[UserEmailCount] = (
        test_db_session.query(
            User.email_address,
            count(User.user_id).label("count"),
            min(User.created_at).label("oldest_created_at"),
        )
        .group_by(User.email_address)
        .having(func.count(User.user_id) > 1)
        .all()
    )

    assert len(duplicated_users_counts) == 4
    assert duplicated_users_counts[0].count == 11
    assert duplicated_users_counts[1].count == 11
    assert duplicated_users_counts[2].count == 11
    assert duplicated_users_counts[3].count == 11

    duplicated_emails = [row.email_address for row in duplicated_users_counts]

    duplicated_users: List[User] = (
        test_db_session.query(User).filter(User.email_address.in_(duplicated_emails)).all()
    )

    assert len(duplicated_users) == 44

    oldest_duplicated_users: List[User] = (
        test_db_session.query(User).filter(User.email_address.in_(duplicated_emails)).all()
    )

    # Get the user we are keeping
    oldest_created_dup_users: Dict[str, User] = dict()
    for dup_user in duplicated_users:
        if not dup_user.email_address in oldest_created_dup_users:
            oldest_created_dup_users[dup_user.email_address] = dup_user
        elif dup_user.created_at < oldest_created_dup_users[dup_user.email_address].created_at:
            oldest_created_dup_users[dup_user.email_address] = dup_user

    # Get the data from other users
    dup_user_leave_administrators: Dict[str, List[UserLeaveAdministrator]] = dict()
    dup_user_applications: Dict[str, List[Application]] = dict()
    dup_user_documents: Dict[str, List[Document]] = dict()
    dup_user_managed_reqs: Dict[str, List[ManagedRequirement]] = dict()
    dup_user_roles: Dict[str, List[UserRole]] = dict()

    main_user_leave_administrators: Dict[str, List[UserLeaveAdministrator]] = dict()
    main_user_applications: Dict[str, List[Application]] = dict()
    main_user_documents: Dict[str, List[Document]] = dict()
    main_user_managed_reqs: Dict[str, List[ManagedRequirement]] = dict()
    main_user_roles: Dict[str, List[UserRole]] = dict()

    for email_address in duplicated_emails:
        oldest_dup_user = oldest_created_dup_users[email_address]
        assert oldest_dup_user is not None

        leave_administrators = (
            test_db_session.query(UserLeaveAdministrator)
            .join(
                User,
                and_(
                    User.email_address == email_address,
                    User.user_id != oldest_dup_user.user_id,
                    User.user_id == UserLeaveAdministrator.user_id,
                ),
            )
            .all()
        )

        assert len(leave_administrators) == 10

        leave_administrators_main = (
            test_db_session.query(UserLeaveAdministrator)
            .join(
                User,
                and_(
                    User.user_id == oldest_dup_user.user_id,
                    User.user_id == UserLeaveAdministrator.user_id,
                ),
            )
            .all()
        )

        assert len(leave_administrators_main) == 22

        applications = (
            test_db_session.query(Application)
            .join(
                User,
                and_(
                    User.email_address == email_address,
                    User.user_id != oldest_dup_user.user_id,
                    User.user_id == Application.user_id,
                ),
            )
            .all()
        )

        assert len(applications) == 60

        applications_main = (
            test_db_session.query(Application)
            .join(
                User,
                and_(User.user_id == oldest_dup_user.user_id, User.user_id == Application.user_id,),
            )
            .all()
        )

        assert len(applications_main) == 22

        documents = (
            test_db_session.query(Document)
            .join(
                User,
                and_(
                    User.email_address == email_address,
                    User.user_id != oldest_dup_user.user_id,
                    User.user_id == Document.user_id,
                ),
            )
            .all()
        )

        assert len(documents) == 240

        documents_main = (
            test_db_session.query(Document)
            .join(
                User,
                and_(User.user_id == oldest_dup_user.user_id, User.user_id == Document.user_id,),
            )
            .all()
        )

        assert len(documents_main) == 132

        managed_reqs = (
            test_db_session.query(ManagedRequirement)
            .join(
                User,
                and_(
                    User.email_address == email_address,
                    User.user_id != oldest_dup_user.user_id,
                    User.user_id == ManagedRequirement.respondent_user_id,
                ),
            )
            .all()
        )

        assert len(managed_reqs) == 60

        managed_reqs_main = (
            test_db_session.query(ManagedRequirement)
            .join(
                User,
                and_(
                    User.user_id == oldest_dup_user.user_id,
                    User.user_id == ManagedRequirement.respondent_user_id,
                ),
            )
            .all()
        )

        assert len(managed_reqs_main) == 22

        roles = (
            test_db_session.query(UserRole)
            .join(
                User,
                and_(
                    User.email_address == email_address,
                    User.user_id != oldest_dup_user.user_id,
                    User.user_id == UserRole.user_id,
                ),
            )
            .all()
        )

        assert len(roles) == 30

        roles_main = (
            test_db_session.query(UserRole)
            .join(
                User,
                and_(User.user_id == oldest_dup_user.user_id, User.user_id == UserRole.user_id,),
            )
            .all()
        )

        assert len(roles_main) == 1

        dup_user_leave_administrators[email_address] = leave_administrators
        dup_user_applications[email_address] = applications
        dup_user_documents[email_address] = documents
        dup_user_managed_reqs[email_address] = managed_reqs
        dup_user_roles[email_address] = roles
        main_user_leave_administrators[email_address] = leave_administrators_main
        main_user_applications[email_address] = applications_main
        main_user_documents[email_address] = documents_main
        main_user_managed_reqs[email_address] = managed_reqs_main
        main_user_roles[email_address] = roles_main

    test_db_session.execute(sql_file)

    duplicated_users_remaining: List[UserEmailCount] = (
        test_db_session.query(User.email_address, count(User.user_id).label("count"))
        .group_by(User.email_address)
        .having(func.count(User.user_id) > 1)
        .all()
    )

    assert len(duplicated_users_remaining) == 0

    all_users_final = test_db_session.query(User).all()
    assert len(all_users_final) == 4

    for user in all_users_final:
        assert oldest_created_dup_users[user.email_address] is not None
        assert oldest_created_dup_users[user.email_address].user_id == user.user_id

        leave_administrators = (
            test_db_session.query(UserLeaveAdministrator)
            .join(
                User,
                and_(User.user_id == user.user_id, User.user_id == UserLeaveAdministrator.user_id),
            )
            .all()
        )

        assert len(leave_administrators) == 128

        applications = (
            test_db_session.query(Application)
            .join(User, and_(User.user_id == user.user_id, User.user_id == Application.user_id))
            .all()
        )

        documents = (
            test_db_session.query(Document)
            .join(User, and_(User.user_id == user.user_id, User.user_id == Document.user_id))
            .all()
        )

        managed_reqs = (
            test_db_session.query(ManagedRequirement)
            .join(
                User,
                and_(
                    User.user_id == user.user_id,
                    User.user_id == ManagedRequirement.respondent_user_id,
                ),
            )
            .all()
        )

        roles = (
            test_db_session.query(UserRole)
            .join(User, and_(User.user_id == user.user_id, User.user_id == UserRole.user_id))
            .all()
        )

        assert len(roles) == 3

