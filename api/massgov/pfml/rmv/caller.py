import abc
import os
import urllib
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Generic, List, Optional, TypeVar

import boto3
import zeep
from requests import Session
from requests_pkcs12 import Pkcs12Adapter
from zeep.transports import Transport

CallerResponse = TypeVar("CallerResponse", dict, zeep.proxy.ServiceProxy)


@dataclass
class RmvConfig:
    base_url: str
    pkcs12_data: bytes
    pkcs12_pw: str

    @classmethod
    def from_env_and_secrets_manager(cls):
        pkcs12_arn = os.environ["RMV_CLIENT_CERTIFICATE_BINARY_ARN"]

        secrets_client = boto3.client("secretsmanager")
        pkcs12_data = secrets_client.get_secret_value(SecretId=pkcs12_arn).get("SecretBinary")

        return RmvConfig(
            base_url=os.environ["RMV_CLIENT_BASE_URL"],
            pkcs12_pw=os.environ["RMV_CLIENT_CERTIFICATE_PASSWORD"],
            pkcs12_data=pkcs12_data,
        )


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
        url = urllib.parse.urljoin(self.base_url, "/gateway/VendorLicenseInquiry/?WSDL")
        return zeep.Client(url, transport=Transport(session=self.session)).service


class MockZeepCaller(LazyApiCaller[dict], ApiCaller[dict]):
    """
    Zeep caller object mock to track calls and provided arguments.

    Takes in an response object to always return for VendorLicenseInquiry
    requests.
    """

    def __init__(self, response: Optional[Dict[str, Any]] = None):

        self.args: Dict[str, List[Any]] = defaultdict(lambda: [])
        self.calls: Dict[str, int] = defaultdict(int)

        default_response = {
            "CustomerKey": "12345",
            "LicenseID": "ABC12345",
            # Set the expiration date to some date in the future.
            "License1ExpirationDate": (datetime.now() + timedelta(days=30)).strftime("%Y%m%d"),
            "LicenseSSN": "12345678",
            "CustomerInActive": False,
            "CFLSanctions": False,
            "CFLSanctionsActive": False,
            "Street1": "",
            "Street2": "",
            "City": "",
            "Zip": "",
            "Sex": "",
            "OtherStuff": None,
            "Acknowledgement": None,
        }

        if response:
            if response.get("Acknowledgement", None) is not None:
                # When the RMV responds with an Acknowledgement value, all other
                # fields in the response are None
                empty_response = dict.fromkeys(default_response, None)
                empty_response.update(response)

                response = empty_response
            else:
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
