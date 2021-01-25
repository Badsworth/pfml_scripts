import massgov.pfml.util.logging as logging
from massgov.pfml.servicenow.models import OutboundMessage

logger = logging.get_logger(__name__)


class MockServiceNowClient:
    def send_message(
        self, message: OutboundMessage, table: str = "mock_u_cps_notifications"
    ) -> None:
        logger.warning("Sent message to mock Service Now client")
        logger.info("Message: %s", message.json())
