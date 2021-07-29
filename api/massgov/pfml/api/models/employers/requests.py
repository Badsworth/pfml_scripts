from typing import Optional

from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import FEINUnformattedStr


class EmployerAddFeinRequest(PydanticBaseModel):
    employer_fein: Optional[FEINUnformattedStr]
