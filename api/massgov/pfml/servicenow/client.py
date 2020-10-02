from typing import Optional, Union

import requests

from massgov.pfml.servicenow.models import OutboundMessage


class ServiceNowException(requests.HTTPError):
    """ Generic rebrand of HTTPError """

    pass


class ServiceNowClient:
    def __init__(
        self, base_url: str, username: str, password: str, response: Optional[bool] = False
    ):
        # TODO: This auth may change from HTTP basic to OAuth2 https://lwd.atlassian.net/browse/EMPLOYER-401
        self._base_url = base_url
        self._session = requests.Session()
        self._session.auth = (username, password)
        self._session.headers.update(
            {"Accept": "application/json", "Content-Type": "application/json"}
        )
        self._response = response

        if not self._response:
            self._session.headers.update({"X-no-response-body": "true"})

    def send_message(self, message: OutboundMessage, table: str = "incident") -> Union[None, dict]:
        """ Make a request to a "Table API" that has been configured to trigger outbound email delivery using templates
            See docs at: https://docs.servicenow.com/bundle/orlando-application-development/page/integrate/inbound-rest/concept/c_TableAPI.html#c_TableAPI
        """
        # TODO: Finalize table name with Contact Center - https://lwd.atlassian.net/browse/EMPLOYER-400
        response = self._session.post(
            f"{self._base_url}/api/now/table/{table}", data=message.json()
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise ServiceNowException from e

        if response.text and self._response:
            return response.json()
        return None
