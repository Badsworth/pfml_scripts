from itertools import chain
from typing import Iterable, Optional

from massgov.pfml.api.models.applications.common import OtherIncome
from massgov.pfml.api.models.common import ConcurrentLeave, EmployerBenefit, PreviousLeave
from massgov.pfml.fineos.transforms.to_fineos.base import (
    EFormAttributeBuilder,
    EFormBody,
    EFormBuilder,
)


class EmployerBenefitAttributeBuilder(EFormAttributeBuilder):
    ATTRIBUTE_MAP = {
        "benefit_start_date": {"name": "StartDate", "type": "dateValue"},
        "benefit_end_date": {"name": "EndDate", "type": "dateValue"},
        "benefit_amount_dollars": {"name": "Amount", "type": "decimalValue"},
        "benefit_amount_frequency": {"name": "Frequency", "type": "stringValue"},
        "benefit_type": {
            "name": "WRT",
            "type": "enumValue",
            "domainName": "WageReplacementType",
            # The suffixes here are nonstandard -- they should increase by 2 eg WRT1, WRT3, WRT5
            "suffixOverride": lambda index: 2 * index + 1,
        },
    }

    STATIC_ATTRIBUTES = [
        {
            "name": "WRT",
            "type": "enumValue",
            "domainName": "WageReplacementType2",
            "instanceValue": "Please Select",
            # The suffixes here are nonstandard -- they should increase by 2 eg WRT2, WRT4, WRT6
            "suffixOverride": lambda index: 2 * index + 2,
        },
        {
            "name": "ProgramType",
            "type": "enumValue",
            "domainName": "Program Type",
            "instanceValue": "Employer",
        },
        {
            "name": "ReceiveWageReplacement",
            "type": "enumValue",
            "domainName": "YesNoI'veApplied",
            "instanceValue": "Yes",
        },
    ]


class OtherIncomeAttributeBuilder(EFormAttributeBuilder):
    ATTRIBUTE_MAP = {
        "income_start_date": {"name": "StartDate", "type": "dateValue"},
        "income_end_date": {"name": "EndDate", "type": "dateValue"},
        "income_amount_dollars": {"name": "Amount", "type": "decimalValue"},
        "income_amount_frequency": {"name": "Frequency", "type": "stringValue"},
        "income_type": {
            "name": "WRT",
            "type": "enumValue",
            "domainName": "WageReplacementType2",
            # The suffixes here are nonstandard -- they should increase by 2 eg WRT2, WRT4, WRT6
            "suffixOverride": lambda index: 2 * index + 2,
        },
    }

    STATIC_ATTRIBUTES = [
        {
            "name": "WRT",
            "type": "enumValue",
            "domainName": "WageReplacementType",
            "instanceValue": "Please Select",
            # The suffixes here are nonstandard -- they should increase by 2 eg WRT1, WRT3, WRT5
            "suffixOverride": lambda index: 2 * index + 1,
        },
        {
            "name": "ProgramType",
            "type": "enumValue",
            "domainName": "Program Type",
            "instanceValue": "Non-Employer",
        },
        {
            "name": "ReceiveWageReplacement",
            "type": "enumValue",
            "domainName": "YesNoI'veApplied",
            "instanceValue": "Yes",
        },
    ]


class OtherIncomeAwaitingApprovalAttributeBuilder(EFormAttributeBuilder):
    STATIC_ATTRIBUTES = [
        {
            "name": "ReceiveWageReplacement",
            "type": "enumValue",
            "domainName": "YesNoI'veApplied",
            "instanceValue": "I've applied, but haven't been approved",
        },
    ]

    def __init__(self):
        super().__init__(None)


class OtherIncomesEFormBuilder(EFormBuilder):
    @classmethod
    def build(
        cls,
        employer_benefits: Iterable[EmployerBenefit],
        other_incomes: Iterable[OtherIncome],
        other_incomes_awaiting_approval: Optional[bool],
    ) -> EFormBody:

        other_income_builders: Iterable[EFormAttributeBuilder] = []
        if other_incomes_awaiting_approval:
            other_income_builders = [OtherIncomeAwaitingApprovalAttributeBuilder()]
        else:
            other_income_builders = map(
                lambda income: OtherIncomeAttributeBuilder(income), other_incomes
            )

        employer_benefit_builders = map(
            lambda benefit: EmployerBenefitAttributeBuilder(benefit), employer_benefits,
        )

        attributes = list(
            cls.to_serialized_attributes(
                list(chain(employer_benefit_builders, other_income_builders)), False
            ),
        )

        return EFormBody("Other Income", attributes)


class IntermediaryConcurrentLeave:
    def __init__(self, leave: ConcurrentLeave):
        self.leave_start_date = leave.leave_start_date
        self.leave_end_date = leave.leave_end_date
        self.is_for_current_employer = "Yes" if leave.is_for_current_employer else "No"


