from massgov.pfml.db.models.employees import UserLeaveAdministrator
from massgov.pfml.db.models.factories import EmployerFactory, UserFactory, VerificationFactory


def test_user_leave_admin_has_fineos_registration():
    user_leave_admin = UserLeaveAdministrator(
        user=UserFactory.build(), employer=EmployerFactory.build(),
    )
    assert user_leave_admin.has_fineos_registration is False

    user_leave_admin.fineos_web_id = "fake-fineos-web-id"
    assert user_leave_admin.has_fineos_registration is True


def test_user_leave_admin_verified():
    user_leave_admin = UserLeaveAdministrator(
        user=UserFactory.build(), employer=EmployerFactory.build(),
    )
    assert user_leave_admin.verified is False

    user_leave_admin.verification_id = VerificationFactory.build().verification_id
    assert user_leave_admin.verified is True
