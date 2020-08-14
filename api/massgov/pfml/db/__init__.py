import os
import urllib.parse
from contextlib import contextmanager
from typing import Generator, List, Optional, Union

import sqlalchemy
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

import massgov.pfml.db.models
import massgov.pfml.util.logging
from massgov.pfml.db.config import DbConfig, get_config

logger = massgov.pfml.util.logging.get_logger(__name__)


def init(config: Optional[DbConfig] = None) -> scoped_session:
    logger.info("connecting to postgres db")

    engine = create_engine(config)
    conn = engine.connect()

    conn_info = conn.connection.connection.info
    logger.info(
        "connected to postgres db",
        extra={
            "dbname": conn_info.dbname,
            "user": conn_info.user,
            "host": conn_info.host,
            "port": conn_info.port,
            "options": conn_info.options,
            "dsn_parameters": conn_info.dsn_parameters,
            "protocol_version": conn_info.protocol_version,
            "server_version": conn_info.server_version,
        },
    )
    verify_ssl(conn_info)

    # Explicitly commit sessions — usually with session_scope. Also disable expiry on commit,
    # as we don't need to be strict on consistency within our routes. Once we've retrieved data
    # from the database, we shouldn't make any extra requests to the db when grabbing existing
    # attributes.
    session_factory = scoped_session(
        sessionmaker(autocommit=False, expire_on_commit=False, bind=engine)
    )

    massgov.pfml.db.models.init_lookup_tables(session_factory)

    return session_factory


def verify_ssl(connection_info):
    """Verify that the database connection is encrypted and log a warning if not.

    TODO: raise a RuntimeError if not."""
    if connection_info.ssl_in_use:
        logger.info(
            "database connection is using SSL: %s",
            ", ".join(
                name + " " + connection_info.ssl_attribute(name)
                for name in connection_info.ssl_attribute_names
            ),
        )
    else:
        logger.warning("database connection is not using SSL")


def create_engine(config: Optional[DbConfig] = None) -> Engine:
    if config is None:
        config = get_config()

    connection_uri = make_connection_uri(config)

    # TODO: make this configurable?
    # https://lwd.atlassian.net/browse/API-188
    connect_args = {}
    if os.getenv("ENVIRONMENT") != "local":
        # TODO: should this be one of the verify-{ca,full} options?
        connect_args["sslmode"] = "require"

    return sqlalchemy.create_engine(connection_uri, connect_args=connect_args)


@contextmanager
def session_scope(session: Session, close: bool = False) -> Generator[Session, None, None]:
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
    password = urllib.parse.quote(config.password) if config.password else None
    schema = config.schema
    port = config.port

    netloc_parts = []

    if username and password:
        netloc_parts.append(f"{username}:{password}@")
    elif username:
        netloc_parts.append(f"{username}@")
    elif password:
        netloc_parts.append(f":{password}@")

    netloc_parts.append(host)

    if port:
        netloc_parts.append(f":{port}")

    netloc = "".join(netloc_parts)

    uri = f"postgresql://{netloc}/{db_name}?options=-csearch_path={schema}"

    return uri


def create_user(
    db_conn: Connection, username: str, password: Union[str, None], roles: List[str]
) -> None:
    logger.info(f"Creating '{username}' if they don't exist")
    db_conn.execute(
        f"""
    DO $$
    BEGIN
        CREATE USER {username};
        EXCEPTION WHEN DUPLICATE_OBJECT THEN
        RAISE NOTICE 'not creating user {username} -- it already exists';
    END
    $$;
    """
    )

    if password is not None:
        logger.info(f"Setting password for '{username}'")
        db_conn.execute(f"ALTER USER {username} PASSWORD '{password}'")

    # TODO: revoke any roles not listed?
    for role in roles:
        logger.info(f"Granting '{role}' to '{username}'")
        db_conn.execute(f"GRANT {role} TO {username};")
