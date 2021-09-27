def test_cors_success(app_cors):
    client = app_cors.app.test_client()
    body = {"email": "janedoe@example.com", "auth_id": "00000"}
    response = client.post("v1/users", json=body, headers={"Origin": "http://example.com"})

    assert response.headers.get("Access-Control-Allow-Origin") == "http://example.com"
    assert response.headers.get("Access-Control-Allow-Credentials") == "true"


def test_cors_invalid(app_cors):
    client = app_cors.app.test_client()
    response = client.options(
        "v1/users",
        headers={"Origin": "http://notthistime.com", "Access-Control-Request-Method": "POST"},
    )
    assert response.headers.get("Access-Control-Allow-Origin") is None
