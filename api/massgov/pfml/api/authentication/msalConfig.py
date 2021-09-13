import os
from datetime import datetime
from typing import Optional

import requests

import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)


class MSALClientConfig:
    client_id: str
    client_secret: str
    tenant_id: str
    authority_domain: str
    public_keys: list[dict]
    public_keys_url: str
    public_keys_last_updated: datetime
    authority: str
    redirect_uri: str
    logout_uri: str
    scopes: list[str]

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: str,
        authority_domain: str,
        redirect_uri: str,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.authority_domain = authority_domain
        self.redirect_uri = redirect_uri

        self.authority = f"https://{self.authority_domain}/{self.tenant_id}"
        self.public_keys_url = f"{self.authority}/discovery/v2.0/keys?appid={self.client_id}"

        self.logout_uri = f"{self.authority}/oauth2/v2.0/logout?post_logout_redirect_uri={self.redirect_uri}?logged_out=true"

        self.scopes = [f"{self.client_id}/.default"]

        self.public_keys = self._get_public_keys(self.public_keys_url)
        self.public_keys_last_updated = datetime.now()

    def _get_public_keys(self, public_keys_url: str) -> list:
        response = requests.get(public_keys_url, timeout=5)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logger.warning("Failed to get Azure public keys")
            raise err
        return response.json().get("keys")


def get_msal_client_config() -> Optional[MSALClientConfig]:
    client_id = os.environ.get("AZURE_AD_APPLICATION_CLIENT_ID", "")
    client_secret = os.environ.get("AZURE_AD_SECRET_VALUE", "")
    tenant_id = os.environ.get("AZURE_AD_DIRECTORY_TENANT_ID", "")
    authority_domain = os.environ.get("AZURE_AD_AUTHORITY_DOMAIN", "")
    redirect_uri = os.environ.get("ADMIN_PORTAL_BASE_URL", "")
    if not all([client_id, client_secret, tenant_id, authority_domain, redirect_uri]):
        logger.warning("Azure variables are not set.")
        return None
    return MSALClientConfig(client_id, client_secret, tenant_id, authority_domain, redirect_uri)
