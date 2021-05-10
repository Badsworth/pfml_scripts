"""
conftest.py files are automatically loaded by pytest, they are an easy place to
put shared test fixtures as well as define other pytest configuration (define
hooks, load plugins, define new/override assert behavior, etc.).

More info:
https://docs.pytest.org/en/latest/fixture.html#conftest-py-sharing-fixture-functions
"""
import logging.config  # noqa: B1
import os
import uuid
from datetime import datetime, timedelta

import _pytest.monkeypatch
import boto3
import moto
import pytest
import sentry_sdk
import sqlalchemy
from jose import jwt

import massgov.pfml.api.app
import massgov.pfml.api.authentication as authentication
import massgov.pfml.api.employees
import massgov.pfml.db.models.employees as employee_models
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.factories import UserFactory

logger = massgov.pfml.util.logging.get_logger("massgov.pfml.api.tests.conftest")


@pytest.fixture(autouse=True)
def disable_sentry(monkeypatch):
    monkeypatch.setattr(sentry_sdk, "init", lambda: None)
    monkeypatch.setattr(sentry_sdk, "capture_exception", lambda: None)
    monkeypatch.setattr(sentry_sdk, "capture_message", lambda: None)


@pytest.fixture(autouse=True, scope="session")
def set_no_db_factories_alert():
    """By default, ensure factories do not attempt to access the database.

    The tests that need generated models to actually hit the database can pull
    in the `initialize_factories_session` fixture to their test case to enable
    factory writes to the database.
    """
    os.environ["DB_FACTORIES_DISABLE_DB_ACCESS"] = "1"


@pytest.fixture
def app_cors(monkeypatch, test_db):
    monkeypatch.setenv("CORS_ORIGINS", "http://example.com")
    return massgov.pfml.api.app.create_app(check_migrations_current=False)


@pytest.fixture
def app(test_db_session, initialize_factories_session, set_auth_public_keys):
    return massgov.pfml.api.app.create_app(
        check_migrations_current=False, db_session_factory=test_db_session
    )


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


@pytest.fixture(scope="session")
def auth_claims_unit():
    claims = {
        "exp": datetime.now() + timedelta(days=1),
        "sub": "foo",
    }

    return claims


@pytest.fixture
def auth_claims(auth_claims_unit, user):
    auth_claims = auth_claims_unit.copy()
    auth_claims["sub"] = str(user.active_directory_id)

    return auth_claims


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


@pytest.fixture(scope="session")
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
def mock_cognito(monkeypatch, reset_aws_env_vars):
    import boto3

    with moto.mock_cognitoidp():
        cognito = boto3.client("cognito-idp", "us-east-1")

        def mock_create_cognito_client():
            return cognito

        monkeypatch.setattr(
            massgov.pfml.util.aws.cognito, "create_cognito_client", mock_create_cognito_client
        )

        yield cognito


@pytest.fixture
def mock_cognito_user_pool(monkeypatch, mock_cognito):
    with moto.mock_cognitoidp():
        user_pool_id = mock_cognito.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
        user_pool_client_id = mock_cognito.create_user_pool_client(
            UserPoolId=user_pool_id, ClientName="test"
        )["UserPoolClient"]["ClientId"]

        monkeypatch.setenv("COGNITO_USER_POOL_ID", user_pool_id)
        monkeypatch.setenv("COGNITO_USER_POOL_CLIENT_ID", user_pool_client_id)

        yield {"id": user_pool_id, "client_id": user_pool_client_id}


