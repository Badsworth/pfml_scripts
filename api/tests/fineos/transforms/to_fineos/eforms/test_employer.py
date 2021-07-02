import random
from decimal import Decimal

import pytest

from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.api.models.common import ConcurrentLeave, EmployerBenefit, PreviousLeave
from massgov.pfml.fineos.transforms.to_fineos.eforms.employer import (
    EmployerClaimReviewEFormBuilder,
    EmployerClaimReviewV1EFormBuilder,
)


@pytest.fixture
def concurrent_leave():
    return ConcurrentLeave(leave_start_date="2021-06-01", leave_end_date="2021-06-30",)


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


class TestV1EmployerEformFunctionality:
    @pytest.fixture
    def v1_employer_claim_review(self, employer_benefit):
        return EmployerClaimReview(
            comment="Test Claim",
            employer_benefits=[employer_benefit],
            previous_leaves=[],
            hours_worked_per_week=22,
            employer_decision="Approve",
            fraud="Yes",
            leave_reason="Pregnancy/Maternity",
            believe_relationship_accurate=None,
            relationship_inaccurate_reason=None,
        )

    def test_employer_claim_review_eform_no_entries(self, v1_employer_claim_review):
        v1_employer_claim_review.employer_benefits = []
        eform_body = EmployerClaimReviewV1EFormBuilder.build(v1_employer_claim_review)
        assert eform_body.eformType == "Employer Response to Leave Request"
        assert len(eform_body.eformAttributes) == 5
        expected_attributes = [
            {"name": "Comment", "stringValue": v1_employer_claim_review.comment},
            {
                "decimalValue": float(v1_employer_claim_review.hours_worked_per_week),
                "name": "AverageWeeklyHoursWorked",
            },
            {"name": "EmployerDecision", "stringValue": v1_employer_claim_review.employer_decision},
            {"name": "Fraud1", "stringValue": "Yes"},
            {
                "name": "NatureOfLeave",
                "enumValue": {"domainName": "Nature of leave", "instanceValue": "Pregnancy"},
            },
        ]

        assert eform_body.eformAttributes == expected_attributes

    def test_employer_claim_review_eform_single_entries(self, v1_employer_claim_review):
        eform_body = EmployerClaimReviewV1EFormBuilder.build(v1_employer_claim_review)
        employer_benefits = v1_employer_claim_review.employer_benefits
        assert eform_body.eformType == "Employer Response to Leave Request"
        assert len(eform_body.eformAttributes) == 11
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
                "name": "ReceiveWageReplacement",
                "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
            },
            {"name": "Comment", "stringValue": v1_employer_claim_review.comment},
            {
                "decimalValue": float(v1_employer_claim_review.hours_worked_per_week),
                "name": "AverageWeeklyHoursWorked",
            },
            {"name": "EmployerDecision", "stringValue": v1_employer_claim_review.employer_decision},
            {"name": "Fraud1", "stringValue": "Yes"},
            {
                "name": "NatureOfLeave",
                "enumValue": {"domainName": "Nature of leave", "instanceValue": "Pregnancy"},
            },
        ]

        assert eform_body.eformAttributes == expected_attributes

    def test_employer_claim_review_eform_multiple_entries(self, v1_employer_claim_review):
        employer_benefits = [
            EmployerBenefit(
                benefit_amount_dollars=Decimal(round(random.random() * 400, 2)),
                benefit_amount_frequency="Per Week",
                benefit_start_date="2020-04-01",
                benefit_end_date="2020-05-01",
                benefit_type="Short-term disability insurance",
            ),
            EmployerBenefit(
                benefit_amount_dollars=Decimal(round(random.random() * 400, 2)),
                benefit_amount_frequency="Per Month",
                benefit_start_date="2020-04-02",
                benefit_end_date="2020-05-02",
                benefit_type="Accrued paid leave",
            ),
        ]
        v1_employer_claim_review.employer_benefits = employer_benefits
        eform_body = EmployerClaimReviewV1EFormBuilder.build(v1_employer_claim_review)
        employer_benefits = v1_employer_claim_review.employer_benefits
        assert eform_body.eformType == "Employer Response to Leave Request"
        assert len(eform_body.eformAttributes) == 17
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
                "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
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
                "name": "ReceiveWageReplacement2",
                "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
            },
            {"name": "Comment", "stringValue": v1_employer_claim_review.comment},
            {
                "decimalValue": float(v1_employer_claim_review.hours_worked_per_week),
                "name": "AverageWeeklyHoursWorked",
            },
            {"name": "EmployerDecision", "stringValue": v1_employer_claim_review.employer_decision},
            {"name": "Fraud1", "stringValue": "Yes"},
            {
                "name": "NatureOfLeave",
                "enumValue": {"domainName": "Nature of leave", "instanceValue": "Pregnancy"},
            },
        ]

        assert eform_body.eformAttributes == expected_attributes


