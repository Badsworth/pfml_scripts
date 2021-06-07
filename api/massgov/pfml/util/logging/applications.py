from collections import defaultdict
from datetime import datetime
from typing import DefaultDict, Dict, Iterable, Optional, Union

from massgov.pfml.db.models.applications import (
    Application,
    ContinuousLeavePeriod,
    EmployerBenefit,
    EmployerBenefitType,
    IntermittentLeavePeriod,
    LeaveReason,
    OtherIncome,
    OtherIncomeType,
    PreviousLeave,
    PreviousLeaveQualifyingReason,
    ReducedScheduleLeavePeriod,
)


def get_leave_dates(
    leave_periods: Optional[
        Iterable[Union[ContinuousLeavePeriod, IntermittentLeavePeriod, ReducedScheduleLeavePeriod]]
    ],
    leave_type: str,
) -> Dict[str, str]:
    leave_period_dates = {}
    if leave_periods:
        for i, leave_period in enumerate(leave_periods):
            if leave_period.start_date:
                leave_period_dates[
                    f"application.{leave_type}[{i+1}].start_date"
                ] = leave_period.start_date.isoformat()
            if leave_period.end_date:
                leave_period_dates[
                    f"application.{leave_type}[{i+1}].end_date"
                ] = leave_period.end_date.isoformat()

    return leave_period_dates


def get_leave_period_log_attributes(application: Application) -> Dict[str, str]:
    result = {}
    if application.has_continuous_leave_periods:
        result.update(get_leave_dates(application.continuous_leave_periods, "continuous_leave"))
    if application.has_reduced_schedule_leave_periods:
        result.update(
            get_leave_dates(application.reduced_schedule_leave_periods, "reduced_schedule_leave")
        )
    if application.has_intermittent_leave_periods:
        result.update(get_leave_dates(application.intermittent_leave_periods, "intermittent_leave"))
    return result


def get_application_log_attributes(application: Application) -> Dict[str, Optional[str]]:
    attributes_to_log = [
        "application_id",
        "employer_id",
        "has_state_id",
        "has_continuous_leave_periods",
        "has_employer_benefits",
        "has_future_child_date",
        "has_intermittent_leave_periods",
        "has_mailing_address",
        "has_other_incomes",
        "has_previous_leaves_other_reason",
        "has_previous_leaves_same_reason",
        "has_reduced_schedule_leave_periods",
        "has_submitted_payment_preference",
        "pregnant_or_recent_birth",
        "start_time",
        "updated_time",
        "completed_time",
        "submitted_time",
    ]

    timestamp_attributes_to_log = [
        "start_time",
        "updated_time",
        "completed_time",
        "submitted_time",
    ]

    result = {}
    for name in attributes_to_log:
        value = getattr(application, name)
        result[f"application.{name}"] = str(value) if value is not None else None

    for name in timestamp_attributes_to_log:
        dt_value: Optional[datetime] = getattr(application, name)
        result[f"application.{name}.timestamp"] = (
            str(dt_value.timestamp()) if dt_value is not None else None
        )

    # Use a different attribute name for other_incomes_awaiting_approval to be consistent with other booleans
    has_other_incomes_awaiting_approval = application.other_incomes_awaiting_approval
    result["application.has_other_incomes_awaiting_approval"] = (
        str(has_other_incomes_awaiting_approval)
        if has_other_incomes_awaiting_approval is not None
        else None
    )

    # Use a different attribute name for fineos_absence_id to avoid using vendor specific names
    result["application.absence_case_id"] = (
        application.claim.fineos_absence_id if application.claim else None
    )

    # leave_reason and leave_reason_qualifier are objects, so get the underlying string description
    result["application.leave_reason"] = (
        application.leave_reason.leave_reason_description if application.leave_reason else None
    )
    result["application.leave_reason_qualifier"] = (
        application.leave_reason_qualifier.leave_reason_qualifier_description
        if application.leave_reason_qualifier
        else None
    )

    # for caring leave, log relationship type
    if (
        application.leave_reason_id == LeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_id
        and application.caring_leave_metadata
        and application.caring_leave_metadata.relationship_to_caregiver
    ):
        result[
            "application.leave_details.caring_leave_metadata.relationship_to_caregiver"
        ] = (
            application.caring_leave_metadata.relationship_to_caregiver.relationship_to_caregiver_description
        )

    result["work_pattern.work_pattern_type"] = (
        application.work_pattern.work_pattern_type.work_pattern_type_description
        if application.work_pattern and application.work_pattern.work_pattern_type
        else None
    )

    # add leave start_date and end_date for each type of leave period
    result.update(get_leave_period_log_attributes(application))

    result.update(
        get_previous_leaves_log_attributes(application.previous_leaves_other_reason, "other_reason")
    )
    result.update(
        get_previous_leaves_log_attributes(application.previous_leaves_same_reason, "same_reason")
    )
    result.update(get_employer_benefits_log_attributes(application.employer_benefits))
    result.update(get_other_incomes_log_attributes(application.other_incomes))

    return result