class ConcurrentLeaveAttributeBuilder(EFormAttributeBuilder):
    ATTRIBUTE_MAP = {
        "leave_start_date": {"name": "V2AccruedStartDate", "type": "dateValue"},
        "leave_end_date": {"name": "V2AccruedEndDate", "type": "dateValue"},
        "is_for_current_employer": {
            "name": "V2AccruedPLEmployer",
            "type": "enumValue",
            "domainName": "PleaseSelectYesNo",
        },
    }

    STATIC_ATTRIBUTES = [
        {
            "name": "V2AccruedPaidLeave",
            "type": "enumValue",
            "domainName": "PleaseSelectYesNo",
            "instanceValue": "Yes",
        }
    ]

    def __init__(self, target):
        intermediary_target = IntermediaryConcurrentLeave(target)
        super().__init__(intermediary_target)


class IntermediaryPreviousLeave:
    def __init__(self, leave: PreviousLeave):
        self.leave_start_date = leave.leave_start_date
        self.leave_end_date = leave.leave_end_date
        self.is_for_current_employer = "Yes" if leave.is_for_current_employer else "No"
        self.is_for_same_reason = "Yes" if leave.type == "same_reason" else "No"
        self.leave_reason = leave.leave_reason
        if leave.worked_per_week_minutes:
            self.worked_per_week_hours = int(leave.worked_per_week_minutes / 60)
            self.worked_per_week_minutes = format(leave.worked_per_week_minutes % 60, "02d")
        else:
            self.worked_per_week_hours = 0
            self.worked_per_week_minutes = "Please Select"
        if leave.leave_minutes:
            self.leave_hours = int(leave.leave_minutes / 60)
            self.leave_minutes = format(leave.leave_minutes % 60, "02d")
        else:
            self.leave_hours = 0
            self.leave_minutes = "Please Select"


class PreviousLeaveAttributeBuilder(EFormAttributeBuilder):
    ATTRIBUTE_MAP = {
        "leave_start_date": {"name": "V2OtherLeavesPastLeaveStartDate", "type": "dateValue"},
        "leave_end_date": {"name": "V2OtherLeavesPastLeaveEndDate", "type": "dateValue"},
        "leave_reason": {
            "name": "V2QualifyingReason",
            "type": "enumValue",
            "domainName": "QualifyingReasons",
        },
        "is_for_current_employer": {
            "name": "V2LeaveFromEmployer",
            "type": "enumValue",
            "domainName": "PleaseSelectYesNo",
        },
        "is_for_same_reason": {
            "name": "V2Leave",
            "type": "enumValue",
            "domainName": "PleaseSelectYesNo",
        },
        "worked_per_week_hours": {"name": "V2HoursWorked", "type": "integerValue"},
        "worked_per_week_minutes": {
            "name": "V2MinutesWorked",
            "type": "enumValue",
            "domainName": "15MinuteIncrements",
        },
        "leave_hours": {"name": "V2TotalHours", "type": "integerValue"},
        "leave_minutes": {
            "name": "V2TotalMinutes",
            "type": "enumValue",
            "domainName": "15MinuteIncrements",
        },
    }

    STATIC_ATTRIBUTES = [
        {
            "name": "V2Applies",
            "type": "enumValue",
            "domainName": "PleaseSelectYesNo",
            "instanceValue": "Yes",
        }
    ]

    def __init__(self, target):
        intermediary_target = IntermediaryPreviousLeave(target)
        super().__init__(intermediary_target)


class PreviousLeavesEFormBuilder(EFormBuilder):
    @classmethod
    def build(
        cls, previous_leaves: Iterable[PreviousLeave], concurrent_leave: Optional[ConcurrentLeave]
    ) -> Optional[EFormBody]:
        previous_leave_transforms = (
            map(
                lambda previous_leave: PreviousLeaveAttributeBuilder(previous_leave),
                previous_leaves,
            )
            if previous_leaves
            else None
        )

        concurrent_leave_transforms = None
        if concurrent_leave:
            concurrent_leaves = [concurrent_leave]
            concurrent_leave_transforms = map(
                lambda concurrent_leave_item: ConcurrentLeaveAttributeBuilder(
                    concurrent_leave_item
                ),
                concurrent_leaves,
            )

        attributes = None

        if previous_leave_transforms and concurrent_leave_transforms:
            attributes = list(
                chain(
                    cls.to_serialized_attributes(list(previous_leave_transforms), True),
                    cls.to_serialized_attributes(concurrent_leave_transforms, True),
                )
            )
        else:
            if previous_leave_transforms:
                attributes = list(
                    chain(cls.to_serialized_attributes(list(previous_leave_transforms), True),)
                )
            if concurrent_leave_transforms:
                attributes = list(
                    chain(cls.to_serialized_attributes(concurrent_leave_transforms, True),)
                )

        return EFormBody("Other Leaves - current version", attributes) if attributes else None
