#
# Custom validation implementations to support custom API response formats
#
import re
from typing import Callable, Optional

import jsonschema
from connexion.decorators.response import ResponseValidator
from connexion.decorators.validation import (
    ParameterValidator,
    RequestBodyValidator,
    ResponseBodyValidator,
)
from connexion.json_schema import Draft4RequestValidator, Draft4ResponseValidator
from connexion.utils import is_null

import massgov.pfml.util.logging as logging
import massgov.pfml.util.newrelic.events as newrelic_util
from massgov.pfml.api.validation.exceptions import (
    IssueType,
    ValidationErrorDetail,
    ValidationException,
)

logger = logging.get_logger(__name__)


# via https://python-jsonschema.readthedocs.io/en/stable/faq/#why-doesn-t-my-schema-s-default-property-set-the-default-on-my-instance
def extend_with_set_default(validator_class):
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for property, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(property, subschema["default"])

        for error in validate_properties(validator, properties, instance, schema):
            yield error

    return jsonschema.validators.extend(validator_class, {"properties": set_defaults})


DefaultsEnforcingDraft4RequestValidator = extend_with_set_default(Draft4RequestValidator)
DefaultsEnforcingDraft4ResponseValidator = extend_with_set_default(Draft4ResponseValidator)


def validate_schema_util(validator_decorator, data, error_message):
    errors = list(validator_decorator.validator.iter_errors(data))
    if errors:
        error_list = []
        for error in errors:
            # Fix an error where items in error.path are ints. Convert to strings.
            field_path = list(map(lambda x: str(x), list(error.path)))
            error_value = (
                error.instance if error.validator == "type" or error.validator == "enum" else None
            )
            error_list.append(
                ValidationErrorDetail(
                    message=error.message,
                    type=error.validator,
                    rule=error.validator_value,
                    field=".".join(field_path) if field_path else "",
                    value=type(error_value).__name__ if error.validator == "type" else error_value,
                )
            )

        invalid_data_payload = data
        if isinstance(data, dict) and "data" in data:
            invalid_data_payload = data["data"]
        raise ValidationException(
            errors=error_list, message=error_message, data=invalid_data_payload
        )


class CustomParameterValidator(ParameterValidator):
    def __init__(self, *args, **kwargs):
        super(CustomParameterValidator, self).__init__(*args, **kwargs)

    def validate_formdata_parameter_list(self, request):
        # In multipart/form-data requests in the OpenAPI spec requestBody, the payload is sent as formBody elements. Connexion tries to validate these as parameters and will fail since those properties are included as part of the request body. Example: https://swagger.io/docs/specification/describing-request-body/multipart-requests/
        # Below we check if the requestBody is multipart/form-data and skip parameter validation.The validation will be handled by RequestBodyValidator.validate_formdata_parameter_list (https://github.com/zalando/connexion/blob/master/connexion/decorators/validation.py#L125)
        is_multi_part_form = request.headers.get("Content-Type") and request.headers.get(
            "Content-Type"
        ).startswith("multipart/form-data")
        if is_multi_part_form:
            return None

        return ParameterValidator.validate_formdata_parameter_list(self, request)


class CustomRequestBodyValidator(RequestBodyValidator):
    def __init__(self, *args, **kwargs):
        super(CustomRequestBodyValidator, self).__init__(
            *args, validator=DefaultsEnforcingDraft4RequestValidator, **kwargs
        )

    def validate_schema(self, data, url):
        if self.is_null_value_valid and is_null(data):
            return None

        if not self.is_null_value_valid and is_null(data):
            errors = [
                ValidationErrorDetail(
                    field="", message="Missing request body", type=IssueType.required
                )
            ]

            raise ValidationException(errors=errors, message="Request Validation Error", data=data)

        validate_schema_util(self, data, "Request Validation Error")


class CustomResponseBodyValidator(ResponseBodyValidator):
    def __init__(self, *args, **kwargs):
        super(CustomResponseBodyValidator, self).__init__(
            *args, validator=DefaultsEnforcingDraft4ResponseValidator, **kwargs
        )

    def validate_schema(self, data, url):
        validate_schema_util(self, data, "Response Validation Error")


def log_validation_error(
    validation_exception: ValidationException,
    error: ValidationErrorDetail,
    unexpected_error_check_func: Optional[Callable[[ValidationErrorDetail], bool]] = None,
    only_warn: bool = False,
) -> None:
    # Create a readable message for the individual error.
    # Do not use the error's actual message since it may include PII.
    #
    # Note that the field is modified in the message so array-based fields can be aggregated, e.g.
    #
    #   error.field: data.0.absence_periods.12.reason_qualifier_two
    #   aggregated_field: data.<NUM>.absence_periods.<NUM>.reason_qualifier_two
    #
    aggregated_field = error.field

    if aggregated_field:
        aggregated_field = re.sub(r"\.\d+\.", ".<NUM>.", aggregated_field)

    message = "%s (field: %s, type: %s, rule: %s)" % (
        validation_exception.message,
        aggregated_field,
        error.type,
        error.rule,
    )

    log_attributes = {
        "error.class": "ValidationException",
        "error.type": error.type,
        "error.rule": error.rule,
        "error.field": error.field,
        "error.value": error.value,
    }
    if unexpected_error_check_func and not unexpected_error_check_func(error):
        logger.info(message, extra=log_attributes)
    else:
        # Log explicit errors in the case of unexpected validation errors.
        newrelic_util.log_and_capture_exception(message, extra=log_attributes, only_warn=only_warn)


class CustomResponseValidator(ResponseValidator):
    response_validation = False

    @classmethod
    def enable_response_validation(cls):
        cls.response_validation = True

    def validate_helper(self, data, status_code, headers, url):
        content_type = headers.get("Content-Type", self.mimetype)
        content_type = content_type.rsplit(";", 1)[0]  # remove things like utf8 metadata

        response_schema = self.operation.response_schema(str(status_code), content_type)

        v = CustomResponseBodyValidator(response_schema)
        v.validate_schema(data, url)

    def validate_response(self, data, status_code, headers, url):
        # Only validate json responses
        if headers.get("Content-Type") != "application/json":
            return True

        response_body = self.operation.json_loads(data)

        if url.endswith("/status"):
            return True

        try:
            self.validate_helper(response_body, status_code, headers, url)
        except ValidationException as validation_exception:
            if CustomResponseValidator.response_validation:
                raise validation_exception
            for error in validation_exception.errors:
                # For Response Validation exceptions, we want to log as warnings rather than errors
                log_validation_error(validation_exception, error, only_warn=True)
            return True
