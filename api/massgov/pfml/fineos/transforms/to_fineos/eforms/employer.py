from enum import Enum
from itertools import chain

from massgov.pfml.api.models.claims.common import EmployerClaimReview, YesNoUnknown
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


class FineosNatureOfLeave(str, Enum):
    ILLNESS_OR_INJURY = "An illness or injury"
    PREGNANCY = "Pregnancy"
    CHILD_BONDING = "Bonding with my child after birth or placement"
    MILITARY_CAREGIVER = "Caring for a family member who serves in the armed forces"
    MILITARY_EXIGENCY = (
        "Managing family affairs while a family member is on active duty in the armed forces"
    )
    FAMILY_CAREGIVER = "Caring for a family member with a serious health condition"


class FineosBelieveAccurate(str, Enum):
    YES = "Yes"
    NO = "No"
    UNSURE = "I Don't Know"


# Intermediary for handling transforms from our data to FINEOS enums and values
class IntermediaryEmployerClaimReview:
    # TODO: use LeaveReason enum
    # https://lwd.atlassian.net/browse/EMPLOYER-1358
    LEAVE_REASON_TO_NATURE_OF_LEAVE_MAPPING = {
        "Military Exigency Family": FineosNatureOfLeave.MILITARY_EXIGENCY,
        "Child Bonding": FineosNatureOfLeave.CHILD_BONDING,
        "Care for a Family Member": FineosNatureOfLeave.FAMILY_CAREGIVER,
        "Serious Health Condition - Employee": FineosNatureOfLeave.ILLNESS_OR_INJURY,
        "Pregnancy/Maternity": FineosNatureOfLeave.PREGNANCY,
        "Military Caregiver": FineosNatureOfLeave.MILITARY_CAREGIVER,
    }

    BELIEVE_RELATIONSHIP_ACCURATE_MAPPING = {
        YesNoUnknown.YES: FineosBelieveAccurate.YES,
        YesNoUnknown.NO: FineosBelieveAccurate.NO,
        YesNoUnknown.UNKNOWN: FineosBelieveAccurate.UNSURE,
    }

    def __init__(self, review: EmployerClaimReview):
        self.comment = review.comment
        self.hours_worked_per_week = review.hours_worked_per_week
        self.employer_decision = review.employer_decision
        self.fraud = review.fraud

        if review.leave_reason is not None:
            self.nature_of_leave = self.LEAVE_REASON_TO_NATURE_OF_LEAVE_MAPPING.get(
                review.leave_reason
            )
        else:
            self.nature_of_leave = None

        if review.believe_relationship_accurate is not None:
            self.believe_accurate = self.BELIEVE_RELATIONSHIP_ACCURATE_MAPPING.get(
                review.believe_relationship_accurate
            )
        else:
            self.believe_accurate = None

        self.relationship_inaccurate_reason = review.relationship_inaccurate_reason


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
        "believe_accurate": {
            "name": "BelieveAccurate",
            "type": "enumValue",
            "domainName": "PleaseSelectYesNoIdontKnow",
        },
        "relationship_inaccurate_reason": {"name": "WhyInaccurate", "type": "stringValue"},
    }

    def __init__(self, target):
        intermediary_target = IntermediaryEmployerClaimReview(target)
        super().__init__(intermediary_target)


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
