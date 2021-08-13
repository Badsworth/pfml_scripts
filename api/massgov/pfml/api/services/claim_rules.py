from datetime import date
from decimal import Decimal
from itertools import chain
from typing import List, Optional

from massgov.pfml.api.models.claims.common import EmployerClaimReview, PreviousLeave
from massgov.pfml.api.models.common import EmployerBenefit
from massgov.pfml.api.validation.exceptions import IssueType, ValidationErrorDetail

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
            type="missing_expected_field",
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
                    type="invalid_previous_leave_start_date",
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
