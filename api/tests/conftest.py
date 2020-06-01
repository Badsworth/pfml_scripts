"""
conftest.py files are automatically loaded by pytest, they are an easy place to
put shared test fixtures as well as define other pytest configuration (define
hooks, load plugins, define new/override assert behavior, etc.).

More info:
https://docs.pytest.org/en/latest/fixture.html#conftest-py-sharing-fixture-functions
"""
import os
import uuid

import boto3
import moto
import pytest

import massgov.pfml.api.app
import massgov.pfml.api.employees
import massgov.pfml.api.generate_fake_data as fake


@pytest.fixture
def app_cors(monkeypatch, test_db):
    monkeypatch.setenv("CORS_ORIGINS", "http://example.com")
    return massgov.pfml.api.app.create_app()


@pytest.fixture
def app(test_db, initialize_factories_session):
    return massgov.pfml.api.app.create_app()


@pytest.fixture
def client(app):
    return app.app.test_client()


@pytest.fixture
def test_employee(monkeypatch):
    employee = fake.create_employee()
    ssn_or_itin = employee.get("ssn_or_itin")

    monkeypatch.setitem(fake.employees, ssn_or_itin, employee)

    return employee


@pytest.fixture
def test_user(test_db_session):
    from massgov.pfml.db.models.employees import Status, User

    user = fake.create_user("johnsmith@example.com", "0000-111-2222")

    status = Status(status_description="unverified")
    test_db_session.add(status)

    u = User(
        user_id=user["user_id"],
        active_directory_id=user["auth_id"],
        email_address=user["email_address"],
        status=status,
    )

    test_db_session.add(u)
    test_db_session.commit()

    return user


@pytest.fixture
def test_wages(test_employee, monkeypatch):
    wages = fake.create_wages(test_employee["employee_id"], str(uuid.uuid4()))

    monkeypatch.setitem(fake.wages, test_employee["employee_id"], [wages])

    return wages, test_employee


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
def test_application(test_employee, test_db_session):
    from massgov.pfml.db.models.applications import Application

    employee_id = test_employee["employee_id"]
    fake_wages = fake.create_wages(employee_id, str(uuid.uuid4()))
    fake.wages[employee_id] = [fake_wages]
    created_application = fake.create_application(test_employee)

    db_application = Application(
        application_id=created_application["application_id"],
        nickname=created_application["application_nickname"],
    )

    test_db_session.add(db_application)
    test_db_session.commit()

    return created_application


@pytest.fixture
def test_applications(test_employee, test_db_session):
    from massgov.pfml.db.models.applications import Application

    employee_id = test_employee["employee_id"]
    fake_wages = fake.create_wages(employee_id, "0000-0000-0000-0000")
    fake.wages[employee_id] = [fake_wages]
    created_application1 = fake.create_application(test_employee)

    db_application1 = Application(
        application_id=created_application1["application_id"],
        nickname=created_application1["application_nickname"],
    )

    created_application2 = fake.create_application(test_employee)

    db_application2 = Application(
        application_id=created_application2["application_id"],
        nickname=created_application2["application_nickname"],
    )

    test_db_session.add(db_application1)
    test_db_session.add(db_application2)
    test_db_session.commit()

    return [created_application1, created_application2]


@pytest.fixture
def create_app_statuses(test_db_session):
    from massgov.pfml.db.models.employees import Status

    draft_status = Status(status_description="Draft")
    test_db_session.add(draft_status)
    completed_status = Status(status_description="Completed")
    test_db_session.add(completed_status)
    test_db_session.commit()

    return [
        {
            "status_type": draft_status.status_type,
            "status_description": draft_status.status_description,
        },
        {
            "status_type": completed_status.status_type,
            "status_description": completed_status.status_description,
        },
    ]


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

    yield schema_name

    exec_sql(f"DROP SCHEMA {schema_name} CASCADE;")


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
