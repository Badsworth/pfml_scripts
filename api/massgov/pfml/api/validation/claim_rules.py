from datetime import date
from decimal import Decimal
from itertools import chain
from typing import List, Optional

from massgov.pfml.api.models.claims.common import EmployerClaimReview, PreviousLeave
from massgov.pfml.api.models.common import EmployerBenefit
from massgov.pfml.api.validation.exceptions import IssueType, ValidationErrorDetail
from massgov.pfml.db.models.absences import AbsenceReasonQualifierOne
from massgov.pfml.db.models.employees import (
    ChangeRequest,
    ChangeRequestType,
    Claim,
    LeaveRequestDecision,
)

# there are 168 hours in a week
MAX_HOURS_WORKED_PER_WEEK = 168


def get_employer_claim_review_issues(
    claim_review: EmployerClaimReview,
) -> List[ValidationErrorDetail]:
    """Takes in an employer claim review request and outputs any validation issues."""
    return list(
        chain(
            get_hours_worked_per_week_issues(claim_review.hours_worked_per_week),
            get_previous_leaves_issues(claim_review.previous_leaves),
            get_employer_benefits_issues(
                claim_review.employer_benefits, claim_review.uses_second_eform_version
            ),
        )
    )


def get_hours_worked_per_week_issues(
    hours_worked_per_week: Optional[Decimal],
) -> List[ValidationErrorDetail]:
    if hours_worked_per_week is None:
        error = ValidationErrorDetail(
            message="hours_worked_per_week must be populated",
            type=IssueType.required,
            field="hours_worked_per_week",
        )
        return [error]

    if hours_worked_per_week <= 0:
        error = ValidationErrorDetail(
            message="hours_worked_per_week must be greater than 0",
            type=IssueType.minimum,
            field="hours_worked_per_week",
        )
        return [error]

    if hours_worked_per_week > MAX_HOURS_WORKED_PER_WEEK:
        error = ValidationErrorDetail(
            message="hours_worked_per_week must be 168 or fewer",
            type=IssueType.maximum,
            field="hours_worked_per_week",
        )
        return [error]

    return []


def get_previous_leaves_issues(previous_leaves: List[PreviousLeave]) -> List[ValidationErrorDetail]:
    error_list: List[ValidationErrorDetail] = []

    if not previous_leaves:
        return error_list

    for index, previous_leave in enumerate(previous_leaves):
        # FINEOS does not require that leave_start_date or leave_end_date is populated.
        # The existence of one also does not imply the existence of the other.
        if previous_leave.leave_start_date is None:
            continue

        if previous_leave.leave_start_date < date(2021, 1, 1):
            error_list.append(
                ValidationErrorDetail(
                    message="Previous leaves cannot start before 2021",
                    type=IssueType.invalid_previous_leave_start_date,
                    field=f"previous_leaves[{index}].leave_start_date",
                )
            )

        if previous_leave.leave_end_date is None:
            continue

        if previous_leave.leave_start_date > previous_leave.leave_end_date:
            error_list.append(
                ValidationErrorDetail(
                    message="leave_end_date cannot be earlier than leave_start_date",
                    type=IssueType.minimum,
                    field=f"previous_leaves[{index}].leave_end_date",
                )
            )

    return error_list


def get_employer_benefits_issues(
    employer_benefits: List[EmployerBenefit], uses_second_eform_version: bool
) -> List[ValidationErrorDetail]:
    error_list: List[ValidationErrorDetail] = []

    if not employer_benefits:
        return error_list

    # TODO (EMPLOYER-1453): Remove v1 eform functionality
    if not uses_second_eform_version and len(employer_benefits) > 4:
        error_list.append(
            ValidationErrorDetail(
                message="Employer benefits cannot exceed limit of 4",
                type=IssueType.maximum,
                field="employer_benefits",
            )
        )

    for index, employer_benefit in enumerate(employer_benefits):
        # FINEOS does not require that benefit_start_date or benefit_end_date is populated.
        # The existence of one also does not imply the existence of the other.
        if employer_benefit.benefit_start_date is None or employer_benefit.benefit_end_date is None:
            continue

        if employer_benefit.benefit_start_date > employer_benefit.benefit_end_date:
            error_list.append(
                ValidationErrorDetail(
                    message="benefit_end_date cannot be earlier than benefit_start_date",
                    type=IssueType.minimum,
                    field=f"employer_benefits[{index}].benefit_end_date",
                )
            )

    return error_list


