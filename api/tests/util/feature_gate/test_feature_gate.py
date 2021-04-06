import io
from datetime import datetime, timedelta
from pathlib import Path

import mock
import pytest
from freezegun import freeze_time

from massgov.pfml.util.feature_gate import check_enabled
from massgov.pfml.util.feature_gate.features_cache import FeaturesCache


@pytest.mark.integration
class TestFeaturesCache:
    def test_enabled_feature(self, features_file_path):
        features_cache = FeaturesCache(file_path=features_file_path, ttl=60 * 15)
        enabled = features_cache.check_enabled(
            feature_name="test_feature_enabled", user_email="user_1_email@domain.org",
        )

        assert enabled is True

    def test_feature_gate_unknown_feature(self, features_file_path):
        features_cache = FeaturesCache(file_path=features_file_path, ttl=60 * 15)
        enabled = features_cache.check_enabled(
            feature_name="unknown_feature", user_email="test_user@domain.com",
        )

        assert enabled is False

    def test_feature_gate_unknown_user(self, features_file_path):
        features_cache = FeaturesCache(file_path=features_file_path, ttl=60 * 15)
        enabled = features_cache.check_enabled(
            feature_name="test_feature_1", user_email="unknown_user@domain.com",
        )
        assert enabled is False

    def test_feature_gate_disabled_feature(self, features_file_path):
        features_cache = FeaturesCache(file_path=features_file_path, ttl=60 * 15)
        enabled = features_cache.check_enabled(
            feature_name="test_feature_disabled", user_email="user_1_email@domain.com",
        )

        assert enabled is False

    def test_feature_gate_disabled_feature_user_overrides(self, features_file_path):
        features_cache = FeaturesCache(file_path=features_file_path, ttl=60 * 15)

        expectations = {
            # users 1 to 3 are explicitly defined as override values in features.yaml
            # fixture for "test_feature_disabled_users_overrides"
            "user_1_email@domain.org": True,
            "user_2_email@domain.org": True,
            "user_3_email@domain.org": True,
            "user_4_email@domain.org": False,
            "user_5_email@domain.org": False,
            "user_6_email@domain.org": False,
        }

        for user_email, expectation in expectations.items():
            enabled = features_cache.check_enabled(
                feature_name="test_feature_disabled_users_overrides", user_email=user_email,
            )

            assert enabled is expectation

    def test_feature_gate_enabled(self, features_file_path):
        features_cache = FeaturesCache(file_path=features_file_path, ttl=60 * 15)

        expectations = {
            # Only user 1 is explicitly defined as an override values  in features.yaml
            "user_1_email@domain.org": True,
            "user_2_email@domain.org": True,
            "user_3_email@domain.org": True,
            "user_4_email@domain.org": True,
            "user_5_email@domain.org": True,
            "user_6_email@domain.org": True,
        }

        for user_email, expectation in expectations.items():
            enabled = features_cache.check_enabled(
                feature_name="test_feature_enabled", user_email=user_email,
            )

            assert enabled is expectation

    def test_feature_gate_ttl_expiry(self, features_file_path):
        start_time = datetime.now()
        ttl = 60 * 15
        features_cache = FeaturesCache(file_path=features_file_path, ttl=ttl)

        enabled = features_cache.check_enabled(
            feature_name="test_feature_disabled", user_email="user_1_email@domain.org",
        )
        assert enabled is False

        # Add user_1 to test_feature_disabled.users override
        mock_features_file = io.StringIO(
            """
test_feature_disabled:
    enabled: 0
    users:
        - user_1_email@domain.org"""
        )

        with mock.patch(
            "massgov.pfml.util.files.open_stream", return_value=mock_features_file,
        ):
            enabled = features_cache.check_enabled(
                feature_name="test_feature_disabled", user_email="user_1_email@domain.org",
            )
            # Enabled is still False for user_1
            assert enabled is False

            # Travel 15 minutes and 30 seconds into the future. features.yaml
            # should have been reloaded from disc and enabled should now be True
            with freeze_time(start_time + timedelta(seconds=ttl + 30)):
                enabled = features_cache.check_enabled(
                    feature_name="test_feature_disabled", user_email="user_1_email@domain.org",
                )
                assert enabled is True

    def test_feature_gate_malformed_file(self, features_file_path):
        mock_features_file = io.StringIO("""garbage format""")

        with mock.patch(
            "massgov.pfml.util.files.open_stream", return_value=mock_features_file,
        ):
            features_cache = FeaturesCache(file_path=features_file_path, ttl=60 * 15)
            enabled = features_cache.check_enabled(
                feature_name="test_feature", user_email="test_user@domain.com",
            )

            assert enabled is False

    def test_feature_gate_invalid_path(self):
        features_cache = FeaturesCache(
            file_path="/does/not/exist/invalid_feature_path.yaml", ttl=60 * 15,
        )
        enabled = features_cache.check_enabled(
            feature_name="test_feature", user_email="test_user@domain.com",
        )

        assert enabled is False

    def test_feature_gate_missing_path(self):
        features_cache = FeaturesCache(file_path="", ttl=60 * 15)
        enabled = features_cache.check_enabled(
            feature_name="test_feature", user_email="test_user@domain.com",
        )

        assert enabled is False


class TestFeaturesEnabled:
    """
    Tests the check_enabled public function of the feature_gate package. Note that
    file_path is defined via an environment variable
    """

    @pytest.fixture(autouse=True)
    def env_features_file(self, monkeypatch, features_file_path):
        monkeypatch.setenv("FEATURES_FILE_PATH", str(features_file_path))
        yield
        monkeypatch.delenv("FEATURES_FILE_PATH")

    def test_check_enabled(self):
        enabled = check_enabled(
            feature_name="test_feature_enabled", user_email="user_1_email@domain.org",
        )
        assert enabled is True

    def test_raise_arbitrary_error(self, monkeypatch):
        class ArbitraryError(Exception):
            """An arbitrary error"""

            pass

        enabled = check_enabled(
            feature_name="test_feature_enabled", user_email="user_1_email@domain.org",
        )
        assert enabled is True

        def mock_check_enabled(feature_name: str, user_email: str):
            raise ArbitraryError

        monkeypatch.setattr(FeaturesCache, "check_enabled", mock_check_enabled)
        enabled = check_enabled(
            feature_name="test_feature_enabled", user_email="user_1_email@domain.org",
        )
        assert enabled is False  # Default to false if FeatureCache errors out


@pytest.fixture
def features_file_path():
    path = Path(__file__).parent / "features.yaml"
    return str(path)
