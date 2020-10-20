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
    eformAttributes: Optional[List[EFormAttribute]] = Field(
        None, description="An array of EForm attributes."
    )


class TransformEmployerBenefit(TransformEformAttributes):
    ATTRIBUTE_MAP = {
        "benefit_amount_dollars": {"name": "Amount", "type": "decimalValue"},
        "benefit_amount_frequency": {"name": "Frequency", "type": "stringValue"},
        "benefit_start_date": {"name": "StartDate", "type": "dateValue"},
        "benefit_end_date": {"name": "EndDate", "type": "dateValue"},
        "benefit_type": {"name": "WRT", "type": "enumValue"},
    }


class TransformPreviousLeave(TransformEformAttributes):
    ATTRIBUTE_MAP = {
        "leave_start_date": {"name": "StartDate", "type": "dateValue"},
        "leave_end_date": {"name": "EndDate", "type": "dateValue"},
        "leave_type": {"name": "PrimaryReason", "type": "stringValue"},
    }


class TransformOtherInfo(TransformEformAttributes):
    ATTRIBUTE_MAP = {
        "comment": {"name": "comment", "type": "stringValue"},
        "employer_notification_date": {"name": "notifiedDate", "type": "dateValue"},
        "hours_worked_per_week": {"name": "HoursWorked", "type": "integerValue"},
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

        return EFormBody(eformType="Employer Info Request", eformAttributes=attributes)