def get_change_request_issues(
    change_request: ChangeRequest, claim: Claim
) -> List[ValidationErrorDetail]:
    error_list: List[ValidationErrorDetail] = []

    # Only should be requesting a modification on a submitted claim,
    # so this should be set (saves problems with linter)
    assert claim.absence_period_start_date

    if change_request.type == ChangeRequestType.WITHDRAWAL.description:
        error_list.extend(get_withdrawal_issues(change_request, claim))
    if change_request.type == ChangeRequestType.MODIFICATION.description:
        error_list.extend(get_modification_issues(change_request, claim))
    if change_request.type == ChangeRequestType.MEDICAL_TO_BONDING.description:
        error_list.extend(get_medical_to_bonding_issues(change_request, claim))

    start_date = (
        claim.absence_period_start_date
        if change_request.start_date is None
        else change_request.start_date
    )
    if change_request.end_date:
        # the end date cannot be before the original or modified start date
        if start_date > change_request.end_date:
            error_list.append(
                ValidationErrorDetail(
                    message="Start date must be less than end date",
                    type=IssueType.maximum,
                    field="end_date",
                )
            )

    return error_list


def get_withdrawal_issues(
    change_request: ChangeRequest, claim: Claim
) -> List[ValidationErrorDetail]:
    error_list: List[ValidationErrorDetail] = []
    # for a withdrawal, start and end dates should be null
    if change_request.start_date:
        error_list.append(
            ValidationErrorDetail(
                message="Start date is invalid for this request type",
                type=IssueType.withdrawal_dates_must_be_null,
                field="start_date",
            )
        )
    if change_request.end_date:
        error_list.append(
            ValidationErrorDetail(
                message="End date is invalid for this request type",
                type=IssueType.withdrawal_dates_must_be_null,
                field="end_date",
            )
        )
    approved_id = LeaveRequestDecision.APPROVED.leave_request_decision_id
    pending_id = LeaveRequestDecision.PENDING.leave_request_decision_id
    absence_periods = claim.absence_periods if claim.absence_periods else []
    approved_or_pending_absence_periods = [
        ap for ap in absence_periods if ap.leave_request_decision_id in [approved_id, pending_id]
    ]
    if len(approved_or_pending_absence_periods) == 0:
        error_list.append(
            ValidationErrorDetail(
                message="Claim must have at least one approved or pending absence period to submit a withdrawal",
                type=IssueType.must_be_approved_or_pending_claim,
                field="fineos_absence_id",
            )
        )
    return error_list


def get_modification_issues(
    change_request: ChangeRequest, claim: Claim
) -> List[ValidationErrorDetail]:
    error_list: List[ValidationErrorDetail] = []
    # for a modification, start date should be null
    if change_request.start_date:
        error_list.append(
            ValidationErrorDetail(
                message="Start date is invalid for this request type",
                type=IssueType.change_start_date_is_unsupported,
                field="start_date",
            )
        )
    if not change_request.end_date:
        error_list.append(
            ValidationErrorDetail(
                message="End date is required for this request type",
                type=IssueType.required,
                field="end_date",
            )
        )
    error_list.extend(has_approved_absence_period(claim))
    return error_list


def get_medical_to_bonding_issues(
    change_request: ChangeRequest, claim: Claim
) -> List[ValidationErrorDetail]:
    error_list: List[ValidationErrorDetail] = []
    if not change_request.start_date:
        error_list.append(
            ValidationErrorDetail(
                message="Start date is required for this request type",
                type=IssueType.required,
                field="start_date",
            )
        )
    if not change_request.end_date:
        error_list.append(
            ValidationErrorDetail(
                message="End date is required for this request type",
                type=IssueType.required,
                field="end_date",
            )
        )
    error_list.extend(has_approved_absence_period(claim))
    absence_reason_ids = []
    birth_disability_id = AbsenceReasonQualifierOne.BIRTH_DISABILITY.absence_reason_qualifier_one_id
    if claim.absence_periods:
        absence_reason_ids = [ap.absence_reason_qualifier_one_id for ap in claim.absence_periods]
    if birth_disability_id not in absence_reason_ids:
        error_list.append(
            ValidationErrorDetail(
                message="Claimant did not apply for bonding leave in initial application",
                type=IssueType.not_medical_to_bonding_claim,
            )
        )
    return error_list


def has_approved_absence_period(claim: Claim) -> List[ValidationErrorDetail]:
    error_list: List[ValidationErrorDetail] = []
    # user can request a modification only on a claim with an approved period
    leave_request_approved_id = LeaveRequestDecision.APPROVED.leave_request_decision_id
    absence_periods = claim.absence_periods if claim.absence_periods else []
    approved_absence_periods = [
        ap for ap in absence_periods if ap.leave_request_decision_id == leave_request_approved_id
    ]
    if len(approved_absence_periods) == 0:
        error_list.append(
            ValidationErrorDetail(
                type=IssueType.must_be_approved_claim,
                message="Claim must have at least one approved absence period to submit a change request",
                field="fineos_absence_id",
            )
        )
    return error_list
