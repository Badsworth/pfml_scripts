from contextlib import contextmanager
from typing import Optional

import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker

import massgov.pfml.util.logging
from massgov.pfml.db.config import DbConfig, get_config

logger = massgov.pfml.util.logging.get_logger(__name__)


def init(config: Optional[DbConfig] = None):
    logger.info("connecting to postgres db")

    engine = create_engine(config)
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

    return session_factory


def create_engine(config: Optional[DbConfig] = None):
    if config is None:
        config = get_config()

    connection_uri = make_connection_uri(config)

    return sqlalchemy.create_engine(connection_uri)


@contextmanager
def session_scope(session, close: bool = False):
    """Provide a transactional scope around a series of operations.

    See https://docs.sqlalchemy.org/en/13/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it
    """

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        if close:
            session.close()


def make_connection_uri(config: DbConfig) -> str:
    """Construct PostgreSQL connection URI

    More details at:
    https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING
    """
    host = config.host
    db_name = config.name
    username = config.username
    password = config.password
    schema = config.schema

    uri = f"postgresql://{username}:{password}@{host}/{db_name}?options=-csearch_path={schema}"

    return uri
