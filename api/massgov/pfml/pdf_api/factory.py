#
# PDF client - factory.
#

# import os
# import urllib.parse
from typing import Optional

from pydantic import ValidationError

import massgov.pfml.util.logging
from massgov.pfml.util.pydantic import PydanticBaseSettings

from . import client, mock_client, pdf_client

logger = massgov.pfml.util.logging.get_logger(__name__)


class PDFClientConfig(PydanticBaseSettings):
    host: str

    class Config:
        env_prefix = "pdf_api_"


def create_client(config: Optional[PDFClientConfig] = None) -> client.AbstractPDFClient:
    """Factory to create the right type of client object for the given configuration."""
    if config is None:
        try:
            config = PDFClientConfig()
        except ValidationError as err:
            logger.info("Env var 'PDF_API_HOST' has not been defined.", exc_info=err)
            return mock_client.MockPDFClient(host="http://localhost:5001")

    return pdf_client.PDFClient(host=config.host)
