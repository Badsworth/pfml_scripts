import uuid


def test_applications_get_valid(client, test_application):
    application_id = test_application["application_id"]
    response = client.get(
        "/v1/applications/{}".format(application_id), headers={"user_id": str(uuid.uuid4())},
    )
    assert response.status_code == 200


def test_applications_get_invalid(client):
    response = client.get(
        "/v1/applications/{}".format("foo"), headers={"user_id": str(uuid.uuid4())},
    )
    assert response.status_code == 404


def test_applications_get_no_userid(client, test_application):
    application_id = test_application["application_id"]
    response = client.get("/v1/applications/{}".format(application_id))
    assert response.status_code == 400


def test_applications_get_all_for_user(client):
    response = client.get("/v1/applications", headers={"user_id": str(uuid.uuid4())})
    assert response.status_code == 200


def test_applications_post_start_app(client):
    response = client.post("/v1/applications", headers={"user_id": str(uuid.uuid4())})
    response_body = response.get_json()
    application_id = response_body.get("application_id")
    assert uuid.UUID(application_id).version == 4
    assert response.status_code == 201


def test_application_patch(client, test_application):
    application_id = test_application["application_id"]
    # Change last name
    test_application["last_name"] = "Perez"
    response = client.patch(
        "/v1/applications/{}".format(application_id),
        headers={"user_id": str(uuid.uuid4())},
        json=test_application,
    )
    assert response.status_code == 200

    response = client.get(
        "/v1/applications/{}".format(application_id), headers={"user_id": str(uuid.uuid4())},
    )
    response_body = response.get_json()
    updated_last_name = response_body.get("last_name")
    assert updated_last_name == "Perez"


def test_application_post_submit_app(client, test_application):
    application_id = test_application["application_id"]
    response = client.post(
        "/v1/applications/{}/submit_application".format(application_id),
        headers={"user_id": str(uuid.uuid4())},
    )
    assert response.status_code == 201
