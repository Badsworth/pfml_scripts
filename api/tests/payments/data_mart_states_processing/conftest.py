import pytest


@pytest.fixture
def mock_data_mart_client(mocker):
    return mocker.patch("massgov.pfml.payments.data_mart.RealClient", autospec=True)
