"""
conftest.py files are automatically loaded by pytest, they are an easy place to
put shared test fixtures as well as define other pytest configuration (define
hooks, load plugins, define new/override assert behavior, etc.).

More info:
https://docs.pytest.org/en/latest/fixture.html#conftest-py-sharing-fixture-functions
"""
import os
import uuid

import pytest

import massgov.pfml.api
import massgov.pfml.api.employees
import massgov.pfml.api.generate_fake_data as fake
from massgov.pfml.config import config


@pytest.fixture
def app_cors(monkeypatch, test_db):
    monkeypatch.setitem(config, "cors_origins", "http://example.com")
    return massgov.pfml.api.create_app()


@pytest.fixture
def app(test_db):
    return massgov.pfml.api.create_app()


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
def test_employer(monkeypatch):
    employer = fake.create_employer()
    employer_id = employer.get("employer_id")

    monkeypatch.setitem(fake.employers, employer_id, employer)

    return employer


@pytest.fixture
def test_user(test_db_session):
    from massgov.pfml.db.models import Status, User

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
    wages = fake.create_wages(test_employee["employee_id"], "0000-0000-0000-0000")

    monkeypatch.setitem(fake.wages, test_employee["employee_id"], [wages])

    return (wages, test_employee)


@pytest.fixture
def test_db_schema(monkeypatch):
    """
    Create a test schema, if it doesn't already exist, and drop it after the
    test completes.
    """
    schema_name = f"api_test_{uuid.uuid4().int}"

    monkeypatch.setitem(config, "db_schema", schema_name)

    import massgov.pfml.db as db

    db_test_user = config["db_username"]

    def exec_sql(sql):
        engine = db.create_engine()
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
    import massgov.pfml.db.models as models  # noqa: F401

    engine = db.create_engine()

    Base.metadata.create_all(bind=engine)


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

    db_session = db.get_session()

    yield db_session

    db_session.close()
    db_session.remove()
