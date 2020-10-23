from typing import Iterable, List, Optional

from massgov.pfml.api.services.applications import (
    ContinuousLeavePeriod,
    IntermittentLeavePeriod,
    ReducedScheduleLeavePeriod,
)
from massgov.pfml.api.util.response import Issue, IssueRule, IssueType
from massgov.pfml.db.models.applications import (
    Application,
    EmploymentStatus,
    LeaveReasonQualifier,
    LeaveType,
    WorkPatternType,
)
from massgov.pfml.db.models.employees import PaymentType


def get_application_issues(application: Application) -> Optional[List[Issue]]:
    """Takes in application and outputs any validation issues.
    These issues are either fields that are always required for an application or fields that are conditionally required based on previous input
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

    if (
        application.employer_notified is None
        and application.employment_status_id is EmploymentStatus.EMPLOYED.employment_status_id
    ):
        issues.append(
            Issue(
                type=IssueType.required,
                rule=IssueRule.conditional,
                message="leave_details.employer_notified is required if employment_status is set to Employed",
                field="leave_details.employer_notified",
            )
        )

    if application.leave_type and (
        application.leave_type.leave_type_id == LeaveType.MEDICAL_LEAVE.leave_type_id
    ):
        issues += get_medical_leave_issues(application)

    if application.leave_type and (
        application.leave_type.leave_type_id == LeaveType.BONDING_LEAVE.leave_type_id
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

    # Fields involved in Part 2 of the progressive application
    if application.payment_preferences:
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
    for i, preference in enumerate(application.payment_preferences):
        if preference.payment_type_id == PaymentType.ACH.payment_type_id:
            if not preference.account_number:
                issues.append(
                    Issue(
                        type=IssueType.required,
                        rule=IssueRule.conditional,
                        message="Account number is required for direct deposit",
                        field=f"payment_preferences[{i}].account_details.account_number",
                    )
                )
            if not preference.routing_number:
                issues.append(
                    Issue(
                        type=IssueType.required,
                        rule=IssueRule.conditional,
                        message="Routing number is required for direct deposit",
                        field=f"payment_preferences[{i}].account_details.routing_number",
                    )
                )
            if not preference.type_of_account:
                issues.append(
                    Issue(
                        type=IssueType.required,
                        rule=IssueRule.conditional,
                        message="Account type is required for direct deposit",
                        field=f"payment_preferences[{i}].account_details.account_type",
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
    issues += get_reduced_schedule_leave_issues(application.reduced_schedule_leave_periods)

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


def get_continuous_leave_issues(leave_periods: Iterable[ContinuousLeavePeriod]) -> List[Issue]:
    issues = []

    for i, current_period in enumerate(leave_periods):
        if not current_period.start_date:
            issues.append(
                Issue(
                    type=IssueType.required,
                    message=f"Start date is required for continuous_leave_periods[{i}]",
                    field=f"leave_details.continuous_leave_periods[{i}].start_date",
                )
            )
        if not current_period.end_date:
            issues.append(
                Issue(
                    type=IssueType.required,
                    message=f"End date is required for continuous_leave_periods[{i}]",
                    field=f"leave_details.continuous_leave_periods[{i}].end_date",
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
        "frequency_interval_basis",
        "start_date",
    ]

    for i, current_period in enumerate(leave_periods):
        for field in required_leave_period_fields:
            val = getattr(current_period, field, None)

            if val is None:
                issues.append(
                    Issue(
                        type=IssueType.required,
                        message=f"{field} is required",
                        field=f"leave_details.intermittent_leave_periods[{i}].{field}",
                    )
                )

    return issues


def get_reduced_schedule_leave_issues(
    leave_periods: Iterable[ReducedScheduleLeavePeriod],
) -> List[Issue]:
    issues = []

    for i, current_period in enumerate(leave_periods):
        if not current_period.start_date:
            issues.append(
                Issue(
                    type=IssueType.required,
                    message=f"Start date is required for reduced_schedule_leave_periods[{i}]",
                    field=f"leave_details.reduced_schedule_leave_periods[{i}].start_date",
                )
            )
        if not current_period.end_date:
            issues.append(
                Issue(
                    type=IssueType.required,
                    message=f"End date is required for reduced_schedule_leave_periods[{i}]",
                    field=f"leave_details.reduced_schedule_leave_periods[{i}].end_date",
                )
            )
    return issues


def get_work_pattern_issues(application: Application) -> List[Issue]:
    issues = []

    work_pattern = application.work_pattern

    if (
        work_pattern.work_pattern_type_id == WorkPatternType.ROTATING.work_pattern_type_id
        and work_pattern.pattern_start_date is None
    ):
        issues.append(
            Issue(
                type=IssueType.required,
                message="Pattern start date is required for rotating work patterns",
                field="work_pattern.pattern_start_date",
            )
        )

    if (
        work_pattern.work_pattern_type_id != WorkPatternType.ROTATING.work_pattern_type_id
        and work_pattern.pattern_start_date is not None
    ):
        issues.append(
            Issue(
                type=IssueType.conflicting,
                message="Pattern start date is not expected for fixed or variable work patterns.",
                field="work_pattern.pattern_start_date",
            )
        )

    if len(list(work_pattern.work_pattern_days)) == 0:
        issues.append(
            Issue(
                type=IssueType.required,
                message="Work patterns days are required",
                field="work_pattern.work_pattern_days",
            )
        )

    return issues
