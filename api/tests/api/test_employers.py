import pytest

pytestmark = pytest.mark.skip("not setup to test database stuff right now")


def test_employers_get(client, test_employer):
    response = client.get("/v1/employers/{}".format(test_employer["employer_id"]))
    assert response.status_code == 200


def test_employers_get_404(client):
    response = client.get("/v1/employers/0038386b-94dc-48c1-a674-f9a14f94e07b")
    assert response.status_code == 404
