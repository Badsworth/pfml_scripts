from typing import List

from massgov.pfml.api.models.users.requests import UserCreateRequest
from massgov.pfml.api.util.deepgetattr import deepgetattr
from massgov.pfml.api.util.response import Issue, IssueRule, IssueType
from massgov.pfml.db.models.employees import Role


def get_users_post_issues(user_create_request: UserCreateRequest) -> List[Issue]:
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
