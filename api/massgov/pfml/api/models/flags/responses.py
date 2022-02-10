from datetime import datetime
from typing import Optional

from massgov.pfml.util.pydantic import PydanticBaseModel


class FlagResponse(PydanticBaseModel):
    name: str
    start: Optional[datetime]
    end: Optional[datetime]
    options: Optional[dict]
    enabled: bool


class FlagLogResponse(FlagResponse):
    first_name: str
    last_name: str
    updated_at: datetime
