#
# Utility functions to support custom validation handlers on connexion
#
import traceback

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
    Unauthorized,
)

import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging as logging
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail, ValidationException
from massgov.pfml.api.validation.validators import (
    CustomParameterValidator,
    CustomRequestBodyValidator,
    CustomResponseValidator,
)

logger = logging.get_logger(__name__)


def validation_request_handler(validation_exception: ValidationException) -> Response:
    errors = []
    for error in validation_exception.errors:
        logger.info(
            validation_exception.message,
            extra={
                "error.class": "ValidationException",
                "error.type": error.type,
                "error.rule": error.rule,
                "error.field": error.field,
            },
        )

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
    stacktrace = "".join(traceback.TracebackException.from_exception(exception).format())

    logger.error(
        str(exception), extra={"error.class": type(error).__name__, "traceback": stacktrace}
    )

    return http_exception_handler(error)


def add_error_handlers_to_app(connexion_app):
    connexion_app.add_error_handler(ValidationException, validation_request_handler)
    connexion_app.add_error_handler(BadRequestProblem, connexion_400_handler)
    connexion_app.add_error_handler(ExtraParameterProblem, connexion_400_handler)
    # These are all handled with the same generic exception handler to make them uniform in structure.
    connexion_app.add_error_handler(NotFound, http_exception_handler)
    connexion_app.add_error_handler(Forbidden, http_exception_handler)
    connexion_app.add_error_handler(Unauthorized, http_exception_handler)
    connexion_app.add_error_handler(InternalServerError, internal_server_error_handler)
    connexion_app.add_error_handler(pydantic.ValidationError, handle_pydantic_validation_error)


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

        errors.append(
            ValidationErrorDetail(
                type=err_type,
                message=e["msg"],
                rule=None,
                field=".".join(str(loc) for loc in e["loc"]),
            )
        )

    return ValidationException(errors=errors, message="Request Validation Error", data={})
