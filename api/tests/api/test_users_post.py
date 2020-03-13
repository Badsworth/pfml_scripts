import massgov.pfml.api
import massgov.pfml.api.users

app = massgov.pfml.api.create_app()


def test_valid_post():
    client = app.app.test_client()
    body = {"email": "joe@example.com", "auth_id": "00000"}
    response = client.post("/v1/users", json=body)
    assert response.status_code == 200


def test_missing_post_parameters():
    client = app.app.test_client()
    body = {"email": "joe@example.com"}
    response = client.post("/v1/users", json=body)
    assert response.status_code == 400
