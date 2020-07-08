import uuid
from datetime import date, datetime

from freezegun import freeze_time
from sqlalchemy import inspect

from massgov.pfml.api.models.applications.responses import ApplicationStatus
from massgov.pfml.db.models.applications import (
    ApplicationPaymentPreference,
    ContinuousLeavePeriod,
    RelationshipToCareGiver,
)
from massgov.pfml.db.models.employees import Occupation, PaymentType
from massgov.pfml.db.models.factories import ApplicationFactory


def sqlalchemy_object_as_dict(obj):
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}


# The UUID used in this test was generated online. Hopefully it will never match any of
# the IDs generated by our seed data generator. If it does the test will fail.
def test_applications_get_invalid(client):
    response = client.get(
        "/v1/applications/{}".format("b26aa854-dd50-4aed-906b-c72b062f0275"),
        headers={"user_id": str(uuid.uuid4())},
    )
    assert response.status_code == 404


@freeze_time("2020-01-01")
def test_applications_get_valid(client):
    application = ApplicationFactory.create(updated_time=datetime.now())

    response = client.get(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
    )

    assert response.status_code == 200
    response_body = response.get_json()
    assert response_body.get("application_id") == str(application.application_id)
    assert response_body.get("updated_time") == "2020-01-01T00:00:00Z"
    assert response_body.get("status") == ApplicationStatus.Started.value


def test_applications_get_no_userid(client):
    application = ApplicationFactory.create()
    response = client.get("/v1/applications/{}".format(application.application_id))
    assert response.status_code == 400


def test_applications_get_with_payment_preferences(client, test_db_session):
    application = ApplicationFactory.create()
    application.payment_preferences = [
        ApplicationPaymentPreference(
            description="Test", is_default=True, account_name="Foo", name_in_check="Bob"
        )
    ]

    test_db_session.commit()

    response = client.get(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
    )

    assert response.status_code == 200
    response_body = response.get_json()
    assert response_body.get("application_id") == str(application.application_id)

    payment_preferences = response_body.get("payment_preferences")
    assert payment_preferences
    assert len(payment_preferences) == 1

    payment_preference = payment_preferences[0]
    assert payment_preference["description"] == "Test"
    assert payment_preference["is_default"] is True
    assert payment_preference["account_details"]["account_name"] == "Foo"
    assert payment_preference["cheque_details"]["name_to_print_on_check"] == "Bob"


def test_applications_get_all_for_user(client):
    applications = [ApplicationFactory.create(), ApplicationFactory.create()]

    response = client.get("/v1/applications", headers={"user_id": str(uuid.uuid4())})
    assert response.status_code == 200

    response_body = response.get_json()
    for (application, app_response) in zip(applications, response_body):
        assert str(application.application_id) == app_response["application_id"]
        assert application.nickname == app_response["application_nickname"]


def test_applications_post_start_app(client):
    response = client.post("/v1/applications", headers={"user_id": str(uuid.uuid4())})
    response_body = response.get_json()

    application_id = response_body.get("application_id")
    assert uuid.UUID(application_id).version == 4
    assert response.status_code == 201


@freeze_time("2020-01-01")
def test_application_patch(client, test_db_session):
    application = ApplicationFactory.create()
    update_request_body = sqlalchemy_object_as_dict(application)
    # Change last name
    update_request_body["last_name"] = "Perez"
    update_request_body["occupation"] = "Engineer"
    update_request_body["leave_details"] = {"relationship_to_caregiver": "Parent"}

    # Remove foreign keys as DB does not have all tables populated
    update_request_body.pop("employer_id", None)
    update_request_body.pop("employee_id", None)

    # Seed lookup values until they are done automatically
    occupation = Occupation(occupation_id=1, occupation_description="Engineer")
    test_db_session.add(occupation)
    relationship = RelationshipToCareGiver(relationship_to_caregiver_description="Parent")
    test_db_session.add(relationship)
    test_db_session.commit()

    response = client.patch(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
        json=update_request_body,
    )

    assert response.status_code == 200

    response = client.get(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
    )

    response_body = response.get_json()
    assert response_body.get("last_name") == "Perez"
    assert response_body.get("updated_time") == "2020-01-01T00:00:00Z"
    assert response_body.get("occupation") == "Engineer"
    assert response_body.get("leave_details").get("relationship_to_caregiver") == "Parent"


