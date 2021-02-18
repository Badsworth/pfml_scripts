# When imported, this file registers validation functions for formats that
# are used in the OpenAPI schema file. Connexion will run these validations
# for fields that are defined using these formats.
#
from datetime import datetime

from jsonschema import draft4_format_checker


# Date is not validated by default using the Draft4 validator,
# so we re-implement it here and register it.
@draft4_format_checker.checks("date", raises=ValueError)
def is_date(val):
    # If date is not a string, it will get caught by the type validator
    # so we can skip format validation.
    if not isinstance(val, str):
        return True

    return datetime.strptime(val, "%Y-%m-%d")


# Some dates are masked in responses and can be re-sent in requests
# as the masked value, so we need to represent that here. We use a custom
# format instead of -oneOf to maintain a more human-readable error message.
@draft4_format_checker.checks("maskable_date", raises=ValueError)
def is_maskable_date(val):
    # If date is not a string, it will get caught by the type validator
    # so we can skip format validation.
    if not isinstance(val, str):
        return True

    try:
        return datetime.strptime(val, "%Y-%m-%d")
    except ValueError:
        return datetime.strptime(val, "****-%m-%d")
