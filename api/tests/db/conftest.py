import pytest


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
def verbose_test_db_session(monkeypatch, test_db):
    import massgov.pfml.db as db
    from massgov.pfml.db.config import DbConfig, get_config

    # set hide sql parameter to true
    db_config: DbConfig = get_config()
    db_config.hide_sql_parameter_logs = False
    db_session = db.init(db_config, sync_lookups=True)

    yield db_session

    db_session.close()
    db_session.remove()
