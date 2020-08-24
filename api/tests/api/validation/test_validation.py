import pathlib

import connexion

from massgov.pfml.api.util.response import success_response
from massgov.pfml.api.validation import add_error_handlers_to_app, get_custom_validator_map

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

    request_validation_success_response_with_warnings = client.post(
        "/user", headers={"X-PFML-Warn-On-Missing-Required-Fields": "true"}, json=MISSING_DATA_USER
    ).get_json()

    assert request_validation_success_response_with_warnings.get("warnings", None) is not None
    assert request_validation_success_response_with_warnings["status_code"] == 200

    request_validation_error_response_with_warnings = client.post(
        "/user", headers={"X-PFML-Warn-On-Missing-Required-Fields": "true"}, json=INVALID_USER
    ).get_json()

    assert request_validation_error_response_with_warnings.get("warnings", None) is not None
    assert request_validation_error_response_with_warnings["status_code"] == 400

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
