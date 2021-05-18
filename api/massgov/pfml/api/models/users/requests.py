from typing import Optional

from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import FEINUnformattedStr


class RoleRequest(PydanticBaseModel):
    role_description: Optional[str]


class UserLeaveAdminRequest(PydanticBaseModel):
    employer_fein: Optional[FEINUnformattedStr]


class UserCreateRequest(PydanticBaseModel):
    # Enforcement of these fields' presence is via user_rules.py
    email_address: Optional[str]
    password: Optional[str]
    role: Optional[RoleRequest]
    user_leave_administrator: Optional[UserLeaveAdminRequest]


class UserUpdateRequest(PydanticBaseModel):
    consented_to_data_sharing: bool