class TestCaringLeaveReviewV1:
    @pytest.fixture
    def caring_leave_review(self):
        return EmployerClaimReview(
            comment="Test Claim",
            employer_benefits=[],
            previous_leaves=[],
            hours_worked_per_week=40,
            employer_decision="Allow",
            fraud="No",
            leave_reason="Care for a Family Member",
            believe_relationship_accurate="No",
            relationship_inaccurate_reason="I dunno",
        )

    @pytest.fixture
    def eform(self, caring_leave_review):
        return EmployerClaimReviewV1EFormBuilder.build(caring_leave_review)

    def test_nature_of_leave_attribute(self, eform):
        nature_of_leave_attr = eform.get_attribute("NatureOfLeave")
        expected_attr = {
            "name": "NatureOfLeave",
            "enumValue": {
                "domainName": "Nature of leave",
                "instanceValue": "Caring for a family member with a serious health condition",
            },
        }
        assert nature_of_leave_attr == expected_attr

    def test_invalid_leave_reason_attribute(self, caring_leave_review):
        caring_leave_review.leave_reason = "foo"
        eform = EmployerClaimReviewV1EFormBuilder.build(caring_leave_review)

        assert eform.get_attribute("NatureOfLeave") is None

    def test_believe_accurate_attribute(self, eform):
        believe_accurate_attr = eform.get_attribute("BelieveAccurate")
        expected_attr = {
            "name": "BelieveAccurate",
            "enumValue": {"domainName": "PleaseSelectYesNoIdontKnow", "instanceValue": "No"},
        }
        assert believe_accurate_attr == expected_attr

    def test_why_inaccurate_attribute(self, eform):
        why_inaccurate_attr = eform.get_attribute("WhyInaccurate")
        expected_attr = {
            "name": "WhyInaccurate",
            "stringValue": "I dunno",
        }
        assert why_inaccurate_attr == expected_attr


