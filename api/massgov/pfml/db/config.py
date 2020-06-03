import os
from dataclasses import dataclass
from typing import Any

from massgov.pfml.util.aws_ssm import get_secret


@dataclass
class DbConfig:
    host: str
    name: str
    username: str
    password: str
    schema: str


def get_config(aws_ssm: Any = None) -> DbConfig:
    return DbConfig(
        host=os.environ.get("DB_HOST", "localhost"),
        name=os.environ.get("DB_NAME", "pfml"),
        username=os.environ.get("DB_USERNAME", "pfml"),
        password=get_db_password(aws_ssm),
        schema=os.environ.get("DB_SCHEMA", "public"),
    )


def get_db_password(aws_ssm: Any = None) -> str:
    key = "DB_PASSWORD"
    db_pass: str

    if os.getenv(key) is not None:
        db_pass = os.environ[key]
    elif os.getenv(f"{key}_SSM_PATH") is not None:
        db_pass = get_secret(aws_ssm, os.environ[f"{key}_SSM_PATH"])
    else:
        raise Exception(f"Could not find database password via {key} or {key}_SSM_PATH")

    return db_pass
