# Utilities for gating user access to features

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional

import yaml

import massgov.pfml.util.files as file_utils
import massgov.pfml.util.logging as logging

logger = logging.get_logger(__name__)


@dataclass
class Feature:
    name: str
    enabled: bool = False
    options: Optional[Dict] = None
    start: Optional[str] = None
    end: Optional[str] = None


class FeaturesCache:
    """
    Expected features.yaml format

    feature_1_name:     # unique identifier for a given feature
        enabled: 0      # controls whether a feature is globally enabled or disabled for all users
    feature_2_name:
        enabled: 1
        options:
          page_routes:
           - /applications/*
           - /employers/*
        start: "2021-06-19 17:00:00-04"
        end: "2021-06-19 18:00:00-04"
    """

    def __init__(self, file_path: str, ttl: int):
        self.file_path = file_path.strip()
        self.ttl = timedelta(seconds=ttl)
        self.expiry = datetime.now() + self.ttl
        self._features_mapping = self._load_features_mapping()

    def features_mapping(self) -> Dict[str, Feature]:
        if datetime.now() >= self.expiry:
            self._features_mapping = self._load_features_mapping()
            self.expiry = datetime.now() + self.ttl
        return self._features_mapping

    def check_enabled(self, name: str) -> bool:
        """
        Check if the feature is currently enabled.
        """
        if datetime.now() >= self.expiry:
            self._features_mapping = self._load_features_mapping()
            self.expiry = datetime.now() + self.ttl
        feature = self._features_mapping.get(name, None)
        if feature is None:
            return False
        return bool(feature.enabled)

    def _load_features_mapping(self) -> Dict[str, Feature]:
        """
        This loads the features from the YAML file and is intended to be
        "private". If this is called directly, the cache/ttl will not be used.
        """
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
            if not (isinstance(state, dict) and "enabled" in state.keys()):
                logger.error(
                    "Error parsing features. Missing attributes for features file",
                    extra={"file_path": self.file_path},
                )
                return features_mapping

            state["name"] = feature

            features_mapping[feature] = Feature(**state)

        return features_mapping