class TestEmployerBenefitsReview:
    @pytest.fixture
    def employer_benefits_claim_review(self, employer_benefit):
        return EmployerClaimReview(
            uses_second_eform_version=True,
            comment="Test Claim",
            concurrent_leave=None,
            employer_benefits=[employer_benefit, employer_benefit],
            previous_leaves=[],
            hours_worked_per_week=40,
            employer_decision="Allow",
            fraud="No",
            leave_reason="Pregnancy/Maternity",
        )

    @pytest.fixture
    def eform(self, employer_benefits_claim_review):
        return EmployerClaimReviewEFormBuilder.build(employer_benefits_claim_review)

    def test_employer_benefits_review(self, eform):
        assert len(eform.eformAttributes) == 19

        first_benefit_amount_dollars = eform.get_attribute("V2Amount1")
        first_benefit_amount_frequency = eform.get_attribute("V2Frequency1")
        first_benefit_start_date = eform.get_attribute("V2EmployerBenefitStartDate1")
        first_benefit_end_date = eform.get_attribute("V2EmployerBenefitEndDate1")
        first_benefit_type = eform.get_attribute("V2ERBenefitType1")
        first_is_full_salary_continuous = eform.get_attribute("V2SalaryCont1")
        first_receive_wage_replacement = eform.get_attribute("V2ReceiveWageReplacement1")

        second_benefit_amount_dollars = eform.get_attribute("V2Amount2")
        second_benefit_amount_frequency = eform.get_attribute("V2Frequency2")
        second_benefit_start_date = eform.get_attribute("V2EmployerBenefitStartDate2")
        second_benefit_end_date = eform.get_attribute("V2EmployerBenefitEndDate2")
        second_benefit_type = eform.get_attribute("V2ERBenefitType2")
        second_is_full_salary_continuous = eform.get_attribute("V2SalaryCont2")
        second_receive_wage_replacement = eform.get_attribute("V2ReceiveWageReplacement2")

        third_benefit_amount_dollars = eform.get_attribute("V2Amount3")
        third_benefit_amount_frequency = eform.get_attribute("V2Frequency3")
        third_benefit_start_date = eform.get_attribute("V2EmployerBenefitStartDate3")
        third_benefit_end_date = eform.get_attribute("V2EmployerBenefitEndDate3")
        third_benefit_type = eform.get_attribute("V2ERBenefitType3")
        third_is_full_salary_continuous = eform.get_attribute("V2SalaryCont3")
        third_receive_wage_replacement = eform.get_attribute("V2ReceiveWageReplacement3")

        assert first_benefit_amount_dollars == {"decimalValue": 100.25, "name": "V2Amount1"}
        assert first_benefit_amount_frequency == {
            "enumValue": {"domainName": "FrequencyEforms", "instanceValue": "Per Week"},
            "name": "V2Frequency1",
        }
        assert first_benefit_start_date == {
            "dateValue": "2020-04-01",
            "name": "V2EmployerBenefitStartDate1",
        }
        assert first_benefit_end_date == {
            "dateValue": "2020-05-01",
            "name": "V2EmployerBenefitEndDate1",
        }
        assert first_benefit_type == {
            "enumValue": {
                "domainName": "WageReplacementType",
                "instanceValue": "Temporary disability insurance (Long- or Short-term)",
            },
            "name": "V2ERBenefitType1",
        }
        assert first_is_full_salary_continuous == {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "No"},
            "name": "V2SalaryCont1",
        }
        assert first_receive_wage_replacement == {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
            "name": "V2ReceiveWageReplacement1",
        }

        assert second_benefit_amount_dollars == {"decimalValue": 100.25, "name": "V2Amount2"}
        assert second_benefit_amount_frequency == {
            "enumValue": {"domainName": "FrequencyEforms", "instanceValue": "Per Week"},
            "name": "V2Frequency2",
        }
        assert second_benefit_start_date == {
            "dateValue": "2020-04-01",
            "name": "V2EmployerBenefitStartDate2",
        }
        assert second_benefit_end_date == {
            "dateValue": "2020-05-01",
            "name": "V2EmployerBenefitEndDate2",
        }
        assert second_benefit_type == {
            "enumValue": {
                "domainName": "WageReplacementType",
                "instanceValue": "Temporary disability insurance (Long- or Short-term)",
            },
            "name": "V2ERBenefitType2",
        }
        assert second_is_full_salary_continuous == {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "No"},
            "name": "V2SalaryCont2",
        }
        assert second_receive_wage_replacement == {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
            "name": "V2ReceiveWageReplacement2",
        }

        assert third_benefit_amount_dollars is None
        assert third_benefit_amount_frequency is None
        assert third_benefit_start_date is None
        assert third_benefit_end_date is None
        assert third_benefit_type is None
        assert third_is_full_salary_continuous is None
        assert third_receive_wage_replacement is None


class TestConcurrentLeaveReview:
    @pytest.fixture
    def concurrent_leave_claim_review(self, concurrent_leave):
        return EmployerClaimReview(
            uses_second_eform_version=True,
            comment="Test Claim",
            concurrent_leave=concurrent_leave,
            employer_benefits=[],
            previous_leaves=[],
            hours_worked_per_week=40,
            employer_decision="Allow",
            fraud="No",
            leave_reason="Pregnancy/Maternity",
        )

    @pytest.fixture
    def eform(self, concurrent_leave_claim_review):
        return EmployerClaimReviewEFormBuilder.build(concurrent_leave_claim_review)

    def test_concurrent_leave_review(self, eform):
        assert len(eform.eformAttributes) == 8

        leave_start_date = eform.get_attribute("V2AccruedStartDate")
        leave_end_date = eform.get_attribute("V2AccruedEndDate")
        accrued_paid_leave = eform.get_attribute("V2AccruedPaidLeave")

        assert leave_start_date == {"dateValue": "2021-06-01", "name": "V2AccruedStartDate"}
        assert leave_end_date == {"dateValue": "2021-06-30", "name": "V2AccruedEndDate"}
        assert accrued_paid_leave == {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
            "name": "V2AccruedPaidLeave",
        }


