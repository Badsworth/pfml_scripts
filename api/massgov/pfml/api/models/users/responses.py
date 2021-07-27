from typing import List

from pydantic import UUID4, Field

from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import FEINFormattedStr


class RoleResponse(PydanticBaseModel):
    role_id: int
    role_description: str


class EmployerResponse(PydanticBaseModel):
    employer_dba: str
    employer_fein: FEINFormattedStr
    employer_id: UUID4
    has_verification_data: bool


class UserLeaveAdminResponse(PydanticBaseModel):
    employer: EmployerResponse
    has_fineos_registration: bool
    verified: bool


class UserResponse(PydanticBaseModel):
    """Response object for a given User result """

    user_id: UUID4
    auth_id: str = Field(alias="sub_id")
    email_address: str
    consented_to_data_sharing: bool
    not_fraud: bool
    roles: List[RoleResponse]
    user_leave_administrators: List[UserLeaveAdminResponse]
