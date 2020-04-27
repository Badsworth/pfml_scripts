import uuid

import pytest

import massgov.pfml.api.generate_fake_data as fake

pytestmark = pytest.mark.skip("not setup to test database stuff right now")


@pytest.fixture
def user_post_request_body():
    return {"auth_id": str(uuid.uuid4()), "email_address": fake.fake.email()}


def test_users_post(client, user_post_request_body):
    response = client.post("/v1/users", json=user_post_request_body)
    assert response.status_code == 200


def test_user_post_missing_parameters(client, user_post_request_body):
    del user_post_request_body["auth_id"]
    response = client.post("/v1/users", json=user_post_request_body)
    assert response.status_code == 400


def test_user_post_invalid_format(client, user_post_request_body):
    user_post_request_body["email_address"] = "joe"
    response = client.post("/v1/users", json=user_post_request_body)
    assert response.status_code == 400


def test_users_get(client, test_user):
    response = client.get("/v1/users/{}".format(test_user["user_id"]))
    assert response.status_code == 200


def test_users_get_404(client):
    response = client.get("/v1/users/{}".format("00000000-0000-0000-0000-000000000000"))
    assert response.status_code == 404
