import random

import pytest

from massgov.pfml.api.models.claims.common import (
    EmployerBenefit,
    EmployerClaimReview,
    PreviousLeave,
)
from massgov.pfml.fineos.transforms.to_fineos.eforms.employer import EmployerClaimReviewEFormBuilder


@pytest.fixture
def employer_benefit():
    return EmployerBenefit(
        benefit_amount_dollars=round(random.random() * 400, 2),
        benefit_amount_frequency="Per Week",
        benefit_start_date="2020-04-01",
        benefit_end_date="2020-05-01",
        benefit_type="Short-term disability insurance",
    )


@pytest.fixture
def previous_leave():
    return PreviousLeave(
        leave_start_date="2021-05-15",
        leave_end_date="2021-06-01",
        leave_reason="Pregnancy / Maternity",
    )


@pytest.fixture
def employer_claim_review(previous_leave, employer_benefit):
    return EmployerClaimReview(
        comment="Test Claim",
        employer_benefits=[employer_benefit],
        previous_leaves=[previous_leave],
        hours_worked_per_week=22,
        employer_decision="Approve",
        fraud="Yes",
        nature_of_leave="Pregnancy",
        believe_relationship_accurate=None,
        relationship_inaccurate_reason=None,
    )


def test_employer_claim_review_eform_no_entries(employer_claim_review):
    employer_claim_review.employer_benefits = []
    employer_claim_review.previous_leaves = []
    eform_body = EmployerClaimReviewEFormBuilder.build(employer_claim_review)
    assert eform_body.eformType == "Employer Response to Leave Request"
    assert len(eform_body.eformAttributes) == 5
    expected_attributes = [
        {"name": "Comment", "stringValue": employer_claim_review.comment},
        {
            "decimalValue": float(employer_claim_review.hours_worked_per_week),
            "name": "AverageWeeklyHoursWorked",
        },
        {"name": "EmployerDecision", "stringValue": employer_claim_review.employer_decision},
        {"name": "Fraud1", "stringValue": "Yes"},
        {
            "name": "NatureOfLeave",
            "enumValue": {"domainName": "Nature of leave", "instanceValue": "Pregnancy"},
        },
    ]

    assert eform_body.eformAttributes == expected_attributes


def test_employer_claim_review_eform_single_entries(employer_claim_review):
    eform_body = EmployerClaimReviewEFormBuilder.build(employer_claim_review)
    employer_benefits = employer_claim_review.employer_benefits
    previous_leaves = employer_claim_review.previous_leaves
    assert eform_body.eformType == "Employer Response to Leave Request"
    assert len(eform_body.eformAttributes) == 13
    expected_attributes = [
        {"decimalValue": employer_benefits[0].benefit_amount_dollars, "name": "Amount"},
        {"name": "Frequency", "stringValue": "Per Week"},
        {
            "dateValue": employer_benefits[0].benefit_start_date.isoformat(),
            "name": "EmployerBenefitStartDate",
        },
        {
            "dateValue": employer_benefits[0].benefit_end_date.isoformat(),
            "name": "EmployerBenefitEndDate",
        },
        {"name": "BenefitType", "stringValue": "Short-term disability insurance"},
        {
            "dateValue": previous_leaves[0].leave_start_date.isoformat(),
            "name": "PastLeaveStartDate",
        },
        {"dateValue": previous_leaves[0].leave_end_date.isoformat(), "name": "PastLeaveEndDate",},
        {"name": "QualifyingReason", "stringValue": previous_leaves[0].leave_reason,},
        {"name": "Comment", "stringValue": employer_claim_review.comment},
        {
            "decimalValue": float(employer_claim_review.hours_worked_per_week),
            "name": "AverageWeeklyHoursWorked",
        },
        {"name": "EmployerDecision", "stringValue": employer_claim_review.employer_decision},
        {"name": "Fraud1", "stringValue": "Yes"},
        {
            "name": "NatureOfLeave",
            "enumValue": {"domainName": "Nature of leave", "instanceValue": "Pregnancy"},
        },
    ]

    assert eform_body.eformAttributes == expected_attributes


