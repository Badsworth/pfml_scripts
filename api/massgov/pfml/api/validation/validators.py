#
# Custom validation implementations to support custom API response formats
#

import flask
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
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail, ValidationException

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
    # Should this header string be defined as a global constant? If so, where?
    warn_on_required = flask.request.headers.get("X-PFML-Warn-On-Missing-Required-Fields", None)

    errors = list(validator_decorator.validator.iter_errors(data))
    if errors:
        error_list = []
        for error in errors:
            # Fix an error where items in error.path are ints. Convert to strings.
            field_path = list(map(lambda x: str(x), list(error.path)))
            error_list.append(
                ValidationErrorDetail(
                    message=error.message,
                    type=error.validator,
                    rule=error.validator_value,
                    field=".".join(field_path) if field_path else "",
                )
            )

        if warn_on_required:
            warning_list = list(filter(lambda error: error.type == "required", error_list))
            error_list = list(filter(lambda error: error.type != "required", error_list))

            flask.request.warning_list = warning_list

            if len(error_list) > 0:
                invalid_data_payload = data.get("data", data)
                raise ValidationException(
                    errors=error_list, message=error_message, data=invalid_data_payload
                )
        else:
            invalid_data_payload = data.get("data", data)
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

        validate_schema_util(self, data, "Request Validation Error")


class CustomResponseBodyValidator(ResponseBodyValidator):
    def __init__(self, *args, **kwargs):
        super(CustomResponseBodyValidator, self).__init__(
            *args, validator=DefaultsEnforcingDraft4ResponseValidator, **kwargs
        )

    def validate_schema(self, data, url):
        validate_schema_util(self, data, "Response Validation Error")


class CustomResponseValidator(ResponseValidator):
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

        # Do not validate GET responses.
        if flask.request.method == "GET":
            return True

        if url.endswith("/status"):
            return True

        self.validate_helper(response_body, status_code, headers, url)
