def test_employers_get(client, test_employer):
    response = client.get("/v1/employers/{}".format(test_employer["employer_id"]))
    assert response.status_code == 200


def test_employers_get_404(client):
    response = client.get("/v1/employers/12345")
    assert response.status_code == 404
