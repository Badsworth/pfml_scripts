import massgov.pfml.db.config


def monkeypatch_env_vars(monkeypatch, env_vars):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)


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
    monkeypatch.setenv("ENVIRONMENT", "not-local")
    db_config = massgov.pfml.db.config.get_config()

    assert db_config.password is None
    assert db_config.use_iam_auth is True
