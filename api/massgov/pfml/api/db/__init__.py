from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import massgov.pfml.util.logging
from massgov.pfml.api.config import config

logger = massgov.pfml.util.logging.get_logger(__name__)

session_factory = None


def init():
    global session_factory

    uri = get_uri()
    logger.info("connecting to postgres db")

    try:
        engine = create_engine(uri, convert_unicode=True)
        engine.connect()
        logger.info("connected to db")
        session_factory = sessionmaker(bind=engine)

    except Exception as e:
        logger.error("Error trying to connect to db: %s", e)


def get_session():
    return scoped_session(session_factory)


def get_uri():
    url = config["db_url"]
    db_name = config["db_name"]
    username = config["db_username"]
    password = config["db_password"]
    uri = f"postgresql://{username}:{password}@{url}/{db_name}"

    return uri
