from typing import Any, Dict, List, Optional

from pydantic import UUID4, Field
from sqlalchemy.orm import contains_eager

import massgov.pfml.api.app as app
from massgov.pfml.api.models.common import LookupEnum, MaskedPhoneResponse
from massgov.pfml.db import Session
from massgov.pfml.db.models.applications import Application
from massgov.pfml.db.models.employees import (
    Employer,
    EmployerQuarterlyContribution,
    User,
    UserLeaveAdministrator,
)
from massgov.pfml.db.models.verifications import Verification
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import FEINFormattedStr


class MFADeliveryPreference(str, LookupEnum):
    sms = "SMS"
    opt_out = "Opt Out"


class RoleResponse(PydanticBaseModel):
    role_id: int
    role_description: str


class ApplicationNamesResponse(PydanticBaseModel):
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]


class UserEmployerResponse(PydanticBaseModel):
    employer_dba: Optional[str]
    employer_fein: FEINFormattedStr
    employer_id: UUID4
    has_verification_data: bool


class UserLeaveAdminResponse(PydanticBaseModel):
    employer: UserEmployerResponse
    has_fineos_registration: bool
    verified: bool


class UserResponse(PydanticBaseModel):
    """Response object for a given User result"""

    user_id: UUID4
    auth_id: str = Field(alias="sub_id")
    email_address: str
    mfa_delivery_preference: Optional[MFADeliveryPreference]
    mfa_phone_number: Optional[MaskedPhoneResponse]
    first_name: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[MaskedPhoneResponse]
    # Optional since it isn't populated at first in from_orm(). After that it
    # should always be a potentially empty list.
    application_names: Optional[List[ApplicationNamesResponse]]
    consented_to_data_sharing: bool
    roles: List[RoleResponse]
    user_leave_administrators: list

    @classmethod
    def from_orm(cls, user: User) -> "UserResponse":
        user_response = super().from_orm(user)
        with app.db_session() as db_session:
            user_leave_administrators = get_user_leave_administrators(user, db_session)
            application_names_data = (
                db_session.query(
                    Application.first_name, Application.middle_name, Application.last_name
                )
                .filter(Application.user_id == user.user_id)
                .distinct()
                .limit(5)
                .all()
            )
        user_leave_administrators_data = [
            normalize_user_leave_admin_response(UserLeaveAdminResponse.from_orm(ula))
            for ula in user_leave_administrators
        ]
        user_response.user_leave_administrators = user_leave_administrators_data
        user_response.application_names = [
            ApplicationNamesResponse(
                first_name=n.first_name, middle_name=n.middle_name, last_name=n.last_name
            )
            for n in application_names_data
        ]
        if user_response.phone_number:
            user_response.phone_number.extension = user.phone_extension
        return user_response


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
    """Response object for a given AzureUser object"""

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
