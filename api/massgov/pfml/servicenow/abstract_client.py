#
# ServiceNow client - abstract base class.
#

import abc
from typing import Optional

from . import models


class AbstractServiceNowClient(abc.ABC, metaclass=abc.ABCMeta):
    """Abstract base class for a ServiceNow API client."""

    @abc.abstractmethod
    def send_message(
        self, message: models.OutboundMessage, table: str = "u_cps_notifications"
    ) -> Optional[dict]:
        pass
