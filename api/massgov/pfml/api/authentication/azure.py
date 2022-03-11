from datetime import datetime
from typing import Optional

import requests
from pydantic import Field, ValidationError

import massgov.pfml.util.logging
from massgov.pfml.util.pydantic import PydanticBaseSettings

logger = massgov.pfml.util.logging.get_logger(__name__)


class AzureSettings(PydanticBaseSettings):
    authority_domain: str
    client_id: str
    client_secret: str
    parent_group: str
    redirect_uri: str = Field(..., env="ADMIN_PORTAL_BASE_URL")
    tenant_id: str

    class Config:
        env_prefix = "azure_ad_"


class AzureClientConfig:
    authority: str
    authority_domain: str
    azure_settings: AzureSettings
    client_id: str
    client_secret: str
    logout_uri: str
    parent_group: str
    public_keys: list[dict]
    public_keys_url: str
    public_keys_last_updated: datetime
    redirect_uri: str
    scopes: list[str]

    def __init__(self, azure_settings: AzureSettings):
        self.azure_settings = azure_settings
        self.authority_domain = self.azure_settings.authority_domain
        self.client_id = self.azure_settings.client_id
        self.client_secret = self.azure_settings.client_secret
        self.parent_group = self.azure_settings.parent_group
        self.redirect_uri = self.azure_settings.redirect_uri

        self.authority = (
            f"https://{self.azure_settings.authority_domain}/{self.azure_settings.tenant_id}"
        )
        self.public_keys_url = f"{self.authority}/discovery/v2.0/keys?appid={self.client_id}"

        self.logout_uri = f"{self.authority}/oauth2/v2.0/logout?post_logout_redirect_uri={self.redirect_uri}?logged_out=true"

        self.scopes = [f"{self.azure_settings.client_id}/.default"]

        self.public_keys = self._get_public_keys(self.public_keys_url)
        self.public_keys_last_updated = datetime.now()

    def _get_public_keys(self, public_keys_url: str) -> list:
        logger.info("Retrieving public keys from %s", public_keys_url)
        response = requests.get(public_keys_url, timeout=5)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logger.error("Failed to get Azure public keys", exc_info=err)
            return []
        return response.json().get("keys")

    def update_keys(self):
        now = datetime.now()
        seconds_in_24_hours = 86400
        if (now - self.public_keys_last_updated).total_seconds() > seconds_in_24_hours:
            self.public_keys = self._get_public_keys(self.public_keys_url)
            self.public_keys_last_updated = now


class AzureUser:
    email_address: str
    first_name: str
    groups: list[str]
    last_name: str
    permissions: list[int]
    sub_id: str

    def __init__(self, email_address, first_name, groups, last_name, permissions, sub_id):
        self.email_address = email_address
        self.first_name = first_name
        self.groups = groups
        self.last_name = last_name
        self.permissions = permissions
        self.sub_id = sub_id


def create_azure_client_config(
    azure_settings: Optional[AzureSettings] = None,
) -> Optional[AzureClientConfig]:
    if azure_settings is None:
        try:
            azure_settings = AzureSettings()
        except ValidationError as err:
            logger.info("Azure AD is not configured", exc_info=err)
            return None
    if not azure_settings.client_id:
        logger.info("Azure AD client id is empty")
        return None
    return AzureClientConfig(azure_settings)