@pytest.fixture
def mock_ses(monkeypatch, reset_aws_env_vars):
    import boto3

    monkeypatch.setenv("DFML_PROJECT_MANAGER_EMAIL_ADDRESS", "test@test.gov")
    monkeypatch.setenv("PFML_EMAIL_ADDRESS", "noreplypfml@mass.gov")
    monkeypatch.setenv("BOUNCE_FORWARDING_EMAIL", "noreplypfml@mass.gov")
    monkeypatch.setenv(
        "BOUNCE_FORWARDING_EMAIL_ADDRESS_ARN",
        "arn:aws:ses:us-east-1:498823821309:identity/noreplypfml@mass.gov",
    )
    monkeypatch.setenv("CTR_GAX_BIEVNT_EMAIL_ADDRESS", "test1@example.com")
    monkeypatch.setenv("CTR_VCC_BIEVNT_EMAIL_ADDRESS", "test2@example.com")
    monkeypatch.setenv("DFML_BUSINESS_OPERATIONS_EMAIL_ADDRESS", "test3@example.com")

    with moto.mock_ses():
        ses = boto3.client("ses")
        ses.verify_email_identity(EmailAddress=os.getenv("PFML_EMAIL_ADDRESS"))
        yield ses


@pytest.fixture
def mock_s3(reset_aws_env_vars):
    with moto.mock_s3():
        yield boto3.resource("s3")


@pytest.fixture
def mock_s3_bucket_resource(mock_s3):
    bucket = mock_s3.Bucket("test_bucket")
    bucket.create()
    yield bucket


@pytest.fixture
def mock_s3_bucket(mock_s3_bucket_resource):
    yield mock_s3_bucket_resource.name


@pytest.fixture
def mock_sftp_client():
    class MockSftpClient:
        calls = []
        files = {}

        def get(self, src: str, dest: str):
            self.calls.append(("get", src, dest))
            body = self.files.get(src)
            if body is not None:
                with open(dest, "w") as f:
                    f.write(body)

        def put(self, src: str, dest: str, confirm: bool):
            self.calls.append(("put", src, dest))
            with open(src) as f:
                self.files[dest] = f.read()

        def remove(self, filename: str):
            self.calls.append(("remove", filename))
            body = self.files.get(filename)
            if body is not None:
                del self.files[filename]

        def rename(self, oldpath: str, newpath: str):
            self.calls.append(("rename", oldpath, newpath))
            body = self.files.get(oldpath)
            if body is not None:
                self.files[newpath] = body
                del self.files[oldpath]

        def listdir(self, dir: str):
            self.calls.append(("listdir", dir))
            # Remove the directory from the front of the file name to match the behaviour of the
            # non-mocked SFTP client we use which returns the filenames relative to the directory
            # passed in instead of the entire path to the file.
            first_char_index = len(dir) + 1 if len(dir) else 0
            return sorted(
                [fn[first_char_index:] for fn in list(self.files.keys()) if fn.startswith(dir)]
            )

        # Non-standard method to add/modify the SFTP client with files of our choosing.
        def _add_file(self, path: str, body: str):
            self.files[path] = body

        # Tests that inspect the contents of the calls attribute can call this function to
        # conveniently reset the calls attribute back to an empty list between tests.
        def reset_calls(self):
            self.calls = []

    return MockSftpClient()


@pytest.fixture
def setup_mock_sftp_client(monkeypatch, mock_sftp_client):
    # Mock SFTP client so we can inspect the method calls we make later in the test.
    monkeypatch.setattr(
        file_util, "get_sftp_client", lambda uri, ssh_key_password, ssh_key: mock_sftp_client,
    )


@pytest.fixture(scope="session")
def test_db_schema(monkeypatch_session):
    """
    Create a test schema, if it doesn't already exist, and drop it after the
    test completes.
    """
    schema_name = f"api_test_{uuid.uuid4().int}"

    monkeypatch_session.setenv("DB_SCHEMA", schema_name)

    db_schema_create(schema_name)
    try:
        yield schema_name
    finally:
        db_schema_drop(schema_name)


def db_schema_create(schema_name):
    """Create a database schema."""
    db_config = massgov.pfml.db.config.get_config()
    db_test_user = db_config.username

    exec_sql_admin(f"CREATE SCHEMA IF NOT EXISTS {schema_name} AUTHORIZATION {db_test_user};")
    logger.info("create schema %s", schema_name)


