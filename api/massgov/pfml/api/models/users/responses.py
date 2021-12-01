from typing import Any, Dict, List, Optional

from pydantic import UUID4, Field
from sqlalchemy.orm import contains_eager

from massgov.pfml.db import Session
from massgov.pfml.db.models.employees import (
    Employer,
    EmployerQuarterlyContribution,
    User,
    UserLeaveAdministrator,
)
from massgov.pfml.db.models.verifications import Verification
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
    mfa_phone_number: Optional[str]
    consented_to_data_sharing: bool
    roles: List[RoleResponse]
    user_leave_administrators: List[UserLeaveAdminResponse]


class AuthURIResponse(PydanticBaseModel):
    auth_uri: str
    claims_challenge: Optional[str]
    code_verifier: str
    nonce: str
    redirect_uri: str
    scope: list
    state: str


class AuthCodeResponse(PydanticBaseModel):
    code: str
    session_state: str
    state: str


class AdminTokenResponse(PydanticBaseModel):
    access_token: str
    refresh_token: str
    id_token: str


class AdminUserResponse(PydanticBaseModel):
    """Response object for a given AzureUser object """

    sub_id: str
    first_name: Optional[str]
    last_name: Optional[str]
    email_address: str
    groups: List[str]
    permissions: List[str]


def get_user_leave_administrators(user: User, db: Session) -> List[UserLeaveAdministrator]:
    """
    Get User Leave Administrators and load required relationship data in place
    for better performance when users are a leave admin for multiple employers
    """
    return (
        db.query(UserLeaveAdministrator)
        .join(Employer)
        .join(EmployerQuarterlyContribution, isouter=True)
        .join(Verification, isouter=True)
        .options(
            contains_eager(UserLeaveAdministrator.employer).contains_eager(
                Employer.employer_quarterly_contribution
            )
        )
        .filter(UserLeaveAdministrator.user_id == user.user_id)
        .all()
    )


def user_response(user: User, db: Session) -> Dict[str, Any]:
    user_leave_administrators = get_user_leave_administrators(user, db)
    response = UserResponse.from_orm(user)
    user_leave_administrators_data = [
        normalize_user_leave_admin_response(UserLeaveAdminResponse.from_orm(ula))
        for ula in user_leave_administrators
    ]
    response_data = response.dict()
    response_data["user_leave_administrators"] = user_leave_administrators_data
    return response_data


def normalize_user_leave_admin_response(
    leave_admin_response: UserLeaveAdminResponse,
) -> Dict[str, Any]:
    leave_admin_dict = leave_admin_response.dict()
    return {
        "employer_dba": leave_admin_dict["employer"]["employer_dba"],
        "employer_fein": leave_admin_dict["employer"]["employer_fein"],
        "employer_id": leave_admin_dict["employer"]["employer_id"],
        "has_fineos_registration": leave_admin_dict["has_fineos_registration"],
        "verified": leave_admin_dict["verified"],
        "has_verification_data": leave_admin_dict["employer"]["has_verification_data"],
    }
