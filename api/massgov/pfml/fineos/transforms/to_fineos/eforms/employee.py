from itertools import chain
from typing import Iterable

from massgov.pfml.api.models.common import PreviousLeave
from massgov.pfml.fineos.transforms.to_fineos.base import (
    EFormAttributeBuilder,
    EFormBody,
    EFormBuilder,
)


class IntermediaryPreviousLeave:
    def __init__(self, leave: PreviousLeave):
        self.leave_start_date = leave.leave_start_date
        self.leave_end_date = leave.leave_end_date
        self.is_for_current_employer = "Yes" if leave.is_for_current_employer else "No"
        self.leave_reason = leave.leave_reason


class PreviousLeaveAttributeBuilder(EFormAttributeBuilder):
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

    JOINING_ATTRIBUTE = {
        "name": "Applies",
        "type": "enumValue",
        "domainName": "PleaseSelectYesNoUnknown",
        "instanceValue": "Yes",
    }

    def __init__(self, target):
        intermediary_target = IntermediaryPreviousLeave(target)
        super().__init__(intermediary_target)


class PreviousLeavesEFormBuilder(EFormBuilder):
    @classmethod
    def build(cls, previous_leaves: Iterable[PreviousLeave]) -> EFormBody:
        transforms = map(lambda leave: PreviousLeaveAttributeBuilder(leave), previous_leaves)
        attributes = list(chain(cls.to_serialized_attributes(list(transforms), True),))

        return EFormBody("Other Leaves", attributes)
