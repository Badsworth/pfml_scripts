import os
from dataclasses import dataclass
from typing import List

import massgov.pfml.db.config as db_config
from massgov.pfml.util.strings import split_str


@dataclass
class AppConfig:
    environment: str
    port: int
    cors_origins: List[str]
    db: db_config.DbConfig


def get_config() -> AppConfig:
    return AppConfig(
        environment=os.environ["ENVIRONMENT"],
        port=int(os.environ.get("PORT", 1550)),
        cors_origins=split_str(os.environ.get("CORS_ORIGINS")),
        db=db_config.get_config(),
    )
