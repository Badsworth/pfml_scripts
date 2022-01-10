from typing import Optional

from massgov.pfml.util.pydantic import PydanticBaseModel


class EmployeeUpdateRequest(PydanticBaseModel):
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    email_address: Optional[str]


class EmployeeSearchRequest(PydanticBaseModel):
    first_name: str
    middle_name: Optional[str]
    last_name: str
    tax_identifier_last4: str
