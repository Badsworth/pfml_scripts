from datetime import datetime, timedelta

import pytest

from massgov.pfml.api.validation.employer_rules import (
    EmployerRequiresVerificationDataException,
    validate_employer_being_added,
)
from massgov.pfml.api.validation.exceptions import (
    IssueType,
    ValidationErrorDetail,
    ValidationException,
)
from massgov.pfml.db.models.factories import EmployerFactory, EmployerQuarterlyContributionFactory


class TestEmployerAddFeinIssue:
    @pytest.fixture
    def employer_with_fineos_id(self):
        return EmployerFactory.create(fineos_employer_id=1)

    @pytest.mark.integration
    def test_employer_is_valid(self, initialize_factories_session, employer_with_fineos_id):
        filing_period = datetime.now() - timedelta(days=1)
        EmployerQuarterlyContributionFactory.create(
            employer=employer_with_fineos_id, filing_period=filing_period
        )

        issue = validate_employer_being_added(employer_with_fineos_id)

        assert issue is None

    def test_employer_does_not_have_verification_data(self):
        employer_with_fineos_id = EmployerFactory.build(fineos_employer_id=1)

        with pytest.raises(EmployerRequiresVerificationDataException) as exc:
            validate_employer_being_added(employer_with_fineos_id)

            assert exc.value.errors == [
                ValidationErrorDetail(
                    type=IssueType.employer_requires_verification_data,
                    message="Employer has no verification data",
                    field="employer_fein",
                )
            ]

    @pytest.mark.integration
    def test_employer_verification_data_too_far_in_past(
        self, initialize_factories_session, employer_with_fineos_id
    ):
        filing_period = datetime.now() - timedelta(days=-400)
        EmployerQuarterlyContributionFactory.create(
            employer=employer_with_fineos_id, filing_period=filing_period
        )

        with pytest.raises(EmployerRequiresVerificationDataException) as exc:
            validate_employer_being_added(employer_with_fineos_id)

            assert exc.value.errors == [
                ValidationErrorDetail(
                    type=IssueType.employer_requires_verification_data,
                    message="Employer has no verification data",
                    field="employer_fein",
                )
            ]

    @pytest.mark.integration
    def test_employer_verification_data_only_in_future(
        self, initialize_factories_session, employer_with_fineos_id
    ):
        filing_period = datetime.now() + timedelta(days=1)
        EmployerQuarterlyContributionFactory.create(
            employer=employer_with_fineos_id, filing_period=filing_period
        )

        with pytest.raises(EmployerRequiresVerificationDataException) as exc:
            validate_employer_being_added(employer_with_fineos_id)

            assert exc.value.errors == [
                ValidationErrorDetail(
                    type=IssueType.employer_requires_verification_data,
                    message="Employer has no verification data",
                    field="employer_fein",
                )
            ]

    def test_employer_does_not_exist(self):
        with pytest.raises(ValidationException) as exc:
            validate_employer_being_added(None)

            assert exc.value.errors == [
                ValidationErrorDetail(
                    type=IssueType.require_employer, message="Invalid FEIN", field="employer_fein",
                )
            ]

    def test_employer_does_not_have_fineos_id(self, initialize_factories_session):
        employer = EmployerFactory.build(fineos_employer_id=None)

        with pytest.raises(ValidationException) as exc:
            validate_employer_being_added(employer)

            assert exc.value.errors == [
                ValidationErrorDetail(
                    type=IssueType.require_contributing_employer,
                    message="Confirm that you have the correct EIN, and that the Employer is contributing to Paid Family and Medical Leave.",
                    field="employer_fein",
                )
            ]
