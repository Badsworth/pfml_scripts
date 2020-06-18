import os
from dataclasses import dataclass
from typing import List

import massgov.pfml.db.config as db_config
from massgov.pfml.util.strings import split_str


@dataclass
class AppConfig:
    environment: str
    port: int
    enable_full_error_logs: bool
    cors_origins: List[str]
    db: db_config.DbConfig
    cognito_user_pool_keys_url: str


def get_config() -> AppConfig:
    return AppConfig(
        environment=str(os.environ.get("ENVIRONMENT")),
        port=int(os.environ.get("PORT", 1550)),
        enable_full_error_logs=os.environ.get("ENABLE_FULL_ERROR_LOGS", "0") == "1",
        cors_origins=split_str(os.environ.get("CORS_ORIGINS")),
        db=db_config.get_config(),
        cognito_user_pool_keys_url=(os.environ["COGNITO_USER_POOL_KEYS_URL"]),
    )
