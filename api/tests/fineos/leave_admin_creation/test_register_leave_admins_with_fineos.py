import pytest

import massgov.pfml.fineos.leave_admin_creation.register_leave_admins_with_fineos as register_leave_admins_with_fineos
import massgov.pfml.fineos.mock_client
from massgov.pfml import fineos
from massgov.pfml.db.models.employees import UserLeaveAdministrator
from massgov.pfml.db.models.factories import EmployerFactory, VerificationFactory

# every test in here requires real resources
pytestmark = pytest.mark.integration


class TestFindUserAndRegister:
    def test_valid_users_are_successfully_registered(self, test_db_session, employer_user):
        employer = EmployerFactory.create()
        fineos_client = fineos.create_client()

        verification = VerificationFactory.create()
        leave_admin = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id=None,
            verification=verification,
        )

        test_db_session.add(leave_admin)
        test_db_session.commit()

        massgov.pfml.fineos.mock_client.start_capture()

        register_leave_admins_with_fineos.find_user_and_register(
            test_db_session, leave_admin, fineos_client
        )

        capture = massgov.pfml.fineos.mock_client.get_capture()

        test_db_session.refresh(leave_admin)

        fineos_call_handler, _, _ = capture[0]

        assert leave_admin is not None
        assert leave_admin.fineos_web_id is not None
        assert leave_admin.fineos_web_id.startswith("pfml_leave_admin_")
        assert fineos_call_handler == "create_or_update_leave_admin"

    def test_does_not_register_leave_admins_linked_to_employers_without_fineos_employer_ids(
        self, test_db_session, monkeypatch, employer_user
    ):
        employer = EmployerFactory.create(fineos_employer_id=None)
        fineos_client = fineos.create_client()

        leave_admin = UserLeaveAdministrator(
            user_id=employer_user.user_id, employer_id=employer.employer_id, fineos_web_id=None,
        )

        test_db_session.add(leave_admin)
        test_db_session.commit()

        register_leave_admins_with_fineos.find_user_and_register(
            test_db_session, leave_admin, fineos_client
        )

        test_db_session.refresh(leave_admin)

        assert leave_admin is not None
        assert leave_admin.fineos_web_id is None

    def test_does_not_register_users_not_verified(self, test_db_session, employer_user):
        employer = EmployerFactory.create()
        fineos_client = fineos.create_client()

        leave_admin = UserLeaveAdministrator(
            user_id=employer_user.user_id, employer_id=employer.employer_id, fineos_web_id=None
        )

        test_db_session.add(leave_admin)
        test_db_session.commit()

        register_leave_admins_with_fineos.find_user_and_register(
            test_db_session, leave_admin, fineos_client
        )

        test_db_session.refresh(leave_admin)

        assert leave_admin is not None
        assert leave_admin.fineos_web_id is None


class TestFindAdminsWithoutRegistration:
    def test_registers_valid_leave_admins(self, test_db_session, employer_user):
        employer = EmployerFactory.create()
        verification = VerificationFactory.create()
        leave_admin = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id=None,
            verification=verification,
        )

        test_db_session.add(leave_admin)
        test_db_session.commit()

        register_leave_admins_with_fineos.find_admins_without_registration(test_db_session)

        test_db_session.refresh(leave_admin)

        assert leave_admin is not None
        assert leave_admin.fineos_web_id is not None

    def test_does_not_register_leave_admins_that_already_have_fineos_ids(
        self, test_db_session, employer_user
    ):
        employer = EmployerFactory.create()
        verification = VerificationFactory.create()
        leave_admin = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=verification,
        )

        test_db_session.add(leave_admin)
        test_db_session.commit()

        register_leave_admins_with_fineos.find_admins_without_registration(test_db_session)

        test_db_session.refresh(leave_admin)

        assert leave_admin is not None
        assert leave_admin.fineos_web_id == "fake-fineos-web-id"

    def test_does_not_register_leave_admins_that_have_not_verified(
        self, test_db_session, employer_user
    ):
        employer = EmployerFactory.create()
        leave_admin = UserLeaveAdministrator(
            user_id=employer_user.user_id, employer_id=employer.employer_id, fineos_web_id=None,
        )

        test_db_session.add(leave_admin)
        test_db_session.commit()

        register_leave_admins_with_fineos.find_admins_without_registration(test_db_session)

        test_db_session.refresh(leave_admin)

        assert leave_admin is not None
        assert leave_admin.fineos_web_id is None
