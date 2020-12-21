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
import massgov.pfml.db.models.employees as employee_models
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
def oauth_claims(user):
    claims = {
        "exp": datetime.now() + timedelta(days=1),
        "sub": str(user.active_directory_id),
    }

    return claims


@pytest.fixture
def employer_claims(employer_user):
    claims = {
        "exp": datetime.now() + timedelta(days=1),
        "sub": str(employer_user.active_directory_id),
    }

    return claims


@pytest.fixture
def consented_user(initialize_factories_session):
    user = UserFactory.create(consented_to_data_sharing=True)
    return user


@pytest.fixture
def fineos_user(initialize_factories_session):
    user = UserFactory.create(roles=[employee_models.Role.FINEOS])
    return user


@pytest.fixture
def employer_user(initialize_factories_session):
    user = UserFactory.create(roles=[employee_models.Role.EMPLOYER])
    return user


@pytest.fixture
def disable_employee_endpoint(monkeypatch):
    new_env = monkeypatch.setenv("ENABLE_EMPLOYEE_ENDPOINTS", "0")
    return new_env


@pytest.fixture
def enable_application_fraud_check(monkeypatch):
    new_env = monkeypatch.setenv("ENABLE_APPLICATION_FRAUD_CHECK", "1")
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
def fineos_user_claims(fineos_user):
    claims = {
        "a": "b",
        "exp": datetime.now() + timedelta(days=1),
        "sub": str(fineos_user.active_directory_id),
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
def fineos_user_token(fineos_user_claims, auth_key):

    encoded = jwt.encode(fineos_user_claims, auth_key)
    return encoded


@pytest.fixture
def auth_token(auth_claims, auth_key):

    encoded = jwt.encode(auth_claims, auth_key)
    return encoded


@pytest.fixture
def oauth_auth_token(oauth_claims, auth_key):

    encoded = jwt.encode(oauth_claims, auth_key)
    return encoded


@pytest.fixture
def employer_auth_token(employer_claims, auth_key):

    encoded = jwt.encode(employer_claims, auth_key)
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
def mock_s3_bucket(reset_aws_env_vars):
    with moto.mock_s3():
        s3 = boto3.resource("s3")
        bucket_name = "test_bucket"
        s3.create_bucket(Bucket=bucket_name)
        yield bucket_name


@pytest.fixture
def mock_sftp_default_listdir_filenames():
    return ["attleboro.txt", "beverly.csv", "chicopee.csv", "duxbury.txt"]


@pytest.fixture
def mock_sftp_dir_with_conflicts():
    return "mock_sftp_dir_with_conflicts"


@pytest.fixture
def mock_sftp_filename_conflicts():
    return ["file1.txt", "file2.txt"]


@pytest.fixture
def mock_sftp_dir_with_no_files():
    return "mock_sftp_dir_with_no_files"


@pytest.fixture
def mock_sftp_client(
    mock_sftp_dir_with_conflicts,
    mock_sftp_filename_conflicts,
    mock_sftp_default_listdir_filenames,
    mock_sftp_dir_with_no_files,
):
    class MockSftpClient:
        calls = []

        def get(self, src: str, dest: str):
            self.calls.append(("get", src, dest))

        def put(self, src: str, dest: str):
            self.calls.append(("put", src, dest))

        def remove(self, filename: str):
            self.calls.append(("remove", filename))

        def rename(self, oldpath: str, newpath: str):
            self.calls.append(("rename", oldpath, newpath))

        def listdir(self, dir: str):
            self.calls.append(("listdir", dir))
            if dir == mock_sftp_dir_with_conflicts:
                return mock_sftp_filename_conflicts
            if dir == mock_sftp_dir_with_no_files:
                return []
            return mock_sftp_default_listdir_filenames

    return MockSftpClient()


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

    db_admin_config = massgov.pfml.db.config.get_config(prefer_admin=True)

    db_config = massgov.pfml.db.config.get_config()
    db_test_user = db_config.username

    def exec_sql_admin(sql):
        engine = db.create_engine(db_admin_config)
        with engine.connect() as connection:
            connection.execute(sql)

    exec_sql_admin(f"CREATE SCHEMA IF NOT EXISTS {schema_name} AUTHORIZATION {db_test_user};")
    logger.info("create schema %s", schema_name)

    try:
        yield schema_name
    finally:
        exec_sql_admin(f"DROP SCHEMA {schema_name} CASCADE;")
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

    db_session = db.init(sync_lookups=True)

    yield db_session

    db_session.close()
    db_session.remove()


@pytest.fixture
def test_db_other_session(test_db):
    import massgov.pfml.db as db

    db_session = db.init(sync_lookups=True)

    yield db_session

    db_session.close()
    db_session.remove()


@pytest.fixture
def set_env_to_local(monkeypatch):
    # this should always be the case for the tests, but the when testing
    # behavior that depends on the ENVIRONMENT value, best set it explicitly, to
    # be sure we test the correct behavior
    monkeypatch.setenv("ENVIRONMENT", "local")


@pytest.fixture
def reset_aws_env_vars(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")


# This fixture was necessary at the time of this PR as
# the test_db_via_migration was not working. Will refactor
# once that fixture is fixed. The code here is functionally
# equal to migration file:
# 2020_10_20_15_46_57_2b4295929525_add_postgres_triggers_4_employer_employee.py
@pytest.fixture
def create_triggers(initialize_factories_session):
    import massgov.pfml.db as db

    engine = db.create_engine()
    with engine.connect() as connection:
        # Create postgres triggers not uploaded by test db
        connection.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
        connection.execute(
            "CREATE OR REPLACE FUNCTION audit_employee_func() RETURNS TRIGGER AS $$\
                DECLARE affected_record record;\
                BEGIN\
                    IF (TG_OP = 'DELETE') THEN\
                        FOR affected_record IN SELECT * FROM old_table\
                            LOOP\
                                INSERT INTO employee_log(employee_log_id, employee_id, action, modified_at)\
                                    VALUES (public.gen_random_uuid(), affected_record.employee_id,\
                                        TG_OP, current_timestamp);\
                            END loop;\
                    ELSE\
                        FOR affected_record IN SELECT * FROM new_table\
                            LOOP\
                                INSERT INTO employee_log(employee_log_id, employee_id, action, modified_at)\
                                    VALUES (public.gen_random_uuid(), affected_record.employee_id,\
                                        TG_OP, current_timestamp);\
                            END loop;\
                    END IF;\
                    RETURN NEW;\
                END;\
            $$ LANGUAGE plpgsql;"
        )
        connection.execute(
            "CREATE TRIGGER after_employee_insert AFTER INSERT ON employee\
                REFERENCING NEW TABLE AS new_table\
                FOR EACH STATEMENT EXECUTE PROCEDURE audit_employee_func();"
        )
        connection.execute(
            "CREATE TRIGGER after_employee_update AFTER UPDATE ON employee\
                REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table\
                FOR EACH STATEMENT EXECUTE PROCEDURE audit_employee_func();"
        )
        connection.execute(
            "CREATE TRIGGER after_employee_delete AFTER DELETE ON employee\
                REFERENCING OLD TABLE AS old_table\
                FOR EACH STATEMENT EXECUTE PROCEDURE audit_employee_func();"
        )

        connection.execute(
            "CREATE OR REPLACE FUNCTION audit_employer_func() RETURNS TRIGGER AS $$\
                DECLARE affected_record record;\
                BEGIN\
                    IF (TG_OP = 'DELETE') THEN\
                        FOR affected_record IN SELECT * FROM old_table\
                            LOOP\
                                INSERT INTO employer_log(employer_log_id, employer_id, action, modified_at)\
                                    VALUES (public.gen_random_uuid(), affected_record.employer_id,\
                                        TG_OP, current_timestamp);\
                            END loop;\
                    ELSE\
                        FOR affected_record IN SELECT * FROM new_table\
                            LOOP\
                                INSERT INTO employer_log(employer_log_id, employer_id, action, modified_at)\
                                    VALUES (public.gen_random_uuid(), affected_record.employer_id,\
                                        TG_OP, current_timestamp);\
                            END loop;\
                    END IF;\
                    RETURN NEW;\
                END;\
            $$ LANGUAGE plpgsql;"
        )
        connection.execute(
            "CREATE TRIGGER after_employer_insert AFTER INSERT ON employer\
                REFERENCING NEW TABLE AS new_table\
                FOR EACH STATEMENT EXECUTE PROCEDURE audit_employer_func();"
        )
        connection.execute(
            "CREATE TRIGGER after_employer_update AFTER UPDATE ON employer\
                REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table\
                FOR EACH STATEMENT EXECUTE PROCEDURE audit_employer_func();"
        )
        connection.execute(
            "CREATE TRIGGER after_employer_delete AFTER DELETE ON employer\
                REFERENCING OLD TABLE AS old_table\
                FOR EACH STATEMENT EXECUTE PROCEDURE audit_employer_func();"
        )


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Format output for GitHub Actions.

    See https://docs.github.com/en/free-pro-team@latest/actions/reference/workflow-commands-for-github-actions
    """
    yield

    if "CI" not in os.environ:
        return

    for report in terminalreporter.stats.get("failed", []):
        print(
            "::error file=api/%s,line=%s::%s %s\n"
            % (
                report.location[0],
                report.longrepr.reprcrash.lineno,
                report.location[2],
                report.longrepr.reprcrash.message,
            )
        )
