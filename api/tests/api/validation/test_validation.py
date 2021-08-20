import logging  # noqa: B1
import pathlib

import connexion
import pytest
from pydantic import ValidationError

from massgov.pfml.api.util.response import success_response
from massgov.pfml.api.validation import (
    add_error_handlers_to_app,
    convert_pydantic_error_to_validation_exception,
    get_custom_validator_map,
    log_validation_error,
)
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail, ValidationException
from massgov.pfml.fineos.models.customer_api import Customer

TEST_FOLDER = pathlib.Path(__file__).parent
INVALID_USER = {"first_name": 123, "interests": ["sports", "activity", "sports"]}
VALID_USER = {"first_name": "Jane", "last_name": "Smith", "interests": ["sports", "sketching"]}
MISSING_DATA_USER = {"first_name": "Foo"}


def post_user():
    """handler for test api (see 'test.yml' file in this directory)"""
    return success_response(message="Success", data=VALID_USER,).to_api_response()


def get_user():
    """handler for test api (see 'test.yml' file in this directory)"""
    return success_response(message="Success", data=MISSING_DATA_USER).to_api_response()


def post_user_invalid_response():
    """handler for test api (see 'test.yml' file in this directory)"""
    return success_response(message="Success", data=INVALID_USER).to_api_response()


# validate end to end
def test_request_response_validation():
    spec_file_path = TEST_FOLDER / "test.yml"

    validator_map = get_custom_validator_map()

    flask_app = connexion.FlaskApp("Test API")
    flask_app.add_api(
        spec_file_path, validator_map=validator_map, strict_validation=True, validate_responses=True
    )

    add_error_handlers_to_app(flask_app)

    client = flask_app.app.test_client()

    request_validation_error_response = client.post("/user", json=INVALID_USER).get_json()
    validate_invalid_response(
        request_validation_error_response, "/user", "Request Validation Error"
    )

    request_validation_error_response_no_body = client.post("/user").get_json()

    assert request_validation_error_response_no_body.get("message") == "Request Validation Error"
    assert (
        request_validation_error_response_no_body.get("errors")[0]["message"]
        == "Missing request body"
    )

    response_validation_error_response = client.post(
        "/user-invalid-response", json=VALID_USER,
    ).get_json()
    validate_invalid_response(
        response_validation_error_response,
        "/user-invalid-response",
        "Response Validation Error",
        field_prefix="data.",
    )

    success_response = client.post("/user", json=VALID_USER,).get_json()

    request_validation_error_response_get_warnings = client.get(
        "/user", json=MISSING_DATA_USER
    ).get_json()
    assert request_validation_error_response_get_warnings.get("warnings", None) is None

    request_validation_error_response_no_warnings = client.post(
        "/user", json=MISSING_DATA_USER
    ).get_json()
    assert request_validation_error_response_no_warnings.get("warnings", None) is None

    assert success_response["message"] == "Success"
    assert success_response["data"] is not None
    assert success_response.get("data") is not None


def validate_invalid_response(response, url, message, field_prefix=""):
    assert response["status_code"] == 400
    assert response["meta"] is not None
    assert response["meta"]["method"] == "POST"
    assert response["meta"]["resource"] == url
    assert response["message"] == message
    assert len(response["errors"]) == 4

    def filter_errors_by_field_value(field_name, value):
        return list(filter(lambda e: e[field_name] == value, response["errors"]))

    first_name_errors = filter_errors_by_field_value(
        "field", "{}{}".format(field_prefix, "first_name")
    )
    assert len(first_name_errors) == 1
    assert first_name_errors[0]["type"] == "type"
    assert first_name_errors[0]["rule"] == "string"

    last_name_errors = filter_errors_by_field_value("type", "required")
    assert len(last_name_errors) == 1
    assert last_name_errors[0]["rule"] == ["first_name", "last_name"]

    interests_errors = filter_errors_by_field_value(
        "field", "{}{}".format(field_prefix, "interests")
    )
    assert len(interests_errors) == 2
    assert interests_errors[0]["type"] == "maxItems"
    assert interests_errors[0]["rule"] == 2
    assert interests_errors[1]["type"] == "uniqueItems"
    assert interests_errors[1]["rule"]


def test_log_validation_error_unexpected_exception_handling(caplog):
    caplog.set_level(logging.INFO)  # noqa: B1

    unexpected_exception = ValidationErrorDetail(
        rule="number", type="type", field="cents", message="something that might be PII",
    )

    expected_exception = ValidationErrorDetail(
        rule="anything", type="format", field="anything", message="something that might be PII 2",
    )

    errors = [unexpected_exception, expected_exception, unexpected_exception, expected_exception]

    exception = ValidationException(errors, "Request Validation Exception", {})

    for error in exception.errors:
        log_validation_error(exception, error)

    assert [(r.funcName, r.levelname, r.message) for r in caplog.records] == [
        (
            "log_and_capture_exception",
            "ERROR",
            "Request Validation Exception (field: cents, type: type, rule: number)",
        ),
        (
            "log_validation_error",
            "INFO",
            "Request Validation Exception (field: anything, type: format, rule: anything)",
        ),
        (
            "log_and_capture_exception",
            "ERROR",
            "Request Validation Exception (field: cents, type: type, rule: number)",
        ),
        (
            "log_validation_error",
            "INFO",
            "Request Validation Exception (field: anything, type: format, rule: anything)",
        ),
    ]


class TestConvertPydanticErrorToValidationException:
    @pytest.fixture
    def validation_error_first_name(self):
        try:
            Customer(firstName="a" * 51)
        except ValidationError as e:
            return e

    @pytest.fixture
    def validation_error_multiple_issues(self):
        try:
            Customer(firstName="a" * 51, lastName="a" * 51)
        except ValidationError as e:
            return e

    def test_validation_error_name_too_long(self, validation_error_first_name):
        validation_exception = convert_pydantic_error_to_validation_exception(
            validation_error_first_name
        )
        assert validation_exception is not None

        errors = validation_exception.errors
        error_detail = next((e for e in errors if e.field == "firstName"), None)

        assert error_detail is not None
        assert (
            error_detail.message
            == 'Error in field: "firstName". Ensure this value has at most 50 characters.'
        )

    def test_validation_error_multiple_issues(self, validation_error_multiple_issues):
        validation_exception = convert_pydantic_error_to_validation_exception(
            validation_error_multiple_issues
        )
        assert validation_exception is not None

        errors = validation_exception.errors

        error_detail = next((e for e in errors if e.field == "firstName"), None)
        assert error_detail is not None
        assert (
            error_detail.message
            == 'Error in field: "firstName". Ensure this value has at most 50 characters.'
        )

        error_detail = next((e for e in errors if e.field == "lastName"), None)
        assert error_detail is not None
        assert (
            error_detail.message
            == 'Error in field: "lastName". Ensure this value has at most 50 characters.'
        )
