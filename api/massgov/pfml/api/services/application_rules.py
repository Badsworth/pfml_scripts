from datetime import date
from itertools import chain, combinations
from typing import Any, Dict, Iterable, List, Optional, Union

from dateutil.relativedelta import relativedelta
from werkzeug.datastructures import Headers

import massgov.pfml.db as db
from massgov.pfml.api.models.applications.common import DurationBasis, FrequencyIntervalBasis
from massgov.pfml.api.services.applications import (
    ContinuousLeavePeriod,
    IntermittentLeavePeriod,
    ReducedScheduleLeavePeriod,
)
from massgov.pfml.api.util.deepgetattr import deepgetattr
from massgov.pfml.api.util.response import Issue, IssueRule, IssueType
from massgov.pfml.db.models.applications import (
    Application,
    EmployerBenefit,
    EmploymentStatus,
    LeaveReason,
    LeaveReasonQualifier,
    OtherIncome,
    PreviousLeave,
)
from massgov.pfml.db.models.employees import PaymentMethod
from massgov.pfml.util.routing_number_validation import validate_routing_number

PFML_PROGRAM_LAUNCH_DATE = date(2021, 1, 1)
MAX_DAYS_IN_ADVANCE_TO_SUBMIT = 60
MAX_DAYS_IN_LEAVE_PERIOD_RANGE = 364
MAX_MINUTES_IN_WEEK = 10080  # 60 * 24 * 7


def get_application_issues(application: Application, headers: Headers) -> List[Issue]:
    """Takes in application and outputs any validation issues.
    These issues are either fields that are always required for an application or fields that are conditionally required based on previous input.
    """
    issues = []
    issues += get_always_required_issues(application)
    issues += get_leave_periods_issues(application)
    issues += get_conditional_issues(application, headers)

    return issues


def get_address_issues(application: Application, address_field_name: str) -> List[Issue]:
    issues = []
    address_field_db_name_to_api_name_map = {
        f"{address_field_name}.address_line_one": f"{address_field_name}.line_1",
        f"{address_field_name}.city": f"{address_field_name}.city",
        f"{address_field_name}.geo_state_id": f"{address_field_name}.state",
        f"{address_field_name}.zip_code": f"{address_field_name}.zip",
    }

    for (field, openapi_field) in address_field_db_name_to_api_name_map.items():
        val = deepgetattr(application, field)
        if val is None:
            issues.append(
                Issue(
                    type=IssueType.required,
                    message=f"{openapi_field} is required",
                    field=openapi_field,
                )
            )

    return issues


def handle_rename(renames: Union[Dict[str, str], None], field_name: str) -> str:
    if renames:
        return renames.get(field_name, field_name)

    return field_name


def check_required_fields(
    path: str, item: Any, required_fields: List[str], renames: Optional[Dict[str, str]] = None
) -> List[Issue]:
    """
    Check that a set of required fields are present on item. Returns an issue for each missing required field.
    """
    issues = []

    for field in required_fields:
        val = getattr(item, field)
        if val is None:
            field_name = f"{path}.{handle_rename(renames, field)}"
            issues.append(
                Issue(
                    type=IssueType.required, message=f"{field_name} is required", field=field_name,
                )
            )

    return issues


def check_codependent_fields(
    path: str, item: Any, field_a: str, field_b: str, renames: Optional[Dict[str, str]] = None
) -> List[Issue]:
    """
    Checks that neither or both of the specified fields (field_a and _field_b) are set on item. If only one
    field is set then the returned issues will not be empty.
    """
    issues = []

    val_a = getattr(item, field_a)
    val_b = getattr(item, field_b)
    field_a_path = f"{path}.{handle_rename(renames, field_a)}"
    field_b_path = f"{path}.{handle_rename(renames, field_b)}"
    if val_a and not val_b:
        issues.append(
            Issue(
                type=IssueType.required,
                rule=IssueRule.conditional,
                message=f"{field_b_path} is required if {field_a_path} is set",
                field=field_b_path,
            )
        )
    elif val_b and not val_a:
        issues.append(
            Issue(
                type=IssueType.required,
                rule=IssueRule.conditional,
                message=f"{field_a_path} is required if {field_b_path} is set",
                field=field_a_path,
            )
        )

    return issues


