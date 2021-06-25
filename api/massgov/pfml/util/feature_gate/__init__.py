from os import getenv
from typing import List

from .features_cache import Feature, FeaturesCache

features_cache = None  # Singleton instance of FeaturesCache


def get_features_cache() -> FeaturesCache:
    global features_cache

    if features_cache is None:
        features_file_path = getenv("FEATURES_FILE_PATH", "")

        features_cache = FeaturesCache(
            file_path=features_file_path, ttl=60 * 15,  # hardcoded to 15 minutes
        )

    return features_cache


def load_all() -> List[Feature]:
    mapping = get_features_cache().features_mapping()
    return [feature for feature in mapping.values()]
