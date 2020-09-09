def test_status_get(client):
    response = client.get("/v1/status")

    assert response.status_code == 200
