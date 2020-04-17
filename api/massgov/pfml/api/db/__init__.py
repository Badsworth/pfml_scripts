from flask_sqlalchemy import SQLAlchemy

import massgov.pfml.util.logging
from massgov.pfml.api.config import config

logger = massgov.pfml.util.logging.get_logger(__name__)
orm = SQLAlchemy()


def init(app):
    url = config["db_url"]
    db_name = config["db_name"]
    username = config["db_username"]
    password = config["db_password"]
    uri = f"postgresql://{username}:{password}@{url}/{db_name}"

    logger.info("connecting to postgres db: %s @ %s ...", db_name, url)

    try:
        # config keys: https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/#configuration-keys
        app.config.from_mapping(SQLALCHEMY_TRACK_MODIFICATIONS=False, SQLALCHEMY_DATABASE_URI=uri)
        orm.init_app(app)
        logger.info("orm initialized")
        return orm

    except Exception as e:
        logger.error("Error trying to connect to db: %s", e)
        # TODO throw exception when DB is full supported on non-local environments
        # raise Exception("Unable to connect to db")
