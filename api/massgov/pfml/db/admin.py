# Admin scripts for managing the PFML DB
import os
from dataclasses import dataclass, field
from typing import List

import massgov.pfml.util.logging
from massgov.pfml.db import create_engine, create_user, get_config

massgov.pfml.util.logging.init("DB Admin Tasks")


@dataclass
class UserConfig:
    username: str
    roles: List[str] = field(default_factory=list)


def create_users():
    engine = create_engine(get_config(prefer_admin=True))

    user_configs = [
        UserConfig(username="pfml_api", roles=["app"]),
    ]

    with engine.connect() as db_conn:
        for user_config in user_configs:
            roles = user_config.roles

            if os.getenv("ENVIRONMENT") == "local":
                # for local environments, set the user's password to whatever is
                # specified in DB_PASSWORD for simplicity
                password = os.getenv("DB_PASSWORD")
            else:
                # in AWS environments, we use IAM authentication, which requires
                # the user to be granted the `rds_iam` and since a temporary
                # access credential is created when connecting, the user does
                # not need a static password
                roles.append("rds_iam")
                password = None

            with db_conn.begin():
                create_user(
                    db_conn, username=user_config.username, password=password, roles=roles,
                )
