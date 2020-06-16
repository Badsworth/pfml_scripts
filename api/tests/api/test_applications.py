import uuid


# The UUID used in this test was generated online. Hopefully it will never match any of
# the IDs generated by our seed data generator. If it does the test will fail.
def test_applications_get_invalid(client):
    response = client.get(
        "/v1/applications/{}".format("b26aa854-dd50-4aed-906b-c72b062f0275"),
        headers={"user_id": str(uuid.uuid4())},
    )
    assert response.status_code == 404


def test_applications_get_valid(client, test_application):
    application_id = test_application["application_id"]

    response = client.get(
        "/v1/applications/{}".format(application_id), headers={"user_id": str(uuid.uuid4())},
    )

    assert response.status_code == 200
    response_body = response.get_json()
    assert response_body.get("application_id") == application_id


def test_applications_get_no_userid(client, test_application):
    application_id = test_application["application_id"]
    response = client.get("/v1/applications/{}".format(application_id))
    assert response.status_code == 400


def test_applications_get_all_for_user(client, test_applications):
    response = client.get("/v1/applications", headers={"user_id": str(uuid.uuid4())})
    response_body = response.get_json()

    response_matches_test_applications = match_response_to_test_applications(
        response_body, test_applications
    )
    assert response_matches_test_applications is True

    assert response.status_code == 200


def match_response_to_test_applications(response_body, test_applications):
    lists_match = True
    for application in test_applications:
        if (
            len(
                list(
                    filter(
                        lambda x: x["application_id"] == application["application_id"],
                        response_body,
                    )
                )
            )
            == 0
        ):
            lists_match = False
        if (
            len(
                list(
                    filter(
                        lambda x: x["application_nickname"] == application["application_nickname"],
                        response_body,
                    )
                )
            )
            == 0
        ):
            lists_match = False

    return lists_match


def test_applications_post_start_app(client, create_app_statuses):
    response = client.post("/v1/applications", headers={"user_id": str(uuid.uuid4())})
    response_body = response.get_json()
    application_id = response_body.get("application_id")
    assert uuid.UUID(application_id).version == 4
    assert response.status_code == 201


def test_application_patch(client, test_application):
    application_id = test_application["application_id"]
    # Change last name
    test_application["last_name"] = "Perez"
    # Remove foreign keys as DB does not have all tables populated
    test_application.pop("employer_id", None)
    test_application.pop("employee_id", None)

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


def test_application_patch_leave_reason(client, test_application):
    application_id = test_application["application_id"]

    response = client.patch(
        "/v1/applications/{}".format(application_id),
        headers={"user_id": str(uuid.uuid4())},
        json={"leave_details": {"reason": "Serious Health Condition - Employee"}},
    )
    assert response.status_code == 200

    response = client.get(
        "/v1/applications/{}".format(application_id), headers={"user_id": str(uuid.uuid4())},
    )
    response_body = response.get_json()
    print(response_body)
    updated_leave_details = response_body.get("leave_details")
    updated_leave_reason = updated_leave_details.get("reason")
    assert updated_leave_reason == "Serious Health Condition - Employee"


def test_application_patch_minimum_payload(client, test_application):
    application_id = test_application.get("application_id")
    update_json = {"first_name": "John"}

    response = client.patch(
        "/v1/applications/{}".format(application_id),
        headers={"user_id": str(uuid.uuid4())},
        json=update_json,
    )
    assert response.status_code == 200


def test_application_patch_null_values(client, test_application):
    application_id = test_application.get("application_id")

    response = client.patch(
        "/v1/applications/{}".format(application_id),
        headers={"user_id": str(uuid.uuid4())},
        json=null_request_body,
    )
    assert response.status_code == 200


def test_application_post_submit_app(client, test_application, create_app_statuses):
    application_id = test_application["application_id"]
    response = client.post(
        "/v1/applications/{}/submit_application".format(application_id),
        headers={"user_id": str(uuid.uuid4())},
    )
    assert response.status_code == 201

    response = client.get(
        "/v1/applications/{}".format(application_id), headers={"user_id": str(uuid.uuid4())},
    )
    assert response.status_code == 200

    response_body = response.get_json()
    assert response_body["status"] == "Completed"


null_request_body = {
    "application_id": "2a340cf8-6d2a-4f82-a075-73588d003f8f",
    "application_nickname": None,
    "employee_ssn": None,
    "employer_fein": None,
    "first_name": None,
    "last_name": None,
    "leave_details": {
        "continuous_leave_periods": [
            {
                "end_date": None,
                "end_date_full_day": None,
                "end_date_off_hours": None,
                "end_date_off_minutes": None,
                "expected_return_to_work_date": None,
                "last_day_worked": None,
                "start_date": None,
                "start_date_full_day": None,
                "start_date_off_hours": None,
                "start_date_off_minutes": None,
                "status": None,
            }
        ],
        "employer_notification_date": None,
        "employer_notification_method": None,
        "employer_notified": None,
        "intermittent_leave_periods": [
            {
                "duration": None,
                "duration_basis": None,
                "end_date": None,
                "frequency": None,
                "frequency_interval": None,
                "frequency_interval_basis": None,
                "start_date": None,
            }
        ],
        "reason": None,
        "reason_qualifier": None,
        "reduced_schedule_leave_periods": [
            {
                "end_date": None,
                "friday_off_hours": None,
                "friday_off_minutes": None,
                "monday_off_hours": None,
                "monday_off_minutes": None,
                "saturday_off_hours": None,
                "saturday_off_minutes": None,
                "start_date": None,
                "status": None,
                "sunday_off_hours": None,
                "sunday_off_minutes": None,
                "thursday_off_hours": None,
                "thursday_off_minutes": None,
                "tuesday_off_hours": None,
                "tuesday_off_minutes": None,
                "wednesday_off_hours": None,
                "wednesday_off_minutes": None,
            }
        ],
        "relationship_qualifier": None,
        "relationship_to_caregiver": None,
    },
    "occupation": None,
    "payment_preferences": [
        {
            "account_details": {
                "account_name": None,
                "account_no": None,
                "account_type": None,
                "routing_number": None,
            },
            "cheque_details": {"name_to_print_on_check": None},
            "description": None,
            "is_default": None,
            "payment_method": None,
        }
    ],
}