def test_application_patch_leave_reason(client, test_db_session):
    application = ApplicationFactory.create()

    # set to empty value
    application.leave_reason = None
    test_db_session.commit()

    response = client.patch(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
        json={"leave_details": {"reason": "Serious Health Condition - Employee"}},
    )

    assert response.status_code == 200

    response = client.get(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
    )
    response_body = response.get_json()
    updated_leave_details = response_body.get("leave_details")
    assert updated_leave_details
    updated_leave_reason = updated_leave_details.get("reason")
    assert updated_leave_reason == "Serious Health Condition - Employee"


def test_application_patch_add_leave_period(client):
    application = ApplicationFactory.create()

    response = client.patch(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
        json={"leave_details": {"continuous_leave_periods": [{"start_date": "2020-06-11"}]}},
    )

    assert response.status_code == 200

    response = client.get(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
    )
    response_body = response.get_json()
    updated_leave_details = response_body.get("leave_details")
    assert updated_leave_details

    updated_leave_periods = updated_leave_details.get("continuous_leave_periods")
    assert updated_leave_periods
    assert len(updated_leave_periods) == 1

    updated_leave_period = updated_leave_periods[0]
    assert updated_leave_period["leave_period_id"]
    assert updated_leave_period["start_date"] == "2020-06-11"


def test_application_patch_update_leave_period(client, test_db_session):
    application = ApplicationFactory.create()

    leave_period = ContinuousLeavePeriod(
        start_date=date(2020, 6, 11), application_id=application.application_id
    )
    test_db_session.add(leave_period)
    test_db_session.commit()

    response = client.patch(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
        json={
            "leave_details": {
                "continuous_leave_periods": [
                    {"leave_period_id": leave_period.leave_period_id, "start_date": "2020-06-12"}
                ]
            }
        },
    )

    assert response.status_code == 200

    response = client.get(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
    )
    response_body = response.get_json()
    updated_leave_details = response_body.get("leave_details")
    assert updated_leave_details

    updated_leave_periods = updated_leave_details.get("continuous_leave_periods")
    assert updated_leave_periods
    assert len(updated_leave_periods) == 1

    updated_leave_period = updated_leave_periods[0]
    assert updated_leave_period["leave_period_id"]
    assert updated_leave_period["start_date"] == "2020-06-12"


def test_application_patch_update_leave_period_belonging_to_other_application_blocked(
    client, test_db_session
):
    application_1 = ApplicationFactory.create()
    application_2 = ApplicationFactory.create()

    leave_period = ContinuousLeavePeriod(
        start_date=date(2020, 6, 11), application_id=application_1.application_id
    )
    test_db_session.add(leave_period)
    test_db_session.commit()

    response = client.patch(
        "/v1/applications/{}".format(application_2.application_id),
        headers={"user_id": str(uuid.uuid4())},
        json={
            "leave_details": {
                "continuous_leave_periods": [
                    {"leave_period_id": leave_period.leave_period_id, "start_date": "2020-06-12"}
                ]
            }
        },
    )

    assert response.status_code == 403

    # assert existing leave period has not changed
    test_db_session.refresh(leave_period)
    assert leave_period.application_id == application_1.application_id
    assert leave_period.start_date == date(2020, 6, 11)

    # assert other application does not have the leave period
    response = client.get(
        "/v1/applications/{}".format(application_2.application_id),
        headers={"user_id": str(uuid.uuid4())},
    )
    response_body = response.get_json()
    updated_leave_details = response_body.get("leave_details")
    assert updated_leave_details

    updated_leave_periods = updated_leave_details.get("continuous_leave_periods")
    assert len(updated_leave_periods) == 0


def test_application_patch_add_payment_preferences(client, test_db_session):
    application = ApplicationFactory.create()

    # seed lookup value we care about
    payment_method = PaymentType(payment_type_description="Check")
    test_db_session.add(payment_method)
    test_db_session.commit()

    response = client.patch(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
        json={
            "payment_preferences": [
                {
                    "description": "Test",
                    "payment_method": "Check",
                    "account_details": {"account_type": "Checking"},
                    "cheque_details": {"name_to_print_on_check": "Bob"},
                }
            ]
        },
    )

    assert response.status_code == 200

    response = client.get(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
    )
    response_body = response.get_json()
    payment_preferences_response = response_body.get("payment_preferences")
    assert len(payment_preferences_response) == 1

    payment_preference = payment_preferences_response[0]
    assert payment_preference.get("description") == "Test"
    assert payment_preference.get("payment_method") == "Check"
    assert payment_preference.get("account_details").get("account_type") == "Checking"
    assert payment_preference.get("cheque_details").get("name_to_print_on_check") == "Bob"


