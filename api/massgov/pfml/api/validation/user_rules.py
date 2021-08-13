from typing import List, Optional

import massgov.pfml.db as db
from massgov.pfml.api.models.users.requests import UserCreateRequest
from massgov.pfml.api.util.deepgetattr import deepgetattr
from massgov.pfml.api.validation.exceptions import IssueRule, IssueType, ValidationErrorDetail
from massgov.pfml.db.models.applications import Application
from massgov.pfml.db.models.employees import Employer, Role, User


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
                    type=IssueType.required, message=f"{field} is required", field=field,
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
