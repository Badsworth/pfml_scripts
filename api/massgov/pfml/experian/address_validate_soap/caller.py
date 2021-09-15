import abc
import os
from functools import cached_property
from typing import Any, Dict, Optional

import zeep
from pydantic import Field
from requests import Session
from zeep.transports import Transport

import massgov.pfml.util.pydantic

# https://docs.experianaperture.io/address-validation/address-validate-soap/api-reference/api-specification/#v3-endpoint
# Note: After running into issues with non secure imports in the WSDL, using a modified version of the WSDL we ship with the code
SOAP_WSDL_DEFAULT_URL = os.path.join(os.path.dirname(__file__), "wsdl/ProOnDemandV3.wsdl")


class ExperianSOAPConfig(massgov.pfml.util.pydantic.PydanticBaseSettings):
    auth_token: str = Field(..., min_length=1)
    # Code expects a v3 endpoint. Defaults to US regional endpoint.
    soap_wsdl_uri: str = Field(SOAP_WSDL_DEFAULT_URL, min_length=1)

    class Config:
        # Shares a prefix with ExperianConfig as the same authentication token
        # is used for the different services. The configs could be merged into a
        # shared one at some point if simpler.
        env_prefix = "EXPERIAN_"


class ApiCaller(abc.ABC, metaclass=abc.ABCMeta):
    """
    Abstract class for implementing an Experian Address Validate SOAP API caller.
    """

    @abc.abstractmethod
    def DoSearch(self, **kwargs: Any) -> Dict[str, Any]:
        """Perform the DoSearch operation.

        Docs for request params: https://docs.experianaperture.io/address-validation/address-validate-soap/api-reference/soap-requests/#do-search
        Docs for response params: https://docs.experianaperture.io/address-validation/address-validate-soap/api-reference/soap-responses/#do-search
        """


class LazyApiCaller(abc.ABC, metaclass=abc.ABCMeta):
    """
    Abstract class for implementing a lazily-loaded Experian Address Validate
    SOAP API caller.
    """

    @abc.abstractmethod
    def get(self) -> ApiCaller:
        """Return an ApiCaller.

        Implicit requirement that a child class implementing this will not
        perform the caller initialization in its __init__(), but when this
        method is called.
        """


class LazyZeepApiCaller(LazyApiCaller, ApiCaller):
    def __init__(self, config: Optional[ExperianSOAPConfig] = None):
        if config is None:
            config = ExperianSOAPConfig()

        self.config = config

        self.soap_wsdl_uri = config.soap_wsdl_uri.rstrip("/")
        self.init_session()

    def init_session(self):
        """
        Initialize a persistent HTTPS session for connecting to the Experian
        Address Validate SOAP API.
        """
        self.session = Session()

        self.session.headers.update({"Auth-Token": self.config.auth_token})

    def get(self) -> ApiCaller:
        # The Experian WSDL unfortunately includes some schemas that require
        # forbid_entities to be turned off
        settings = zeep.Settings(forbid_entities=False)

        service_proxy = zeep.Client(
            self.soap_wsdl_uri, settings=settings, transport=Transport(session=self.session)
        ).service

        return service_proxy

    @cached_property
    def _caller(self) -> ApiCaller:
        return self.get()

    def DoSearch(self, **kwargs: Any) -> Dict[str, Any]:
        return self._caller.DoSearch(**kwargs)
