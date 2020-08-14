import os
from dataclasses import dataclass
from typing import Optional, Union

import boto3

import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)


@dataclass
class DbConfig:
    host: str
    name: str
    username: str
    password: Union[str, None]
    schema: str
    port: str


def get_config(prefer_admin: bool = False) -> DbConfig:
    username: Optional[str] = None
    password: Optional[str] = None

    if prefer_admin:
        if _username := os.getenv("DB_ADMIN_USERNAME"):
            username = _username

        password = os.getenv("DB_ADMIN_PASSWORD")

    db_config = DbConfig(
        host=os.getenv("DB_HOST", "localhost"),
        name=os.getenv("DB_NAME", "pfml"),
        username=(username if username is not None else os.getenv("DB_USERNAME", "pfml_api")),
        password=password or os.getenv("DB_PASSWORD"),
        schema=os.getenv("DB_SCHEMA", "public"),
        port=os.getenv("DB_PORT", "5432"),
    )

    if os.getenv("ENVIRONMENT") != "local" and db_config.password is None:
        db_config.password = get_iam_auth_token(db_config)

    logger.info(
        "Constructed database configuration",
        extra={
            "host": db_config.host,
            "dbname": db_config.name,
            "username": db_config.username,
            "password": "***" if db_config.password is not None else None,
            "schema": db_config.schema,
            "port": db_config.port,
        },
    )

    return db_config


def get_iam_auth_token(config: DbConfig, region: str = "us-east-1") -> str:
    logger.info("Generating IAM authentication token for RDS")

    rds_client = boto3.client("rds", region_name=region)
    return rds_client.generate_db_auth_token(
        DBHostname=config.host, Port=config.port, DBUsername=config.username, Region=region
    )
