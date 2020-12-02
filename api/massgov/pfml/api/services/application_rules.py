from datetime import date
from itertools import chain, combinations
from typing import Iterable, List, Optional, Union

import massgov.pfml.db as db
from massgov.pfml.api.services.applications import (
    ContinuousLeavePeriod,
    IntermittentLeavePeriod,
    ReducedScheduleLeavePeriod,
)
from massgov.pfml.api.util.response import Issue, IssueRule, IssueType
from massgov.pfml.db.models.applications import (
    Application,
    EmploymentStatus,
    LeaveReason,
    LeaveReasonQualifier,
)
from massgov.pfml.db.models.employees import PaymentMethod

PFML_PROGRAM_LAUNCH_DATE = date(2021, 1, 1)
MAX_DAYS_IN_ADVANCE_TO_SUBMIT = 60
MAX_DAYS_IN_LEAVE_PERIOD_RANGE = 364


def get_application_issues(application: Application) -> Optional[List[Issue]]:
    """Takes in application and outputs any validation issues.
    These issues are either fields that are always required for an application or fields that are conditionally required based on previous input.
    """
    issues = []
    issues += get_always_required_issues(application)
    issues += get_leave_periods_issues(application)
    issues += get_conditional_issues(application)

    if len(issues) == 0:
        return None
    else:
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


def get_employer_benefits_issues(application: Application) -> List[Issue]:
    employer_benefit_fields = [
        "benefit_amount_dollars",
        "benefit_amount_frequency",
        "benefit_end_date",
        "benefit_start_date",
        "benefit_type",
    ]
    issues = []

    for index, benefit in enumerate(application.employer_benefits, 0):
        for field in employer_benefit_fields:
            val = getattr(benefit, field)
            if val is None:
                field_name = f"employer_benefits[{index}].{field}"
                issues.append(
                    Issue(
                        type=IssueType.required,
                        message=f"{field_name} is required",
                        field=field_name,
                    )
                )

    return issues


def get_other_incomes_issues(application: Application) -> List[Issue]:
    other_income_fields = [
        "income_amount_dollars",
        "income_amount_frequency",
        "income_end_date",
        "income_start_date",
        "income_type",
    ]
    issues = []

    for index, income in enumerate(application.other_incomes, 0):
        for field in other_income_fields:
            val = getattr(income, field)
            if val is None:
                field_name = f"other_incomes[{index}].{field}"
                issues.append(
                    Issue(
                        type=IssueType.required,
                        message=f"{field_name} is required",
                        field=field_name,
                    )
                )

    return issues


def get_conditional_issues(application: Application) -> List[Issue]:
    issues = []

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

    if application.leave_reason and (
        application.leave_reason.leave_reason_id
        in [
            LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_id,
            LeaveReason.PREGNANCY_MATERNITY.leave_reason_id,
        ]
    ):
        issues += get_medical_leave_issues(application)

    if application.leave_reason and (
        application.leave_reason.leave_reason_id == LeaveReason.CHILD_BONDING.leave_reason_id
    ):
        issues += get_bonding_leave_issues(application)

    if application.employer_notified and not application.employer_notification_date:
        issues.append(
            Issue(
                type=IssueType.required,
                rule=IssueRule.conditional,
                message="employer_notification_date is required for leave_details if employer_notified is set",
                field="leave_details.employer_notification_date",
            )
        )

    if application.work_pattern:
        issues += get_work_pattern_issues(application)

    if (
        application.employment_status
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

    if application.employer_benefits:
        issues += get_employer_benefits_issues(application)

    if application.other_incomes:
        issues += get_other_incomes_issues(application)

    # Fields involved in Part 2 of the progressive application
    if application.payment_preference:
        issues += get_payments_issues(application)

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


def get_payments_issues(application: Application) -> List[Issue]:
    issues = []
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
        if not application.payment_preference.bank_account_type:
            issues.append(
                Issue(
                    type=IssueType.required,
                    rule=IssueRule.conditional,
                    message="Account type is required for direct deposit",
                    field="payment_preference.bank_account_type",
                )
            )

    return issues


def deepgetattr(obj, attr):
    """Recurses through an attribute chain to get the ultimate value."""
    fields = attr.split(".")
    value = obj

    for field in fields:
        # Bail at the first instance where a field is empty
        if value is None:
            return None
        else:
            value = getattr(value, field, None)

    return value


# This maps the required field name in the DB to its equivalent in the API
# Because the DB schema and the API schema differ
ALWAYS_REQUIRED_FIELDS_DB_NAME_TO_API_NAME_MAP = {
    "date_of_birth": "date_of_birth",
    "first_name": "first_name",
    "employment_status": "employment_status",
    "employer_notified": "leave_details.employer_notified",
    "has_continuous_leave_periods": "has_continuous_leave_periods",
    "has_intermittent_leave_periods": "has_intermittent_leave_periods",
    "has_mailing_address": "has_mailing_address",
    "has_reduced_schedule_leave_periods": "has_reduced_schedule_leave_periods",
    "has_state_id": "has_state_id",
    "hours_worked_per_week": "hours_worked_per_week",
    "last_name": "last_name",
    "leave_reason": "leave_details.reason",
    "residential_address": "residential_address",
    "tax_identifier": "tax_identifier",
    "work_pattern.work_pattern_type": "work_pattern.work_pattern_type",
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

    return issues


def get_continuous_leave_issues(leave_periods: Iterable[ContinuousLeavePeriod]) -> List[Issue]:
    issues = []
    required_leave_period_fields = [
        "end_date",
        "start_date",
    ]

    for i, current_period in enumerate(leave_periods):
        leave_period_path = f"leave_details.continuous_leave_periods[{i}]"
        issues += get_leave_period_date_issues(current_period, leave_period_path)

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
        issues += get_leave_period_date_issues(current_period, leave_period_path)

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
        issues += get_leave_period_date_issues(current_period, leave_period_path)
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
    # These fields should be ordered in the same order as DayOfWeek (Monday–Sunday)
    minute_fields = [
        "monday_off_minutes",
        "tuesday_off_minutes",
        "wednesday_off_minutes",
        "thursday_off_minutes",
        "friday_off_minutes",
        "saturday_off_minutes",
        "sunday_off_minutes",
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
            work_pattern_minutes_each_day = [
                day.minutes
                # TODO (CP-1344): Guarantee the order of work_pattern_days closer to the DB query rather than here
                for day in sorted(work_pattern_days, key=lambda day: day.day_of_week_id)
            ]

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
