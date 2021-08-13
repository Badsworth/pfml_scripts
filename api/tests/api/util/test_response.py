#
# Tests for massgov.pfml.api.util.response
#

from werkzeug.exceptions import NotFound

import massgov.pfml.api.util.response as response_util
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail

user_payload = {
    "id": "5072cd9d-5aca-4c93-979b-8adf131bdb89",
    "username": "testUser1",
    "email": "testUser1@example.com",
}


def test_create_success():
    response = response_util.success_response(message="Success", data=user_payload)
    validate_success_response(response)
    assert response.data is not None

    response = response_util.success_response(message="Success", data=[user_payload, user_payload])
    validate_success_response(response)
    assert response.data is not None
    assert isinstance(response.data, list)
    assert len(response.data) == 2


def test_create_success_with_warning():
    response = response_util.success_response(
        message="successfuly created user",
        data=user_payload,
        warnings=[
            ValidationErrorDetail(
                message="first_name is required", type="required", field="first_name"
            ),
            ValidationErrorDetail(
                message="last_name is required", type="required", field="last_name"
            ),
        ],
    )

    validate_success_response(response)
    assert response.warnings is not None and len(response.warnings) == 2


def test_create_error_response():
    response = response_util.error_response(
        status_code=NotFound,
        message="Error creating user.",
        errors=[
            ValidationErrorDetail(
                message="first_name is required", type="required", field="first_name"
            ),
            ValidationErrorDetail(
                message="last_name is required", type="required", field="last_name"
            ),
        ],
        data={"item": user_payload},
    )

    validate_error_response(response)
    assert response.errors is not None and len(response.errors) == 2


# validation helpers


def validate_success_response(response_obj):
    assert 200 <= response_obj.status_code < 300
    assert response_obj.data is not None


def validate_error_response(response_obj):
    assert 400 <= response_obj.status_code < 500
    assert response_obj.errors is not None
