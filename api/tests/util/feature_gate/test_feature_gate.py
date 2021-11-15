import io
from datetime import datetime, timedelta
from pathlib import Path

import mock
import pytest
from freezegun import freeze_time

from massgov.pfml.util.feature_gate.features_cache import FeaturesCache


def test_enabled_feature(features_file_path):
    features_cache = FeaturesCache(file_path=features_file_path, ttl=60 * 15)
    enabled = features_cache.check_enabled("test_feature_enabled")

    assert enabled is True


def test_feature_gate_unknown_feature(features_file_path):
    features_cache = FeaturesCache(file_path=features_file_path, ttl=60 * 15)
    enabled = features_cache.check_enabled("unknown_feature")

    assert enabled is False


def test_feature_gate_disabled_feature(features_file_path):
    features_cache = FeaturesCache(file_path=features_file_path, ttl=60 * 15)
    enabled = features_cache.check_enabled("test_feature_disabled")

    assert enabled is False


def test_feature_gate_enabled(features_file_path):
    features_cache = FeaturesCache(file_path=features_file_path, ttl=60 * 15)

    enabled = features_cache.check_enabled("test_feature_enabled")

    assert enabled is True


def test_feature_gate_ttl_expiry(features_file_path):
    start_time = datetime.now()
    ttl = 60 * 15
    features_cache = FeaturesCache(file_path=features_file_path, ttl=ttl)

    enabled = features_cache.check_enabled("test_feature_disabled")
    assert enabled is False

    # Add user_1 to test_feature_disabled.users override
    mock_features_file = io.StringIO(
        """
test_feature_disabled:
    enabled: 1
"""
    )

    with mock.patch(
        "massgov.pfml.util.files.open_stream", return_value=mock_features_file,
    ):
        enabled = features_cache.check_enabled("test_feature_disabled")
        # Enabled is still False
        assert enabled is False

        # Travel 15 minutes and 30 seconds into the future. features.yaml
        # should have been reloaded from disc and enabled should now be True
        with freeze_time(start_time + timedelta(seconds=ttl + 30)):
            enabled = features_cache.check_enabled("test_feature_disabled")
            assert enabled is True


def test_feature_gate_malformed_file(features_file_path):
    mock_features_file = io.StringIO("""garbage format""")

    with mock.patch(
        "massgov.pfml.util.files.open_stream", return_value=mock_features_file,
    ):
        features_cache = FeaturesCache(file_path=features_file_path, ttl=60 * 15)
        enabled = features_cache.check_enabled("test_feature")

        assert enabled is False


def test_feature_gate_invalid_path():
    features_cache = FeaturesCache(
        file_path="/does/not/exist/invalid_feature_path.yaml", ttl=60 * 15,
    )
    enabled = features_cache.check_enabled("test_feature")

    assert enabled is False


def test_feature_gate_missing_path():
    features_cache = FeaturesCache(file_path="", ttl=60 * 15)
    enabled = features_cache.check_enabled("test_feature")

    assert enabled is False


@pytest.fixture
def features_file_path():
    path = Path(__file__).parent / "features.yaml"
    return str(path)
