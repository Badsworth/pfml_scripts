import json

import pytest

import tests.api
from massgov.pfml.api.employers import EmployerResponse
from massgov.pfml.db.models.factories import EmployerFactory


@pytest.fixture
def employer():
    employer = EmployerFactory.create()
    return employer


def test_get_employer_info(client, auth_token, employer):
    response = client.get(
        f"/v1/employers/{employer.employer_id}",
        headers={"Authorization": "Bearer {}".format(auth_token)},
    )
    assert response.status_code == 200
    response_data = response.get_json().get("data")
    assert response_data == json.loads(EmployerResponse.from_orm(employer).json())


def test_get_404(client, auth_token):
    response = client.get(
        "/v1/employers/00000000-291b-403f-a85a-15e938c26f2f",
        headers={"Authorization": "Bearer {}".format(auth_token)},
    )
    tests.api.validate_error_response(response, 404)


def test_get_employer_fineos_user_forbidden(client, fineos_user_token, employer):
    # Fineos role cannot access this endpoint
    response = client.get(
        f"/v1/employers/{employer.employer_id}",
        headers={"Authorization": "Bearer {}".format(fineos_user_token)},
    )
    assert response.status_code == 403


def test_employee_auth_get(disable_employer_endpoint, client, auth_token, employer):
    response = client.get(
        f"/v1/employers/{employer.employer_id}",
        headers={"Authorization": "Bearer {}".format(auth_token)},
    )
    tests.api.validate_error_response(response, 403)
