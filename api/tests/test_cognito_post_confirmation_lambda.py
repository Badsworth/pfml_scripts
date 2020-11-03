import json
import os

import pytest

import massgov.pfml.cognito_post_confirmation_lambda.lib as lib


@pytest.fixture
def event_json():
    with open(
        f"{os.path.dirname(__file__)}/../lambdas/cognito_post_confirmation/test_event.json"
    ) as fp:
        event = fp.read()

    return event


@pytest.fixture
def event_dict(event_json):
    return json.loads(event_json)


def test_main_success(test_db_session, event_dict, logging_fix):
    from massgov.pfml.db.models.employees import User
    import massgov.pfml.cognito_post_confirmation_lambda.main as main

    main.db_session_raw = test_db_session

    response = main.handler(event_dict, {})

    created_user = (
        test_db_session.query(User)
        .filter(User.active_directory_id == event_dict["request"]["userAttributes"]["sub"])
        .one()
    )

    expected_response = event_dict
    expected_response["request"]["clientMetadata"] = None

    assert created_user.email_address == event_dict["request"]["userAttributes"]["email"]
    assert response == expected_response


def test_main_does_not_throw_exception_on_bad_input(test_db_session, logging_fix):
    from massgov.pfml.db.models.employees import User
    import massgov.pfml.cognito_post_confirmation_lambda.main as main

    main.db_session_raw = test_db_session

    bad_event = {"foo": "bar"}
    response = main.handler(bad_event, {})

    num_users = test_db_session.query(User).count()

    assert num_users == 0
    assert response == bad_event


def test_lib_success(test_db_session, event_dict):
    from massgov.pfml.db.models.employees import User

    event = lib.PostConfirmationEvent(**event_dict)

    response = lib.handler(test_db_session, event, {})

    created_user = (
        test_db_session.query(User)
        .filter(User.active_directory_id == event.request.userAttributes["sub"])
        .one()
    )

    assert created_user.email_address == event.request.userAttributes["email"]
    assert response == event


def test_lib_skip_non_post_confirmation_event(test_db_session, event_dict):
    from massgov.pfml.db.models.employees import User

    event = lib.PostConfirmationEvent(**event_dict)
    event.triggerSource = "foo"

    response = lib.handler(test_db_session, event, {})

    user_that_should_not_exist = (
        test_db_session.query(User)
        .filter(User.active_directory_id == event.request.userAttributes["sub"])
        .one_or_none()
    )

    assert user_that_should_not_exist is None
    assert response == event


def test_user_active_directory_id_uniqueness(test_db_session, event_dict):
    from massgov.pfml.db.models.employees import User

    event1 = lib.PostConfirmationEvent(**event_dict)

    # create second event with different email address
    event_dict["request"]["userAttributes"]["email"] = "user2@example.com"
    event2 = lib.PostConfirmationEvent(**event_dict)

    # a request for user comes in
    lib.handler(test_db_session, event1, {})

    # user is created as normal
    created_user_initial = (
        test_db_session.query(User)
        .filter(User.active_directory_id == event1.request.userAttributes["sub"])
        .one()
    )

    # a second request for same user comes in
    lib.handler(test_db_session, event2, {})

    # there should still only be one User record with the requested `active_directory_id`
    created_user_after_second_request = (
        test_db_session.query(User)
        .filter(User.active_directory_id == event2.request.userAttributes["sub"])
        .one()
    )

    # make sure it's the same user as before
    assert created_user_initial.user_id == created_user_after_second_request.user_id
    assert created_user_initial.email_address == created_user_after_second_request.email_address
