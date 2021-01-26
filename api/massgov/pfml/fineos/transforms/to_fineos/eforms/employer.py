from itertools import chain

from pydantic import BaseModel

from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.fineos.models.group_client_api import EFormAttribute, ModelEnum
from massgov.pfml.fineos.transforms.to_fineos.base import EFormBody, TransformEformAttributes


class TransformEmployerBenefit(TransformEformAttributes):
    ATTRIBUTE_MAP = {
        "benefit_amount_dollars": {"name": "Amount", "type": "decimalValue"},
        "benefit_amount_frequency": {"name": "Frequency", "type": "stringValue"},
        "benefit_start_date": {"name": "EmployerBenefitStartDate", "type": "dateValue"},
        "benefit_end_date": {"name": "EmployerBenefitEndDate", "type": "dateValue"},
        "benefit_type": {"name": "BenefitType", "type": "stringValue"},
    }

    ADDITIONAL_OBJECT = EFormAttribute(
        name="ReceiveWageReplacement",
        enumValue=ModelEnum(domainName="PleaseSelectYesNoUnknown", instanceValue="Yes"),
    )


class TransformPreviousLeave(TransformEformAttributes):
    ATTRIBUTE_MAP = {
        "leave_start_date": {"name": "PastLeaveStartDate", "type": "dateValue"},
        "leave_end_date": {"name": "PastLeaveEndDate", "type": "dateValue"},
        "leave_reason": {"name": "QualifyingReason", "type": "stringValue"},
    }

    ADDITIONAL_OBJECT = EFormAttribute(
        name="Applies",
        enumValue=ModelEnum(domainName="PleaseSelectYesNoUnknown", instanceValue="Yes"),
    )


class TransformOtherInfo(TransformEformAttributes):
    ATTRIBUTE_MAP = {
        "comment": {"name": "Comment", "type": "stringValue"},
        "hours_worked_per_week": {"name": "AverageWeeklyHoursWorked", "type": "decimalValue"},
        "employer_decision": {"name": "EmployerDecision", "type": "stringValue"},
        "fraud": {"name": "Fraud1", "type": "stringValue"},
    }


class TransformEmployerClaimReview(BaseModel):
    @classmethod
    def to_fineos(cls, api_model: EmployerClaimReview) -> EFormBody:
        attributes = list(
            chain(
                TransformEmployerBenefit.list_to_attributes(api_model.employer_benefits),
                TransformPreviousLeave.list_to_attributes(api_model.previous_leaves),
                TransformOtherInfo.to_attributes(api_model),
            )
        )

        return EFormBody(eformType="Employer Response to Leave Request", eformAttributes=attributes)
