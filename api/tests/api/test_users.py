import uuid
from datetime import date
from typing import Any, Dict

import botocore.exceptions
import faker
import pytest
from dateutil.relativedelta import relativedelta

import tests.api
from massgov.pfml.db.models.employees import Role, User, UserLeaveAdministrator
from massgov.pfml.db.models.factories import (
    EmployerFactory,
    EmployerQuarterlyContributionFactory,
    UserFactory,
)
from massgov.pfml.util.aws.cognito import CognitoUserExistsValidationError
from massgov.pfml.util.strings import format_fein

fake = faker.Faker()

# every test in here requires real resources
pytestmark = pytest.mark.integration


@pytest.fixture
def valid_claimant_creation_request_body() -> Dict[str, Any]:
    return {
        "email_address": fake.email(domain="example.com"),
        "password": fake.password(length=12),
        "role": {"role_description": "Claimant"},
    }


@pytest.fixture
def employer_for_new_user(initialize_factories_session) -> EmployerFactory:
    return EmployerFactory.create()


@pytest.fixture
def valid_employer_creation_request_body(employer_for_new_user) -> Dict[str, Any]:
    ein = employer_for_new_user.employer_fein

    return {
        "email_address": fake.email(domain="example.com"),
        "password": fake.password(length=12),
        "role": {"role_description": "Employer"},
        "user_leave_administrator": {"employer_fein": format_fein(ein)},
    }


def test_users_post_claimant(
    client,
    mock_cognito,
    mock_cognito_user_pool,
    test_db_session,
    valid_claimant_creation_request_body,
):
    email_address = valid_claimant_creation_request_body.get("email_address")
    response = client.post("/v1/users", json=valid_claimant_creation_request_body,)
    response_body = response.get_json()

    # Response includes the user data
    assert response.status_code == 201
    assert response_body.get("data").get("email_address") == email_address

    # User added to DB
    user = test_db_session.query(User).filter(User.email_address == email_address).one_or_none()
    assert user.active_directory_id is not None

    # User added to user pool
    cognito_users = mock_cognito.list_users(UserPoolId=mock_cognito_user_pool["id"],)
    assert cognito_users["Users"][0]["Username"] == email_address


def test_users_post_employer(
    client,
    employer_for_new_user,
    mock_cognito,
    mock_cognito_user_pool,
    test_db_session,
    valid_employer_creation_request_body,
):
    email_address = valid_employer_creation_request_body.get("email_address")
    employer_fein = valid_employer_creation_request_body.get("user_leave_administrator").get(
        "employer_fein"
    )
    response = client.post("/v1/users", json=valid_employer_creation_request_body,)
    response_body = response.get_json()
    response_user = response_body.get("data")

    # Response includes the user data
    assert response.status_code == 201
    assert response_user.get("email_address") == email_address
    assert len(response_user.get("user_leave_administrators")) == 1
    # EIN is masked in response
    assert response_user.get("user_leave_administrators")[0].get("employer_fein") == employer_fein

    # User added to DB
    user = test_db_session.query(User).filter(User.email_address == email_address).one_or_none()
    assert user.active_directory_id is not None

    # Employer records added to DB
    assert len(user.roles) == 1
    assert user.roles[0].role_id == Role.EMPLOYER.role_id
    assert len(user.user_leave_administrators) == 1
    assert user.user_leave_administrators[0].employer_id == employer_for_new_user.employer_id

    # User added to user pool
    cognito_users = mock_cognito.list_users(UserPoolId=mock_cognito_user_pool["id"],)
    assert cognito_users["Users"][0]["Username"] == email_address