def check_date_range(
    start_date: Optional[date],
    start_date_path: str,
    end_date: Optional[date],
    end_date_path: str,
    minimum_date: date,
) -> List[Issue]:
    """
    Checks if a start and end date are valid, if set. start_date is valid if it is greater than or equal to
    minimum_date. end_date is valid if it is greater than or equal to minimum_date and start_date. A date is
    not checked if it isn't set.
    """
    issues = []
    if start_date and start_date < minimum_date:
        issues.append(
            Issue(
                type=IssueType.minimum,
                message=f"{start_date_path} cannot be earlier than {minimum_date.isoformat()}",
                field=f"{start_date_path}",
            )
        )

    if end_date and end_date < minimum_date:
        issues.append(
            Issue(
                type=IssueType.minimum,
                message=f"{end_date_path} cannot be earlier than {minimum_date.isoformat()}",
                field=f"{end_date_path}",
            )
        )
    elif start_date and end_date and start_date > end_date:
        issues.append(
            Issue(
                type=IssueType.invalid_date_range,
                message=f"{end_date_path} cannot be earlier than {start_date_path}",
                field=f"{end_date_path}",
            )
        )

    return issues


def get_employer_benefits_issues(application: Application) -> List[Issue]:
    issues = []

    if application.has_employer_benefits and len(list(application.employer_benefits)) == 0:
        issues.append(
            Issue(
                type=IssueType.required,
                rule=IssueRule.conditional,
                message="when has_employer_benefits is true, employer_benefits cannot be empty",
                field="employer_benefits",
            )
        )
    else:
        for index, benefit in enumerate(application.employer_benefits, 0):
            issues += get_employer_benefit_issues(benefit, index)

    return issues


def get_employer_benefit_issues(benefit: EmployerBenefit, index: int) -> List[Issue]:
    benefit_path = f"employer_benefits[{index}]"
    issues = []

    required_fields = [
        "benefit_start_date",
        "benefit_type_id",
        "is_full_salary_continuous",
    ]
    issues += check_required_fields(
        benefit_path, benefit, required_fields, {"benefit_type_id": "benefit_type"}
    )
    issues += check_codependent_fields(
        benefit_path,
        benefit,
        "benefit_amount_dollars",
        "benefit_amount_frequency_id",
        {"benefit_amount_frequency_id": "benefit_amount_frequency"},
    )

    start_date = benefit.benefit_start_date
    start_date_path = f"{benefit_path}.benefit_start_date"
    end_date = benefit.benefit_end_date
    end_date_path = f"{benefit_path}.benefit_end_date"
    issues += check_date_range(
        start_date, start_date_path, end_date, end_date_path, PFML_PROGRAM_LAUNCH_DATE
    )

    return issues


def get_other_incomes_issues(application: Application) -> List[Issue]:
    issues = []

    if application.has_other_incomes and len(list(application.other_incomes)) == 0:
        issues.append(
            Issue(
                type=IssueType.required,
                rule=IssueRule.conditional,
                message="when has_other_incomes is true, other_incomes cannot be empty",
                field="other_incomes",
            )
        )
    else:
        for index, income in enumerate(application.other_incomes, 0):
            issues += get_other_income_issues(income, index)

    return issues


def get_other_income_issues(income: OtherIncome, index: int) -> List[Issue]:
    income_path = f"other_incomes[{index}]"
    issues = []

    required_fields = [
        "income_end_date",
        "income_start_date",
        "income_type_id",
    ]
    issues += check_required_fields(
        income_path, income, required_fields, {"income_type_id": "income_type"}
    )
    issues += check_codependent_fields(
        income_path,
        income,
        "income_amount_dollars",
        "income_amount_frequency_id",
        {"income_amount_frequency_id": "income_amount_frequency"},
    )

    start_date = income.income_start_date
    start_date_path = f"{income_path}.income_start_date"
    end_date = income.income_end_date
    end_date_path = f"{income_path}.income_end_date"
    issues += check_date_range(
        start_date, start_date_path, end_date, end_date_path, PFML_PROGRAM_LAUNCH_DATE
    )

    return issues


def get_concurrent_leave_issues(application: Application) -> List[Issue]:
    issues = []

    if application.has_concurrent_leave and application.concurrent_leave:
        concurrent_leave = application.concurrent_leave
        issues += check_date_range(
            concurrent_leave.leave_start_date,
            "concurrent_leave.leave_start_date",
            concurrent_leave.leave_end_date,
            "concurrent_leave.leave_end_date",
            PFML_PROGRAM_LAUNCH_DATE,
        )

        required_fields = [
            "leave_start_date",
            "leave_end_date",
            "is_for_current_employer",
        ]

        issues += check_required_fields(
            "concurrent_leave", application.concurrent_leave, required_fields
        )
    else:
        if application.has_concurrent_leave and not application.concurrent_leave:
            issues.append(
                Issue(
                    type=IssueType.required,
                    rule=IssueRule.conditional,
                    message="when has_concurrent_leave is true, concurrent_leave must be present",
                    field="concurrent_leave",
                )
            )
        else:
            if not application.has_concurrent_leave and application.concurrent_leave:
                issues.append(
                    Issue(
                        type=IssueType.required,
                        rule=IssueRule.conditional,
                        message="when has_concurrent_leave is false, concurrent_leave must be null",
                        field="concurrent_leave",
                    )
                )

    return issues


