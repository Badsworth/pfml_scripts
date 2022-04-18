#
# PDF client - PDF implementation.
#

# import base64
import datetime

# import json
# import os.path
import urllib.parse
from typing import Any  # , Dict, Optional

import flask
import newrelic.agent

# import pydantic
import requests

import massgov.pfml.util.logging

from . import client, common, exception, models

# from requests.models import Response


logger = massgov.pfml.util.logging.get_logger(__name__)
MILLISECOND = datetime.timedelta(milliseconds=1)


class PDFClient(client.AbstractPDFClient):
    """PDF API client."""

    host: str
    updateTemplateEndpoint: str
    generateEndpoint: str
    mergeEndpoint: str

    def __init__(self, host: str):
        # if host is None:
        #     raise Exception("Env var 'PDF_API_HOST' has not been defined.")

        self.host = host
        # TBD, remove this endpoint?
        # Why do we need to have the template in S3?
        self.updateTemplateEndpoint = urllib.parse.urljoin(self.host, "/updateTemplate")
        self.generateEndpoint = urllib.parse.urljoin(self.host, "/generate")
        self.mergeEndpoint = urllib.parse.urljoin(self.host, "/merge")

        logger.info("host %s", self.host)
        # auth needed?

    def updateTemplate(self) -> requests.Response:
        try:
            response = self._request("get", self.updateTemplateEndpoint)
            return response
        except requests.exceptions.RequestException as error:
            logger.error(error)
            raise Exception("Api error to update Pdf template.")

    def generate(self, request: models.GeneratePDFRequest) -> requests.Response:
        try:
            url = self.generateEndpoint
            if request.type in common.DOC_TYPES:
                url = f"{self.generateEndpoint}/{request.type}"

            response = self._request(
                "post",
                url,
                json=request,
            )

            return response

        except requests.exceptions.RequestException as error:
            logger.error(error)
            raise Exception("Api error to generate Pdf.")

    def merge(self, request: models.MergePDFRequest) -> requests.Response:
        try:
            response = self._request(
                "post",
                self.mergeEndpoint,
                json=request,
            )

            if response.ok:
                logger.info(f"Pdfs were successfully merged for batchId: {request.batchId}")

            return response

        except requests.exceptions.RequestException as error:
            logger.error(error)
            raise Exception("Api error to merge Pdf.")

    def _request(self, method: str, url: str, **args: Any) -> requests.Response:
        """Make a request and handle errors."""
        # self.request_count += 1
        has_flask_context = flask.has_request_context()
        logger.debug("%s %s start", method, url)
        method_name = url.split("/")[-1]
        headers = {"Content-type": "application/json", "Accept": "application/json"}

        try:
            response = requests.request(method, url, headers=headers, **args)
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as ex:
            self._handle_client_side_exception(method, url, ex, method_name)

        if response.status_code != requests.codes.ok:

            logger.debug(
                "%s %s detail",
                method,
                url,
                extra={"request.headers": headers, "request.args": args},
            )
            # PDF returned an error. Record it in New Relic before raising the exception.
            newrelic.agent.record_custom_event(
                "PDFError",
                {
                    "PDF.error.class": "PDFClientBadResponse",
                    "PDF.error.message": response.text,
                    "PDF.response.status": response.status_code,
                    "PDF.request.method": method,
                    "PDF.request.uri": url,
                    "PDF.request.response_millis": response.elapsed / MILLISECOND,
                    "api.request.method": flask.request.method if has_flask_context else None,
                    "api.request.uri": flask.request.path if has_flask_context else None,
                    "api.request.headers.x-amzn-requestid": flask.request.headers.get(
                        "x-amzn-requestid", None
                    )
                    if has_flask_context
                    else None,
                },
            )

            err: exception.PDFClientError

            err = exception.PDFFatalResponseError(
                response_status=response.status_code,
                message=response.text,
                method_name=method_name,
            )
            log_fn = logger.error

            log_fn(
                "%s %s => %s (%ims)",
                method,
                url,
                response.status_code,
                response.elapsed / MILLISECOND,
                extra={
                    "response.text": response.text,
                    "response.json": response.json(),
                },
                exc_info=err,
            )
            raise err

        logger.info(
            "%s %s => %s (%ims)", method, url, response.status_code, response.elapsed / MILLISECOND
        )
        return response

    def __repr__(self):
        return "<PDFClient %s>" % urllib.parse.urlparse(self.host).hostname

    def _handle_client_side_exception(
        self, method: str, url: str, ex: Exception, method_name: str
    ) -> None:
        # Make sure New Relic records errors from PDF API, even if the API does not ultimately
        # return an error.
        has_flask_context = flask.has_request_context()
        newrelic.agent.record_custom_event(
            "PDFError",
            {
                "PDF.error.class": type(ex).__name__,
                "PDF.error.message": str(ex),
                "PDF.request.method": method,
                "PDF.request.uri": url,
                "api.request.method": flask.request.method if has_flask_context else None,
                "api.request.uri": flask.request.path if has_flask_context else None,
                "api.request.headers.x-amzn-requestid": flask.request.headers.get(
                    "x-amzn-requestid", None
                )
                if has_flask_context
                else None,
            },
        )

        if isinstance(
            ex,
            (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
            ),
        ):
            logger.warning("%s %s => %r", method, url, ex)
            raise exception.PDFFatalUnavailable(method_name=method_name, cause=ex)
        else:
            logger.exception("%s %s => %r", method, url, ex)
            raise exception.PDFFatalClientSideError(method_name=method_name, cause=ex)
