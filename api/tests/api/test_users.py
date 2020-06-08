import pytest

from massgov.pfml.db.models.factories import UserFactory

# every test in here requires real resources
pytestmark = pytest.mark.integration


def test_users_get(client):
    user = UserFactory.create()
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
