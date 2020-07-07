#
# Tests for massgov.pfml.api.util.response
#

import pytest
from werkzeug.exceptions import NotFound

import massgov.pfml.api.util.response as response_util
from massgov.pfml.api.util.response import ErrorIssue, WarningIssue

user_payload = {
    "id": "5072cd9d-5aca-4c93-979b-8adf131bdb89",
    "username": "testUser1",
    "email": "testUser1@example.com",
}


def test_create_issue():
    issue1 = response_util.field_issue(WarningIssue.MISSING_FIELD, "first_name")
    assert issue1.type == WarningIssue.MISSING_FIELD.value.type
    assert issue1.message == WarningIssue.MISSING_FIELD.value.message
    assert issue1.field == "first_name"
    assert issue1.extra is None

    with pytest.raises(
        ValueError, match="Expected extra object with properties: \\['multiple_of'\\]"
    ):
        response_util.field_issue(ErrorIssue.MULTIPLE_OF, "income")

    with pytest.raises(
        ValueError,
        match="Extra object properties do not match - expected: \\['multiple_of'\\], got: \\['multiple'\\]",
    ):
        response_util.field_issue(ErrorIssue.MULTIPLE_OF, "income", {"multiple": 5})

    issue2 = response_util.field_issue(ErrorIssue.MULTIPLE_OF, "income", {"multiple_of": 5})
    assert issue2.extra == {"multiple_of": 5}

    issue3 = response_util.custom_issue("CustomType", "Custom message")
    assert issue3.type == "CustomType"
    assert issue3.message == "Custom message"
    assert issue3.field is None
    assert issue3.extra is None


def test_create_success():
    response = response_util.success_response(
        message="Success", data=response_util.single_data_payload(user_payload)
    )
    validate_success_response(response)
    assert response.data.item is not None
    assert response.data.items is None

    response = response_util.success_response(
        message="Success", data=response_util.multiple_data_payload([user_payload, user_payload])
    )
    validate_success_response(response)
    assert response.data.item is None
    assert response.data.items is not None and len(response.data.items) == 2


def test_create_success_with_warning():
    response = response_util.success_response(
        message="successfuly created user",
        data=response_util.single_data_payload(user_payload),
        warning=[
            response_util.field_issue(WarningIssue.MISSING_FIELD, "first_name"),
            response_util.field_issue(WarningIssue.MISSING_FIELD, "last_name"),
        ],
    )

    validate_success_response(response)
    assert response.warning is not None and len(response.warning) == 2


def test_create_error_response():
    response = response_util.error_response(
        status_code=NotFound,
        message="Error creating user.",
        error=[
            response_util.field_issue(ErrorIssue.MISSING_FIELD, "first_name"),
            response_util.field_issue(ErrorIssue.MISSING_FIELD, "last_name"),
        ],
        data={"item": user_payload},
    )

    validate_error_response(response)
    assert response.error is not None and len(response.error) == 2


# validation helpers


def validate_success_response(response_obj):
    assert 200 <= response_obj.status_code < 300
    assert response_obj.data is not None


def validate_error_response(response_obj):
    assert 400 <= response_obj.status_code < 500
    assert response_obj.error is not None