def get_previous_leaves_other_reason_issues(application: Application) -> List[Issue]:
    issues = []

    if (
        application.has_previous_leaves_other_reason
        and len(list(application.previous_leaves_other_reason)) == 0
    ):
        issues.append(
            Issue(
                type=IssueType.required,
                rule=IssueRule.conditional,
                message="when has_previous_leaves_other_reason is true, previous_leaves_other_reason cannot be empty",
                field="previous_leaves_other_reason",
            )
        )
    else:
        for index, leave in enumerate(application.previous_leaves_other_reason, 0):
            issues += get_previous_leave_issues(leave, f"previous_leaves_other_reason[{index}]")

    return issues


def get_previous_leaves_same_reason_issues(application: Application) -> List[Issue]:
    issues = []

    if (
        application.has_previous_leaves_same_reason
        and len(list(application.previous_leaves_same_reason)) == 0
    ):
        issues.append(
            Issue(
                type=IssueType.required,
                rule=IssueRule.conditional,
                message="when has_previous_leaves_same_reason is true, previous_leaves_same_reason cannot be empty",
                field="previous_leaves_same_reason",
            )
        )
    else:
        for index, leave in enumerate(application.previous_leaves_same_reason, 0):
            issues += get_previous_leave_issues(leave, f"previous_leaves_same_reason[{index}]")

    return issues


def get_previous_leave_issues(leave: PreviousLeave, leave_path: str) -> List[Issue]:
    issues = []

    required_fields = [
        "leave_start_date",
        "leave_end_date",
        "is_for_current_employer",
        "leave_reason_id",
        "leave_minutes",
        "worked_per_week_minutes",
    ]
    issues += check_required_fields(
        leave_path, leave, required_fields, {"leave_reason_id": "leave_reason"}
    )

    if leave.worked_per_week_minutes and leave.worked_per_week_minutes > MAX_MINUTES_IN_WEEK:
        issues.append(
            Issue(
                type=IssueType.maximum,
                message=f"Minutes worked per week cannot exceed {MAX_MINUTES_IN_WEEK}",
                field=f"{leave_path}.worked_per_week_minutes",
            )
        )

    start_date = leave.leave_start_date
    start_date_path = f"{leave_path}.leave_start_date"
    end_date = leave.leave_end_date
    end_date_path = f"{leave_path}.leave_end_date"
    issues += check_date_range(
        start_date, start_date_path, end_date, end_date_path, minimum_date=PFML_PROGRAM_LAUNCH_DATE,
    )

    return issues


