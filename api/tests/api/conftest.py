"""
conftest.py files are automatically loaded by pytest, they are an easy place to
put shared test fixtures as well as define other pytest configuration (define
hooks, load plugins, define new/override assert behavior, etc.).

More info:
https://docs.pytest.org/en/latest/fixture.html#conftest-py-sharing-fixture-functions
"""
import pytest

import massgov.pfml.api
import massgov.pfml.api.employees
import massgov.pfml.api.generate_fake_data as fake
from massgov.pfml.api.config import config


@pytest.fixture
def app_cors(monkeypatch):
    monkeypatch.setitem(config, "cors_origins", "http://example.com")
    return massgov.pfml.api.create_app()


@pytest.fixture
def app():
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
def test_user(monkeypatch):
    user = fake.create_user("johnsmith@example.com", "0000-111-2222")
    user_id = user.get("user_id")

    monkeypatch.setitem(massgov.pfml.api.users.users, user_id, user)

    return user


@pytest.fixture
def test_wages(test_employee, monkeypatch):
    wages = fake.create_wages(test_employee["employee_id"], "0000-0000-0000-0000")

    monkeypatch.setitem(fake.wages, test_employee["employee_id"], [wages])

    return (wages, test_employee)
