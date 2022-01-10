from unittest import mock

import pytest

import tests.api
from massgov.pfml.db.models.applications import Application
from massgov.pfml.db.models.factories import ApplicationFactory


@pytest.fixture
def application(user):
    return ApplicationFactory.create(user=user)


@pytest.fixture
def application_withholding_set(user):
    return ApplicationFactory.create(user=user, is_withholding_tax=False)


@mock.patch("massgov.pfml.api.applications.send_tax_withholding_preference")
@mock.patch("massgov.pfml.api.applications.logger.info")
def test_submit_withholding_preference_success(
    mock_info_logger, mock_send_tax_preference, client, application, auth_token, test_db_session
):
    application_id = application.application_id
    application = test_db_session.query(Application).get(application_id)
    assert application.is_withholding_tax is None

    response = client.post(
        "/v1/applications/{}/submit_tax_withholding_preference".format(application_id),
        headers={"Authorization": "Bearer {}".format(auth_token)},
        json={"is_withholding_tax": True},
    )
    assert response.status_code == 201
    response_body = response.get_json()
    assert response_body["data"]["is_withholding_tax"] is True
    assert application.is_withholding_tax is True

    msg_arg, _ = mock_info_logger.call_args_list[0]
    assert msg_arg[0] == "tax_withholding_preference_submit success"

    mock_send_tax_preference.assert_called_once_with(application, True)


def test_submit_withholding_preference_selection_missing(client, application, auth_token):
    response = client.post(
        "/v1/applications/{}/submit_tax_withholding_preference".format(application.application_id),
        headers={"Authorization": "Bearer {}".format(auth_token)},
        json={"is_withholding_tax": None},
    )
    tests.api.validate_error_response(
        response,
        400,
        message="Invalid request",
        errors=[
            {
                "field": "is_withholding_tax",
                "message": "Tax withholding preference is required",
                "type": "required",
            }
        ],
    )


@mock.patch("massgov.pfml.api.applications.logger.info")
def test_submit_withholding_preference_already_set(
    mock_info_logger, client, application_withholding_set, auth_token, test_db_session
):
    application_id = application_withholding_set.application_id
    application = test_db_session.query(Application).get(application_id)
    assert application.is_withholding_tax is False

    response = client.post(
        "/v1/applications/{}/submit_tax_withholding_preference".format(application_id),
        headers={"Authorization": "Bearer {}".format(auth_token)},
        json={"is_withholding_tax": True},
    )
    tests.api.validate_error_response(
        response,
        400,
        message="Invalid request",
        errors=[
            {
                "field": "is_withholding_tax",
                "message": "Tax withholding preference is already set",
                "type": "duplicate",
            }
        ],
    )
    assert application.is_withholding_tax is False
    assert mock_info_logger.call_count == 1
    msg_arg, _ = mock_info_logger.call_args_list[0]
    assert msg_arg[0] == "submit_tax_withholding_preference failure - preference already set"
