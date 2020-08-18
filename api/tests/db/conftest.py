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
