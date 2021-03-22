import faker

from massgov.pfml.api.models.users.requests import (
    RoleRequest,
    UserCreateRequest,
    UserLeaveAdminRequest,
)
from massgov.pfml.api.services.user_rules import get_users_post_issues
from massgov.pfml.api.util.response import Issue, IssueRule, IssueType
from massgov.pfml.db.models.employees import Role

fake = faker.Faker()


def test_get_users_post_issues_always_required_fields():
    issues = get_users_post_issues(UserCreateRequest())

    assert (
        Issue(type=IssueType.required, field="email_address", message="email_address is required")
        in issues
    )
    assert (
        Issue(type=IssueType.required, field="password", message="password is required") in issues
    )
    assert (
        Issue(
            type=IssueType.required,
            field="role.role_description",
            message="role.role_description is required",
        )
        in issues
    )
    assert len(issues) == 3


def test_get_users_post_issues_ein_required_for_employer():
    def expect_ein_issue(issues):
        assert (
            Issue(
                type=IssueType.required,
                rule=IssueRule.conditional,
                field="user_leave_administrator.employer_fein",
                message="user_leave_administrator.employer_fein is required",
            )
            in issues
        )

    expect_ein_issue(
        get_users_post_issues(
            UserCreateRequest(role=RoleRequest(role_description=Role.EMPLOYER.role_description),)
        )
    )

    expect_ein_issue(
        get_users_post_issues(
            UserCreateRequest(
                user_leave_administrator=UserLeaveAdminRequest(),
                role=RoleRequest(role_description=Role.EMPLOYER.role_description),
            )
        )
    )


def test_get_users_post_issues_valid_claimant():
    issues = get_users_post_issues(
        UserCreateRequest(
            email_address=fake.email(domain="example.com"),
            password=fake.password(length=12),
            role=RoleRequest(role_description="Claimant"),
        )
    )

    assert len(issues) == 0


def test_get_users_post_issues_valid_employer():
    issues = get_users_post_issues(
        UserCreateRequest(
            email_address=fake.email(domain="example.com"),
            password=fake.password(length=12),
            role=RoleRequest(role_description=Role.EMPLOYER.role_description),
            user_leave_administrator=UserLeaveAdminRequest(employer_fein="123456789"),
        )
    )

    assert len(issues) == 0
