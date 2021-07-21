import os
from dataclasses import dataclass

import massgov.pfml.util.logging

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
    publicKeysUrl: str

    @classmethod
    def from_env(cls) -> "MSALClientConfig":
        clientId = os.environ.get("AZURE_AD_APPLICATION_CLIENT_ID", None)
        clientSecret = os.environ.get("AZURE_AD_SECRET_VALUE", None)
        tenantId = os.environ.get("AZURE_AD_DIRECTORY_TENANT_ID", None)
        authorityDomain = os.environ.get("AZURE_AD_AUTHORITY_DOMAIN", None)

        b2cStates = {
            "SIGN_IN": "sign_in",
        }
        b2cPolicies = {
            "authorityDomain": authorityDomain,
            "authorities": {"login": {"authority": f"https://{authorityDomain}/{tenantId}",},},
        }
        keysUrl = f"https://{authorityDomain}/{tenantId}/discovery/v2.0/keys?appid={clientId}"

        return MSALClientConfig(
            clientId=clientId,
            clientSecret=clientSecret,
            authority=b2cPolicies["authorities"]["login"]["authority"],
            knownAuthorities=[b2cPolicies["authorityDomain"]],
            redirectUri="http://localhost:3000",
            postLogoutRedirectUri="http://localhost:3000/logout",
            scopes=[f"{clientId}/.default"],
            policies=b2cPolicies,
            states=b2cStates,
            publicKeysUrl=keysUrl
            # "https://graph.microsoft.com/user.read"
            # "protocolMode": "AAD",
            # "endpoint": "https://graph.microsoft.com/v1.0/users"
        )
