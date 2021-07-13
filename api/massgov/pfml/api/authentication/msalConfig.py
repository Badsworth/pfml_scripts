import os
import msal
import json
import requests
import massgov.pfml.util.logging
from dataclasses import dataclass
from typing import Optional

logger = massgov.pfml.util.logging.get_logger(__name__)

@dataclass
class MSALClientConfig:
    clientId: str
    clientSecret: str
    authority: str
    knownAuthorities: [str]
    redirectUri: str
    postLogoutRedirectUri: str
    scopes: [str]
    states: dict
    policies: dict

    @classmethod
    def from_env(cls) -> "MSALClientConfig":
        b2cStates = {
            "SIGN_IN": "sign_in",
            # CALL_API: "call_api",
            # PASSWORD_RESET: "password_reset",
        }

        b2cPolicies = {
            "authorityDomain": os.environ.get("AZURE_AD_AUTHORITY_DOMAIN", None),
            "authorities": {
                "login": {
                    "authority": f'https://{os.environ.get("AZURE_AD_AUTHORITY_DOMAIN", None)}/{os.environ.get("AZURE_AD_DIRECTORY_TENANT_ID", None)}',
                },
            },
        }

        return MSALClientConfig(
            clientId=os.environ.get("AZURE_AD_APPLICATION_CLIENT_ID", None),
            clientSecret=os.environ.get("AZURE_AD_SECRET_VALUE", None),
            authority=b2cPolicies["authorities"]["login"]["authority"],
            knownAuthorities=[b2cPolicies["authorityDomain"]],
            redirectUri="http://localhost:3000",
            postLogoutRedirectUri="http://localhost:3000",
            scopes=[f'{os.environ.get("AZURE_AD_APPLICATION_CLIENT_ID", None)}/.default'],
            policies=b2cPolicies,
            states=b2cStates
            # "https://graph.microsoft.com/user.read"
            # "protocolMode": "AAD",
            # "endpoint": "https://graph.microsoft.com/v1.0/users"
        )
