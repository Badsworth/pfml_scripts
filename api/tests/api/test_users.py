import uuid

import pytest

import massgov.pfml.api.generate_fake_data as fake

# every test in here requires real resources
pytestmark = pytest.mark.integration


@pytest.fixture
def user_post_request_body():
    return {
        "auth_id": str(uuid.uuid4()),
        "email_address": fake.fake.email(),
        "consented_to_data_sharing": True,
    }


def test_users_post(client, user_post_request_body):
    response = client.post("/v1/users", json=user_post_request_body)
    response_body = response.get_json()

    assert response.status_code == 200
    # TODO: do we really care about asserting everything in the response
    assert response_body["user_id"]
    del response_body["user_id"]
    assert response_body == dict(
        auth_id=user_post_request_body["auth_id"],
        email_address=user_post_request_body["email_address"],
        status="unverified",
        consented_to_data_sharing=user_post_request_body["consented_to_data_sharing"],
    )


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
    response_body = response.get_json()

    assert response.status_code == 200
    assert response_body["user_id"] == test_user["user_id"]


def test_users_get_404(client):
    response = client.get("/v1/users/{}".format("00000000-0000-0000-0000-000000000000"))
    assert response.status_code == 404


# technically an integration test as client -> app -> create db, though the
# actual handler is a mock
def test_users_get_current(client):
    response = client.get("/v1/users/current")
    response_body = response.get_json()

    assert response.status_code == 200
    assert response_body["user_id"] == "009fa369-291b-403f-a85a-15e938c26f2f"
