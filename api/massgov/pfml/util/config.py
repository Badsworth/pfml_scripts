import os
from typing import Any, Optional

from pydantic.validators import bool_validator

from massgov.pfml.util.aws_ssm import get_secret


def get_secret_from_env(aws_ssm: Any, key: str) -> Optional[str]:
    secret_value: str

    if os.getenv(key) is not None:
        secret_value = os.environ[key]
    elif os.getenv(f"{key}_SSM_PATH") is not None:
        secret_value = get_secret(aws_ssm, os.environ[f"{key}_SSM_PATH"])
    else:
        return None

    return secret_value


def get_env_bool(key: str, default: Optional[bool] = None) -> Optional[bool]:
    """Read environment variable value as a boolean.

    Supports most commonly used values for boolean-ness:
    - The integers 0 or 1
    - a str which when converted to lower case is one of '0', 'off', 'f',
      'false', 'n', 'no', '1', 'on', 't', 'true', 'y', 'yes'

    Args:
        key: The environment variable name to lookup a value for.
        default: Value to return if key does not exist or value is empty string.

    Raises:
        TypeError: If value can not be parsed to a boolean.
    """
    str_val = os.getenv(key)

    if str_val is None or str_val.strip() == "":
        return default

    return bool_validator(str_val)
