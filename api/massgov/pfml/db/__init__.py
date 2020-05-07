from contextlib import contextmanager
from typing import Optional

import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker

import massgov.pfml.util.logging
from massgov.pfml.config import config

logger = massgov.pfml.util.logging.get_logger(__name__)

session_factory = None


def init():
    global session_factory

    logger.info("connecting to postgres db")

    engine = create_engine()
    conn = engine.connect()

    conn_info = conn.connection.connection.info
    logger.info(
        "connected to db %s, server version %s", conn_info.dbname, conn_info.server_version,
    )
    logger.info("connected to db")

    # Explicitly commit sessions — usually with session_scope.
    # Also disable expiry on commit, as we don't need to be strict on consistency within our routes. Once
    # we've retrieved data from the database, we shouldn't make any extra requests to the db when grabbing existing attributes.
    session_factory = scoped_session(
        sessionmaker(autocommit=False, expire_on_commit=False, bind=engine)
    )


def create_engine(connection_uri: Optional[str] = None):
    if connection_uri is None:
        connection_uri = get_connection_uri()

    return sqlalchemy.create_engine(connection_uri)


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