def db_schema_drop(schema_name):
    """Drop a database schema."""
    exec_sql_admin(f"DROP SCHEMA {schema_name} CASCADE;")
    logger.info("drop schema %s", schema_name)


def exec_sql_admin(sql):
    db_admin_config = massgov.pfml.db.config.get_config(prefer_admin=True)
    engine = massgov.pfml.db.create_engine(db_admin_config)
    with engine.connect() as connection:
        connection.execute(sql)


@pytest.fixture(scope="session")
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

    db_session = db.init(sync_lookups=True)
    db_session.close()
    db_session.remove()

    return engine


Session = sqlalchemy.orm.sessionmaker()


@pytest.fixture
def test_db_session(test_db):
    # Based on https://docs.sqlalchemy.org/en/13/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    connection = test_db.connect()
    trans = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    trans.rollback()
    connection.close()


@pytest.fixture
def test_db_other_session(test_db):
    # Based on https://docs.sqlalchemy.org/en/13/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    connection = test_db.connect()
    trans = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    trans.rollback()
    connection.close()


@pytest.fixture
def initialize_factories_session(monkeypatch, test_db_session):
    monkeypatch.delenv("DB_FACTORIES_DISABLE_DB_ACCESS")

    import massgov.pfml.db.models.factories as factories

    logger.info("set factories db_session to %s", test_db_session)
    factories.db_session = test_db_session


@pytest.fixture
def local_test_db_schema(monkeypatch):
    """
    Create a test schema, if it doesn't already exist, and drop it after the
    test completes.
    """
    schema_name = f"api_test_{uuid.uuid4().int}"

    monkeypatch.setenv("DB_SCHEMA", schema_name)

    db_schema_create(schema_name)
    try:
        yield schema_name
    finally:
        db_schema_drop(schema_name)


@pytest.fixture
def local_test_db(local_test_db_schema):
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

    db_session = db.init(sync_lookups=True, check_migrations_current=False)
    db_session.close()
    db_session.remove()

    return engine


@pytest.fixture
def local_test_db_session(local_test_db):
    import massgov.pfml.db as db

    db_session = db.init(sync_lookups=False, check_migrations_current=False)

    yield db_session

    db_session.close()
    db_session.remove()


@pytest.fixture
def local_test_db_other_session(local_test_db):
    import massgov.pfml.db as db

    db_session = db.init(sync_lookups=False, check_migrations_current=False)

    yield db_session

    db_session.close()
    db_session.remove()


@pytest.fixture
def local_initialize_factories_session(monkeypatch, local_test_db_session):
    monkeypatch.delenv("DB_FACTORIES_DISABLE_DB_ACCESS")
    import massgov.pfml.db.models.factories as factories

    logger.info("set factories db_session to %s", local_test_db_session)
    factories.db_session = local_test_db_session


@pytest.fixture
def migrations_test_db_schema(monkeypatch):
    """
    Create a test schema, if it doesn't already exist, and drop it after the
    test completes.
    """
    schema_name = f"api_test_{uuid.uuid4().int}"

    monkeypatch.setenv("DB_SCHEMA", schema_name)

    db_schema_create(schema_name)
    try:
        yield schema_name
    finally:
        db_schema_drop(schema_name)


@pytest.fixture
def test_db_via_migrations(migrations_test_db_schema, logging_fix):
    """
    Creates a test schema, runs migrations through Alembic. Schema is dropped
    after the test completes.
    """
    from alembic.config import Config
    from alembic import command
    from pathlib import Path

    alembic_cfg = Config(
        os.path.join(os.path.dirname(__file__), "../massgov/pfml/db/migrations/alembic.ini")
    )
    # Change directory location so the relative script_location in alembic config works.
    os.chdir(Path(__file__).parent.parent)
    command.upgrade(alembic_cfg, "head")

    return migrations_test_db_schema


@pytest.fixture
def test_db_session_via_migrations(test_db_via_migrations):
    import massgov.pfml.db as db

    db_session = db.init()

    yield db_session

    db_session.close()
    db_session.remove()


