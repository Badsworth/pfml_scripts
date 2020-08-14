import os
from typing import Any, Optional

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
