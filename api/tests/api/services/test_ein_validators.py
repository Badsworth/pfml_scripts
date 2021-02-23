from massgov.pfml.api.services.ein_validators import get_contributing_employer_issue
from massgov.pfml.api.util.response import Issue, IssueType
from massgov.pfml.db.models.factories import EmployerFactory


def test_valid_contributing_employer(test_db_session, initialize_factories_session):
    employer = EmployerFactory.create()

    issue = get_contributing_employer_issue(test_db_session, employer.employer_fein)

    assert issue is None


def test_ein_not_required(test_db_session, initialize_factories_session):
    employer_fein = None
    issue = get_contributing_employer_issue(test_db_session, employer_fein)

    assert issue is None


def test_employer_with_fineos_id_is_required(test_db_session, initialize_factories_session):
    employer = EmployerFactory.create(fineos_employer_id=None)

    issue = get_contributing_employer_issue(test_db_session, employer.employer_fein)

    assert issue == Issue(
        field="employer_fein",
        type=IssueType.require_contributing_employer,
        message="Confirm that you have the correct EIN, and that the Employer is contributing to Paid Family and Medical Leave.",
    )
