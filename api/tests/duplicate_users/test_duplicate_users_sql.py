import os
from datetime import datetime, tzinfo
from typing import Dict, List, Set, Type, cast
from uuid import UUID

import pytest
import pytz
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import mapper
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.elements import and_
from sqlalchemy.sql.expression import select, text
from sqlalchemy.sql.functions import count, func

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

    # Keep track of expected UUIDS from merge
    expected_leave_administrator_ids: Dict[str, Set[UUID]] = dict()
    expected_application_ids: Dict[str, Set[UUID]] = dict()
    expected_document_ids: Dict[str, Set[UUID]] = dict()
    expected_managed_req_ids: Dict[str, Set[UUID]] = dict()
    expected_user_role_ids: Dict[str, Set[str]] = dict()

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

        # ----

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

        # ----

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

        # ----

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

        # ----

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

        # ----

        if not email_address in expected_leave_administrator_ids:
            expected_leave_administrator_ids[email_address] = set()
        if not email_address in expected_application_ids:
            expected_application_ids[email_address] = set()
        if not email_address in expected_document_ids:
            expected_document_ids[email_address] = set()
        if not email_address in expected_managed_req_ids:
            expected_managed_req_ids[email_address] = set()
        if not email_address in expected_user_role_ids:
            expected_user_role_ids[email_address] = set()

        for x in leave_administrators:
            expected_leave_administrator_ids[email_address].add(x.user_leave_administrator_id)
        for x in leave_administrators_main:
            expected_leave_administrator_ids[email_address].add(x.user_leave_administrator_id)

        for x in applications + applications_main:
            expected_application_ids[email_address].add(x.application_id)

        for x in documents + documents_main:
            expected_document_ids[email_address].add(x.document_id)

        for x in managed_reqs + managed_reqs_main:
            expected_managed_req_ids[email_address].add(x.managed_requirement_id)

        for x in roles + roles_main:
            expected_user_role_ids[email_address].add(x.role_id)

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

    # MERGE DATA AND REMOVE DUPLICATES
    test_db_session.execute(sql_file)

    # Make sure all records are preserved
    leave_admin_count_end = test_db_session.query(UserLeaveAdministrator).count()
    assert leave_admin_count_end == 128

    leave_administrators_distinct = (
        test_db_session.query(UserLeaveAdministrator).distinct(UserLeaveAdministrator.user_id).all()
    )
    print(leave_administrators_distinct[0].user_id)
    assert len(leave_administrators_distinct) == 4

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

    # Make sure all records got moved over to the correct user
    for user in all_users_final:
        found_user = next(
            old_user
            for old_user in oldest_duplicated_users
            if old_user.email_address == user.email_address
        )

        assert found_user is not None
        assert found_user.user_id == user.user_id

        # ----
        leave_administrators = (
            test_db_session.query(UserLeaveAdministrator)
            .filter(UserLeaveAdministrator.user_id == user.user_id)
            .all()
        )
        assert len(leave_administrators) == 32
        assert len(leave_administrators) == len(
            expected_leave_administrator_ids[found_user.email_address]
        )
        actual_leave_administrator_ids_set = set(
            x.user_leave_administrator_id for x in leave_administrators
        )

        found_missing_leave_administrators = [
            x
            for x in expected_leave_administrator_ids[found_user.email_address]
            if x not in actual_leave_administrator_ids_set
        ]
        assert len(found_missing_leave_administrators) == 0

        found_extra_leave_administrators = [
            x
            for x in leave_administrators
            if x.user_leave_administrator_id
            not in expected_leave_administrator_ids[found_user.email_address]
        ]
        assert len(found_extra_leave_administrators) == 0

        # ----

        applications = (
            test_db_session.query(Application).filter(Application.user_id == user.user_id).all()
        )
        assert len(applications) == 82

        assert len(applications) == len(expected_application_ids[found_user.email_address])

        actual_application_ids_set = set(x.application_id for x in applications)

        found_missing_applications = [
            x
            for x in expected_application_ids[found_user.email_address]
            if x not in actual_application_ids_set
        ]
        assert len(found_missing_applications) == 0

        found_extra_applications = [
            x
            for x in applications
            if x.application_id not in expected_application_ids[found_user.email_address]
        ]
        assert len(found_extra_applications) == 0

        # ----

        documents = test_db_session.query(Document).filter(Document.user_id == user.user_id).all()
        assert len(documents) == 372

        assert len(documents) == len(expected_document_ids[found_user.email_address])

        actual_document_ids_set = set(x.document_id for x in documents)

        found_missing_documents = [
            x
            for x in expected_document_ids[found_user.email_address]
            if x not in actual_document_ids_set
        ]
        assert len(found_missing_documents) == 0

        found_extra_documents = [
            x
            for x in documents
            if x.document_id not in expected_document_ids[found_user.email_address]
        ]
        assert len(found_extra_documents) == 0

        # ----

        managed_reqs = (
            test_db_session.query(ManagedRequirement)
            .join(User, ManagedRequirement.respondent_user_id == user.user_id)
            .all()
        )
        assert len(managed_reqs) == 82

        assert len(managed_reqs) == len(expected_managed_req_ids[found_user.email_address])

        actual_managed_req_ids_set = set(x.managed_requirement_id for x in managed_reqs)

        found_missing_managed_reqs = [
            x
            for x in expected_managed_req_ids[found_user.email_address]
            if x not in actual_managed_req_ids_set
        ]
        assert len(found_missing_managed_reqs) == 0

        found_extra_managed_reqs = [
            x
            for x in managed_reqs
            if x.managed_requirement_id not in expected_managed_req_ids[found_user.email_address]
        ]
        assert len(found_extra_managed_reqs) == 0

        # ----

        roles = test_db_session.query(UserRole).join(User, UserRole.user_id == user.user_id).all()
        assert len(roles) == 3

        assert len(roles) == len(expected_user_role_ids[found_user.email_address])

        actual_user_role_ids_set = set(x.role_id for x in roles)

        found_missing_user_roles = [
            x
            for x in expected_user_role_ids[found_user.email_address]
            if x not in actual_user_role_ids_set
        ]
        assert len(found_missing_user_roles) == 0

        found_extra_roles = [
            x for x in roles if x.role_id not in expected_user_role_ids[found_user.email_address]
        ]
        assert len(found_extra_roles) == 0