def test_employer_claim_review_eform_multiple_entries(employer_claim_review):
    employer_benefits = [
        EmployerBenefit(
            benefit_amount_dollars=round(random.random() * 400, 2),
            benefit_amount_frequency="Per Week",
            benefit_start_date="2020-04-01",
            benefit_end_date="2020-05-01",
            benefit_type="Short-term disability insurance",
        ),
        EmployerBenefit(
            benefit_amount_dollars=round(random.random() * 400, 2),
            benefit_amount_frequency="Per Month",
            benefit_start_date="2020-04-02",
            benefit_end_date="2020-05-02",
            benefit_type="Accrued paid leave",
        ),
    ]
    previous_leaves = [
        PreviousLeave(
            leave_start_date="2021-05-16",
            leave_end_date="2021-06-02",
            leave_reason="Pregnancy / Maternity",
        ),
        PreviousLeave(
            leave_start_date="2021-05-16",
            leave_end_date="2021-06-02",
            leave_reason="Child bonding",
        ),
    ]
    employer_claim_review.employer_benefits = employer_benefits
    employer_claim_review.previous_leaves = previous_leaves
    eform_body = EmployerClaimReviewEFormBuilder.build(employer_claim_review)
    employer_benefits = employer_claim_review.employer_benefits
    previous_leaves = employer_claim_review.previous_leaves
    assert eform_body.eformType == "Employer Response to Leave Request"
    assert len(eform_body.eformAttributes) == 23
    expected_attributes = [
        {"decimalValue": employer_benefits[0].benefit_amount_dollars, "name": "Amount"},
        {"name": "Frequency", "stringValue": "Per Week"},
        {
            "dateValue": employer_benefits[0].benefit_start_date.isoformat(),
            "name": "EmployerBenefitStartDate",
        },
        {
            "dateValue": employer_benefits[0].benefit_end_date.isoformat(),
            "name": "EmployerBenefitEndDate",
        },
        {"name": "BenefitType", "stringValue": employer_benefits[0].benefit_type},
        {
            "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
            "name": "ReceiveWageReplacement",
        },
        {"decimalValue": employer_benefits[1].benefit_amount_dollars, "name": "Amount2"},
        {"name": "Frequency2", "stringValue": "Per Month"},
        {
            "dateValue": employer_benefits[1].benefit_start_date.isoformat(),
            "name": "EmployerBenefitStartDate2",
        },
        {
            "dateValue": employer_benefits[1].benefit_end_date.isoformat(),
            "name": "EmployerBenefitEndDate2",
        },
        {"name": "BenefitType2", "stringValue": employer_benefits[1].benefit_type},
        {
            "dateValue": previous_leaves[0].leave_start_date.isoformat(),
            "name": "PastLeaveStartDate",
        },
        {"dateValue": previous_leaves[0].leave_end_date.isoformat(), "name": "PastLeaveEndDate",},
        {"name": "QualifyingReason", "stringValue": previous_leaves[0].leave_reason,},
        {
            "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
            "name": "Applies",
        },
        {
            "dateValue": previous_leaves[1].leave_start_date.isoformat(),
            "name": "PastLeaveStartDate2",
        },
        {"dateValue": previous_leaves[1].leave_end_date.isoformat(), "name": "PastLeaveEndDate2"},
        {"name": "QualifyingReason2", "stringValue": previous_leaves[1].leave_reason},
        {"name": "Comment", "stringValue": employer_claim_review.comment},
        {
            "decimalValue": float(employer_claim_review.hours_worked_per_week),
            "name": "AverageWeeklyHoursWorked",
        },
        {"name": "EmployerDecision", "stringValue": employer_claim_review.employer_decision},
        {"name": "Fraud1", "stringValue": "Yes"},
        {
            "name": "NatureOfLeave",
            "enumValue": {"domainName": "Nature of leave", "instanceValue": "Pregnancy"},
        },
    ]

    assert eform_body.eformAttributes == expected_attributes


@pytest.fixture
def caring_leave_review():
    return EmployerClaimReview(
        comment="Test Claim",
        employer_benefits=[],
        previous_leaves=[],
        hours_worked_per_week=40,
        employer_decision="Deny",
        fraud="No",
        nature_of_leave="Caring for a family member with a serious health condition",
        believe_relationship_accurate="No",
        relationship_inaccurate_reason="I don't know, it just seems unlikely",
    )


def test_employer_claim_review_eform_caring_leave(caring_leave_review):
    eform = EmployerClaimReviewEFormBuilder.build(caring_leave_review)

    nature_of_leave_attr = eform.get_attribute("NatureOfLeave")
    expected_attr = {
        "name": "NatureOfLeave",
        "enumValue": {
            "domainName": "Nature of leave",
            "instanceValue": "Caring for a family member with a serious health condition",
        },
    }
    assert nature_of_leave_attr == expected_attr

    believe_accurate_attr = eform.get_attribute("BelieveAccurate")
    expected_attr = {
        "name": "BelieveAccurate",
        "enumValue": {"domainName": "PleaseSelectYesNoIdontKnow", "instanceValue": "No"},
    }
    assert believe_accurate_attr == expected_attr

    why_inaccurate_attr = eform.get_attribute("WhyInaccurate")
    expected_attr = {"name": "WhyInaccurate", "stringValue": "I don't know, it just seems unlikely"}
    assert why_inaccurate_attr == expected_attr
