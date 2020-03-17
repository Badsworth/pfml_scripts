def test_wages_get(client, test_wages):
    (wages, employee) = test_wages

    response = client.get("/v1/wages?employee_id={}".format(employee["employee_id"]))
    assert response.status_code == 200


def test_wages_get_404(client):
    response = client.get("/v1/wages?employee_id=0000000")
    assert response.status_code == 404
