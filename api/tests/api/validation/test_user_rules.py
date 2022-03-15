import faker

from massgov.pfml.api.models.users.requests import (
    RoleRequest,
    UserCreateRequest,
    UserLeaveAdminRequest,
    UserUpdateRequest,
)
from massgov.pfml.api.validation.exceptions import IssueRule, IssueType, ValidationErrorDetail
from massgov.pfml.api.validation.user_rules import (
    get_users_convert_employer_issues,
    get_users_patch_issues,
    get_users_post_employer_issues,
    get_users_post_required_fields_issues,
)
from massgov.pfml.db.models.employees import Role
from massgov.pfml.db.models.factories import (
    ApplicationFactory,
    EmployerFactory,
    EmployerOnlyRequiredFactory,
    UserFactory,
)

fake = faker.Faker()


class TestGetUsersConvertEmployerIssues:
    def test_already_employer(self, test_db_session, initialize_factories_session):
        user = UserFactory.create(roles=[Role.EMPLOYER])
        issues = get_users_convert_employer_issues(user, test_db_session)
        assert (
            ValidationErrorDetail(
                type=IssueType.conflicting,
                field="user_leave_administrator.employer_fein",
                message="You're already an employer!",
            )
            in issues
        )

    def test_existing_applications(self, user, test_db_session, initialize_factories_session):
        ApplicationFactory.create(user=user)
        issues = get_users_convert_employer_issues(user, test_db_session)
        assert (
            ValidationErrorDetail(
                type=IssueType.conflicting,
                field="applications",
                message="Your account has submitted applications!",
            )
            in issues
        )


class TestGetUsersPostRequiredFieldsIssues:
    def test_always_required_fields(self):
        issues = get_users_post_required_fields_issues(UserCreateRequest())

        assert (
            ValidationErrorDetail(
                type=IssueType.required, field="email_address", message="email_address is required"
            )
            in issues
        )
        assert (
            ValidationErrorDetail(
                type=IssueType.required, field="password", message="password is required"
            )
            in issues
        )
        assert (
            ValidationErrorDetail(
                type=IssueType.required,
                field="role.role_description",
                message="role.role_description is required",
            )
            in issues
        )
        assert len(issues) == 3

    def test_ein_required_for_employer(self):
        def expect_ein_issue(issues):
            assert (
                ValidationErrorDetail(
                    type=IssueType.required,
                    rule=IssueRule.conditional,
                    field="user_leave_administrator.employer_fein",
                    message="user_leave_administrator.employer_fein is required",
                )
                in issues
            )

        expect_ein_issue(
            get_users_post_required_fields_issues(
                UserCreateRequest(role=RoleRequest(role_description=Role.EMPLOYER.role_description))
            )
        )

        expect_ein_issue(
            get_users_post_required_fields_issues(
                UserCreateRequest(
                    user_leave_administrator=UserLeaveAdminRequest(),
                    role=RoleRequest(role_description=Role.EMPLOYER.role_description),
                )
            )
        )

    def test_valid_claimant(self):
        issues = get_users_post_required_fields_issues(
            UserCreateRequest(
                email_address=fake.email(domain="example.com"),
                password=fake.password(length=12),
                role=RoleRequest(role_description="Claimant"),
            )
        )

        assert len(issues) == 0

    def test_valid_employer(self):
        issues = get_users_post_required_fields_issues(
            UserCreateRequest(
                email_address=fake.email(domain="example.com"),
                password=fake.password(length=12),
                role=RoleRequest(role_description=Role.EMPLOYER.role_description),
                user_leave_administrator=UserLeaveAdminRequest(employer_fein="123456789"),
            )
        )

        assert len(issues) == 0


class TestGetUsersPostEmployerIssues:
    def test_valid(self):
        issues = get_users_post_employer_issues(EmployerFactory.build())

        assert len(issues) == 0

    def test_require_employer(self):
        issues = get_users_post_employer_issues(None)

        assert (
            ValidationErrorDetail(
                field="user_leave_administrator.employer_fein",
                message="Invalid EIN",
                type=IssueType.require_employer,
            )
            in issues
        )

    def test_contributing_employer_required(self):
        issues = get_users_post_employer_issues(EmployerOnlyRequiredFactory.build())

        assert (
            ValidationErrorDetail(
                field="user_leave_administrator.employer_fein",
                message="Confirm that you have the correct EIN, and that the Employer is contributing to Paid Family and Medical Leave.",
                type=IssueType.require_contributing_employer,
            )
            in issues
        )


class TestUsersPatchIssues:
    def test_valid_requests(self):
        # doesn't throw errors when the phone number is there
        issues = get_users_patch_issues(
            UserUpdateRequest(
                mfa_phone_number={
                    "int_code": "1",
                    "phone_number": "4134788837",
                    "phone_type": "Cell",
                }
            )
        )
        assert len(issues) == 0

        # doesn't throw errors if mfa_phone_number is not included
        issues = get_users_patch_issues(UserUpdateRequest(consent_to_data_sharing=True))
        assert len(issues) == 0

    def test_missing_fields(self):
        issues = get_users_patch_issues(UserUpdateRequest(mfa_phone_number={}))

        assert (
            ValidationErrorDetail(
                field="mfa_phone_number.phone_number",
                message="phone_number is required when mfa_phone_number is included in request",
                type=IssueType.required,
            )
            in issues
        )
        assert (
            ValidationErrorDetail(
                field="mfa_phone_number.phone_type",
                message="phone_type is required when mfa_phone_number is included in request",
                type=IssueType.required,
            )
            in issues
        )
        assert (
            ValidationErrorDetail(
                field="mfa_phone_number.int_code",
                message="int_code is required when mfa_phone_number is included in request",
                type=IssueType.required,
            )
            in issues
        )
