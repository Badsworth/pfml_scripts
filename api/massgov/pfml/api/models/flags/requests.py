from datetime import datetime
from typing import Optional

from massgov.pfml.util.pydantic import PydanticBaseModel


class FlagRequest(PydanticBaseModel):
    start: Optional[datetime]
    end: Optional[datetime]
    options: Optional[dict]
    enabled: bool
