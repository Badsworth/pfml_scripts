from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import massgov.pfml.util.logging
from massgov.pfml.api.config import config

logger = massgov.pfml.util.logging.get_logger(__name__)


def init_db():
    url = config["db_url"]
    db_name = config["db_name"]
    username = config["db_username"]
    password = config["db_password"]
    uri = f"postgresql://{username}:{password}@{url}/{db_name}"

    logger.info("connecting to postgres db: %s @ %s ...", db_name, url)

    try:
        engine = create_engine(uri, convert_unicode=True)
        engine.connect()
        db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
        logger.info("connected to db")
        return db_session
    except Exception as e:
        logger.error("Error trying to connect to db: %s", e)
        # TODO throw exception when DB is full supported on non-local environments
        # raise Exception("Unable to connect to db")
