from pydantic import UUID4

from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import FEINFormattedStr


class EmployerAddFeinResponse(PydanticBaseModel):
    employer_dba: str
    employer_fein: FEINFormattedStr
    employer_id: UUID4
