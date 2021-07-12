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
            scopes=[f'{os.environ.get("AZURE_AD_APPLICATION_CLIENT_ID", None)}/.default'],
            policies=b2cPolicies,
            states=b2cStates
            # "https://graph.microsoft.com/user.read"
            # "postLogoutRedirectUri": "http://localhost:3000",
            # "protocolMode": "AAD",
            # "endpoint": "https://graph.microsoft.com/v1.0/users"
        )

class MSALClient:
    config: MSALClientConfig
    client: msal.ConfidentialClientApplication
    
    def __init__(self, config: Optional[MSALClientConfig] = None): # response type?
        """Factory to create the right type of client object for the given configuration."""
        self.config = config
        if self.config is None:
            self.config = MSALClientConfig.from_env()
        
        # Create a preferably long-lived app instance which maintains a token cache.
        self.client = msal.ConfidentialClientApplication(
            self.config.clientId,
            authority=self.config.authority,
            client_credential=self.config.clientSecret,
            # token_cache=...  # Default cache is in memory only.
                            # You can learn how to use SerializableTokenCache from
                            # https://msal-python.readthedocs.io/en/latest/#msal.SerializableTokenCache
        )

    def get_azure_ad_sso_token(self):
        # creates client & config if not sent in params
        result = None
        # Firstly, looks up a token from cache
        # Since we are looking for token for the current app, NOT for an end user,
        # notice we give account parameter as None.

        result = self.client.acquire_token_silent(self.config.scopes, account=None)

        if not result:
            logger.info("No suitable token exists in cache. Let's get a new one from AAD.")
            result = self.client.acquire_token_for_client(scopes=self.config.scopes)
            
        logger.info(result)


        return result