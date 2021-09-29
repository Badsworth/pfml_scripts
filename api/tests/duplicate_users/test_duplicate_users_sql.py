from datetime import datetime, tzinfo
import os
from typing import Dict, List, Type, cast
from uuid import UUID
import pytest
import pytz
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
            func.min(User.created_at).label("oldest_created_at"),
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
        test_db_session.query(User)
        .filter(
            User.email_address.in_(duplicated_emails),
            User.created_at == datetime(2021, 9, 1, 1, 1, 1, tzinfo=pytz.UTC),
        )
        .all()
    )

    assert len(oldest_duplicated_users) == 4
    assert oldest_duplicated_users[0].email_address == "test@email.com"
    assert oldest_duplicated_users[1].email_address == "test2@email.com"
    assert oldest_duplicated_users[2].email_address == "test3@email.com"
    assert oldest_duplicated_users[3].email_address == "test4@email.com"

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

    for oldest_dup_user in oldest_duplicated_users:
        email_address = oldest_dup_user.email_address
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

    leave_admin_count_init = test_db_session.query(UserLeaveAdministrator).count()
    assert leave_admin_count_init == 128

    applications_count_init = test_db_session.query(Application).count()
    assert applications_count_init == 328

    documents_count_init = test_db_session.query(Document).count()
    assert documents_count_init == 1488

    managed_reqs_count_init = test_db_session.query(ManagedRequirement).count()
    assert managed_reqs_count_init == 328

    roles_count_init = test_db_session.query(UserRole).count()
    assert roles_count_init == 124

    # ACT
    test_db_session.execute(sql_file)

    # ASSERT

    leave_admin_count_end = test_db_session.query(UserLeaveAdministrator).count()
    assert leave_admin_count_end == 128

    applications_count_end = test_db_session.query(Application).count()
    assert applications_count_end == 328

    documents_count_end = test_db_session.query(Document).count()
    assert documents_count_end == 1488

    managed_reqs_count_end = test_db_session.query(ManagedRequirement).count()
    assert managed_reqs_count_end == 328

    roles_count_end = test_db_session.query(UserRole).count()
    assert roles_count_end == 12

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
        found_user = next(
            old_user
            for old_user in oldest_duplicated_users
            if old_user.email_address == user.email_address
        )

        assert found_user is not None
        assert found_user.user_id == user.user_id

        leave_administrators = (
            test_db_session.query(UserLeaveAdministrator)
            .join(User, User.user_id == UserLeaveAdministrator.user_id,)
            .filter(User.email_address == email_address,)
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

