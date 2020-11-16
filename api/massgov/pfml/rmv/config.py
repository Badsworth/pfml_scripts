#
# RMV client - configuration classes.
#

import enum
import os
from dataclasses import dataclass

import boto3

import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)


class RMVCheckBehavior(enum.Enum):
    # Fully mocked endpoint
    MOCK = "fully_mocked"
    # Partially mocked endpoint, will call the RMV API when called with certain records. Mocked
    # responses otherwise.
    PARTIAL_MOCK = "partially_mocked"
    # All requests hit RMV API
    NO_MOCK = "not_mocked"


@dataclass
class RmvConfig:
    check_behavior: RMVCheckBehavior
    check_mock_success: bool
    base_url: str
    pkcs12_data: bytes
    pkcs12_pw: str

    @classmethod
    def from_env_and_secrets_manager(cls):
        check_behavior = RMVCheckBehavior(
            os.environ.get("RMV_CHECK_BEHAVIOR", RMVCheckBehavior.MOCK.value)
        )
        # "1" always passes id proofing, "0" always fails id proofing
        check_mock_success = os.environ.get("RMV_CHECK_MOCK_SUCCESS", "1") == "1"

        if check_behavior == RMVCheckBehavior.MOCK:
            base_url = ""
            pkcs12_pw = ""
            pkcs12_data = ""
        else:
            base_url = os.environ["RMV_CLIENT_BASE_URL"]
            pkcs12_pw = os.environ["RMV_CLIENT_CERTIFICATE_PASSWORD"]
            pkcs12_arn = os.environ["RMV_CLIENT_CERTIFICATE_BINARY_ARN"]

            secrets_client = boto3.client("secretsmanager")
            pkcs12_data = secrets_client.get_secret_value(SecretId=pkcs12_arn).get("SecretBinary")

        logger.info("rmv configured as %s", check_behavior)

        return RmvConfig(
            check_behavior=check_behavior,
            check_mock_success=check_mock_success,
            base_url=base_url,
            pkcs12_pw=pkcs12_pw,
            pkcs12_data=pkcs12_data,
        )
