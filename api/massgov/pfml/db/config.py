import os
from dataclasses import dataclass


@dataclass
class DbConfig:
    host: str
    name: str
    username: str
    password: str
    schema: str


def get_config() -> DbConfig:
    return DbConfig(
        host=os.environ.get("DB_URL", "localhost"),
        name=os.environ.get("DB_NAME", "pfml"),
        username=os.environ.get("DB_USERNAME", "pfml"),
        password=os.environ["DB_PASSWORD"],
        schema=os.environ.get("DB_SCHEMA", "public"),
    )
