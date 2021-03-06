from itertools import chain
from typing import Iterable, Optional

from massgov.pfml.api.models.applications.common import OtherIncome
from massgov.pfml.api.models.common import ConcurrentLeave, EmployerBenefit, PreviousLeave
from massgov.pfml.fineos.transforms.common import (
    FineosAmountFrequencyEnum,
    FineosEmployerBenefitEnum,
    FineosOtherIncomeEnum,
)
from massgov.pfml.fineos.transforms.to_fineos.base import (
    EFormAttributeBuilder,
    EFormBody,
    EFormBuilder,
)
from massgov.pfml.fineos.transforms.to_fineos.eforms.common import (
    IntermediaryConcurrentLeave,
    IntermediaryEmployerBenefit,
    IntermediaryOtherIncome,
    IntermediaryPreviousLeave,
)


class EmployerBenefitAttributeBuilder(EFormAttributeBuilder):
    ATTRIBUTE_MAP = {
        "benefit_start_date": {"name": "V2StartDate", "type": "dateValue"},
        "benefit_end_date": {"name": "V2EndDate", "type": "dateValue"},
        "benefit_amount_dollars": {"name": "V2Amount", "type": "decimalValue"},
        "benefit_amount_frequency": {
            "name": "V2Frequency",
            "type": "enumValue",
            "domainName": "FrequencyEforms",
            "enumOverride": FineosAmountFrequencyEnum,
        },
        "is_full_salary_continuous": {
            "name": "V2SalaryContinuation",
            "type": "enumValue",
            "domainName": "PleaseSelectYesNo",
        },
        "benefit_type": {
            "name": "V2WRT",
            "type": "enumValue",
            "domainName": "WageReplacementType",
            "enumOverride": FineosEmployerBenefitEnum,
        },
        "receive_wage_replacement": {
            "name": "V2ReceiveWageReplacement",
            "type": "enumValue",
            "domainName": "PleaseSelectYesNo",
        },
    }

    def __init__(self, target):
        intermediary_target = IntermediaryEmployerBenefit(target)
        super().__init__(intermediary_target)


class OtherIncomeAttributeBuilder(EFormAttributeBuilder):
    ATTRIBUTE_MAP = {
        "income_start_date": {
            "name": "V2OtherIncomeNonEmployerBenefitStartDate",
            "type": "dateValue",
        },
        "income_end_date": {"name": "V2OtherIncomeNonEmployerBenefitEndDate", "type": "dateValue"},
        "income_amount_dollars": {
            "name": "V2OtherIncomeNonEmployerBenefitAmount",
            "type": "decimalValue",
        },
        "income_amount_frequency": {
            "name": "V2OtherIncomeNonEmployerBenefitFrequency",
            "type": "enumValue",
            "domainName": "FrequencyEforms",
            "enumOverride": FineosAmountFrequencyEnum,
        },
        "income_type": {
            "name": "V2OtherIncomeNonEmployerBenefitWRT",
            "type": "enumValue",
            "domainName": "WageReplacementType2",
            "enumOverride": FineosOtherIncomeEnum,
        },
        "receive_wage_replacement": {
            "name": "V2ReceiveWageReplacement",
            "type": "enumValue",
            "domainName": "YesNoI'veApplied",
            # The suffixes here are nonstandard -- they should start with index 7
            "suffixOverride": lambda index: index + 7,
        },
    }

    def __init__(self, target):
        intermediary_target = IntermediaryOtherIncome(target)
        super().__init__(intermediary_target)


class OtherIncomesEFormBuilder(EFormBuilder):
    @classmethod
    def build(
        cls, employer_benefits: Iterable[EmployerBenefit], other_incomes: Iterable[OtherIncome]
    ) -> EFormBody:

        other_income_builders = map(
            lambda income: OtherIncomeAttributeBuilder(income), other_incomes
        )

        employer_benefit_builders = map(
            lambda benefit: EmployerBenefitAttributeBuilder(benefit), employer_benefits
        )

        attributes = list(
            chain(
                cls.to_serialized_attributes(employer_benefit_builders, True),
                cls.to_serialized_attributes(other_income_builders, True),
            )
        )

        return EFormBody("Other Income - current version", attributes)


class ConcurrentLeaveAttributeBuilder(EFormAttributeBuilder):
    ATTRIBUTE_MAP = {
        "leave_start_date": {"name": "V2AccruedStartDate", "type": "dateValue"},
        "leave_end_date": {"name": "V2AccruedEndDate", "type": "dateValue"},
        "is_for_current_employer": {
            "name": "V2AccruedPLEmployer",
            "type": "enumValue",
            "domainName": "PleaseSelectYesNo",
        },
        "accrued_paid_leave": {
            "name": "V2AccruedPaidLeave",
            "type": "enumValue",
            "domainName": "PleaseSelectYesNo",
        },
    }

    def __init__(self, target):
        intermediary_target = IntermediaryConcurrentLeave(target)
        super().__init__(intermediary_target)


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
        "applies": {"name": "V2Applies", "type": "enumValue", "domainName": "PleaseSelectYesNo"},
    }

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
                    chain(cls.to_serialized_attributes(list(previous_leave_transforms), True))
                )
            if concurrent_leave_transforms:
                attributes = list(
                    chain(cls.to_serialized_attributes(concurrent_leave_transforms, True))
                )

        return EFormBody("Other Leaves - current version", attributes) if attributes else None
