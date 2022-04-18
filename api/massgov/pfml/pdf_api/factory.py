#
# PDF client - factory.
#

import urllib.parse
from typing import Optional

import massgov.pfml.util.logging
import massgov.pfml.util.pydantic
from massgov.pfml.util.pydantic import PydanticBaseSettings

from . import client, mock_client, pdf_client

logger = massgov.pfml.util.logging.get_logger(__name__)


class PDFClientSettings(PydanticBaseSettings):
    host: str

    class Config:
        env_prefix = "pdf_api_"


class PDFClientConfig:
    host: str

    def __init__(self, settings: PDFClientSettings):

        if os.environ.get("PDF_API_HOST") is None:
            raise Exception("Env var 'PDF_API_HOST' has not being defined.")

        self.host = urllib.parse.urljoin(os.environ.get("PDF_API_HOST"), "/api/pdf")


def create_client(config: Optional[PDFClientConfig] = None) -> client.AbstractPDFClient:
    """Factory to create the right type of client object for the given configuration."""
    if config is None:
        config = PDFClientConfig()

    if config.host:
        return pdf_client.PDFClient(
            host=config.host,
        )
    else:
        logger.warning("using mock PDF API client")
        return mock_client.MockPDFClient()
