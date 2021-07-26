import os
import requests
from datetime import datetime
from dataclasses import dataclass

import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)


@dataclass
class MSALClientConfig:
    client_id: str
    client_secret: str
    authority: str
    known_authorities: [str]
    redirect_uri: str
    post_logout_redirect_uri: str
    scopes: [str]
    states: dict
    policies: dict
    public_keys: [dict]
    public_keys_url: str
    public_keys_last_updated: datetime
    logout_url: str

    @classmethod
    def from_env(cls) -> "MSALClientConfig":
        cls.client_id = os.environ.get("AZURE_AD_APPLICATION_CLIENT_ID", None)
        cls.client_secret = os.environ.get("AZURE_AD_SECRET_VALUE", None)
        cls.tenant_id = os.environ.get("AZURE_AD_DIRECTORY_TENANT_ID", None)
        cls.authority_domain = os.environ.get("AZURE_AD_AUTHORITY_DOMAIN", None)

        # prevents crash in case of missing env. variables
        if cls.client_id is None or cls.tenant_id is None or cls.client_secret is None or cls.authority_domain is None:
            logger.warning("Missing Azure AD environment variables!")
            return cls
            
        cls.b2c_states = {
            "SIGN_IN": "sign_in",
        }
        
        cls.b2c_policies = {
            "authorityDomain": cls.authority_domain,
            "authorities": {"login":{"authority": f"https://{cls.authority_domain}/{cls.tenant_id}",},},
        }

        cls.public_keys_url = f"https://{cls.authority_domain}/{cls.tenant_id}/discovery/v2.0/keys?appid={cls.client_id}"
        response = requests.get(cls.public_keys_url, timeout=5)
        cls.public_keys = response.json()["keys"]
        cls.public_keys_last_updated = datetime.now()

        cls.authority = cls.b2c_policies["authorities"]["login"]["authority"]
        cls.known_authorities = [cls.b2c_policies["authorityDomain"]]
        # @todo: environment based url redirects
        cls.redirect_uri = os.environ.get("CORS_ORIGIN")
        cls.post_logout_redirect_uri = f"{cls.redirect_uri}/logout"
        cls.logout_url = f"{cls.authority}/oauth2/v2.0/logout?post_logout_redirect_uri={cls.post_logout_redirect_uri}"
        cls.scopes = [f"{cls.client_id}/.default"]
        cls.policies = cls.b2c_policies
        cls.states = cls.b2c_states
        return cls
