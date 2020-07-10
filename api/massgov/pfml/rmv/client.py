import os
import urllib
from dataclasses import dataclass
from functools import cached_property
from typing import Optional

import boto3
from requests import Session
from requests_pkcs12 import Pkcs12Adapter
from zeep import Client
from zeep.transports import Transport


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


class RmvClient:
    """
    Client for accessing the Registry of Motor Vehicles (RMV) API.
    """

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

    @cached_property
    def client(self):
        url = urllib.parse.urljoin(self.base_url, "/vs/gateway/VendorLicenseInquiry/?WSDL")
        return Client(url, transport=Transport(session=self.session))