@pytest.fixture
def initialize_factories_session_via_migrations(test_db_session_via_migrations):
    import massgov.pfml.db.models.factories as factories

    factories.db_session = test_db_session_via_migrations


@pytest.fixture(scope="module")
def module_persistent_db(monkeypatch_module, request):
    import massgov.pfml.db as db
    from massgov.pfml.db.models.base import Base

    # not used directly, but loads models into Base
    import massgov.pfml.db.models.employees as employees  # noqa: F401
    import massgov.pfml.db.models.applications as applications  # noqa: F401

    schema_name = f"api_test_persistent_{uuid.uuid4().int}"
    logger.info("use persistent test db for module %s", request.module.__name__)

    monkeypatch_module.setenv("DB_SCHEMA", schema_name)
    db_schema_create(schema_name)

    engine = db.create_engine()
    Base.metadata.create_all(bind=engine)

    create_triggers_on_connection(engine.connect())

    db_session = db.init(sync_lookups=True)

    try:
        yield schema_name
    finally:
        db_session.close()
        db_session.remove()
        db_schema_drop(schema_name)


@pytest.fixture
def module_persistent_db_session(module_persistent_db, monkeypatch):
    import massgov.pfml.db as db
    import massgov.pfml.db.models.factories as factories

    db_session = db.init(sync_lookups=False)

    monkeypatch.delenv("DB_FACTORIES_DISABLE_DB_ACCESS")

    logger.info("set factories db_session to %s", db_session)
    factories.db_session = db_session

    yield db_session

    db_session.close()
    db_session.remove()


@pytest.fixture
def mock_db_session(mocker):
    return mocker.patch("sqlalchemy.orm.Session", autospec=True)


# From https://github.com/pytest-dev/pytest/issues/363
@pytest.fixture(scope="session")
def monkeypatch_session(request):
    mpatch = _pytest.monkeypatch.MonkeyPatch()
    yield mpatch
    mpatch.undo()


# From https://github.com/pytest-dev/pytest/issues/363
@pytest.fixture(scope="module")
def monkeypatch_module(request):
    mpatch = _pytest.monkeypatch.MonkeyPatch()
    yield mpatch
    mpatch.undo()


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
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


# This fixture was necessary at the time of this PR as
# the test_db_via_migration was not working. Will refactor
# once that fixture is fixed. The code here is functionally
# equal to migration file:
# 2020_10_20_15_46_57_2b4295929525_add_postgres_triggers_4_employer_employee.py
@pytest.fixture(scope="session")
def create_triggers(test_db):
    with test_db.connect() as connection:
        create_triggers_on_connection(connection)


@pytest.fixture
def local_create_triggers(local_test_db):
    with local_test_db.connect() as connection:
        create_triggers_on_connection(connection)


def create_triggers_on_connection(connection):
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
                report.location[1],
                report.location[2],
                report.longrepr.reprcrash.message,
            )
        )


# This fixture was necessary at the time of this PR as
# the test_db_via_migration was not working. Will refactor
# once that fixture is fixed. The code here is functionally
# equal to migration file:
# 2021_01_29_15_51_16_14155f78d8e6_create_dua_reduction_payment_table.py
@pytest.fixture
def dua_reduction_payment_unique_index(initialize_factories_session):
    import massgov.pfml.db as db

    engine = db.create_engine()
    with engine.connect() as connection:
        connection.execute(
            """
            create unique index on dua_reduction_payment (
                absence_case_id,
                coalesce(employer_fein, ''),
                coalesce(payment_date, '1788-02-06'),
                coalesce(request_week_begin_date, '1788-02-06'),
                coalesce(gross_payment_amount_cents, 99999999),
                coalesce(payment_amount_cents, 99999999),
                coalesce(fraud_indicator, ''),
                coalesce(benefit_year_end_date, '1788-02-06'),
                coalesce(benefit_year_begin_date, '1788-02-06')
            )
        """
        )
