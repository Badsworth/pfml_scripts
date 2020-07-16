#
# FINEOS client - factory.
#

import os
from dataclasses import dataclass
from typing import Optional

import massgov.pfml.util.logging

from . import client, fineos_client, mock_client

logger = massgov.pfml.util.logging.get_logger(__name__)


@dataclass
class FINEOSClientConfig:
    customer_api_url: Optional[str]
    wscomposer_api_url: Optional[str]
    oauth2_url: Optional[str]
    oauth2_client_id: Optional[str]
    oauth2_client_secret: Optional[str]

    @classmethod
    def from_env(cls):
        return FINEOSClientConfig(
            customer_api_url=os.environ.get("FINEOS_CLIENT_CUSTOMER_API_URL", None),
            wscomposer_api_url=os.environ.get("FINEOS_CLIENT_WSCOMPOSER_API_URL", None),
            oauth2_url=os.environ.get("FINEOS_CLIENT_OAUTH2_URL", None),
            oauth2_client_id=os.environ.get("FINEOS_CLIENT_OAUTH2_CLIENT_ID", None),
            oauth2_client_secret=os.environ.get("FINEOS_CLIENT_OAUTH2_CLIENT_SECRET", None),
        )


def create_client(config: Optional[FINEOSClientConfig] = None) -> client.AbstractFINEOSClient:
    """Factory to create the right type of client object for the given configuration."""
    if config is None:
        config = FINEOSClientConfig.from_env()

    if config.customer_api_url:
        return fineos_client.FINEOSClient(
            customer_api_url=config.customer_api_url,
            wscomposer_url=config.wscomposer_api_url,
            oauth2_url=config.oauth2_url,
            client_id=config.oauth2_client_id,
            client_secret=config.oauth2_client_secret,
        )
    else:
        logger.warning("using mock FINEOS client")
        return mock_client.MockFINEOSClient()
