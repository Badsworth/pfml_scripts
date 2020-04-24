import pytest

pytestmark = pytest.mark.skip("not setup to test database stuff right now")


def test_users_post(client, test_user):
    # body = {"user_id": "009fa369-291b-403f-a85a-15e938c26f2f", "email": "janedoe@example.com", "auth_id": "00000000-291b-403f-a85a-15e938c26f2f"}
    body = {
        "user_id": "009fa369-291b-403f-a85a-15e938c26f2f",
        "active_directory_id": "00000000-291b-403f-a85a-15e938c26f2f",
        "status": "verified",
    }
    response = client.post("/v1/users", json=body)
    assert response.status_code == 200


def test_users_get(client, test_user):
    response = client.get("/v1/users/009fa369-291b-403f-a85a-15e938c26f2f")
    assert response.status_code == 200


def test_users_get_404(client):
    response = client.get("/v1/users/91a27f03-6ee3-46af-9e24-8e0d7c7d500e")
    assert response.status_code == 404


def test_user_post_missing_parameters(client):
    body = {"active_directory_id": "00000000-291b-403f-a85a-15e938c26f2f"}
    response = client.post("/v1/users", json=body)
    assert response.status_code == 500
