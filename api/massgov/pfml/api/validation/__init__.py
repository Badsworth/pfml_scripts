#
# Utility functions to support custom validation handlers on connexion
#
from typing import Union

import botocore.exceptions
import connexion.apps.flask_app
import pydantic
from connexion.exceptions import BadRequestProblem, ExtraParameterProblem, ProblemException
from flask.wrappers import Response
from werkzeug.exceptions import (
    BadRequest,
    Forbidden,
    HTTPException,
    InternalServerError,
    NotFound,
    ServiceUnavailable,
    Unauthorized,
)

import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging as logging
import massgov.pfml.util.newrelic.events as newrelic_util
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail, ValidationException
from massgov.pfml.api.validation.validators import (
    CustomParameterValidator,
    CustomRequestBodyValidator,
    CustomResponseValidator,
)
from massgov.pfml.fineos.exception import FINEOSFatalUnavailable

UNEXPECTED_ERROR_TYPES = {"enum", "type"}
logger = logging.get_logger(__name__)


def is_unexpected_validation_error(error: ValidationErrorDetail) -> bool:
    return (
        error.type in UNEXPECTED_ERROR_TYPES
        or error.type.startswith("type_error")
        or error.type.startswith("value_error")
    )


def log_validation_error(
    validation_exception: ValidationException, error: ValidationErrorDetail
) -> None:
    # Create a readable message for the individual error.
    # Do not use the error's actual message since it may include PII.
    message = "%s (field: %s, type: %s, rule: %s)" % (
        validation_exception.message,
        error.field,
        error.type,
        error.rule,
    )

    log_attributes = {
        "error.class": "ValidationException",
        "error.type": error.type,
        "error.rule": error.rule,
        "error.field": error.field,
    }

    if not is_unexpected_validation_error(error):
        logger.info(message, extra=log_attributes)
    else:
        # Log explicit errors in the case of unexpected validation errors.
        newrelic_util.log_and_capture_exception(message, extra=log_attributes)


def validation_request_handler(validation_exception: ValidationException) -> Response:
    errors = []
    for error in validation_exception.errors:
        log_validation_error(validation_exception, error)
        errors.append(response_util.validation_issue(error))

    return response_util.error_response(
        status_code=BadRequest,
        message=validation_exception.message,
        errors=errors,
        data=validation_exception.data,
    ).to_api_response()


def connexion_400_handler(exception: ProblemException) -> Response:
    # Ensure that we are still logging 400 info, since
    # we are now ignoring most of these errors in New Relic.
    #
    # _do not log response data_, only the machine-readable errors and
    # messages which should definitely not have sensitive info.
    logger.info(exception.detail, extra={"error.class": exception.type})

    return connexion.apps.flask_app.FlaskApp.common_error_handler(exception)


def http_exception_handler(http_exception: HTTPException) -> Response:
    return response_util.error_response(
        status_code=http_exception, message=str(http_exception.description), errors=[]
    ).to_api_response()


def internal_server_error_handler(error: InternalServerError) -> Response:
    # Use the original exception if it exists.
    #
    # Ignore the mypy type error because it hasn't caught up to werkzeug 1.0.0.
    #
    # see: https://github.com/python/typeshed/pull/4210
    #
    exception = error.original_exception or error  # type: ignore

    logger.exception(str(exception), extra={"error.class": type(exception).__name__})

    return http_exception_handler(error)


def handle_fineos_unavailable_error(error: FINEOSFatalUnavailable) -> Response:
    return response_util.error_response(
        status_code=ServiceUnavailable,
        message="The service is currently unavailable. Please try again later.",
        errors=[response_util.custom_issue("fineos_client", "FINEOS is currently unavailable")],
    ).to_api_response()


def handle_aws_connection_error(
    error: Union[botocore.exceptions.ConnectionError, botocore.exceptions.HTTPClientError]
) -> Response:
    return response_util.error_response(
        status_code=ServiceUnavailable,
        message="Connection was closed before receiving a valid response from endpoint.",
        errors=[],
    ).to_api_response()


def add_error_handlers_to_app(connexion_app):
    connexion_app.add_error_handler(ValidationException, validation_request_handler)
    connexion_app.add_error_handler(BadRequestProblem, connexion_400_handler)
    connexion_app.add_error_handler(ExtraParameterProblem, connexion_400_handler)
    connexion_app.add_error_handler(pydantic.ValidationError, handle_pydantic_validation_error)
    connexion_app.add_error_handler(FINEOSFatalUnavailable, handle_fineos_unavailable_error)
    connexion_app.add_error_handler(
        botocore.exceptions.HTTPClientError, handle_aws_connection_error
    )
    connexion_app.add_error_handler(
        botocore.exceptions.ConnectionError, handle_aws_connection_error
    )

    # These are all handled with the same generic exception handler to make them uniform in structure.
    connexion_app.add_error_handler(NotFound, http_exception_handler)
    connexion_app.add_error_handler(HTTPException, http_exception_handler)
    connexion_app.add_error_handler(Forbidden, http_exception_handler)
    connexion_app.add_error_handler(Unauthorized, http_exception_handler)

    # Override the default internal server error handler to prevent Flask
    # from using logging.error with a generic message. We want to log
    # the original exception.
    #
    # We handle all 500s here but only expect InternalServerError instances,
    # as indicated by the documentation. Calling out InterrnalServerError explicitly
    # here would not override the default internal server error handler.
    #
    connexion_app.add_error_handler(500, internal_server_error_handler)


def get_custom_validator_map():
    validator_map = {
        "body": CustomRequestBodyValidator,
        "response": CustomResponseValidator,
        "parameter": CustomParameterValidator,
    }
    return validator_map


def handle_pydantic_validation_error(exception: pydantic.ValidationError) -> Response:
    return validation_request_handler(convert_pydantic_error_to_validation_exception(exception))


# Some pydantic errors aren't of a format we like
pydantic_error_type_map = {"value_error.date": "date"}


# Note that pydantic errors are reported in New Relic
# before being converted into validation exception responses.
def convert_pydantic_error_to_validation_exception(
    exception: pydantic.ValidationError,
) -> ValidationException:
    errors = []

    for e in exception.errors():
        err_type = e["type"]
        if err_type in pydantic_error_type_map:
            err_type = pydantic_error_type_map[err_type]

        err_field = e["loc"][0]
        err_message = e["msg"]

        errors.append(
            ValidationErrorDetail(
                type=err_type,
                message=f'Error in field: "{err_field}". {err_message.capitalize()}.',
                rule=None,
                field=".".join(str(loc) for loc in e["loc"]),
            )
        )

    return ValidationException(errors=errors, message="Request Validation Error", data={})
