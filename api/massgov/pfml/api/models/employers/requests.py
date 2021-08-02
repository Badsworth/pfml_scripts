from typing import Optional

from massgov.pfml.types import Fein
from massgov.pfml.util.pydantic import PydanticBaseModel


class EmployerAddFeinRequest(PydanticBaseModel):
    employer_fein: Optional[Fein]
