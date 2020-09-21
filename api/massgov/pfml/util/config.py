import os
from typing import Any, Optional

from massgov.pfml.util.aws_ssm import get_secret, put_secret


def get_secret_from_env(aws_ssm: Any, key: str) -> Optional[str]:
    secret_value: str

    if os.getenv(key) is not None:
        secret_value = os.environ[key]
    elif os.getenv(f"{key}_SSM_PATH") is not None:
        secret_value = get_secret(aws_ssm, os.environ[f"{key}_SSM_PATH"])
    else:
        return None

    return secret_value


def put_secret_to_env(
    aws_ssm: Any,
    key: str,
    value: str,
    overwrite: bool = True,
    type: str = "SecureString",
    data_type: str = "text",
) -> None:
    if aws_ssm is not None:
        if os.getenv(f"{key}_SSM_PATH") is not None:
            resolved_key = os.environ[f"{key}_SSM_PATH"]
        else:
            resolved_key = key
        put_secret(aws_ssm, resolved_key, value, overwrite, type, data_type)
    else:
        os.putenv(key, value)
