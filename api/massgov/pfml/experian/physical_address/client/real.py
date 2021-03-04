import urllib.parse
from typing import Any, Optional

import requests

import massgov.pfml.util.http as http_util
from massgov.pfml.experian.config import ExperianConfig

from .base import BaseClient
from .models import AddressFormatV1Response, AddressSearchV1Request, AddressSearchV1Response


class Client(BaseClient):
    """
    Client for accessing the Experian Address Validation API endpoints.
    """

    def __init__(
        self, config: Optional[ExperianConfig] = None, session: Optional[requests.Session] = None
    ) -> None:
        if not config:
            config = ExperianConfig()

        self.config = config

        self.session = self._build_session(session)

    def _build_session(self, session: Optional[requests.Session] = None) -> requests.Session:
        """Set things on the session that should be shared between all requests"""
        if not session:
            session = requests.Session()

        session.headers.update(
            {
                "Auth-Token": self.config.auth_token,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        # raise exception on any response with status codes >=400
        session.hooks = {"response": [lambda r, *args, **kwargs: r.raise_for_status()]}

        return session

    def _request(
        self, method: http_util.StandardRequestMethod, path: str, **kwargs: Any
    ) -> requests.Response:
        full_url = urllib.parse.urljoin(self.config.base_url, path)

        # add a default request timeout on our side unless told otherwise
        #
        # note this is separate from the service timeout specified in the
        # `Timeout-Seconds` header to Experian, this timeout is for the request
        # itself on the PFML side
        if "timeout" not in kwargs:
            # Experian will timeout after 15 seconds on their side, so have ours
            # be just a little bigger than that
            kwargs["timeout"] = 16

        return self.session.request(method, full_url, **kwargs)

    def search(
        self,
        req: AddressSearchV1Request,
        *,
        reference_id: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> AddressSearchV1Response:
        headers = dict()

        if reference_id:
            headers["Reference-Id"] = reference_id

        if timeout_seconds:
            headers["Timeout-Seconds"] = str(timeout_seconds)

        response = self._request(
            "POST", "/address/search/v1", data=req.json(exclude_none=True), headers=headers
        )
        return AddressSearchV1Response.parse_raw(response.text)

    def format(
        self,
        global_address_key: str,
        *,
        add_metadata: Optional[bool] = True,
        add_components: Optional[bool] = True,
        reference_id: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> AddressFormatV1Response:
        headers = dict()

        if reference_id:
            headers["Reference-Id"] = reference_id

        if timeout_seconds:
            headers["Timeout-Seconds"] = str(timeout_seconds)

        if add_metadata is not None:
            headers["Add-Metadata"] = "true" if add_metadata else "false"

        if add_components is not None:
            headers["Add-Components"] = "true" if add_components else "false"

        response = self._request("GET", f"/address/format/v1/{global_address_key}", headers=headers)
        return AddressFormatV1Response.parse_obj(response.json())
