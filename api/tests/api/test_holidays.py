from massgov.pfml.db.models.applications import sync_holidays


def test_holidays_search(client, test_db_session):
    sync_holidays(test_db_session)

    json = {"bad_request": "is bad"}
    response = client.post("/v1/holidays/search", json=json)
    assert response.status_code == 400

    json = {"terms": {"start_date": "2021-12-25", "end_date": "2022-01-02"}}
    response = client.post("/v1/holidays/search", json=json)
    assert response.status_code == 200

    response_body = response.get_json()
    assert response_body.get("data") == [
        {"name": "New Year's Day", "date": "2022-01-01"},
    ]

    json = {"terms": {"start_date": "2021-12-25", "end_date": "2022-03-02"}}
    response = client.post("/v1/holidays/search", json=json)
    assert response.status_code == 200

    response_body = response.get_json()
    assert response_body.get("data") == [
        {"name": "New Year's Day", "date": "2022-01-01"},
        {"name": "Martin Luther King, Jr. Day", "date": "2022-01-17"},
        {"name": "Washington's Birthday", "date": "2022-02-21"},
    ]

    json = {"terms": {"start_date": "2022-03-02", "end_date": "2022-03-29"}}
    response = client.post("/v1/holidays/search", json=json)
    assert response.status_code == 200

    response_body = response.get_json()
    assert response_body.get("data") == []
