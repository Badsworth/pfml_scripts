from functools import reduce
from typing import Iterable, List, Optional

from massgov.pfml.api.services.applications import (
    ContinuousLeavePeriod,
    IntermittentLeavePeriod,
    ReducedScheduleLeavePeriod,
)
from massgov.pfml.api.util.response import Issue, IssueType
from massgov.pfml.db.models.applications import Application, LeaveReasonQualifier, LeaveType
from massgov.pfml.db.models.employees import PaymentType


def get_application_issues(application: Application) -> Optional[List[Issue]]:
    """Takes in application and outputs any validation warnings.
    These warnings are either fields that are always required for an application or fields that are conditionally required based on previous input
    """
    issues = []
    issues += get_always_required_issues(application)
    issues += get_leave_periods_issues(application)
    issues += get_conditional_issues(application)

    if len(issues) == 0:
        return None
    else:
        return issues


def get_conditional_issues(application: Application) -> List[Issue]:
    issues = []

    # Fields involved in Part 1 of the progressive application
    if application.has_state_id and not application.mass_id:
        issues.append(
            Issue(
                type=IssueType.required,
                rule="conditional",
                message="mass_id is required if has_mass_id is set",
                field="mass_id",
            )
        )

    # TODO: (CP-1019) add has_mailing_address conditional constraint here

    if application.leave_type and (
        application.leave_type.leave_type_id == LeaveType.MEDICAL_LEAVE.leave_type_id
    ):
        issues += get_medical_leave_issues(application)

    if application.leave_type and (
        application.leave_type.leave_type_id == LeaveType.BONDING_LEAVE.leave_type_id
    ):
        issues += get_bonding_leave_issues(application)

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
                rule="conditional",
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
                rule="conditional",
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
                rule="conditional",
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
                rule="conditional",
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
                        rule="conditional",
                        message="Account number is required for direct deposit",
                        field=f"payment_preferences[{i}].account_details.account_number",
                    )
                )
            if not preference.routing_number:
                issues.append(
                    Issue(
                        type=IssueType.required,
                        rule="conditional",
                        message="Routing number is required for direct deposit",
                        field=f"payment_preferences[{i}].account_details.routing_number",
                    )
                )
            if not preference.type_of_account:
                issues.append(
                    Issue(
                        type=IssueType.required,
                        rule="conditional",
                        message="Account type is required for direct deposit",
                        field=f"payment_preferences[{i}].account_details.account_type",
                    )
                )
        # (CP-1019) once has_mailing_address, update the condition here
        if preference.payment_type_id == PaymentType.DEBIT.payment_type_id and not (
            application.mailing_address or application.residential_address
        ):
            issues.append(
                Issue(
                    type=IssueType.required,
                    rule="conditional",
                    message=f"Address is required for debit card for payment_preference[{i}]",
                    field="residential_address",
                )
            )

    return issues


def deepgetattr(obj, attr):
    """Recurses through an attribute chain to get the ultimate value."""
    return reduce(getattr, attr.split("."), obj)


# This maps the required field name in the DB to its equivalent in the API
# Because the DB schema and the API schema differ
ALWAYS_REQUIRED_FIELDS_DB_NAME_TO_API_NAME_MAP = {
    "first_name": "first_name",
    "last_name": "last_name",
    "date_of_birth": "date_of_birth",
    "has_state_id": "has_state_id",
    "tax_identifier": "tax_identifier",
    "leave_reason": "leave_details.reason",
    "employment_status": "employment_status",
    "residential_address": "residential_address",
}


def get_always_required_issues(application: Application) -> List[Issue]:
    issues = []
    for (field, openapi_field) in ALWAYS_REQUIRED_FIELDS_DB_NAME_TO_API_NAME_MAP.items():
        val = deepgetattr(application, field)
        if val is None:
            issues.append(
                Issue(type=IssueType.required, message=f"{field} is required", field=openapi_field)
            )

    return issues


def get_leave_periods_issues(application: Application) -> List[Issue]:
    issues = []

    # TODO: Add rules isolated for each leave period in these functions
    issues += get_continuous_leave_issues(application.continuous_leave_periods)
    issues += get_intermittent_leave_issues(application.intermittent_leave_periods)
    issues += get_reduced_schedule_leave_issues(application.reduced_schedule_leave_periods)

    # TODO: Add rules for across leave periods here

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
    for i, current_period in enumerate(leave_periods):
        if not current_period.start_date:
            issues.append(
                Issue(
                    type=IssueType.required,
                    message=f"Start date is required for intermittent_leave_periods[{i}]",
                    field=f"leave_details.intermittent_leave_periods[{i}].start_date",
                )
            )
        if not current_period.end_date:
            issues.append(
                Issue(
                    type=IssueType.required,
                    message=f"End date is required for intermittent_leave_periods[{i}]",
                    field=f"leave_details.intermittent_leave_periods[{i}].end_date",
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
