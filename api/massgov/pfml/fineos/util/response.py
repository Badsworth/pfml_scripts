import json
from typing import Any, Optional, Set

import requests

import massgov.pfml.util.newrelic.events as newrelic_util
from massgov.pfml.fineos import exception


def fineos_document_empty_dates_to_none(response_json: dict) -> dict:
    # Document effectiveFrom and effectiveTo are empty and set to empty strings
    # These fields are not set by the portal. Set to none to avoid validation errors.

    if response_json["effectiveFrom"] == "":
        response_json["effectiveFrom"] = None

    if response_json["effectiveTo"] == "":
        response_json["effectiveTo"] = None

    # Documents uploaded through FINEOS use "dateCreated" instead of "receivedDate"
    if response_json["receivedDate"] == "":
        if response_json["dateCreated"]:
            response_json["receivedDate"] = response_json["dateCreated"]
        else:
            response_json["receivedDate"] = None

    return response_json


def get_fineos_correlation_id(response: requests.Response) -> Optional[Any]:
    try:
        response_payload_json = response.json()
        if isinstance(response_payload_json, dict):
            return response_payload_json.get("correlationId", "")
    except ValueError:
        pass

    return None


def is_expected_failure(err_message: str, expected_failures: Optional[Set[str]]) -> bool:
    if expected_failures:
        lowercased_msg = err_message.lower()

        for expected in expected_failures:
            if expected in lowercased_msg:
                return True

    return False


def log_validation_error(
    err: exception.FINEOSClientBadResponse, expected_failures: Optional[Set[str]] = None
) -> None:
    """ Parse 422 responses from FINEOS and log individual validation errors.
        422 responses are expected to be in this format:

        [
           { "validationMessage": "error 1" },
           { "validationMessage": "error 2" },
           ...
        ]
    """
    if err.response_status != 422:
        return

    # Try to parse the error as a JSON array.
    # If it isn't JSON, log the full response message.
    try:
        error_json = json.loads(err.message)  # noqa: B306
    except Exception:
        newrelic_util.log_and_capture_exception(err.message)  # noqa: B306
        return

    # Some FINEOS responses are dicts, but 422 errors should be arrays.
    # If it isn't an array, log the full response message.
    if isinstance(error_json, dict):
        newrelic_util.log_and_capture_exception(err.message)  # noqa: B306
        return

    # Log each validation error object. If there's no validationMessage, just log the whole object.
    # If the message matches one of the expected failures, don't log it.
    for error in error_json:
        message = error.get("validationMessage")
        if message is None:
            newrelic_util.log_and_capture_exception(json.dumps(error))
        elif not is_expected_failure(message, expected_failures):
            newrelic_util.log_and_capture_exception(message)
