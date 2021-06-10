from os import getenv
from typing import Optional

import massgov.pfml.util.logging as logging

from .features_cache import FeaturesCache

logger = logging.get_logger(__name__)
features_cache = None  # Singleton instance of FeaturesCache


def check_enabled(feature_name: str, user_email: Optional[str]) -> bool:
    # Since check_enabled is used in some critical code paths we prefer to
    # fail gracefully, log exceptional states and default to restricting users
    # access
    if user_email is None:
        return False

    try:
        global features_cache

        if features_cache is None:
            features_file_path = getenv("FEATURES_FILE_PATH")
            if features_file_path is None:
                return False

            features_cache = FeaturesCache(
                file_path=features_file_path, ttl=60 * 15,  # hardcoded to 15 minutes
            )

        return features_cache.check_enabled(feature_name, user_email)
    except Exception:
        logger.exception(
            "Unexpected error while checking if feature enabled for user",
            extra={"feature_name": feature_name, "user_email": user_email},
        )
        return False