def get_conditional_issues(application: Application, headers: Headers) -> List[Issue]:
    issues = []
    # TODO (CP-1674): This condition is temporary. It can be removed once we
    # can safely enforce these validation rules across all in-progress claims
    require_other_leaves_fields = (
        headers.get("X-FF-Require-Other-Leaves", None) and not application.submitted_time
    )

    # Fields involved in Part 1 of the progressive application
    if application.has_state_id and not application.mass_id:
        issues.append(
            Issue(
                type=IssueType.required,
                rule=IssueRule.conditional,
                message="mass_id is required if has_mass_id is set",
                field="mass_id",
            )
        )

    if application.residential_address:
        issues += get_address_issues(application, "residential_address")

    if application.mailing_address:
        issues += get_address_issues(application, "mailing_address")
    elif not application.mailing_address and application.has_mailing_address:
        issues.append(
            Issue(
                type=IssueType.required,
                rule=IssueRule.conditional,
                message="mailing_address is required if has_mailing_address is set",
                field="mailing_address",
            )
        )

    if application.leave_reason_id in [
        LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_id,
        LeaveReason.PREGNANCY_MATERNITY.leave_reason_id,
    ]:
        issues += get_medical_leave_issues(application)

    if application.leave_reason_id == LeaveReason.CHILD_BONDING.leave_reason_id:
        issues += get_bonding_leave_issues(application)

    if (
        application.leave_reason_id == LeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_id
        and application.caring_leave_metadata
    ):
        issues += get_caring_leave_issues(application)

    if application.employer_notified:
        if not application.employer_notification_date:
            issues.append(
                Issue(
                    type=IssueType.required,
                    rule=IssueRule.conditional,
                    message="employer_notification_date is required for leave_details if employer_notified is set",
                    field="leave_details.employer_notification_date",
                )
            )
        elif application.employer_notification_date < date.today() - relativedelta(years=2):
            issues.append(
                Issue(
                    type=IssueType.minimum,
                    rule=IssueRule.conditional,
                    message="employer_notification_date year must be within the past 2 years",
                    field="leave_details.employer_notification_date",
                )
            )

    if application.work_pattern:
        issues += get_work_pattern_issues(application)

    if (
        application.employment_status_id
        and not application.employer_fein
        and (
            application.employment_status_id
            in [
                EmploymentStatus.EMPLOYED.employment_status_id,
                # TODO (CP-1176): Uncomment the below line to require FEIN for unemployed claimants
                # EmploymentStatus.UNEMPLOYED.employment_status_id,
            ]
        )
    ):
        issues.append(
            Issue(
                type=IssueType.required,
                rule=IssueRule.conditional,
                # TODO (CP-1176): Update the error message to include Unemployed
                message="employer_fein is required if employment_status is Employed",
                field="employer_fein",
            )
        )

    if (
        application.employment_status_id == EmploymentStatus.EMPLOYED.employment_status_id
        and not application.employer_notified
    ):
        issues.append(
            Issue(
                # `field` is intentionally excluded since this is a submission rule, rather than field rule
                type=IssueType.required,
                rule=IssueRule.require_employer_notified,
                message="employer_notified must be True if employment_status is Employed",
            )
        )

    if application.other_incomes_awaiting_approval:
        if application.has_other_incomes is None:
            issues.append(
                Issue(
                    type=IssueType.required,
                    rule=IssueRule.conditional,
                    message="has_other_incomes must be set if other_incomes_awaiting_approval is set",
                    field="has_other_incomes",
                )
            )
        elif application.has_other_incomes:
            issues.append(
                Issue(
                    type=IssueType.conflicting,
                    rule=IssueRule.disallow_has_other_incomes_when_awaiting_approval,
                    message="has_other_incomes must be false if other_incomes_awaiting_approval is set",
                    field="has_other_incomes",
                )
            )

    issues += get_employer_benefits_issues(application)
    issues += get_other_incomes_issues(application)

    issues += get_previous_leaves_other_reason_issues(application)
    issues += get_previous_leaves_same_reason_issues(application)

    issues += get_concurrent_leave_issues(application)

    if require_other_leaves_fields:
        # TODO (CP-1674): Move these rules into the "always required" set once the
        # X-FF-Require-Other-Leaves header is obsolete.
        for field in ["has_employer_benefits", "has_other_incomes"]:
            val = deepgetattr(application, field)
            if val is None:
                issues.append(
                    Issue(type=IssueType.required, message=f"{field} is required", field=field,)
                )

    # Fields involved in Part 3 of the progressive application
    # TODO: (API-515) Document and certification validations can be called here

    return issues


def get_medical_leave_issues(application: Application) -> List[Issue]:
    issues = []
    if application.pregnant_or_recent_birth is None:
        issues.append(
            Issue(
                type=IssueType.required,
                rule=IssueRule.conditional,
                message="It is required to indicate if there has been a recent pregnancy or birth when medical leave is requested, regardless of if it is related to the leave request",
                field="leave_details.pregnant_or_recent_birth",
            )
        )
    return issues


QUALIFIER_IDS_FOR_BONDING = [
    LeaveReasonQualifier.NEWBORN.leave_reason_qualifier_id,
    LeaveReasonQualifier.ADOPTION.leave_reason_qualifier_id,
    LeaveReasonQualifier.FOSTER_CARE.leave_reason_qualifier_id,
]


def get_bonding_leave_issues(application: Application) -> List[Issue]:
    issues = []

    # This is here for now to consolidate cross-field validation but can be moved to the openapi.yml if this file becomes too unwieldy
    if application.leave_reason_qualifier_id not in QUALIFIER_IDS_FOR_BONDING:
        issues.append(
            Issue(
                type=IssueType.required,
                rule=IssueRule.conditional,
                message="Invalid leave reason qualifier for bonding leave type",
                field="leave_details.reason_qualifier",
            )
        )
    if (
        application.leave_reason_qualifier_id
        == LeaveReasonQualifier.NEWBORN.leave_reason_qualifier_id
    ) and not application.child_birth_date:
        issues.append(
            Issue(
                type=IssueType.required,
                rule=IssueRule.conditional,
                message="Child birth date is required for newborn bonding leave",
                field="leave_details.child_birth_date",
            )
        )
    if (
        application.leave_reason_qualifier_id
        in [
            LeaveReasonQualifier.ADOPTION.leave_reason_qualifier_id,
            LeaveReasonQualifier.FOSTER_CARE.leave_reason_qualifier_id,
        ]
    ) and not application.child_placement_date:
        issues.append(
            Issue(
                type=IssueType.required,
                rule=IssueRule.conditional,
                message="Child placement date is required for foster or adoption bonding leave",
                field="leave_details.child_placement_date",
            )
        )
    return issues


