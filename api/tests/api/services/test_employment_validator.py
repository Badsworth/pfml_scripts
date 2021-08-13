import pytest

from massgov.pfml.api.services.employment_validator import (
    get_contributing_employer_or_employee_issue,
)
from massgov.pfml.api.validation.exceptions import IssueRule, IssueType, ValidationErrorDetail
from massgov.pfml.db.models.factories import (
    EmployeeFactory,
    EmployerFactory,
    TaxIdentifierFactory,
    WagesAndContributionsFactory,
)

# every test in here requires real resources
pytestmark = pytest.mark.integration


def test_valid_contributing_employer_and_employee(test_db_session, initialize_factories_session):
    # No validation issue when an Employer/Employee relationship exists
    employer = EmployerFactory.create()
    employee = EmployeeFactory.create()

    WagesAndContributionsFactory.create(employer=employer, employee=employee)

    issue = get_contributing_employer_or_employee_issue(
        test_db_session, employer.employer_fein, employee.tax_identifier
    )

    assert issue is None


def test_ein_not_required(test_db_session, initialize_factories_session):
    # No validation issue when EIN is empty
    employee = EmployeeFactory.create()

    issue = get_contributing_employer_or_employee_issue(
        test_db_session, None, employee.tax_identifier
    )

    assert issue is None


def test_tax_identifier_not_required(test_db_session, initialize_factories_session):
    # No validation issue when tax identifier is empty
    employer = EmployerFactory.create()

    issue = get_contributing_employer_or_employee_issue(
        test_db_session, employer.employer_fein, None
    )

    assert issue is None


def test_employer_with_fineos_id_is_required(test_db_session, initialize_factories_session):
    # Validation issue when Employer exists, but doesn't have a FINEOS ID
    employer = EmployerFactory.create(fineos_employer_id=None)

    issue = get_contributing_employer_or_employee_issue(
        test_db_session, employer.employer_fein, None
    )

    assert issue == ValidationErrorDetail(
        field="employer_fein",
        type=IssueType.require_contributing_employer,
        message="Confirm that you have the correct EIN, and that the Employer is contributing to Paid Family and Medical Leave.",
    )


def test_employee_is_required(test_db_session, initialize_factories_session):
    # Validation issue when Employee doesn't exist
    employer = EmployerFactory.create()

    issue = get_contributing_employer_or_employee_issue(
        test_db_session, employer.employer_fein, TaxIdentifierFactory.create()
    )

    assert issue == ValidationErrorDetail(
        rule=IssueRule.require_employee,
        message="Couldn't find Employee in our system. Confirm that you have the correct EIN.",
        type="",
    )


def test_employee_with_wages_from_employer_is_required(
    test_db_session, initialize_factories_session
):
    # Validation issue when Employer and Employee exists, but no wages association between the two.
    employer = EmployerFactory.create()
    employee = EmployeeFactory.create()

    issue = get_contributing_employer_or_employee_issue(
        test_db_session, employer.employer_fein, employee.tax_identifier
    )

    assert issue == ValidationErrorDetail(
        rule=IssueRule.require_employee,
        message="Couldn't find Employee in our system. Confirm that you have the correct EIN.",
        type="",
    )
