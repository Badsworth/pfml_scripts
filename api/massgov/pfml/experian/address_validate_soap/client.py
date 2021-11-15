import json
from typing import Optional

import flask
import newrelic.agent
import zeep.helpers as zeep_helpers

import massgov.pfml.util.logging
from massgov.pfml.experian.address_validate_soap.caller import ApiCaller, LazyZeepApiCaller
from massgov.pfml.experian.address_validate_soap.models import SearchRequest, SearchResponse

logger = massgov.pfml.util.logging.get_logger(__name__)


class Client:
    """
    Client for accessing the Experian Address Validate SOAP API
    """

    def __init__(self, caller: Optional[ApiCaller] = None):
        self._caller = caller or LazyZeepApiCaller()

    def search(self, request: SearchRequest) -> SearchResponse:
        req_body = json.loads(request.json(by_alias=True))

        try:
            res = self._caller.DoSearch(**req_body)
        except Exception as e:
            logger.exception("Error making Experian Address Validate SOAP request")

            has_flask_context = flask.has_request_context()
            newrelic.agent.record_custom_event(
                "ExperianAddressValidateSOAPError",
                {
                    "error.class": type(e).__name__,
                    "error.message": str(e),
                    "request.method": flask.request.method if has_flask_context else None,
                    "request.uri": flask.request.path if has_flask_context else None,
                    "request.headers.x-amzn-requestid": flask.request.headers.get(
                        "x-amzn-requestid", None
                    )
                    if has_flask_context
                    else None,
                },
            )

            raise

        return SearchResponse(**zeep_helpers.serialize_object(res)["body"])