def test_application_patch_update_payment_preferences(client, test_db_session):
    application = ApplicationFactory.create()

    payment_preference = ApplicationPaymentPreference(
        description="Foo", application_id=application.application_id
    )
    test_db_session.add(payment_preference)
    test_db_session.commit()

    response = client.patch(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
        json={
            "payment_preferences": [
                {"payment_preference_id": payment_preference.payment_pref_id, "description": "Bar",}
            ]
        },
    )

    assert response.status_code == 200

    response = client.get(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
    )
    response_body = response.get_json()
    payment_preferences_response = response_body.get("payment_preferences")
    assert len(payment_preferences_response) == 1

    payment_preference_response = payment_preferences_response[0]
    assert payment_preference_response["payment_preference_id"] == str(
        payment_preference.payment_pref_id
    )
    assert payment_preference_response["description"] == "Bar"

    test_db_session.refresh(payment_preference)
    assert payment_preference.description == "Bar"


def test_application_patch_update_payment_preference_belonging_to_other_application_blocked(
    client, test_db_session
):
    application_1 = ApplicationFactory.create()
    application_2 = ApplicationFactory.create()

    payment_preference = ApplicationPaymentPreference(
        description="Foo", application_id=application_1.application_id
    )
    test_db_session.add(payment_preference)
    test_db_session.commit()

    response = client.patch(
        "/v1/applications/{}".format(application_2.application_id),
        headers={"user_id": str(uuid.uuid4())},
        json={
            "payment_preferences": [
                {"payment_preference_id": payment_preference.payment_pref_id, "description": "Bar",}
            ]
        },
    )

    assert response.status_code == 403

    # assert existing leave period has not changed
    test_db_session.refresh(payment_preference)
    assert payment_preference.application_id == application_1.application_id
    assert payment_preference.description == "Foo"

    # assert other application does not have the leave period
    response = client.get(
        "/v1/applications/{}".format(application_2.application_id),
        headers={"user_id": str(uuid.uuid4())},
    )
    response_body = response.get_json()
    payment_preferences_response = response_body.get("payment_preferences")
    assert len(payment_preferences_response) == 0


def test_application_patch_minimum_payload(client):
    application = ApplicationFactory.create()

    response = client.patch(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
        json={},
    )

    assert response.status_code == 200

    response = client.get(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
    )


def test_application_patch_null_values(client):
    application = ApplicationFactory.create()

    null_request_body = {
        "application_id": application.application_id,
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
                    "account_number": None,
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

    response = client.patch(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
        json=null_request_body,
    )

    assert response.status_code == 200


def test_application_patch_invalid_values(client):
    application = ApplicationFactory.create()

    response = client.patch(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
        json={"leave_details": {"reduced_schedule_leave_periods": {}}},
    )

    assert response.status_code == 400


def test_application_patch_keys_not_in_body_retain_existing_value(client, test_db_session):
    application = ApplicationFactory.create()

    # establish some existing value
    application.first_name = "Foo"
    test_db_session.commit()

    response = client.get(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
    )
    response_body = response.get_json()
    assert response_body.get("first_name") == "Foo"

    # update some other field
    response = client.patch(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
        json={"last_name": "Bar"},
    )
    assert response.status_code == 200

    # ensure the existing field still has it's existing value
    test_db_session.refresh(application)
    assert application.first_name == "Foo"

    # for extra measure
    response = client.get(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
    )
    response_body = response.get_json()
    assert response_body.get("first_name") == "Foo"


def test_application_patch_key_set_to_null_does_null_field(client, test_db_session):
    application = ApplicationFactory.create()

    # establish some existing value
    application.first_name = "Foo"
    test_db_session.commit()

    response = client.get(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
    )
    response_body = response.get_json()
    assert response_body.get("first_name") == "Foo"

    # null the field
    response = client.patch(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
        json={"first_name": None},
    )
    assert response.status_code == 200

    # ensure it's null in the db
    test_db_session.refresh(application)
    assert application.first_name is None

    # for extra measure
    response = client.get(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
    )
    response_body = response.get_json()
    assert response_body.get("first_name") is None


def test_application_post_submit_app(client):
    application = ApplicationFactory.create()
    assert not application.completed_time

    response = client.post(
        "/v1/applications/{}/submit_application".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
    )
    assert response.status_code == 201

    response = client.get(
        "/v1/applications/{}".format(application.application_id),
        headers={"user_id": str(uuid.uuid4())},
    )
    assert response.status_code == 200

    response_body = response.get_json()
    status = response_body.get("status")
    assert status == ApplicationStatus.Completed.value
