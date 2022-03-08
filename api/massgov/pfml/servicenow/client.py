#
# ServiceNow API client.
#

import datetime
from typing import Optional

import flask
import newrelic.agent
import requests

import massgov.pfml.util.logging
from massgov.pfml.servicenow.exception import (
    MAP_SERVICE_NOW_ERROR_REQUEST_STATUS_CODE,
    ServiceNowError,
    ServiceNowFatalError,
    ServiceNowUnavailable,
)

from . import abstract_client, models

logger = massgov.pfml.util.logging.get_logger(__name__)
MILLISECOND = datetime.timedelta(milliseconds=1)


class ServiceNowClient(abstract_client.AbstractServiceNowClient):
    """ServiceNow API client."""

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
        self, message: models.OutboundMessage, table: str = "u_cps_notifications"
    ) -> Optional[dict]:
        """Make a request to a "Table API" that has been configured to trigger outbound email delivery using templates
        See docs at: https://docs.servicenow.com/bundle/orlando-application-development/page/integrate/inbound-rest/concept/c_TableAPI.html#c_TableAPI
        """
        has_flask_context = flask.has_request_context()
        url = f"{self._base_url}/api/now/table/{table}"
        try:
            response = self._session.post(url, data=message.json())
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as ex:
            self._handle_client_side_exception(url, ex)

        if 400 <= response.status_code < 600:
            err_type = MAP_SERVICE_NOW_ERROR_REQUEST_STATUS_CODE.get(
                response.status_code, ServiceNowError
            )

            err = err_type(url, response.status_code, response.text)

            logger.debug("POST %s detail", url, extra={"request.data": message.json()})
            logger.warning(
                "POST %s => %s (%ims)",
                url,
                response.status_code,
                response.elapsed / MILLISECOND,
                extra={"response.text": response.text},
            )

            newrelic.agent.record_custom_event(
                "ServiceNowError",
                {
                    "error.class": type(err).__name__,
                    "error.message": response.text,
                    "response.status": response.status_code,
                    "service_now.request.method": "POST",
                    "service_now.request.uri": url,
                    "service_now.request.response_millis": response.elapsed / MILLISECOND,
                    "request.method": flask.request.method if has_flask_context else None,
                    "request.uri": flask.request.path if has_flask_context else None,
                    "request.headers.x-amzn-requestid": flask.request.headers.get(
                        "x-amzn-requestid", None
                    )
                    if has_flask_context
                    else None,
                },
            )

            raise err

        logger.info(
            "POST %s => %s (%ims)",
            url,
            response.status_code,
            response.elapsed / MILLISECOND,
            extra={"response.location": response.headers.get("location")},
        )

        if response.text and self._response:
            return response.json()
        return None

    def _handle_client_side_exception(self, url: str, ex: Exception) -> None:
        # Make sure New Relic records errors from ServiceNow, even if the API does not ultimately
        # return an error.
        has_flask_context = flask.has_request_context()
        newrelic.agent.record_custom_event(
            "ServiceNowError",
            {
                "error.class": type(ex).__name__,
                "error.message": str(ex),
                "service_now.request.method": "POST",
                "service_now.request.uri": url,
                "request.method": flask.request.method if has_flask_context else None,
                "request.uri": flask.request.path if has_flask_context else None,
                "request.headers.x-amzn-requestid": flask.request.headers.get(
                    "x-amzn-requestid", None
                )
                if has_flask_context
                else None,
            },
        )

        if isinstance(ex, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
            logger.warning("%s => %r", url, ex)
            raise ServiceNowUnavailable(url)
        logger.exception("%s => %r", url, ex)
        raise ServiceNowFatalError(url, ex)
