import faker

from massgov.pfml.db.models.employees import UserLeaveAdministrator
from massgov.pfml.db.models.factories import EmployerFactory, UserFactory, VerificationFactory

fake = faker.Faker()


def test_roles_delete_404(client, employer_auth_token):
    user = UserFactory.build()
    body = {"role": {"role_description": "Employer"}}
    body["user_id"] = user.user_id
    response = client.delete(
        "/v1/roles", headers={"Authorization": f"Bearer {employer_auth_token}"}, json=body
    )

    assert response.status_code == 404


def test_roles_delete_convert_to_claimant_success(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create()
    link = UserLeaveAdministrator(user_id=employer_user.user_id, employer_id=employer.employer_id)
    test_db_session.add(link)
    test_db_session.commit()
    body = {"role": {"role_description": "Employer"}}
    body["user_id"] = employer_user.user_id

    assert len(employer_user.roles) == 1
    assert len(employer_user.user_leave_administrators) == 1
    response = client.delete(
        "v1/roles", headers={"Authorization": f"Bearer {employer_auth_token}"}, json=body
    )
    assert response.status_code == 200
    test_db_session.refresh(employer_user)

    assert len(employer_user.roles) == 0
    assert len(employer_user.user_leave_administrators) == 0


def test_roles_delete_convert_to_claimant_already_in_fineos(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create()
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()
    body = {"role": {"role_description": "Employer"}}
    body["user_id"] = employer_user.user_id

    assert len(employer_user.roles) == 1
    assert len(employer_user.user_leave_administrators) == 1
    response = client.delete(
        "v1/roles", headers={"Authorization": f"Bearer {employer_auth_token}"}, json=body
    )
    test_db_session.refresh(employer_user)
    errors = response.get_json().get("errors")
    assert len(errors) == 1
    error = errors[0]
    assert error.get("field") == "role.role_description"
    assert error.get("message") == "Verified Leave Admins cannot convert their account!"
    assert response.status_code == 400

    assert len(employer_user.roles) == 1
    assert len(employer_user.user_leave_administrators) == 1


def test_roles_delete_convert_to_claimant_unsupported(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create()
    link = UserLeaveAdministrator(user_id=employer_user.user_id, employer_id=employer.employer_id)
    test_db_session.add(link)
    test_db_session.commit()
    body = {"role": {"role_description": "Fake"}}
    body["user_id"] = employer_user.user_id

    assert len(employer_user.roles) == 1
    assert len(employer_user.user_leave_administrators) == 1
    response = client.delete(
        "v1/roles", headers={"Authorization": f"Bearer {employer_auth_token}"}, json=body
    )
    json = response.get_json()

    assert response.status_code == 400
    assert json.get("message") == "Unsupported role deletion"
    assert len(employer_user.roles) == 1
    assert len(employer_user.user_leave_administrators) == 1


def test_roles_delete_convert_to_claimant_already_verified(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create()
    verification = VerificationFactory.create()
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        verification_id=verification.verification_id,
    )
    test_db_session.add(link)
    test_db_session.commit()
    body = {"role": {"role_description": "Employer"}}
    body["user_id"] = employer_user.user_id

    assert len(employer_user.roles) == 1
    assert len(employer_user.user_leave_administrators) == 1
    response = client.delete(
        "v1/roles", headers={"Authorization": f"Bearer {employer_auth_token}"}, json=body
    )
    test_db_session.refresh(employer_user)
    errors = response.get_json().get("errors")
    assert len(errors) == 1
    error = errors[0]
    assert error.get("field") == "role.role_description"
    assert error.get("message") == "Verified Leave Admins cannot convert their account!"
    assert response.status_code == 400

    assert len(employer_user.roles) == 1
    assert len(employer_user.user_leave_administrators) == 1


def test_roles_delete_convert_to_claimant_unauthorized(
    client, employer_user, auth_token, test_db_session
):
    employer = EmployerFactory.create()
    link = UserLeaveAdministrator(user_id=employer_user.user_id, employer_id=employer.employer_id)
    test_db_session.add(link)
    test_db_session.commit()
    body = {"role": {"role_description": "Employer"}}
    body["user_id"] = employer_user.user_id

    assert len(employer_user.roles) == 1
    assert len(employer_user.user_leave_administrators) == 1
    response = client.delete(
        "v1/roles", headers={"Authorization": f"Bearer {auth_token}"}, json=body
    )
    assert response.status_code == 403
    test_db_session.refresh(employer_user)

    assert len(employer_user.roles) == 1
    assert len(employer_user.user_leave_administrators) == 1
