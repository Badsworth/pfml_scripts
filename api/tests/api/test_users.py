import uuid
from datetime import date
from typing import Any, Dict

import faker
import pytest
from dateutil.relativedelta import relativedelta

import tests.api
from massgov.pfml.db.models.employees import UserLeaveAdministrator
from massgov.pfml.db.models.factories import (
    EmployerFactory,
    EmployerQuarterlyContributionFactory,
    UserFactory,
)

fake = faker.Faker()

# every test in here requires real resources
pytestmark = pytest.mark.integration


@pytest.fixture
def valid_claimant_creation_request_body() -> Dict[str, Any]:
    return {
        "email_address": fake.email(),
        "password": fake.password(length=12),
        "role": {"role_description": "Claimant"},
    }


@pytest.fixture
def valid_employer_creation_request_body(initialize_factories_session) -> Dict[str, Any]:
    # EIN should match an EIN of an Employer in our database
    employer = EmployerFactory.create()
    ein = employer.employer_fein

    return {
        "email_address": fake.email(),
        "password": fake.password(length=12),
        "role": {"role_description": "Employer"},
        "user_leave_administrator": {"employer_fein": "-".join([ein[:2], ein[2:9]]),},
    }


def test_users_post_claimant(client, valid_claimant_creation_request_body):
    response = client.post("/v1/users", json=valid_claimant_creation_request_body,)

    assert response.status_code == 201


def test_users_post_employer(client, valid_employer_creation_request_body):
    response = client.post("/v1/users", json=valid_employer_creation_request_body,)

    assert response.status_code == 201


def test_users_post_openapi_validation(client, valid_employer_creation_request_body):
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
            "employer_fein": f"**-***{employer.employer_fein[5:]}",
            "employer_id": str(employer.employer_id),
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
            "employer_fein": f"**-***{employer.employer_fein[5:]}",
            "employer_id": str(employer.employer_id),
            "verified": False,
            "has_verification_data": False,
        }
    ]


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

    test_db_session.refresh(user)
    assert user.consented_to_data_sharing is True


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

    test_db_session.refresh(user_2)
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
            "employer_fein": f"**-***{employer.employer_fein[5:]}",
            "employer_id": str(employer.employer_id),
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
            "employer_fein": f"**-***{employer.employer_fein[5:]}",
            "employer_id": str(employer.employer_id),
            "verified": False,
            "has_verification_data": False,
        }
    ]
