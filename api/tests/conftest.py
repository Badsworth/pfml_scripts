"""
conftest.py files are automatically loaded by pytest, they are an easy place to
put shared test fixtures as well as define other pytest configuration (define
hooks, load plugins, define new/override assert behavior, etc.).

More info:
https://docs.pytest.org/en/latest/fixture.html#conftest-py-sharing-fixture-functions
"""
import logging.config  # noqa: B1
import os
import sys
import uuid
from datetime import datetime, timedelta

import boto3
import moto
import pytest
from jose import jwt

import massgov.pfml.api.app
import massgov.pfml.api.authentication as authentication
import massgov.pfml.api.employees
import massgov.pfml.util.logging
from massgov.pfml.db.models.factories import UserFactory

# add helpers directory to Python path, so tests modules can import them
sys.path.append(os.path.join(os.path.dirname(__file__), "helpers"))

logger = massgov.pfml.util.logging.get_logger("massgov.pfml.api.tests.conftest")


@pytest.fixture
def app_cors(monkeypatch, test_db):
    monkeypatch.setenv("CORS_ORIGINS", "http://example.com")
    return massgov.pfml.api.app.create_app()


@pytest.fixture
def app(test_db, initialize_factories_session, set_auth_public_keys):
    return massgov.pfml.api.app.create_app()


@pytest.fixture
def client(app):
    return app.app.test_client()


@pytest.fixture
def logging_fix(monkeypatch):
    """Disable the application custom logging setup

    Needed if the code under test calls massgov.pfml.util.logging.init() so that
    tests using the caplog fixture don't break.
    """
    monkeypatch.setattr(logging.config, "dictConfig", lambda config: None)  # noqa: B1


@pytest.fixture
def user(initialize_factories_session):
    user = UserFactory.create()
    return user


@pytest.fixture
def set_auth_public_keys(monkeypatch, auth_key):
    monkeypatch.setattr(authentication, "public_keys", auth_key)


@pytest.fixture
def auth_claims(user):
    claims = {
        "a": "b",
        "exp": datetime.now() + timedelta(days=1),
        "sub": str(user.active_directory_id),
    }

    return claims


@pytest.fixture
def consented_user(initialize_factories_session):
    user = UserFactory.create(consented_to_data_sharing=True)
    return user


@pytest.fixture
def disable_employee_endpoint(monkeypatch):
    new_env = monkeypatch.setenv("ENABLE_EMPLOYEE_ENDPOINTS", "0")
    return new_env


@pytest.fixture
def disable_employer_endpoint(monkeypatch):
    new_env = monkeypatch.setenv("ENABLE_EMPLOYER_ENDPOINTS", "0")
    return new_env


@pytest.fixture
def consented_user_claims(consented_user):
    claims = {
        "a": "b",
        "exp": datetime.now() + timedelta(days=1),
        "sub": str(consented_user.active_directory_id),
    }

    return claims


@pytest.fixture
def auth_key():
    hmac_key = {
        "kty": "oct",
        "kid": "018c0ae5-4d9b-471b-bfd6-eef314bc7037",
        "use": "sig",
        "alg": "HS256",
        "k": "hJtXIZ2uSN5kbQfbtTNWbpdmhkV8FJG-Onbc6mxCcYg",
    }

    return hmac_key


@pytest.fixture
def consented_user_token(consented_user_claims, auth_key):

    encoded = jwt.encode(consented_user_claims, auth_key)
    return encoded


@pytest.fixture
def auth_token(auth_claims, auth_key):

    encoded = jwt.encode(auth_claims, auth_key)
    return encoded


@pytest.fixture
def test_fs_path(tmp_path):
    file_name = "test.txt"
    content = "line 1 text\nline 2 text\nline 3 text"

    test_folder = tmp_path / "test_folder"
    test_folder.mkdir()
    test_file = test_folder / file_name
    test_file.write_text(content)
    return test_folder


@pytest.fixture
def mock_s3_bucket():
    with moto.mock_s3():
        s3 = boto3.resource("s3")
        bucket_name = "test_bucket"
        s3.create_bucket(Bucket=bucket_name)
        yield bucket_name


@pytest.fixture
def test_db_schema(monkeypatch):
    """
    Create a test schema, if it doesn't already exist, and drop it after the
    test completes.
    """
    schema_name = f"api_test_{uuid.uuid4().int}"

    monkeypatch.setenv("DB_SCHEMA", schema_name)

    import massgov.pfml.db as db
    import massgov.pfml.db.config

    db_config = massgov.pfml.db.config.get_config()

    db_test_user = db_config.username

    def exec_sql(sql):
        engine = db.create_engine(db_config)
        with engine.connect() as connection:
            connection.execute(sql)

    exec_sql(f"CREATE SCHEMA IF NOT EXISTS {schema_name} AUTHORIZATION {db_test_user};")
    logger.info("create schema %s", schema_name)

    yield schema_name

    exec_sql(f"DROP SCHEMA {schema_name} CASCADE;")
    logger.info("drop schema %s", schema_name)


@pytest.fixture
def test_db(test_db_schema):
    """
    Creates a test schema, directly creating all tables with SQLAlchemy. Schema
    is dropped after the test completes.
    """
    import massgov.pfml.db as db
    from massgov.pfml.db.models.base import Base

    # not used directly, but loads models into Base
    import massgov.pfml.db.models.employees as employees  # noqa: F401
    import massgov.pfml.db.models.applications as applications  # noqa: F401

    engine = db.create_engine()
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def initialize_factories_session(test_db_session):
    import massgov.pfml.db.models.factories as factories

    factories.db_session = test_db_session


@pytest.fixture
def test_db_via_migrations(test_db_schema):
    """
    Creates a test schema, runs migrations through Alembic. Schema is dropped
    after the test completes.
    """
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config(
        os.path.join(os.path.dirname(__file__), "../../massgov/pfml/db/alembic.ini")
    )
    command.upgrade(alembic_cfg, "head")

    return test_db_schema


@pytest.fixture
def test_db_session(test_db):
    import massgov.pfml.db as db

    db_session = db.init()

    yield db_session

    db_session.close()
    db_session.remove()


@pytest.fixture
def test_db_other_session(test_db):
    import massgov.pfml.db as db

    db_session = db.init()

    yield db_session

    db_session.close()
    db_session.remove()
