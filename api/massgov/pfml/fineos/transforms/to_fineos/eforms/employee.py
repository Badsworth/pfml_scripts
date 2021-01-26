from itertools import chain
from typing import Any, List, Optional

from pydantic import BaseModel

from massgov.pfml.db.models.applications import Application, PreviousLeave
from massgov.pfml.fineos.models.group_client_api import EFormAttribute, ModelEnum
from massgov.pfml.fineos.transforms.to_fineos.base import EFormBody, TransformEformAttributes


class IntermediaryPreviousLeave:
    def __init__(self, leave: PreviousLeave):
        self.leave_start_date = leave.leave_start_date
        self.leave_end_date = leave.leave_end_date
        self.is_for_current_employer = "Yes" if leave.is_for_current_employer else "No"
        assert leave.leave_reason is not None
        self.leave_reason = leave.leave_reason.previous_leave_qualifying_reason_description


class TransformPreviousLeave(TransformEformAttributes):
    ATTRIBUTE_MAP = {
        "leave_start_date": {"name": "BeginDate", "type": "dateValue"},
        "leave_end_date": {"name": "EndDate", "type": "dateValue"},
        "leave_reason": {
            "name": "QualifyingReason",
            "type": "enumValue",
            "domainName": "QualifyingReasons",
        },
        "is_for_current_employer": {
            "name": "LeaveFromEmployer",
            "type": "enumValue",
            "domainName": "YesNoUnknown",
        },
    }

    ADDITIONAL_OBJECT = EFormAttribute(
        name="Applies",
        enumValue=ModelEnum(domainName="PleaseSelectYesNoUnknown", instanceValue="Yes"),
    )

    @classmethod
    def to_attributes(cls, target: Any, suffix: Optional[str] = "") -> List[EFormAttribute]:
        intermediary_target = IntermediaryPreviousLeave(target)
        return super(TransformPreviousLeave, cls).to_attributes(intermediary_target, suffix)


class TransformPreviousLeaves(BaseModel):
    @classmethod
    def to_fineos(cls, application: Application) -> EFormBody:
        attributes = list(
            chain(
                TransformPreviousLeave.list_to_attributes(list(application.previous_leaves), True),
            )
        )

        return EFormBody(eformType="Other Leaves", eformAttributes=attributes)
