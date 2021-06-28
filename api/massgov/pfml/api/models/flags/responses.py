from datetime import datetime
from typing import Optional

from massgov.pfml.util.pydantic import PydanticBaseModel


class FlagResponse(PydanticBaseModel):
    name: str
    start: Optional[datetime]
    end: Optional[datetime]
    options: Optional[dict]
    enabled: bool
