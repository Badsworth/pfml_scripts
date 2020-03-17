def test_users_get(client, test_user):
    response = client.get("/v1/users/{}".format(test_user["user_id"]))
    assert response.status_code == 200


def test_users_get_404(client):
    response = client.get("/v1/users/{}".format("12345"))
    assert response.status_code == 404


def test_users_post(client):
    body = {"email": "joe@example.com", "auth_id": "00000"}
    response = client.post("/v1/users", json=body)
    assert response.status_code == 200


def test_user_post_missing_parameters(client):
    body = {"email": "joe@example.com"}
    response = client.post("/v1/users", json=body)
    assert response.status_code == 400