def get_caring_leave_issues(application: Application) -> List[Issue]:
    issues = []

    required_fields = [
        "family_member_first_name",
        "family_member_last_name",
        "family_member_date_of_birth",
        "relationship_to_caregiver",
    ]
    issues += check_required_fields(
        "leave_details.caring_leave_metadata", application.caring_leave_metadata, required_fields
    )

    return issues


def get_payments_issues(application: Application) -> List[Issue]:
    issues = []

    if not application.payment_preference.payment_method_id:
        issues.append(
            Issue(
                type=IssueType.required,
                message="Payment method is required",
                field="payment_preference.payment_method",
            )
        )
        return issues

    if application.payment_preference.payment_method_id == PaymentMethod.ACH.payment_method_id:
        if not application.payment_preference.account_number:
            issues.append(
                Issue(
                    type=IssueType.required,
                    rule=IssueRule.conditional,
                    message="Account number is required for direct deposit",
                    field="payment_preference.account_number",
                )
            )
        if not application.payment_preference.routing_number:
            issues.append(
                Issue(
                    type=IssueType.required,
                    rule=IssueRule.conditional,
                    message="Routing number is required for direct deposit",
                    field="payment_preference.routing_number",
                )
            )
        elif not validate_routing_number(application.payment_preference.routing_number):
            issues.append(
                Issue(
                    type=IssueType.checksum,
                    message="Routing number is invalid",
                    field="payment_preference.routing_number",
                )
            )

        if not application.payment_preference.bank_account_type_id:
            issues.append(
                Issue(
                    type=IssueType.required,
                    rule=IssueRule.conditional,
                    message="Account type is required for direct deposit",
                    field="payment_preference.bank_account_type",
                )
            )

    return issues


# This maps the required field name in the DB to its equivalent in the API
# Because the DB schema and the API schema differ
ALWAYS_REQUIRED_FIELDS_DB_NAME_TO_API_NAME_MAP = {
    "date_of_birth": "date_of_birth",
    "first_name": "first_name",
    "employment_status_id": "employment_status",
    "employer_notified": "leave_details.employer_notified",
    "has_continuous_leave_periods": "has_continuous_leave_periods",
    "has_intermittent_leave_periods": "has_intermittent_leave_periods",
    "has_mailing_address": "has_mailing_address",
    "has_reduced_schedule_leave_periods": "has_reduced_schedule_leave_periods",
    "has_state_id": "has_state_id",
    "hours_worked_per_week": "hours_worked_per_week",
    "last_name": "last_name",
    "leave_reason_id": "leave_details.reason",
    "phone.phone_number": "phone.phone_number",  # TODO (CP-1467): phone_number here includes the int_code from the request, but int_code will eventually be removed
    "phone.phone_type_id": "phone.phone_type",
    "residential_address": "residential_address",
    "tax_identifier": "tax_identifier",
    "work_pattern.work_pattern_type_id": "work_pattern.work_pattern_type",
}


def get_always_required_issues(application: Application) -> List[Issue]:
    issues = []
    for (field, openapi_field) in ALWAYS_REQUIRED_FIELDS_DB_NAME_TO_API_NAME_MAP.items():
        val = deepgetattr(application, field)
        if val is None:
            issues.append(
                Issue(
                    type=IssueType.required,
                    message=f"{openapi_field} is required",
                    field=openapi_field,
                )
            )

    return issues


def get_leave_periods_issues(application: Application) -> List[Issue]:
    issues = []

    issues += get_continuous_leave_issues(application.continuous_leave_periods)
    issues += get_intermittent_leave_issues(application.intermittent_leave_periods)
    issues += get_reduced_schedule_leave_issues(application)
    issues += get_leave_period_ranges_issues(application)

    if not any(
        [
            application.continuous_leave_periods,
            application.intermittent_leave_periods,
            application.reduced_schedule_leave_periods,
        ]
    ):
        issues.append(
            Issue(
                message="At least one leave period should be entered",
                rule=IssueRule.min_leave_periods,
                type=IssueType.required,
            )
        )

    if application.intermittent_leave_periods and (
        application.continuous_leave_periods or application.reduced_schedule_leave_periods
    ):
        issues.append(
            Issue(
                message="Intermittent leave cannot be taken alongside Continuous or Reduced Schedule leave",
                rule=IssueRule.disallow_hybrid_intermittent_leave,
                type=IssueType.conflicting,
            )
        )

    return issues


