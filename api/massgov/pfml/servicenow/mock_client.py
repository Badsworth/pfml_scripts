#
# ServiceNow client - mock implementation.
#
# This implementation is intended for use in local development or in test cases. It may also be
# used in deployed environments when needed.
#

import massgov.pfml.util.logging as logging

from . import abstract_client, models

logger = logging.get_logger(__name__)


class MockServiceNowClient(abstract_client.AbstractServiceNowClient):
    """Mock ServiceNow API client that returns fake responses."""

    def send_message(
        self, message: models.OutboundMessage, table: str = "mock_u_cps_notifications"
    ) -> None:
        logger.warning("Sent message to mock Service Now client")
        logger.info("Message: %s", message.json())
