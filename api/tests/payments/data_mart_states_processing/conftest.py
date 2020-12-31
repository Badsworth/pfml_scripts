import pytest


@pytest.fixture
def mock_data_mart_engine(mocker):
    return mocker.patch("sqlalchemy.engine.Engine", autospec=True)
