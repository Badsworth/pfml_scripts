from datetime import date

import pytest

from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.api.models.common import EmployerBenefit, PreviousLeave
from massgov.pfml.api.services.claim_rules import (
    get_employer_benefits_issues,
    get_employer_claim_review_issues,
    get_hours_worked_per_week_issues,
    get_previous_leaves_issues,
)
from massgov.pfml.api.util.response import IssueType


@pytest.fixture
def employer_benefit():
    return EmployerBenefit(
        benefit_amount_dollars=100.25,
        benefit_amount_frequency="Per Week",
        benefit_start_date="2020-04-01",
        benefit_end_date="2020-05-01",
        benefit_type="Short-term disability insurance",
        is_full_salary_continuous=False,
    )


@pytest.fixture
def previous_leave():
    return PreviousLeave(
        leave_start_date="2021-07-01",
        leave_end_date="2021-07-31",
        leave_reason="Pregnancy",
        is_for_same_reason=True,
    )


@pytest.fixture
def employer_claim_review():
    return EmployerClaimReview(
        employer_benefits=[employer_benefit],
        previous_leaves=[previous_leave],
        hours_worked_per_week=40.0,
    )


@pytest.fixture
def uses_second_eform_version():
    return True


class TestGetEmployerClaimReviewIssues:
    def test_valid(self, employer_claim_review):
        assert not get_employer_claim_review_issues(employer_claim_review)

    def test_with_multiple_issues(self, employer_claim_review, previous_leave, employer_benefit):
        previous_leave.leave_start_date = date(2020, 1, 1)
        employer_benefit.benefit_end_date = date(2020, 1, 1)
        employer_claim_review.hours_worked_per_week = -1
        employer_claim_review.previous_leaves = [previous_leave]
        employer_claim_review.employer_benefits = [employer_benefit]
        resp = get_employer_claim_review_issues(employer_claim_review)
        assert len(resp) == 3

    def test_no_hours(self, employer_claim_review):
        employer_claim_review.hours_worked_per_week = None
        resp = get_employer_claim_review_issues(employer_claim_review)
        assert len(resp) == 1
        assert resp[0].message == "hours_worked_per_week must be populated"
        assert resp[0].field == "hours_worked_per_week"
        assert resp[0].type == "missing_expected_field"


class TestGetHoursWorkedPerWeekIssues:
    @pytest.mark.parametrize(
        "hours_worked_per_week, expected_type,expected_field, expected_msg_blurb",
        [
            [None, "missing_expected_field", "hours_worked_per_week", "must be populated"],
            [-1, IssueType.minimum, "hours_worked_per_week", "greater than 0"],
            [169, IssueType.maximum, "hours_worked_per_week", "168 or fewer"],
        ],
    )
    def test_get_hours_per_week_issues(
        self, hours_worked_per_week, expected_type, expected_field, expected_msg_blurb
    ):
        resp = get_hours_worked_per_week_issues(hours_worked_per_week)
        assert resp[0].field == expected_field
        assert resp[0].type == expected_type
        assert expected_msg_blurb in resp[0].message


class TestGetPreviousLeaveIssues:
    def test_valid(self, previous_leave):
        assert not get_previous_leaves_issues([previous_leave])

    def test_with_too_early_date(self, previous_leave):
        previous_leave.leave_start_date = date(2020, 1, 1)
        resp = get_previous_leaves_issues([previous_leave])
        assert resp[0].field == "previous_leaves[0].leave_start_date"
        assert resp[0].type == "invalid_previous_leave_start_date"
        assert "cannot start before" in resp[0].message

    def test_with_mismatched_dates(self, previous_leave):
        previous_leave.leave_end_date = date(2021, 5, 5)
        resp = get_previous_leaves_issues([previous_leave])
        assert resp[0].field == "previous_leaves[0].leave_end_date"
        assert resp[0].type == IssueType.minimum
        assert "cannot be earlier than" in resp[0].message

    def test_with_no_leaves(self):
        assert not get_previous_leaves_issues(None)

    def test_with_empty_date_values(self, previous_leave):
        previous_leave.leave_start_date = None
        previous_leave.leave_end_date = None
        assert not get_previous_leaves_issues([previous_leave])


class TestGetEmployerBenefitsIssues:
    def test_get_employer_benefits_issues(self, employer_benefit, uses_second_eform_version):
        assert not get_employer_benefits_issues([employer_benefit], uses_second_eform_version)

    def test_with_mismatched_dates(self, employer_benefit, uses_second_eform_version):
        employer_benefit.benefit_end_date = date(2020, 1, 1)
        resp = get_employer_benefits_issues([employer_benefit], uses_second_eform_version)
        assert resp[0].type == IssueType.minimum
        assert resp[0].field == "employer_benefits[0].benefit_end_date"
        assert "cannot be earlier than" in resp[0].message

    def test_with_no_benefits(self, uses_second_eform_version):
        assert not get_employer_benefits_issues(None, uses_second_eform_version)

    def test_with_empty_date_values(self, employer_benefit, uses_second_eform_version):
        employer_benefit.benefit_start_date = None
        employer_benefit.benefit_end_date = None
        assert not get_employer_benefits_issues([employer_benefit], uses_second_eform_version)

    def test_v1_form_max_benefits_restriction(self, employer_benefit, uses_second_eform_version):
        uses_second_eform_version = False
        resp = get_employer_benefits_issues([employer_benefit] * 5, uses_second_eform_version,)
        assert resp[0].type == IssueType.maximum
        assert resp[0].field == "employer_benefits"
        assert "cannot exceed limit" in resp[0].message
