import abc
import os
import urllib
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

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
    def VendorLicenseInquiry(self, **kwargs) -> CallerResponse:
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
