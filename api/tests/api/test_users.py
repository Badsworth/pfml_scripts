import uuid

import pytest

# every test in here requires real resources
pytestmark = pytest.mark.integration


def test_users_get(client, user):
    response = client.get("/v1/users/{}".format(user.user_id))
    response_body = response.get_json()

    assert response.status_code == 200
    assert response_body["user_id"] == user.user_id


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


def test_users_patch(client, user):
    assert user.consented_to_data_sharing is False

    body = {"consented_to_data_sharing": True}
    response = client.patch("v1/users/{}".format(user.user_id), json=body)
    response_body = response.get_json()
    assert response.status_code == 200
    assert response_body["consented_to_data_sharing"] is True


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
def test_users_patch_invalid(client, user, request_body, expected_code):
    response = client.patch("/v1/users/{}".format(user.user_id), json=request_body)

    assert response.status_code == expected_code


def test_users_patch_404(client):
    body = {"consented_to_data_sharing": True}
    response = client.patch(
        "/v1/users/{}".format("00000000-0000-0000-0000-000000000000"), json=body
    )
    assert response.status_code == 404
