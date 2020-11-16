import abc
import urllib
from collections import defaultdict
from typing import Any, Dict, Generic, List, Optional, TypeVar

import zeep
from requests import Session
from requests_pkcs12 import Pkcs12Adapter
from zeep.transports import Transport

from massgov.pfml.rmv.config import RmvConfig

CallerResponse = TypeVar("CallerResponse", dict, zeep.proxy.ServiceProxy)


class ApiCaller(Generic[CallerResponse], abc.ABC, metaclass=abc.ABCMeta):
    """
    Abstract class for implementing an RMV API caller.
    """

    @abc.abstractmethod
    def VendorLicenseInquiry(self, **kwargs: Any) -> CallerResponse:
        pass


class LazyApiCaller(Generic[CallerResponse], abc.ABC, metaclass=abc.ABCMeta):
    """
    Abstract class for implementing a lazily-loaded RMV API caller.
    """

    @abc.abstractmethod
    def get(self) -> ApiCaller[CallerResponse]:
        pass


class LazyZeepApiCaller(LazyApiCaller[zeep.proxy.ServiceProxy]):
    def __init__(self, config: Optional[RmvConfig] = None):
        if config is None:
            config = RmvConfig.from_env_and_secrets_manager()

        self.base_url = config.base_url.rstrip("/")
        self.pkcs12_data = config.pkcs12_data
        self.pkcs12_pw = config.pkcs12_pw
        self.init_session()

    def init_session(self):
        """
        Initialize a persistent HTTPS session for connecting to the RMV API.
        """
        self.session = Session()
        self.session.mount(
            self.base_url,
            Pkcs12Adapter(pkcs12_data=self.pkcs12_data, pkcs12_password=self.pkcs12_pw),
        )

    def get(self) -> ApiCaller[zeep.proxy.ServiceProxy]:
        url = urllib.parse.urljoin(self.base_url, "/vs/gateway/VendorLicenseInquiry/?WSDL")
        return zeep.Client(url, transport=Transport(session=self.session)).service


class MockZeepCaller(LazyApiCaller[dict], ApiCaller[dict]):
    """
    Zeep caller object mock to track calls and provided arguments.

    Takes in an response object to always return for VendorLicenseInquiry
    requests.
    """

    def __init__(
        self, response: Optional[Dict[str, Any]] = None,
    ):

        self.args: Dict[str, List[Any]] = defaultdict(lambda: [])
        self.calls: Dict[str, int] = defaultdict(int)

        default_response = {
            "CustomerKey": "12345",
            "LicenseID": "ABC12345",
            "License1ExpirationDate": "20210204",
            "LicenseSSN": "12345678",
            "CustomerInActive": False,
            "CFLSanctions": False,
            "CFLSanctionsActive": False,
            "Street1": "",
            "Street2": "",
            "City": "",
            "Zip": "",
            "OtherStuff": None,
            "Acknowledgement": None,
        }

        if response:
            response = {
                **default_response,
                **response,
            }
        else:
            response = default_response

        class AttrDict(dict):
            def __init__(self, *args, **kwargs):
                super(AttrDict, self).__init__(*args, **kwargs)
                self.__dict__ = self

        self.response = AttrDict(**response)

    def get(self) -> ApiCaller[dict]:
        return self

    def VendorLicenseInquiry(self, **kwargs: Any) -> CallerResponse:
        self.args["VendorLicenseInquiry"].append(kwargs)
        self.calls["VendorLicenseInquiry"] += 1
        return self.response
