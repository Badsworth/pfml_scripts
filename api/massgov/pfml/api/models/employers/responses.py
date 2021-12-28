from typing import Optional

from pydantic import UUID4

from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import FEINFormattedStr


class EmployerResponse(PydanticBaseModel):
    employer_dba: Optional[str]
    employer_fein: FEINFormattedStr
    employer_id: UUID4
