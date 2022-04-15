#
# PDF client - PDF implementation.
#

import base64
import datetime
import json
import os.path
import urllib.parse
import xml.etree.ElementTree
from decimal import Decimal
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union, cast
from xml.etree.ElementTree import Element

import flask
import newrelic.agent
import oauthlib.oauth2
import pydantic
import requests
import xmlschema
from requests.models import Response

import massgov.pfml.util.logging

from . import client, exception, models
from .common import DOC_TYPES

logger = massgov.pfml.util.logging.get_logger(__name__)

"""
public abstract class Document
{
    public string Id { get; set; }
    public string BatchId { get; set; }

    public abstract string Type { get; }
    public abstract string FolderName { get; }
    public abstract string FileName { get; }
    public abstract string Template { get; }

    public abstract string ReplaceValuesInTemplate(string template);
}
"""

class GeneratePDFRequest():
    "id": str
    batchId: str
    "type": str


class PDF1099(GeneratePDFRequest):
    pass

class PDFClaimantInfo(GeneratePDFRequest):
    pass


class MergePDFRequest():
    "type": Optional[str]
    batchId: str
    numOfRecords: Optional[int]

class PDFClient(client.AbstractPDFClient):
    """PDF API client."""

    host: str
    updateTemplate: str
    generate: str
    merge: str

    request_count: int

    def __init__(self, host: str):
        self.host = host
        self.updateTemplate = urllib.parse.urljoin(self.host, "/updateTemplate")
        self.generate = urllib.parse.urljoin(self.host, "/generate")
        self.merge = urllib.parse.urljoin(self.host, "/merge")
        
        logger.info("host %s", self.host)
        # auth needed?

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


    def _request(
        self, method: str, url: str, headers: Dict[str, str], **args: Any
    ) -> requests.Response:
        """Make a request and handle errors."""
        self.request_count += 1
        has_flask_context = flask.has_request_context()
        logger.debug("%s %s start", method, url)
        method_name = url.split("/")[-1]

        try:
            response = requests[method](
                url, headers=headers, **args
            )
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as ex:
            self._handle_client_side_exception(method, url, ex)

        if response.status_code != requests.codes.ok:

            # Try to parse correlation ID as metadata from the response.
            pdf_correlation_id = get_pdf_correlation_id(response)

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
                    "PDF.error.correlation_id": pdf_correlation_id,
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
                    "response.pdf_correlation_id": pdf_correlation_id,
                    "response.json": response.json(),
                },
                exc_info=err,
            )
            raise err

        logger.info(
            "%s %s => %s (%ims)", method, url, response.status_code, response.elapsed / MILLISECOND
        )
        return response

    
    def generate(self, request: GeneratePDFRequest):
        try:
            url = self.generate
            if request.type in DOC_TYPES:
                url = f"{self.generate}/{request.type}"
            
            response = self._request(
                "post",
                url,
                json=request,
                headers={"Content-type": "application/json", "Accept": "application/json"},
            )

            if response.ok:
                logger.info("Pdf was successfully generated.")

            return response

        except requests.exceptions.RequestException as error:
            logger.error(error)
            raise Exception("Api error to merge Pdf.")


    def merge(self, request: MergePDFRequest):
        try:
            response = self._request(
                "post",
                self.merge,
                json=request,
                headers={"Content-type": "application/json", "Accept": "application/json"},
            )

            if response.ok:
                logger.info(f"Pdfs were successfully merged for batchId: {request.batchId}")

            return response

        except requests.exceptions.RequestException as error:
            logger.error(error)
            raise Exception("Api error to merge Pdf.")


