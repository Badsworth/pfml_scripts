import json
import os
import urllib.parse
from contextlib import contextmanager
from typing import Any, Dict, Generator, Iterable, List, Optional, TypeVar, Union

import boto3
import psycopg2
import pydantic
import sqlalchemy
import sqlalchemy.pool as pool
from sqlalchemy.engine import RowProxy  # noqa: F401, just re-exporting
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Query, Session, scoped_session, sessionmaker

import massgov.pfml.db.handle_error
import massgov.pfml.db.models
import massgov.pfml.util.logging
from massgov.pfml.db.config import DbConfig, get_config
from massgov.pfml.db.migrations.run import have_all_migrations_run

logger = massgov.pfml.util.logging.get_logger(__name__)


def init(
    config: Optional[DbConfig] = None,
    sync_lookups: bool = False,
    check_migrations_current: bool = False,
) -> scoped_session:
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

    if sync_lookups:
        massgov.pfml.db.models.init_lookup_tables(session_factory)
        massgov.pfml.db.models.applications.sync_state_metrics(session_factory)
        massgov.pfml.db.models.payments.sync_maximum_weekly_benefit_amount(session_factory)

    if check_migrations_current:
        have_all_migrations_run(engine)

    engine.dispose()

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
    db_config: DbConfig = config if config is not None else get_config()

    # We want to be able to control the connection parameters for each
    # connection because for IAM authentication with RDS, short-lived tokens are
    # used as the password, and so we potentially need to generate a fresh token
    # for each connection.
    #
    # For more details on building connection pools, see the docs:
    # https://docs.sqlalchemy.org/en/13/core/pooling.html#constructing-a-pool
    def get_conn():
        return psycopg2.connect(**get_connection_parameters(db_config))

    conn_pool = pool.QueuePool(get_conn, max_overflow=10, pool_size=20, timeout=3)

    # The URL only needs to specify the dialect, since the connection pool
    # handles the actual connections.
    #
    # (a SQLAlchemy Engine represents a Dialect+Pool)
    return sqlalchemy.create_engine(
        "postgresql://",
        pool=conn_pool,
        executemany_mode="batch",
        hide_parameters=db_config.hide_sql_parameter_logs,
        json_serializer=lambda o: json.dumps(o, default=pydantic.json.pydantic_encoder),
    )


def get_connection_parameters(db_config: DbConfig) -> Dict[str, Any]:
    # TODO: make this configurable?
    # https://lwd.atlassian.net/browse/API-188
    connect_args = {}
    environment = os.getenv("ENVIRONMENT")
    if not environment:
        raise Exception("ENVIRONMENT is not set")

    if environment != "local":
        # TODO: should this be one of the verify-{ca,full} options?
        connect_args["sslmode"] = "require"

    password = None
    if db_config.use_iam_auth:
        password = get_iam_auth_token(db_config)
    else:
        password = db_config.password

    return dict(
        host=db_config.host,
        dbname=db_config.name,
        user=db_config.username,
        password=password,
        port=db_config.port,
        options=f"-c search_path={db_config.schema}",
        connect_timeout=3,
        **connect_args,
    )


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


def get_iam_auth_token(config: DbConfig, region: str = "us-east-1") -> str:
    logger.info("Generating IAM authentication token for RDS")

    rds_client = boto3.client("rds", region_name=region)
    return rds_client.generate_db_auth_token(
        DBHostname=config.host, Port=config.port, DBUsername=config.username, Region=region
    )


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


_T = TypeVar("_T")


# https://github.com/sqlalchemy/sqlalchemy/wiki/RangeQuery-and-WindowedRangeQuery
def windowed_query(q: "Query[_T]", column: Any, window_size: int) -> Iterable[_T]:
    """"Break a Query into chunks on a given column."""

    is_single_entity = q.is_single_entity  # type: ignore
    q_modified = q.add_columns(column).order_by(column)
    last_id: Optional[Any] = None

    while True:
        subq = q_modified

        if last_id is not None:
            subq = subq.filter(column > last_id)

        chunk = subq.limit(window_size).all()

        if not chunk:
            break

        last_id = chunk[-1][-1]

        for row in chunk:
            if is_single_entity:
                yield row[0]
            else:
                yield row[0:-1]


def skip_locked_query(q: "Query[_T]", column: Any, of: Optional[Any] = None) -> Iterable[_T]:
    """Generator that uses "SKIP LOCKED" to yield one row to work on.

    This uses the PostgreSQL "SELECT ... FOR UPDATE SKIP LOCKED" feature to select the next
    unprocessed row. Multiple processes can do this simultaneously and will never get the same row
    as the row is locked until the end of the transaction.

    After processing a row, the caller must commit or rollback to end the transaction and release
    the lock on the row. (The lock will also be released if the process crashes and disconnects
    from the PostgreSQL server.)

    https://www.2ndquadrant.com/en/blog/what-is-select-skip-locked-for-in-postgresql-9-5/
    """

    is_single_entity = q.is_single_entity  # type: ignore
    q_modified = q.add_columns(column).order_by(column).with_for_update(skip_locked=True, of=of)
    last_id: Optional[Any] = None

    while True:
        subq = q_modified

        if last_id is not None:
            subq = subq.filter(column > last_id)

        next_row = subq.first()

        if not next_row:
            break

        last_id = next_row[-1]

        if is_single_entity:
            yield next_row[0]
        else:
            yield next_row[0:-1]