def get_previous_leaves_log_attributes(
    leaves: Iterable[PreviousLeave], leave_type: str
) -> Dict[str, str]:
    result = {f"application.num_previous_leaves_{leave_type}": str(len(list(leaves)))}

    reason_values = [
        PreviousLeaveQualifyingReason.PREGNANCY_MATERNITY.previous_leave_qualifying_reason_description,
        PreviousLeaveQualifyingReason.AN_ILLNESS_OR_INJURY.previous_leave_qualifying_reason_description,
        PreviousLeaveQualifyingReason.CARE_FOR_A_FAMILY_MEMBER.previous_leave_qualifying_reason_description,
        PreviousLeaveQualifyingReason.CHILD_BONDING.previous_leave_qualifying_reason_description,
        PreviousLeaveQualifyingReason.MILITARY_CAREGIVER.previous_leave_qualifying_reason_description,
        PreviousLeaveQualifyingReason.MILITARY_EXIGENCY_FAMILY.previous_leave_qualifying_reason_description,
    ]

    reason_counts: DefaultDict[str, int] = defaultdict(int)

    for leave in leaves:
        if leave.leave_reason:
            reason = leave.leave_reason.previous_leave_qualifying_reason_description
            assert reason
            reason_counts[reason] += 1

    for reason in reason_values:
        assert reason
        count = reason_counts[reason]
        result[f"application.num_previous_leave_{leave_type}_reasons.{reason}"] = str(count)

    return result


def get_employer_benefits_log_attributes(benefits: Iterable[EmployerBenefit],) -> Dict[str, str]:
    result = {"application.num_employer_benefits": str(len(list(benefits)))}

    type_values = [
        EmployerBenefitType.ACCRUED_PAID_LEAVE.employer_benefit_type_description,
        EmployerBenefitType.SHORT_TERM_DISABILITY.employer_benefit_type_description,
        EmployerBenefitType.PERMANENT_DISABILITY_INSURANCE.employer_benefit_type_description,
        EmployerBenefitType.FAMILY_OR_MEDICAL_LEAVE_INSURANCE.employer_benefit_type_description,
    ]

    type_counts: DefaultDict[str, int] = defaultdict(int)

    for benefit in benefits:
        if benefit.benefit_type:
            benefit_type = benefit.benefit_type.employer_benefit_type_description
            assert benefit_type
            type_counts[benefit_type] += 1

    for type_value in type_values:
        assert type_value
        count = type_counts[type_value]
        result[f"application.num_employer_benefit_types.{type_value}"] = str(count)

    return result


def get_other_incomes_log_attributes(incomes: Iterable[OtherIncome]) -> Dict[str, str]:
    result = {"application.num_other_incomes": str(len(list(incomes)))}

    type_values = [
        OtherIncomeType.WORKERS_COMP.other_income_type_description,
        OtherIncomeType.UNEMPLOYMENT.other_income_type_description,
        OtherIncomeType.SSDI.other_income_type_description,
        OtherIncomeType.RETIREMENT_DISABILITY.other_income_type_description,
        OtherIncomeType.JONES_ACT.other_income_type_description,
        OtherIncomeType.RAILROAD_RETIREMENT.other_income_type_description,
        OtherIncomeType.OTHER_EMPLOYER.other_income_type_description,
    ]

    income_counts: DefaultDict[str, int] = defaultdict(int)

    for income in incomes:
        if income.income_type:
            income_type = income.income_type.other_income_type_description
            assert income_type
            income_counts[income_type] += 1

    for type_value in type_values:
        assert type_value
        count = income_counts[type_value]
        result[f"application.num_other_income_types.{type_value}"] = str(count)

    return result
