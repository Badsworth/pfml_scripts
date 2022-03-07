def test_holidays_search(client):

    json = {"bad_request": "is bad"}
    response = client.post("/v1/holidays/search", json=json)
    assert response.status_code == 400

    json = {"terms": {"start_date": "2021-12-25", "end_date": "2022-01-02"}}
    response = client.post("/v1/holidays/search", json=json)
    assert response.status_code == 200

    response_body = response.get_json()
    assert response_body.get("data") == [
        {"name": "New Year's Day", "date": "2022-01-01"},
        {"name": "Christmas Day", "date": "2021-12-25"},
    ]
