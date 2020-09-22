import uuid

import pytest

from massgov.pfml.db.models.factories import UserFactory

# every test in here requires real resources
pytestmark = pytest.mark.integration


def test_users_get(client, user, auth_token):
    response = client.get(
        "/v1/users/{}".format(user.user_id), headers={"Authorization": f"Bearer {auth_token}"}
    )
    response_body = response.get_json()

    assert response.status_code == 200
    assert response_body.get("data")["user_id"] == str(user.user_id)


def test_users_unauthorized_get(client, user, auth_token):
    user_2 = UserFactory.create()

    response = client.get(
        "/v1/users/{}".format(user_2.user_id), headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 403


def test_users_get_404(client, auth_token):
    response = client.get(
        "/v1/users/{}".format("00000000-0000-0000-0000-000000000000"),
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 404


def test_users_get_fineos_forbidden(client, fineos_user, fineos_user_token):
    # Fineos role cannot access this endpoint
    response = client.get(
        "/v1/users/{}".format(fineos_user.user_id),
        headers={"Authorization": f"Bearer {fineos_user_token}"},
    )
    assert response.status_code == 403


def test_users_get_current(client, user, auth_token):
    response = client.get("/v1/users/current", headers={"Authorization": f"Bearer {auth_token}"})
    response_body = response.get_json()

    assert response.status_code == 200
    assert response_body.get("data")["user_id"] == str(user.user_id)


def test_users_get_current_fineos_forbidden(client, fineos_user_token):
    # Fineos role cannot access this endpoint
    response = client.get(
        "/v1/users/current", headers={"Authorization": f"Bearer {fineos_user_token}"}
    )
    assert response.status_code == 403


def test_users_get_mask_email(client, user, auth_token):
    response = client.get(
        "/v1/users/{}".format(user.user_id), headers={"Authorization": f"Bearer {auth_token}"}
    )
    response_body = response.get_json()
    email = response_body.get("data")["email_address"]

    assert response.status_code == 200
    assert "*****" in email


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

    assert response.status_code == 403

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
    assert response.status_code == 404


def test_users_patch_fineos_forbidden(client, fineos_user, fineos_user_token):
    # Fineos role cannot access this endpoint
    body = {"consented_to_data_sharing": True}
    response = client.patch(
        "v1/users/{}".format(fineos_user.user_id),
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )
    assert response.status_code == 403
