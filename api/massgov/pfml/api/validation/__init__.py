#
# Utility functions to support custom validation handlers on connexion
#

from flask.wrappers import Response
from werkzeug.exceptions import BadRequest

import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging as logging
from massgov.pfml.api.validation.exceptions import ValidationException
from massgov.pfml.api.validation.validators import (
    CustomParameterValidator,
    CustomRequestBodyValidator,
    CustomResponseValidator,
)

logger = logging.get_logger(__name__)


def validation_request_handler(validation_exception: ValidationException) -> Response:
    errors = []
    for error in validation_exception.errors:
        errors.append(response_util.validation_issue(error))

    return response_util.error_response(
        status_code=BadRequest,
        message=validation_exception.message,
        errors=errors,
        data=validation_exception.data,
    ).to_api_response()


def add_error_handlers_to_app(connexion_app):
    connexion_app.add_error_handler(ValidationException, validation_request_handler)


def get_custom_validator_map():
    validator_map = {
        "body": CustomRequestBodyValidator,
        "response": CustomResponseValidator,
        "parameter": CustomParameterValidator,
    }
    return validator_map
