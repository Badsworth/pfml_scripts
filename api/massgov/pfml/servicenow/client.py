from typing import Optional, Union

import flask
import newrelic.agent
import requests

from massgov.pfml.servicenow.models import OutboundMessage


class ServiceNowException(requests.HTTPError):
    """ Generic rebrand of HTTPError """

    pass


class ServiceNowClient:
    def __init__(
        self, base_url: str, username: str, password: str, response: Optional[bool] = False
    ):
        self._base_url = base_url
        self._username = username
        self._password = password
        self._session = requests.Session()
        self._session.auth = (username, password)
        self._session.headers.update(
            {"Accept": "application/json", "Content-Type": "application/json"}
        )
        self._response = response

        if not self._response:
            self._session.headers.update({"X-no-response-body": "true"})

    def send_message(
        self, message: OutboundMessage, table: str = "u_cps_notifications"
    ) -> Union[None, dict]:
        """ Make a request to a "Table API" that has been configured to trigger outbound email delivery using templates
            See docs at: https://docs.servicenow.com/bundle/orlando-application-development/page/integrate/inbound-rest/concept/c_TableAPI.html#c_TableAPI
        """
        has_flask_context = flask.has_request_context()
        response = self._session.post(
            f"{self._base_url}/api/now/table/{table}", data=message.json()
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as e:

            newrelic.agent.record_custom_event(
                "ServiceNowError",
                {
                    "error.class": "ServiceNowClientBadResponse",
                    "error.message": response.text,
                    "response.status": response.status_code,
                    "request.method": flask.request.method if has_flask_context else None,
                    "request.uri": flask.request.path if has_flask_context else None,
                    "request.headers.x-amzn-requestid": flask.request.headers.get(
                        "x-amzn-requestid", None
                    )
                    if has_flask_context
                    else None,
                },
            )

            raise ServiceNowException from e

        if response.text and self._response:
            return response.json()
        return None