def get_leave_period_ranges_issues(application: Application) -> List[Issue]:
    """Validate all leave period date ranges against each other"""
    issues = []

    all_leave_periods: Iterable[
        Union[ContinuousLeavePeriod, IntermittentLeavePeriod, ReducedScheduleLeavePeriod]
    ] = list(
        chain(
            application.continuous_leave_periods,
            application.intermittent_leave_periods,
            application.reduced_schedule_leave_periods,
        )
    )

    leave_period_start_dates = [
        leave_period.start_date for leave_period in all_leave_periods if leave_period.start_date
    ]
    leave_period_end_dates = [
        leave_period.end_date for leave_period in all_leave_periods if leave_period.end_date
    ]

    leave_period_ranges = [
        (leave_period.start_date, leave_period.end_date)
        for leave_period in all_leave_periods
        # Only store complete ranges
        if leave_period.start_date and leave_period.end_date
    ]
    leave_period_ranges.sort()

    # Prevent submission too far in advance
    earliest_start_date = min(leave_period_start_dates, default=None)
    latest_end_date = max(leave_period_end_dates, default=None)

    if (
        earliest_start_date is not None
        and (earliest_start_date - date.today()).days > MAX_DAYS_IN_ADVANCE_TO_SUBMIT
    ):
        issues.append(
            Issue(
                message=f"Can't submit application more than {MAX_DAYS_IN_ADVANCE_TO_SUBMIT} days in advance of the earliest leave period",
                rule=IssueRule.disallow_submit_over_60_days_before_start_date,
            )
        )

    # Prevent leave that exceed 12 months
    if (
        earliest_start_date is not None
        and latest_end_date is not None
        and (latest_end_date - earliest_start_date).days > MAX_DAYS_IN_LEAVE_PERIOD_RANGE
    ):
        issues.append(
            Issue(
                message=f"Leave cannot exceed {MAX_DAYS_IN_LEAVE_PERIOD_RANGE} days",
                rule=IssueRule.disallow_12mo_leave_period,
            )
        )

    # Prevent overlapping leave periods, which FINEOS will fail on
    for ([start_date_1, end_date_1], [start_date_2, end_date_2]) in combinations(
        leave_period_ranges, 2
    ):
        if start_date_2 <= end_date_1:
            issues.append(
                Issue(
                    message=f"Leave period ranges cannot overlap. Received {start_date_1.isoformat()} – {end_date_1.isoformat()} and {start_date_2.isoformat()} – {end_date_2.isoformat()}.",
                    rule=IssueRule.disallow_overlapping_leave_periods,
                    type=IssueType.conflicting,
                )
            )

    return issues


def get_leave_period_date_issues(
    leave_period: Union[ContinuousLeavePeriod, IntermittentLeavePeriod, ReducedScheduleLeavePeriod],
    leave_period_path: str,
    leave_period_type: str,
) -> List[Issue]:
    """Validate an individual leave period's start and end dates"""
    issues = []
    end_date = getattr(leave_period, "end_date", None)
    start_date = getattr(leave_period, "start_date", None)

    if start_date and start_date < PFML_PROGRAM_LAUNCH_DATE:
        issues.append(
            Issue(
                type=IssueType.minimum,
                message="start_date cannot be in a year earlier than 2021",
                field=f"{leave_period_path}.start_date",
            )
        )

    if start_date and end_date and start_date > end_date:
        issues.append(
            Issue(
                type=IssueType.minimum,
                message="end_date cannot be earlier than the start_date",
                field=f"{leave_period_path}.end_date",
            )
        )

    # Prevent leave that exceed 12 months
    if (
        start_date is not None
        and end_date is not None
        and (end_date - start_date).days > MAX_DAYS_IN_LEAVE_PERIOD_RANGE
    ):
        issues.append(
            Issue(
                message=f"Leave cannot exceed {MAX_DAYS_IN_LEAVE_PERIOD_RANGE} days",
                rule=getattr(IssueRule, f"disallow_12mo_{leave_period_type}_leave_period"),
            )
        )

    return issues


