from typing import List, Optional, Union

from werkzeug.exceptions import Forbidden

import massgov.pfml.db as db
from massgov.pfml.api.models.common import Phone
from massgov.pfml.api.models.users.requests import UserCreateRequest, UserUpdateRequest
from massgov.pfml.api.util.deepgetattr import deepgetattr
from massgov.pfml.api.validation.exceptions import IssueRule, IssueType, ValidationErrorDetail
from massgov.pfml.db.models.applications import Application
from massgov.pfml.db.models.employees import Employer, Role, User


def get_users_convert_claimant_issues(user: User) -> List[ValidationErrorDetail]:
    """Validate that the user is an unverified leave admin"""
    issues = []

    verified_leave_admins = [
        ula
        for ula in user.user_leave_administrators
        if ula.fineos_web_id is not None or ula.verification_id is not None
    ]

    if Role.EMPLOYER.role_id not in [role.role_id for role in user.roles]:
        issues.append(
            ValidationErrorDetail(
                field="role.role_description",
                message="You're not an employer!",
                type=IssueType.conflicting,
            )
        )
    if len(verified_leave_admins) > 0:
        issues.append(
            ValidationErrorDetail(
                field="role.role_description",
                message="Verified Leave Admins cannot convert their account!",
                type=IssueType.conflicting,
            )
        )

    return issues


def get_users_convert_employer_issues(
    user: User, db_session: db.Session
) -> List[ValidationErrorDetail]:
    """Validate that the Employer a user is signing up to administer is valid"""
    issues = []

    if Role.EMPLOYER.role_id in [role.role_id for role in user.roles]:
        issues.append(
            ValidationErrorDetail(
                field="user_leave_administrator.employer_fein",
                message="You're already an employer!",
                type=IssueType.conflicting,
            )
        )

    application_count = (
        db_session.query(Application).filter(Application.user_id == user.user_id).count()
    )
    if application_count:
        issues.append(
            ValidationErrorDetail(
                field="applications",
                message="Your account has submitted applications!",
                type=IssueType.conflicting,
            )
        )

    return issues


def get_users_post_required_fields_issues(
    user_create_request: UserCreateRequest,
) -> List[ValidationErrorDetail]:
    """Validate that the request has all required fields"""
    ALWAYS_REQUIRED_FIELDS = ["email_address", "password", "role.role_description"]
    issues = []
    is_employer = (
        deepgetattr(user_create_request, "role.role_description") == Role.EMPLOYER.role_description
    )

    for field in ALWAYS_REQUIRED_FIELDS:
        val = deepgetattr(user_create_request, field)
        if val is None:
            issues.append(
                ValidationErrorDetail(
                    type=IssueType.required, message=f"{field} is required", field=field
                )
            )

    if (
        is_employer
        and deepgetattr(user_create_request, "user_leave_administrator.employer_fein") is None
    ):
        issues.append(
            ValidationErrorDetail(
                rule=IssueRule.conditional,
                type=IssueType.required,
                message="user_leave_administrator.employer_fein is required",
                field="user_leave_administrator.employer_fein",
            )
        )

    return issues


def get_users_post_employer_issues(employer: Optional[Employer]) -> List[ValidationErrorDetail]:
    """Validate that the Employer a user is signing up to administer is valid"""
    issues = []

    if employer is None:
        issues.append(
            ValidationErrorDetail(
                field="user_leave_administrator.employer_fein",
                message="Invalid EIN",
                type=IssueType.require_employer,
            )
        )
    elif employer.fineos_employer_id is None:
        issues.append(
            ValidationErrorDetail(
                field="user_leave_administrator.employer_fein",
                message="Confirm that you have the correct EIN, and that the Employer is contributing to Paid Family and Medical Leave.",
                type=IssueType.require_contributing_employer,
            )
        )

    return issues


def get_users_patch_issues(
    user_patch_request: UserUpdateRequest, user: Optional[User] = None
) -> List[ValidationErrorDetail]:
    """Validate that the patch request has all required fields"""
    issues = []

    if user_patch_request.mfa_phone_number:
        required_fields = ["phone_number", "int_code", "phone_type"]
        for field in required_fields:
            if deepgetattr(user_patch_request, "mfa_phone_number.{}".format(field)) is None:
                issues.append(
                    ValidationErrorDetail(
                        field="mfa_phone_number.{}".format(field),
                        type=IssueType.required,
                        message="{} is required when mfa_phone_number is included in request".format(
                            field
                        ),
                    )
                )
    if (
        user_patch_request.first_name
        or user_patch_request.last_name
        or user_patch_request.phone_number
    ):
        ## Currently we only update these fields for Employer Users
        if user and user.is_worker_user:
            raise Forbidden()

        ## Each field is required
        required_fields = ["first_name", "last_name", "phone_number"]
        for field in required_fields:
            if _field_is_empty(deepgetattr(user_patch_request, field)):
                issues.append(
                    ValidationErrorDetail(
                        field=field,
                        type=IssueType.required,
                        message="{} is required".format(field),
                    )
                )
    return issues


def _field_is_empty(required_field: Union[Phone, str, None]) -> bool:
    if required_field is None:
        return True
    elif isinstance(required_field, str) and len(required_field) < 1:
        return True
    elif isinstance(required_field, Phone) and required_field.phone_number is None:
        return True
    return False
