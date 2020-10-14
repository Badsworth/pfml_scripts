import random

import pytest

from massgov.pfml.api.models.claims.common import (
    EmployerBenefit,
    EmployerClaimReview,
    PreviousLeave,
)
from massgov.pfml.fineos.models.customer_api import EFormAttribute
from massgov.pfml.fineos.transforms.eforms import (
    TransformEmployerBenefit,
    TransformEmployerClaimReview,
    TransformOtherInfo,
    TransformPreviousLeave,
)


@pytest.fixture
def employer_benefit():
    return EmployerBenefit(
        benefit_amount_dollars=round(random.random() * 400, 2),
        benefit_amount_frequency="Fortnightly",
        benefit_start_date="2020-04-01",
        benefit_end_date="2020-05-01",
        benefit_type="Short Term Disability",
    )


@pytest.fixture
def previous_leave():
    return PreviousLeave(
        leave_start_date="2020-05-15", leave_end_date="2020-06-01", leave_type="Medical"
    )


@pytest.fixture
def employer_claim_review(previous_leave, employer_benefit):
    return EmployerClaimReview(
        comment="Test Claim",
        employer_notification_date="2020-10-01",
        employer_benefits=[employer_benefit],
        previous_leaves=[previous_leave],
        hours_worked_per_week=22,
    )


class TestTransformEformAttributes:
    def test_transform_employer_benefit(self, employer_benefit):
        result = TransformEmployerBenefit.to_attributes(employer_benefit)
        assert len(result) == 5
        for r in result:
            assert type(r) is EFormAttribute
        dollars, frequency, start, end, b_type = result
        assert dollars.decimalValue == employer_benefit.benefit_amount_dollars
        assert frequency.stringValue == employer_benefit.benefit_amount_frequency
        assert start.dateValue == employer_benefit.benefit_start_date
        assert end.dateValue == employer_benefit.benefit_end_date
        assert b_type.enumValue == employer_benefit.benefit_type

    def test_transform_previous_leave(self, previous_leave):
        result = TransformPreviousLeave.to_attributes(previous_leave)
        assert len(result) == 3
        start, end, l_type = result
        assert start.dateValue == previous_leave.leave_start_date
        assert start.name == "StartDate"

    def test_transform_previous_leave_list(self, previous_leave):
        result = TransformPreviousLeave.list_to_attributes([previous_leave, previous_leave])
        assert len(result) == 6
        start, end, l_type, start2, end2, l_type2 = result
        assert start2.name == "StartDate2"
        assert end2.name == "EndDate2"
        assert l_type2.name == "PrimaryReason2"
        assert start.dateValue == start2.dateValue
        assert end.dateValue == end2.dateValue

    def test_transform_other_info(self, employer_claim_review):
        result = TransformOtherInfo.to_attributes(employer_claim_review)
        assert len(result) == 3
        comment, er_notified_date, hours_worked_per_week = result
        assert comment.stringValue == employer_claim_review.comment
        assert er_notified_date.dateValue == employer_claim_review.employer_notification_date
        assert hours_worked_per_week.integerValue == employer_claim_review.hours_worked_per_week


class TestTransformEformBody:
    def test_transform_employer_claim_review(self, employer_claim_review):
        eform_body = TransformEmployerClaimReview.to_fineos(employer_claim_review)
        assert eform_body.eformType == "Employer Info Request"
        assert len(eform_body.eformAttributes) == 11