def test_users_post_openapi_validation(
    client, mock_cognito_user_pool, valid_employer_creation_request_body
):
    # OpenAPI spec enforces format and enum validations for us
    body = valid_employer_creation_request_body
    body["email_address"] = "not-a-valid-email"
    body["role"]["role_description"] = "Dog"
    body["user_leave_administrator"]["employer_fein"] = "123123123"  # missing dash

    response = client.post("/v1/users", json=body,)
    errors = response.get_json().get("errors")

    assert {
        "field": "email_address",
        "message": "'not-a-valid-email' is not a 'email'",
        "rule": "email",
        "type": "format",
    } in errors
    assert {
        "field": "role.role_description",
        "message": "'Dog' is not one of ['Claimant', 'Employer']",
        "rule": ["Claimant", "Employer"],
        "type": "enum",
    } in errors
    assert {
        "field": "user_leave_administrator.employer_fein",
        "message": "'123123123' does not match '^\\\\d{2}-\\\\d{7}$'",
        "rule": "^\\d{2}-\\d{7}$",
        "type": "pattern",
    } in errors
    assert response.status_code == 400


def test_users_post_custom_validations(
    client, mock_cognito_user_pool, valid_claimant_creation_request_body
):
    body = valid_claimant_creation_request_body
    body["email_address"] = None
    body["password"] = None

    response = client.post("/v1/users", json=body,)
    errors = response.get_json().get("errors")

    assert {
        "field": "email_address",
        "message": "email_address is required",
        "type": "required",
    } in errors
    assert {"field": "password", "message": "password is required", "type": "required",} in errors

    assert len(errors) == 2
    assert response.status_code == 400


def test_users_post_cognito_user_error(
    client,
    mock_cognito,
    mock_cognito_user_pool,
    monkeypatch,
    test_db_session,
    valid_claimant_creation_request_body,
):
    # User-recoverable Cognito errors result in 400 error response
    body = valid_claimant_creation_request_body
    body["password"] = "test"

    def sign_up(**kwargs):
        raise mock_cognito.exceptions.InvalidPasswordException(
            error_response={
                "Error": {
                    "Code": "InvalidPasswordException",
                    "Message": "Password did not conform with policy: Password not long enough",
                }
            },
            operation_name="SignUp",
        )

    monkeypatch.setattr(mock_cognito, "sign_up", sign_up)

    response = client.post("/v1/users", json=body,)
    errors = response.get_json().get("errors")
    user = (
        test_db_session.query(User)
        .filter(User.email_address == body.get("email_address"))
        .one_or_none()
    )

    assert user is None
    assert {
        "field": "password",
        "type": "invalid",
        "message": "Password did not conform with policy: Password not long enough",
    } in errors
    assert response.status_code == 400


def test_users_post_cognito_user_exists_error(
    client,
    mock_cognito,
    mock_cognito_user_pool,
    monkeypatch,
    test_db_session,
    valid_claimant_creation_request_body,
):
    existing_user = UserFactory.create(active_directory_id=str(uuid.uuid4()))

    def sign_up(**kwargs):
        raise CognitoUserExistsValidationError(
            "Username already exists", existing_user.active_directory_id
        )

    monkeypatch.setattr(mock_cognito, "sign_up", sign_up)

    response = client.post("/v1/users", json=valid_claimant_creation_request_body,)
    errors = response.get_json().get("errors")

    assert {
        "field": "email_address",
        "type": "exists",
        "message": "Username already exists",
    } in errors
    assert response.status_code == 400


def test_users_post_employer_required(
    client, mock_cognito, test_db_session,
):
    # EIN with no Employer record in the DB
    ein = "12-3456789"
    body = {
        "email_address": fake.email(domain="example.com"),
        "password": fake.password(length=12),
        "role": {"role_description": "Employer"},
        "user_leave_administrator": {"employer_fein": ein,},
    }

    response = client.post("/v1/users", json=body,)
    errors = response.get_json().get("errors")

    assert {
        "field": "user_leave_administrator.employer_fein",
        "message": "Invalid EIN",
        "type": "require_employer",
    } in errors
    assert response.status_code == 400


def test_users_get(client, employer_user, employer_auth_token, test_db_session):
    employer = EmployerFactory.create()
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    response = client.get(
        "/v1/users/{}".format(employer_user.user_id),
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )
    response_body = response.get_json()

    assert response.status_code == 200
    assert response_body.get("data")["user_id"] == str(employer_user.user_id)
    assert response_body.get("data")["roles"] == [
        {"role_description": "Employer", "role_id": 3},
    ]
    assert response_body.get("data")["user_leave_administrators"] == [
        {
            "employer_dba": employer.employer_dba,
            "employer_fein": format_fein(employer.employer_fein),
            "employer_id": str(employer.employer_id),
            "has_fineos_registration": True,
            "verified": False,
            "has_verification_data": False,
        }
    ]


