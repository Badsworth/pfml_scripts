# Utilities for gating user access to features

from datetime import datetime, timedelta
from typing import Dict, List

import yaml

import massgov.pfml.util.files as file_utils
import massgov.pfml.util.logging as logging

logger = logging.get_logger(__name__)


class Feature:
    def __init__(self, name: str, user_emails: List[str], enabled: bool):
        self.name = name
        self.user_emails = set(user_emails)
        self.enabled = enabled


class FeaturesCache:
    """
    Expected features.yaml format

    feature_1_name:     # unique identifier for a given feature
        enabled: 0      # controls whether a feature is globally enabled or disabled for all users
        users:          # email addresses of users with an override for disabled features
            - user_1_email@domain.org
            - user_2_email@domain.org
            - user_3_email@domain.org
    feature_2_name:
        enabled: 1
        users:
            - user_1_email@domain.org
    feature_3_name:
        enabled: 1
        users:
    """

    def __init__(self, file_path: str, ttl: int):
        self.file_path = file_path.strip()
        self.ttl = timedelta(seconds=ttl)
        self.features_mapping = self.load_values()
        self.expiry = datetime.now() + self.ttl

    def check_enabled(self, feature_name: str, user_email: str) -> bool:
        if datetime.now() >= self.expiry:
            self.features_mapping = self.load_values()
            self.expiry = datetime.now() + self.ttl

        feature = self.features_mapping.get(feature_name, None)
        if feature is None:
            return False
        elif feature.enabled:
            return True
        else:
            return user_email in feature.user_emails

    def load_values(self):
        features_mapping: Dict[str, Feature] = dict()

        try:
            with file_utils.open_stream(self.file_path) as f:
                contents = yaml.load(f, Loader=yaml.SafeLoader)
        except FileNotFoundError:
            logger.exception(
                "Error parsing features. Unexpected file format for features file",
                extra={"file_path": self.file_path},
            )
            return features_mapping
        except yaml.YAMLError:
            logger.exception(
                "Error parsing features. Could not process features file as valid yaml",
                extra={"file_path": self.file_path},
            )
            return features_mapping

        if not isinstance(contents, dict):
            logger.error(
                "Error parsing features. Unexpected file format for features file",
                extra={"file_path": self.file_path},
            )
            return features_mapping

        for feature, state in contents.items():
            if not (isinstance(state, dict) and sorted(state.keys()) == ["enabled", "users"]):
                logger.error(
                    "Error parsing features. Missing attributes for features file",
                    extra={"file_path": self.file_path},
                )
                return features_mapping

            user_emails = state["users"] or []
            enabled = state["enabled"] != 0 or False

            features_mapping[feature] = Feature(
                name=feature, user_emails=user_emails, enabled=enabled,
            )

        return features_mapping
