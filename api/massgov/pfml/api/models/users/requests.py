from typing import Optional

from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import FEINUnformattedStr


class RoleRequest(PydanticBaseModel):
    role_description: str


class UserLeaveAdminRequest(PydanticBaseModel):
    employer_fein: FEINUnformattedStr


class UserCreateRequest(PydanticBaseModel):
    email_address: str
    password: str
    role: RoleRequest
    user_leave_administrator: Optional[UserLeaveAdminRequest]


class UserUpdateRequest(PydanticBaseModel):
    consented_to_data_sharing: bool