def test_users_unauthorized_get(client, user, auth_token):
    user_2 = UserFactory.create()

    response = client.get(
        "/v1/users/{}".format(user_2.user_id), headers={"Authorization": f"Bearer {auth_token}"}
    )

    tests.api.validate_error_response(response, 403)


def test_users_get_404(client, auth_token):
    response = client.get(
        "/v1/users/{}".format("00000000-0000-0000-0000-000000000000"),
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    tests.api.validate_error_response(response, 404)


def test_users_get_fineos_forbidden(client, fineos_user, fineos_user_token):
    # Fineos role cannot access this endpoint
    response = client.get(
        "/v1/users/{}".format(fineos_user.user_id),
        headers={"Authorization": f"Bearer {fineos_user_token}"},
    )
    assert response.status_code == 403


def test_users_get_current(client, employer_user, employer_auth_token, test_db_session):
    employer = EmployerFactory.create()
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    response = client.get(
        "/v1/users/current", headers={"Authorization": f"Bearer {employer_auth_token}"}
    )
    response_body = response.get_json()

    assert response.status_code == 200
    assert response_body.get("data")["user_id"] == str(employer_user.user_id)
    assert response_body.get("data")["roles"] == [
        {"role_description": "Employer", "role_id": 3},
    ]
    assert response_body.get("data")["user_leave_administrators"] == [
        {
            "employer_dba": employer.employer_dba,
            "employer_fein": format_fein(employer.employer_fein),
            "employer_id": str(employer.employer_id),
            "has_fineos_registration": True,
            "verified": False,
            "has_verification_data": False,
        }
    ]


def test_users_get_aws_503(client, mock_cognito, monkeypatch, valid_claimant_creation_request_body):

    # valid user input recieves an error because the connection timed out
    body = valid_claimant_creation_request_body

    def sign_up(**kwargs):
        raise botocore.exceptions.HTTPClientError(error="ServiceUnavailable")

    monkeypatch.setattr(mock_cognito, "sign_up", sign_up)
    response = client.post("/v1/users", json=body)

    assert response.status_code == 503


def test_users_get_current_fineos_forbidden(client, fineos_user_token):
    # Fineos role cannot access this endpoint
    response = client.get(
        "/v1/users/current", headers={"Authorization": f"Bearer {fineos_user_token}"}
    )
    assert response.status_code == 403


def test_users_patch(client, user, auth_token, test_db_session):
    assert user.consented_to_data_sharing is False
    body = {"consented_to_data_sharing": True}
    response = client.patch(
        "v1/users/{}".format(user.user_id),
        headers={"Authorization": f"Bearer {auth_token}"},
        json=body,
    )
    response_body = response.get_json()
    assert response.status_code == 200
    assert response_body.get("data")["consented_to_data_sharing"] is True

    # test_db_session.refresh(user)
    assert user.consented_to_data_sharing is True


def test_users_convert_employer(client, user, employer_for_new_user, auth_token, test_db_session):
    ein = employer_for_new_user.employer_fein
    body = {"employer_fein": format_fein(ein)}
    assert len(user.roles) == 0
    response = client.post(
        "v1/users/{}/convert_employer".format(user.user_id),
        headers={"Authorization": f"Bearer {auth_token}"},
        json=body,
    )
    response_body = response.get_json()
    assert response.status_code == 201
    assert response_body.get("data")["user_leave_administrators"] == [
        {
            "employer_dba": employer_for_new_user.employer_dba,
            "employer_fein": format_fein(employer_for_new_user.employer_fein),
            "employer_id": str(employer_for_new_user.employer_id),
            "has_fineos_registration": False,
            "has_verification_data": False,
            "verified": False,
        }
    ]
    assert response_body.get("data")["roles"] == [
        {"role_description": "Employer", "role_id": Role.EMPLOYER.role_id,}
    ]

    assert len(user.roles) == 1
    assert user.roles[0].role_id == Role.EMPLOYER.role_id
    assert len(user.user_leave_administrators) == 1
    assert user.user_leave_administrators[0].employer_id == employer_for_new_user.employer_id


def test_users_convert_employer_bad_fein(client, user, auth_token):
    body = {"employer_fein": "999999999"}
    response = client.post(
        "v1/users/{}/convert_employer".format(user.user_id),
        headers={"Authorization": f"Bearer {auth_token}"},
        json=body,
    )
    assert response.status_code == 400


def test_users_unauthorized_convert_employer(
    client, employer_for_new_user, auth_token, test_db_session
):
    user_2 = UserFactory.create()
    assert len(user_2.user_leave_administrators) == 0
    ein = employer_for_new_user.employer_fein
    body = {"employer_fein": format_fein(ein)}
    response = client.post(
        "v1/users/{}/convert_employer".format(user_2.user_id),
        headers={"Authorization": f"Bearer {auth_token}"},
        json=body,
    )

    tests.api.validate_error_response(response, 403)

    # test_db_session.refresh(user_2)
    assert len(user_2.user_leave_administrators) == 0


def test_users_unauthorized_patch(client, user, auth_token, test_db_session):
    user_2 = UserFactory.create()

    assert user_2.consented_to_data_sharing is False
    body = {"consented_to_data_sharing": True}
    response = client.patch(
        "v1/users/{}".format(user_2.user_id),
        headers={"Authorization": f"Bearer {auth_token}"},
        json=body,
    )

    tests.api.validate_error_response(response, 403)

    # test_db_session.refresh(user_2)
    assert user_2.consented_to_data_sharing is False


@pytest.mark.parametrize(
    "request_body, expected_code",
    [
        # fail if field is invalid
        ({"email_address": "fail@gmail.com"}, 400),
        # fail if there are multiple fields
        (
            {
                "consented_to_data_sharing": False,
                "email_address": "fail@gmail.com",
                "auth_id": uuid.uuid4(),
            },
            400,
        ),
    ],
)
def test_users_patch_invalid(client, user, auth_token, request_body, expected_code):
    response = client.patch(
        "/v1/users/{}".format(user.user_id),
        json=request_body,
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == expected_code


def test_users_patch_404(client, auth_token):
    body = {"consented_to_data_sharing": True}
    response = client.patch(
        "/v1/users/{}".format("00000000-0000-0000-0000-000000000000"),
        json=body,
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    tests.api.validate_error_response(response, 404)


def test_users_patch_fineos_forbidden(client, fineos_user, fineos_user_token):
    # Fineos role cannot access this endpoint
    body = {"consented_to_data_sharing": True}
    response = client.patch(
        "v1/users/{}".format(fineos_user.user_id),
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )
    tests.api.validate_error_response(response, 403)


def test_has_verification_data_flag(client, employer_user, employer_auth_token, test_db_session):
    employer = EmployerFactory.create()
    # yesterday = datetime.today() - relativedelta(days=1)
    yesterday = date.today() - relativedelta(days=1)
    EmployerQuarterlyContributionFactory.create(employer=employer, filing_period=yesterday)
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    response = client.get(
        "/v1/users/{}".format(employer_user.user_id),
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )
    response_body = response.get_json()

    assert response_body.get("data")["user_leave_administrators"] == [
        {
            "employer_dba": employer.employer_dba,
            "employer_fein": format_fein(employer.employer_fein),
            "employer_id": str(employer.employer_id),
            "has_fineos_registration": True,
            "verified": False,
            "has_verification_data": True,
        }
    ]


def test_has_verification_data_flag_old_data(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create()
    EmployerQuarterlyContributionFactory.create(employer=employer, filing_period="2019-02-18")
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    response = client.get(
        "/v1/users/{}".format(employer_user.user_id),
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )
    response_body = response.get_json()

    assert response_body.get("data")["user_leave_administrators"] == [
        {
            "employer_dba": employer.employer_dba,
            "employer_fein": format_fein(employer.employer_fein),
            "employer_id": str(employer.employer_id),
            "has_fineos_registration": True,
            "verified": False,
            "has_verification_data": False,
        }
    ]
