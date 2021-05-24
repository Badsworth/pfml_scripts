from itertools import chain

from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.fineos.transforms.to_fineos.base import (
    EFormAttributeBuilder,
    EFormBody,
    EFormBuilder,
)


class EmployerBenefitAttributeBuilder(EFormAttributeBuilder):
    ATTRIBUTE_MAP = {
        "benefit_amount_dollars": {"name": "Amount", "type": "decimalValue"},
        "benefit_amount_frequency": {"name": "Frequency", "type": "stringValue"},
        "benefit_start_date": {"name": "EmployerBenefitStartDate", "type": "dateValue"},
        "benefit_end_date": {"name": "EmployerBenefitEndDate", "type": "dateValue"},
        "benefit_type": {"name": "BenefitType", "type": "stringValue"},
    }

    JOINING_ATTRIBUTE = {
        "name": "ReceiveWageReplacement",
        "type": "enumValue",
        "domainName": "PleaseSelectYesNoUnknown",
        "instanceValue": "Yes",
    }


class PreviousLeaveAttributeBuilder(EFormAttributeBuilder):
    ATTRIBUTE_MAP = {
        "leave_start_date": {"name": "PastLeaveStartDate", "type": "dateValue"},
        "leave_end_date": {"name": "PastLeaveEndDate", "type": "dateValue"},
        "leave_reason": {"name": "QualifyingReason", "type": "stringValue"},
    }

    JOINING_ATTRIBUTE = {
        "name": "Applies",
        "type": "enumValue",
        "domainName": "PleaseSelectYesNoUnknown",
        "instanceValue": "Yes",
    }


class OtherInfoAttributeBuilder(EFormAttributeBuilder):
    ATTRIBUTE_MAP = {
        "comment": {"name": "Comment", "type": "stringValue"},
        "hours_worked_per_week": {"name": "AverageWeeklyHoursWorked", "type": "decimalValue"},
        "employer_decision": {"name": "EmployerDecision", "type": "stringValue"},
        "fraud": {"name": "Fraud1", "type": "stringValue"},
        "nature_of_leave": {
            "name": "NatureOfLeave",
            "type": "enumValue",
            "domainName": "Nature of leave",
        },
        "believe_relationship_accurate": {
            "name": "BelieveAccurate",
            "type": "enumValue",
            "domainName": "PleaseSelectYesNoIdontKnow",
        },
        "relationship_inaccurate_reason": {"name": "WhyInaccurate", "type": "stringValue"},
    }


class EmployerClaimReviewEFormBuilder(EFormBuilder):
    @classmethod
    def build(cls, review: EmployerClaimReview) -> EFormBody:
        employer_benefits = map(
            lambda benefit: EmployerBenefitAttributeBuilder(benefit), review.employer_benefits
        )
        previous_leaves = map(
            lambda leave: PreviousLeaveAttributeBuilder(leave), review.previous_leaves
        )
        other_info = OtherInfoAttributeBuilder(review)
        attributes = list(
            chain(
                cls.to_serialized_attributes(employer_benefits),
                cls.to_serialized_attributes(previous_leaves),
                cls.to_serialized_attributes([other_info]),
            )
        )

        return EFormBody("Employer Response to Leave Request", attributes)
