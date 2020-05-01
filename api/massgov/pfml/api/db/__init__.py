from contextlib import contextmanager
from typing import Optional

import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker

import massgov.pfml.util.logging
from massgov.pfml.api.config import config

logger = massgov.pfml.util.logging.get_logger(__name__)

session_factory = None


def init():
    global session_factory

    logger.info("connecting to postgres db")

    try:
        engine = create_engine()
        engine.connect()
        logger.info("connected to db")
        session_factory = scoped_session(sessionmaker(autocommit=False, bind=engine))
    except Exception as e:
        logger.error("Error trying to connect to db: %s", e)


def create_engine(connection_uri: Optional[str] = None):
    if connection_uri is None:
        connection_uri = get_connection_uri()

    return sqlalchemy.create_engine(connection_uri, convert_unicode=True)


def get_session():
    return session_factory


@contextmanager
def session_scope(close: bool = False):
    """Provide a transactional scope around a series of operations."""

    session = get_session()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        if close:
            session.close()


def get_connection_uri():
    """Construct PostgreSQL connection URI

    More details at:
    https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING
    """
    url = config["db_url"]
    db_name = config["db_name"]
    username = config["db_username"]
    password = config["db_password"]
    schema = config["db_schema"]

    uri = f"postgresql://{username}:{password}@{url}/{db_name}?options=-csearch_path={schema}"

    return uri