def get_continuous_leave_issues(leave_periods: Iterable[ContinuousLeavePeriod]) -> List[Issue]:
    issues = []
    required_leave_period_fields = [
        "end_date",
        "start_date",
    ]

    for i, current_period in enumerate(leave_periods):
        leave_period_path = f"leave_details.continuous_leave_periods[{i}]"
        issues += get_leave_period_date_issues(current_period, leave_period_path, "continuous")

        for field in required_leave_period_fields:
            val = getattr(current_period, field, None)

            if val is None:
                issues.append(
                    Issue(
                        type=IssueType.required,
                        message=f"{field} is required",
                        field=f"{leave_period_path}.{field}",
                    )
                )

    return issues


def get_intermittent_leave_issues(leave_periods: Iterable[IntermittentLeavePeriod]) -> List[Issue]:
    issues = []
    required_leave_period_fields = [
        "duration",
        "duration_basis",
        "end_date",
        "frequency",
        "frequency_interval",
        "frequency_interval_basis",
        "start_date",
    ]

    for i, current_period in enumerate(leave_periods):
        leave_period_path = f"leave_details.intermittent_leave_periods[{i}]"
        issues += get_leave_period_date_issues(current_period, leave_period_path, "intermittent")

        for field in required_leave_period_fields:
            val = getattr(current_period, field, None)

            if val is None:
                issues.append(
                    Issue(
                        type=IssueType.required,
                        message=f"{field} is required",
                        field=f"{leave_period_path}.{field}",
                    )
                )

        if (
            current_period.duration_basis == DurationBasis.hours.value
            and (current_period.duration or 0) >= 24
        ):
            issues.append(
                Issue(
                    type=IssueType.intermittent_duration_hours_maximum,
                    message=f"{leave_period_path}.duration must be less than 24 if the duration_basis is hours",
                    field=f"{leave_period_path}.duration",
                )
            )

        if (
            current_period.duration is not None
            and current_period.duration_basis is not None
            and current_period.frequency is not None
            and current_period.frequency_interval is not None
            and current_period.frequency_interval_basis is not None
            and current_period.start_date is not None
            and current_period.end_date is not None
            and current_period.end_date > current_period.start_date
        ):
            days_in_leave = (current_period.end_date - current_period.start_date).days + 1

            days_in_frequency_interval_basis = {
                FrequencyIntervalBasis.days.value: 1,
                FrequencyIntervalBasis.weeks.value: 7,
                FrequencyIntervalBasis.months.value: 30,
            }[current_period.frequency_interval_basis]
            # e.g. every 6 (frequency_interval) weeks (frequency_interval_basis) = 6 * 7 = 42
            days_in_request_interval = (
                current_period.frequency_interval * days_in_frequency_interval_basis
            )

            if days_in_request_interval > days_in_leave:
                issues.append(
                    Issue(
                        type=IssueType.intermittent_interval_maximum,
                        message="the total days in the interval (frequency_interval * the number of days in frequency_interval_basis) cannot exceed the total days between the start and end dates of the leave period",
                        field=f"{leave_period_path}.frequency_interval_basis",
                    )
                )

            if current_period.duration_basis == DurationBasis.days.value:
                # e.g. 3 days (duration) 2 times (frequency) per week = 3 * 2 = 6
                days_requested_per_interval = current_period.duration * current_period.frequency

                if days_requested_per_interval > days_in_request_interval:
                    issues.append(
                        Issue(
                            type=IssueType.days_absent_per_intermittent_interval_maximum,
                            message="The total days absent per interval (frequency * duration) cannot exceed the total days in the interval",
                            field=f"{leave_period_path}.duration",
                        )
                    )

    return issues


def get_reduced_schedule_leave_issues(application: Application) -> List[Issue]:
    """Validate required fields are present for each reduced schedule leave period
    and validate that the amount of minutes entered are within a valid range, in
    comparison to the work pattern entered.
    """

    leave_periods = application.reduced_schedule_leave_periods
    issues = []

    required_leave_period_fields = [
        "end_date",
        "start_date",
    ]

    for i, current_period in enumerate(leave_periods):
        leave_period_path = f"leave_details.reduced_schedule_leave_periods[{i}]"
        issues += get_leave_period_date_issues(current_period, leave_period_path, "reduced")
        issues += get_reduced_schedule_leave_minutes_issues(
            current_period, leave_period_path, application
        )

        for field in required_leave_period_fields:
            val = getattr(current_period, field, None)

            if val is None:
                issues.append(
                    Issue(
                        type=IssueType.required,
                        message=f"{field} is required",
                        field=f"{leave_period_path}.{field}",
                    )
                )

    return issues


