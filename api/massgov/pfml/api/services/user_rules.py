from typing import List, Optional

from massgov.pfml.api.models.users.requests import UserCreateRequest
from massgov.pfml.api.util.deepgetattr import deepgetattr
from massgov.pfml.api.util.response import Issue, IssueRule, IssueType
from massgov.pfml.db.models.employees import Employer, Role


def get_users_post_required_fields_issues(user_create_request: UserCreateRequest) -> List[Issue]:
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
                Issue(type=IssueType.required, message=f"{field} is required", field=field,)
            )

    if (
        is_employer
        and deepgetattr(user_create_request, "user_leave_administrator.employer_fein") is None
    ):
        issues.append(
            Issue(
                rule=IssueRule.conditional,
                type=IssueType.required,
                message="user_leave_administrator.employer_fein is required",
                field="user_leave_administrator.employer_fein",
            )
        )

    return issues


def get_users_post_employer_issues(employer: Optional[Employer]) -> List[Issue]:
    """Validate that the Employer a user is signing up to administer is valid"""
    issues = []

    if employer is None:
        issues.append(
            Issue(
                field="user_leave_administrator.employer_fein",
                message="Invalid EIN",
                type=IssueType.require_employer,
            )
        )
    elif employer.fineos_employer_id is None:
        issues.append(
            Issue(
                field="user_leave_administrator.employer_fein",
                message="Confirm that you have the correct EIN, and that the Employer is contributing to Paid Family and Medical Leave.",
                type=IssueType.require_contributing_employer,
            )
        )

    return issues
