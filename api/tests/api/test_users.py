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


def test_users_get_current(client, user, auth_token):
    response = client.get("/v1/users/current", headers={"Authorization": f"Bearer {auth_token}"})
    response_body = response.get_json()

    assert response.status_code == 200
    assert response_body["user_id"] == user.user_id


def test_users_get_current_404(client):
    response = client.get("/v1/users/current")

    assert response.status_code == 404


def test_users_patch(client, user, test_db_session):
    assert user.consented_to_data_sharing is False

    body = {"consented_to_data_sharing": True}
    response = client.patch("v1/users/{}".format(user.user_id), json=body)
    response_body = response.get_json()
    assert response.status_code == 200
    assert response_body["consented_to_data_sharing"] is True

    test_db_session.refresh(user)
    assert user.consented_to_data_sharing is True


def test_users_patch_authenticated_user(client, user, auth_token, test_db_session):
    assert user.consented_to_data_sharing is False

    body = {"consented_to_data_sharing": True}
    response = client.patch(
        "v1/users/{}".format(user.user_id),
        json=body,
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    response_body = response.get_json()
    assert response.status_code == 200
    assert response_body["consented_to_data_sharing"] is True

    test_db_session.refresh(user)
    assert user.consented_to_data_sharing is True


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
