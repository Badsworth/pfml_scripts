from itertools import chain
from typing import List, Optional

from pydantic import BaseModel, Field

from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.fineos.models.group_client_api import EFormAttribute
from massgov.pfml.fineos.transforms.to_fineos.base import TransformEformAttributes


# TODO use EForm from group_client_api model here
class EFormBody(BaseModel):
    eformType: str = Field(
        None, description="Name of the EForm document type", min_length=0, max_length=200
    )
    eformId: Optional[int]
    eformAttributes: List[EFormAttribute] = Field(None, description="An array of EForm attributes.")


class TransformEmployerBenefit(TransformEformAttributes):
    ATTRIBUTE_MAP = {
        "benefit_amount_dollars": {"name": "Amount", "type": "decimalValue"},
        "benefit_amount_frequency": {"name": "Frequency", "type": "stringValue"},
        "benefit_start_date": {"name": "EmployerBenefitStartDate", "type": "dateValue"},
        "benefit_end_date": {"name": "EmployerBenefitenddate", "type": "dateValue"},
        "benefit_type": {"name": "EmployerBenefitType", "type": "stringValue"},
    }


class TransformPreviousLeave(TransformEformAttributes):
    ATTRIBUTE_MAP = {
        "leave_start_date": {"name": "PastLeaveStartDate", "type": "dateValue"},
        "leave_end_date": {"name": "Pastleaveenddate", "type": "dateValue"},
        "leave_type": {"name": "NatureofLeave", "type": "stringValue"},
    }


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
