from datetime import date

import pytest

from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.api.models.common import EmployerBenefit, PreviousLeave
from massgov.pfml.api.validation.claim_rules import (
    get_change_request_issues,
    get_employer_benefits_issues,
    get_employer_claim_review_issues,
    get_hours_worked_per_week_issues,
    get_previous_leaves_issues,
)
from massgov.pfml.api.validation.exceptions import IssueType
from massgov.pfml.db.models.employees import AbsencePeriod, ChangeRequestType
from massgov.pfml.db.models.factories import (
    AbsencePeriodFactory,
    ChangeRequestFactory,
    ClaimFactory,
)


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
        issues = get_employer_claim_review_issues(employer_claim_review)
        assert not issues

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
        assert resp[0].type == IssueType.required


class TestGetHoursWorkedPerWeekIssues:
    @pytest.mark.parametrize(
        "hours_worked_per_week, expected_type,expected_field, expected_msg_blurb",
        [
            [None, IssueType.required, "hours_worked_per_week", "must be populated"],
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
        issues = get_previous_leaves_issues([previous_leave])
        assert not issues

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
        issues = get_employer_benefits_issues([employer_benefit], uses_second_eform_version)
        assert not issues

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
        resp = get_employer_benefits_issues([employer_benefit] * 5, uses_second_eform_version)
        assert resp[0].type == IssueType.maximum
        assert resp[0].field == "employer_benefits"
        assert "cannot exceed limit" in resp[0].message


# Run `initialize_factories_session` for all tests,
# so that it doesn't need to be manually included
@pytest.fixture(autouse=True)
def setup_factories(initialize_factories_session):
    return


@pytest.fixture
def modification_change_request():
    return ChangeRequestFactory.create(
        change_request_type_id=ChangeRequestType.MODIFICATION.change_request_type_id,
        start_date=None,
        end_date=date(2020, 3, 1),
    )


@pytest.fixture
def withdrawal_change_request():
    return ChangeRequestFactory.create(
        change_request_type_id=ChangeRequestType.WITHDRAWAL.change_request_type_id,
        start_date=None,
        end_date=None,
    )


@pytest.fixture
def mtb_change_request():
    return ChangeRequestFactory.create(
        change_request_type_id=ChangeRequestType.MEDICAL_TO_BONDING.change_request_type_id,
        start_date=date(2020, 2, 1),
        end_date=date(2020, 3, 1),
    )


@pytest.fixture()
def claim():
    claim = ClaimFactory.create()
    claim.absence_period_start_date = date(2020, 1, 1)
    absence_period: AbsencePeriod = AbsencePeriodFactory.create(claim=claim)
    absence_period.leave_request_decision_id = 3
    absence_period.absence_reason_qualifier_one_id = 29
    claim.absence_periods = [absence_period]
    return claim


class TestGetChangeRequestIssues:
    def test_start_date_later_than_end_date(self, mtb_change_request, claim):
        mtb_change_request.start_date = date(2020, 5, 1)
        resp = get_change_request_issues(mtb_change_request, claim)
        assert resp[0].type == IssueType.maximum
        assert resp[0].field == "end_date"
        assert "Start date must be less than end date" in resp[0].message

    class TestChangeRequestTypeModification:
        # Test rules specific to the Modification type

        def test_no_issues(self, modification_change_request, claim):
            issues = get_change_request_issues(modification_change_request, claim)
            assert not issues

        def test_start_date_error(self, modification_change_request, claim):
            modification_change_request.start_date = date(2020, 2, 1)
            resp = get_change_request_issues(modification_change_request, claim)
            assert resp[0].type == IssueType.change_start_date_is_unsupported
            assert resp[0].field == "start_date"
            assert "Start date is invalid for this request type" in resp[0].message

        def test_no_end_date_error(self, modification_change_request, claim):
            modification_change_request.end_date = None
            resp = get_change_request_issues(modification_change_request, claim)
            assert resp[0].type == IssueType.required
            assert resp[0].field == "end_date"
            assert "End date is required for this request type" in resp[0].message

        def test_wrong_absence_status(self, modification_change_request, claim):
            claim.absence_periods[0].leave_request_decision_id = 2
            resp = get_change_request_issues(modification_change_request, claim)
            assert resp[0].type == IssueType.must_be_approved_claim
            assert resp[0].field == "fineos_absence_id"
            assert (
                "Claim must have at least one approved absence period to submit a change request"
                in resp[0].message
            )

    class TestChangeRequestTypeWithdrawal:
        # Test rules specific to the Withdrawal type

        def test_no_issues_approved_period(self, withdrawal_change_request, claim):
            assert not get_change_request_issues(withdrawal_change_request, claim)

        def test_no_issues_pending_period(self, withdrawal_change_request, claim):
            claim.absence_periods[0].leave_request_decision_id = 1
            assert not get_change_request_issues(withdrawal_change_request, claim)

        def test_start_date_error(self, withdrawal_change_request, claim):
            withdrawal_change_request.start_date = date(2020, 2, 1)
            resp = get_change_request_issues(withdrawal_change_request, claim)
            assert resp[0].type == IssueType.withdrawal_dates_must_be_null
            assert resp[0].field == "start_date"
            assert "Start date is invalid for this request type" in resp[0].message

        def test_end_date_error(self, withdrawal_change_request, claim):
            withdrawal_change_request.end_date = date(2020, 2, 1)
            resp = get_change_request_issues(withdrawal_change_request, claim)
            assert resp[0].type == IssueType.withdrawal_dates_must_be_null
            assert resp[0].field == "end_date"
            assert "End date is invalid for this request type" in resp[0].message

        def test_wrong_absence_status(self, withdrawal_change_request, claim):
            claim.absence_periods[0].leave_request_decision_id = 2
            resp = get_change_request_issues(withdrawal_change_request, claim)
            assert resp[0].type == IssueType.must_be_approved_or_pending_claim
            assert resp[0].field == "fineos_absence_id"
            assert (
                "Claim must have at least one approved or pending absence period to submit a withdrawal"
                in resp[0].message
            )

    class TestChangeRequestTypeMedicalToBonding:
        # Test rules specific to the Medical To Bonding type

        def test_no_issues(self, mtb_change_request, claim):
            assert not get_change_request_issues(mtb_change_request, claim)

        def test_no_start_date_error(self, mtb_change_request, claim):
            mtb_change_request.start_date = None
            resp = get_change_request_issues(mtb_change_request, claim)
            assert resp[0].type == IssueType.required
            assert resp[0].field == "start_date"
            assert "Start date is required for this request type" in resp[0].message

        def test_no_end_date_error(self, mtb_change_request, claim):
            mtb_change_request.end_date = None
            resp = get_change_request_issues(mtb_change_request, claim)
            assert resp[0].type == IssueType.required
            assert resp[0].field == "end_date"
            assert "End date is required for this request type" in resp[0].message

        def test_missing_absence_period(self, mtb_change_request, claim):
            claim.absence_periods[0].absence_reason_qualifier_one_id = 1
            resp = get_change_request_issues(mtb_change_request, claim)
            assert resp[0].type == IssueType.not_medical_to_bonding_claim
            assert (
                "Claimant did not apply for bonding leave in initial application" in resp[0].message
            )

        def test_wrong_absence_status(self, mtb_change_request, claim):
            claim.absence_periods[0].leave_request_decision_id = 2
            resp = get_change_request_issues(mtb_change_request, claim)
            assert resp[0].type == IssueType.must_be_approved_claim
            assert resp[0].field == "fineos_absence_id"
            assert (
                "Claim must have at least one approved absence period to submit a change request"
                in resp[0].message
            )
