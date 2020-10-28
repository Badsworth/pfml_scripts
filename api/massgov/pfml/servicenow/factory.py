import os
from dataclasses import dataclass
from typing import Optional

import massgov.pfml.util.logging as logging
from massgov.pfml.servicenow.client import ServiceNowClient
from massgov.pfml.servicenow.mock_client import MockServiceNowClient

logger = logging.get_logger(__name__)


@dataclass
class ServiceNowClientConfig:
    base_url: Optional[str]
    username: Optional[str]
    password: Optional[str]

    @classmethod
    def from_env(cls):

        return ServiceNowClientConfig(
            base_url=os.environ.get("SERVICE_NOW_BASE_URL"),
            username=os.environ.get("SERVICE_NOW_USERNAME"),
            password=os.environ.get("SERVICE_NOW_PASSWORD"),
        )


def create_client():
    if os.environ.get("ENABLE_MOCK_SERVICE_NOW_CLIENT"):
        logger.warning("Using mock Service Now client")
        return MockServiceNowClient()

    else:
        config = ServiceNowClientConfig.from_env()

        return ServiceNowClient(
            base_url=config.base_url, username=config.username, password=config.password
        )
