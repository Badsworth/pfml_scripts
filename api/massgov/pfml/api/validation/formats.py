# When imported, this file registers validation functions for formats that
# are used in the OpenAPI schema file. Connexion will run these validations
# for fields that are defined using these formats.
#
import re
from datetime import datetime

from jsonschema import draft4_format_checker

RE_UUID4 = re.compile("^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}", re.I)


@draft4_format_checker.checks("email", raises=ValueError)
def is_valid_email(email):
    # If email is not a string, it will get caught by other validation
    # so we can skip format validation.
    if not isinstance(email, str):
        return True
    regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    if not re.fullmatch(regex, email):
        raise ValueError()
    return True


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


@draft4_format_checker.checks("uuid", raises=ValueError)
def is_uuid(val):
    # If value is not a string, it will get caught by the type validator
    # so we can skip format validation.
    if not isinstance(val, str):
        return True

    if not RE_UUID4.match(val):
        raise ValueError(f"'{val}' is not a valid uuid4")
    return True