class TestPreviousLeaveReview:
    @pytest.fixture
    def previous_leave_claim_review(self, previous_leave):
        return EmployerClaimReview(
            uses_second_eform_version=True,
            comment="Test Claim",
            concurrent_leave=None,
            employer_benefits=[],
            previous_leaves=[previous_leave, previous_leave],
            hours_worked_per_week=40,
            employer_decision="Allow",
            fraud="No",
            leave_reason="Pregnancy/Maternity",
        )

    @pytest.fixture
    def eform(self, previous_leave_claim_review):
        return EmployerClaimReviewEFormBuilder.build(previous_leave_claim_review)

    def test_previous_leave_review(self, eform):
        assert len(eform.eformAttributes) == 15

        first_leave_start_date = eform.get_attribute("V2PastLeaveStartDate1")
        first_leave_end_date = eform.get_attribute("V2PastLeaveEndDate1")
        first_leave_reason = eform.get_attribute("V2NatureOfLeave1")
        first_is_for_same_reason = eform.get_attribute("V2PastLeaveSame1")
        first_applies = eform.get_attribute("V2Applies1")

        second_leave_start_date = eform.get_attribute("V2PastLeaveStartDate2")
        second_leave_end_date = eform.get_attribute("V2PastLeaveEndDate2")
        second_leave_reason = eform.get_attribute("V2NatureOfLeave2")
        second_is_for_same_reason = eform.get_attribute("V2PastLeaveSame2")
        second_applies = eform.get_attribute("V2Applies2")

        third_leave_start_date = eform.get_attribute("V2PastLeaveStartDate3")
        third_leave_end_date = eform.get_attribute("V2PastLeaveEndDate3")
        third_leave_reason = eform.get_attribute("V2NatureOfLeave3")
        third_is_for_same_reason = eform.get_attribute("V2PastLeaveSame3")
        third_applies = eform.get_attribute("V2Applies3")

        assert first_leave_start_date == {
            "dateValue": "2021-07-01",
            "name": "V2PastLeaveStartDate1",
        }
        assert first_leave_end_date == {"dateValue": "2021-07-31", "name": "V2PastLeaveEndDate1"}
        assert first_leave_reason == {
            "enumValue": {"domainName": "Nature of leave", "instanceValue": "Pregnancy"},
            "name": "V2NatureOfLeave1",
        }
        assert first_is_for_same_reason == {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "No"},
            "name": "V2PastLeaveSame1",
        }
        assert first_applies == {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
            "name": "V2Applies1",
        }

        assert second_leave_start_date == {
            "dateValue": "2021-07-01",
            "name": "V2PastLeaveStartDate2",
        }
        assert second_leave_end_date == {"dateValue": "2021-07-31", "name": "V2PastLeaveEndDate2"}
        assert second_leave_reason == {
            "enumValue": {"domainName": "Nature of leave", "instanceValue": "Pregnancy"},
            "name": "V2NatureOfLeave2",
        }
        assert second_is_for_same_reason == {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "No"},
            "name": "V2PastLeaveSame2",
        }
        assert second_applies == {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
            "name": "V2Applies2",
        }

        assert third_leave_start_date is None
        assert third_leave_end_date is None
        assert third_leave_reason is None
        assert third_is_for_same_reason is None
        assert third_applies is None


class TestOtherInfoReview:
    @pytest.fixture
    def other_info_review(self):
        return EmployerClaimReview(
            uses_second_eform_version=True,
            comment="Test Claim",
            concurrent_leave=None,
            employer_benefits=[],
            previous_leaves=[],
            hours_worked_per_week=40,
            employer_decision="Allow",
            fraud="No",
            leave_reason="Care for a Family Member",
            believe_relationship_accurate="No",
            relationship_inaccurate_reason="I dunno",
        )

    @pytest.fixture
    def eform(self, other_info_review):
        return EmployerClaimReviewEFormBuilder.build(other_info_review)

    def test_other_info_review(self, eform):
        assert eform.eformType == "Employer Response to Leave Request - current version"
        assert len(eform.eformAttributes) == 7

        comment = eform.get_attribute("V2Comment")
        hours_worked_per_week = eform.get_attribute("V2AverageWeeklyHoursWorked")
        employer_decision = eform.get_attribute("V2EmployerDecision")
        fraud = eform.get_attribute("Fraud1")
        nature_of_leave = eform.get_attribute("V2NatureOfLeave")
        believe_accurate = eform.get_attribute("V2BelieveAccurate")
        relationship_inaccurate_reason = eform.get_attribute("V2WhyInaccurate")

        assert comment == {"name": "V2Comment", "stringValue": "Test Claim"}
        assert hours_worked_per_week == {"decimalValue": 40.0, "name": "V2AverageWeeklyHoursWorked"}
        assert employer_decision == {"name": "V2EmployerDecision", "stringValue": "Allow"}
        assert fraud == {"name": "Fraud1", "stringValue": "No"}
        assert nature_of_leave == {
            "enumValue": {
                "domainName": "Nature of leave",
                "instanceValue": "Caring for a family member with a serious health condition",
            },
            "name": "V2NatureOfLeave",
        }
        assert believe_accurate == {
            "enumValue": {"domainName": "PleaseSelectYesNoIdontKnow", "instanceValue": "No"},
            "name": "V2BelieveAccurate",
        }
        assert relationship_inaccurate_reason == {
            "name": "V2WhyInaccurate",
            "stringValue": "I dunno",
        }