def get_reduced_schedule_leave_minutes_issues(
    leave_period: ReducedScheduleLeavePeriod, leave_period_path: str, application: Application
) -> List[Issue]:
    """Validate the *_off_minutes fields of a reduced leave period
    """

    issues = []
    # These fields should be ordered in the same order as DayOfWeek (Sunday–Saturday)
    minute_fields = [
        "sunday_off_minutes",
        "monday_off_minutes",
        "tuesday_off_minutes",
        "wednesday_off_minutes",
        "thursday_off_minutes",
        "friday_off_minutes",
        "saturday_off_minutes",
    ]
    minutes_each_day = [getattr(leave_period, field, None) or 0 for field in minute_fields]

    # *_off_minutes fields individually have a minimum of 0, through the OpenAPI spec
    if sum(minutes_each_day) <= 0:
        issues.append(
            Issue(
                type=IssueType.minimum,
                message="Reduced leave minutes must be greater than 0",
                rule=IssueRule.min_reduced_leave_minutes,
            )
        )
    else:
        # We only check if all minute fields are set when the min_reduced_leave_minutes rule
        # is fulfilled. If that rule is not fulfilled, it means all fields are empty or set to 0.
        # We don't want to show the min_reduced_leave_minutes issue alongside the following issues
        # because this is a confusing user experience when these fields are gathered through a
        # single field, which is the user experience when someone works a variable work schedule.
        # For that scenario, the min_reduced_leave_minutes issue is all that's needed.
        for field in minute_fields:
            val = getattr(leave_period, field, None)

            if val is None:
                issues.append(
                    Issue(
                        type=IssueType.required,
                        message=f"{field} is required",
                        field=f"{leave_period_path}.{field}",
                    )
                )

    if application.work_pattern:
        work_pattern_days = application.work_pattern.work_pattern_days

        # There should only ever be one week of days since the length is validated in validate_work_pattern_days
        if len(minute_fields) == len(list(work_pattern_days)):
            work_pattern_minutes_each_day = [day.minutes for day in work_pattern_days]

            for field, work_pattern_minutes in zip(minute_fields, work_pattern_minutes_each_day):
                leave_period_minutes: int = getattr(leave_period, field, None) or 0
                if work_pattern_minutes is not None and leave_period_minutes > work_pattern_minutes:
                    issues.append(
                        Issue(
                            type=IssueType.maximum,
                            message=f"{field} cannot exceed the work pattern minutes for the same day, which is {work_pattern_minutes}",
                            field=f"{leave_period_path}.{field}",
                        )
                    )

    return issues


def get_work_pattern_issues(application: Application) -> List[Issue]:
    issues = []

    minutes_each_day = [day.minutes or 0 for day in application.work_pattern.work_pattern_days]

    if sum(minutes_each_day) <= 0:
        issues.append(
            Issue(
                type=IssueType.minimum,
                field="work_pattern.work_pattern_days",
                message="Total minutes for a work pattern must be greater than 0",
            )
        )
    else:
        # We only check if all minute fields are set when the total minutes are greater than 0
        # which indicates that all fields are empty or set to 0. For that scenario,
        # validating minimum total minutes for the work pattern is all that's needed.
        for i, day in enumerate(application.work_pattern.work_pattern_days):
            if day.minutes is None:
                issues.append(
                    Issue(
                        type=IssueType.required,
                        message=f"work_pattern.work_pattern_days[{i}].minutes is required",
                        field=f"work_pattern.work_pattern_days[{i}].minutes",
                    )
                )
            elif day.minutes > 24 * 60:
                issues.append(
                    Issue(
                        type=IssueType.maximum,
                        message="Total minutes in a work pattern week must be less than a day (1440 minutes)",
                        field=f"work_pattern.work_pattern_days[{i}].minutes",
                    )
                )

    return issues


def validate_application_state(
    existing_application: Application, db_session: db.Session
) -> List[Issue]:
    """
        Utility method for validating an application's state in the entire system is valid
        Currently the only check is one to potentially catch fraud where an SSN is being used
        with multiple email addresses.
    """
    issues = []

    # We consider an application potentially fraudulent if another application exists that:
    #   Has the same tax identifier
    #   Has a different user
    application = (
        db_session.query(Application).filter(
            Application.tax_identifier_id == existing_application.tax_identifier_id,
            Application.application_id != existing_application.application_id,
            Application.user_id != existing_application.user_id,
        )
    ).first()

    # This may be a case of fraud if any application was returned.
    # Add an issue, the portal will display information indicating
    # the user should reach out to the contact center for additional assistance.
    if application:
        issues.append(
            Issue(message="Request by current user not allowed", rule=IssueRule.disallow_attempts,)
        )

    return issues
