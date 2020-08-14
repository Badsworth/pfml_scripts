import urllib.parse

import moto
import pytest

import massgov.pfml.db.config


def monkeypatch_env_vars(monkeypatch, env_vars):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def delete_db_env_vars(monkeypatch):
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)
    monkeypatch.delenv("DB_USERNAME", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    monkeypatch.delenv("DB_SCHEMA", raising=False)
    monkeypatch.delenv("DB_PORT", raising=False)

    monkeypatch.delenv("DB_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("DB_ADMIN_PASSWORD", raising=False)


@pytest.fixture
def set_env_to_local(monkeypatch):
    # this should always be the case for the tests, but the config code does
    # check it explicitly, so be sure so we test the correct behavior
    monkeypatch.setenv("ENVIRONMENT", "local")


def test_get_config_all_defaults(delete_db_env_vars, set_env_to_local):
    db_config = massgov.pfml.db.config.get_config()

    assert db_config == massgov.pfml.db.config.DbConfig(
        host="localhost",
        name="pfml",
        username="pfml_api",
        password=None,
        schema="public",
        port="5432",
    )


def test_get_config_fully_specified(delete_db_env_vars, monkeypatch, set_env_to_local):
    monkeypatch_env_vars(
        monkeypatch,
        {
            "DB_HOST": "foo",
            "DB_NAME": "bar",
            "DB_USERNAME": "baz",
            "DB_PASSWORD": "qux",
            "DB_SCHEMA": "quux",
            "DB_PORT": "quuz",
        },
    )

    db_config = massgov.pfml.db.config.get_config()

    assert db_config == massgov.pfml.db.config.DbConfig(
        host="foo", name="bar", username="baz", password="qux", schema="quux", port="quuz"
    )


def test_get_config_prefer_admin(delete_db_env_vars, monkeypatch, set_env_to_local):
    # if admin user and password are set, use both
    monkeypatch_env_vars(
        monkeypatch,
        {
            "DB_USERNAME": "regular_user",
            "DB_PASSWORD": "foo",
            "DB_ADMIN_USERNAME": "admin_user",
            "DB_ADMIN_PASSWORD": "bar",
        },
    )

    db_config = massgov.pfml.db.config.get_config(prefer_admin=True)

    assert db_config.username == "admin_user"
    assert db_config.password == "bar"

    # if admin password is not provided explicitly, fallback to regular
    monkeypatch.delenv("DB_ADMIN_PASSWORD")

    db_config = massgov.pfml.db.config.get_config(prefer_admin=True)

    assert db_config.username == "admin_user"
    assert db_config.password == "foo"

    # if no password is set at all, don't set one
    monkeypatch.delenv("DB_PASSWORD")

    db_config = massgov.pfml.db.config.get_config(prefer_admin=True)

    assert db_config.username == "admin_user"
    assert db_config.password is None

    # if no admin settings are provided, use default
    monkeypatch.delenv("DB_ADMIN_USERNAME")

    db_config = massgov.pfml.db.config.get_config(prefer_admin=True)

    assert db_config.username == "regular_user"
    assert db_config.password is None


def test_get_config_iam_auth(delete_db_env_vars, monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")

    with moto.mock_rds():
        monkeypatch.setenv("ENVIRONMENT", "not-local")
        db_config = massgov.pfml.db.config.get_config()

        assert db_config.password is not None

        # auth tokens are formatted like a url, but don't have a schema part, so
        # add a dummy `aws://` for the url parse
        password_parts = urllib.parse.urlparse(f"aws://{db_config.password}")
        assert password_parts.netloc == f"{db_config.host}:{db_config.port}"

        password_query_parts = urllib.parse.parse_qs(password_parts.query)
        assert password_query_parts["Action"][0] == "connect"
        assert password_query_parts["DBUser"][0] == db_config.username
        assert len(password_query_parts["X-Amz-Algorithm"]) != 0
        assert len(password_query_parts["X-Amz-Credential"]) != 0
        assert len(password_query_parts["X-Amz-Date"]) != 0
        assert len(password_query_parts["X-Amz-Expires"]) != 0
        assert len(password_query_parts["X-Amz-SignedHeaders"]) != 0
        assert len(password_query_parts["X-Amz-Security-Token"]) != 0
        assert len(password_query_parts["X-Amz-Signature"]) != 0
