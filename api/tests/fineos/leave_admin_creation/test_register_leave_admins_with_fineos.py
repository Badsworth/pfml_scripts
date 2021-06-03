import pytest

import massgov.pfml.fineos.leave_admin_creation.register_leave_admins_with_fineos as register_leave_admins_with_fineos
import massgov.pfml.fineos.mock_client
from massgov.pfml import fineos
from massgov.pfml.db.models.employees import UserLeaveAdministrator
from massgov.pfml.db.models.factories import EmployerFactory, VerificationFactory
from massgov.pfml.util import feature_gate

# every test in here requires real resources
pytestmark = pytest.mark.integration


def test_find_user_and_register(test_db_session, employer_user):
    employer = EmployerFactory.create()
    fineos_client = fineos.create_client()

    leave_admin = UserLeaveAdministrator(
        user_id=employer_user.user_id, employer_id=employer.employer_id, fineos_web_id=None,
    )

    test_db_session.add(leave_admin)
    test_db_session.commit()

    massgov.pfml.fineos.mock_client.start_capture()

    register_leave_admins_with_fineos.find_user_and_register(
        test_db_session, leave_admin, fineos_client
    )

    capture = massgov.pfml.fineos.mock_client.get_capture()

    leave_admin = (
        test_db_session.query(UserLeaveAdministrator)
        .filter(
            UserLeaveAdministrator.user_leave_administrator_id
            == leave_admin.user_leave_administrator_id
        )
        .one_or_none()
    )

    fineos_call_handler, _, _ = capture[0]

    assert leave_admin is not None
    assert leave_admin.fineos_web_id is not None
    assert leave_admin.fineos_web_id.startswith("pfml_leave_admin_")
    assert fineos_call_handler == "create_or_update_leave_admin"


def test_registers_leave_admins_without_fineos_ids(test_db_session, monkeypatch, employer_user):
    def mocked_find_user_and_register(db_session, leave_admin, fineos_client):
        mocked_find_user_and_register.was_called = True
        assert leave_admin.user_id == employer_user.user_id

    mocked_find_user_and_register.was_called = False

    monkeypatch.setattr(
        "massgov.pfml.fineos.leave_admin_creation.register_leave_admins_with_fineos.find_user_and_register",
        mocked_find_user_and_register,
    )
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
    assert mocked_find_user_and_register.was_called is True


@pytest.fixture(params=["env_var", "feature_gate"])
def _enforce_verifications(request, monkeypatch, employer_user):
    if request.param == "env_var":
        monkeypatch.setenv("ENFORCE_LEAVE_ADMIN_VERIFICATION", "1")
    else:
        monkeypatch.setenv("ENFORCE_LEAVE_ADMIN_VERIFICATION", "0")
        monkeypatch.setattr(feature_gate, "check_enabled", lambda feature_name, user_email: True)


def test_registers_leave_admins_with_verifications_but_without_fineos_ids(
    test_db_session, monkeypatch, employer_user, _enforce_verifications
):
    def mocked_find_user_and_register(db_session, leave_admin, fineos_client):
        mocked_find_user_and_register.was_called = True
        assert leave_admin.user_id == employer_user.user_id

    mocked_find_user_and_register.was_called = False

    monkeypatch.setattr(
        "massgov.pfml.fineos.leave_admin_creation.register_leave_admins_with_fineos.find_user_and_register",
        mocked_find_user_and_register,
    )
    employer = EmployerFactory.create()
    verification = VerificationFactory.create()

    leave_admin = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id=None,
        verification_id=verification.verification_id,
    )

    test_db_session.add(leave_admin)
    test_db_session.commit()

    register_leave_admins_with_fineos.find_admins_without_registration(test_db_session)
    assert mocked_find_user_and_register.was_called is True


def test_does_not_register_leave_admins_with_fineos_ids(
    test_db_session, monkeypatch, employer_user
):
    def mocked_find_user_and_register(db_session, leave_admin, fineos_client):
        mocked_find_user_and_register.was_called = True

    mocked_find_user_and_register.was_called = False

    monkeypatch.setattr(
        "massgov.pfml.fineos.leave_admin_creation.register_leave_admins_with_fineos.find_user_and_register",
        mocked_find_user_and_register,
    )
    employer = EmployerFactory.create()

    leave_admin = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )

    test_db_session.add(leave_admin)
    test_db_session.commit()

    register_leave_admins_with_fineos.find_admins_without_registration(test_db_session)
    assert mocked_find_user_and_register.was_called is False


def test_does_not_register_las_linked_to_emps_without_fineos_employer_ids(
    test_db_session, monkeypatch, employer_user
):
    fineos_client = fineos.create_client()
    employer = EmployerFactory.create(fineos_employer_id=None)

    leave_admin = UserLeaveAdministrator(
        user_id=employer_user.user_id, employer_id=employer.employer_id, fineos_web_id=None,
    )

    test_db_session.add(leave_admin)
    test_db_session.commit()

    register_leave_admins_with_fineos.find_user_and_register(
        test_db_session, leave_admin, fineos_client
    )

    leave_admin = (
        test_db_session.query(UserLeaveAdministrator)
        .filter(UserLeaveAdministrator.user_id == employer_user.user_id)
        .one_or_none()
    )

    assert leave_admin.fineos_web_id is None
