from typing import List, Optional

from massgov.pfml.api.util.response import Issue, IssueType
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail, ValidationException
from massgov.pfml.db.models.employees import Employer


class EmployerRequiresVerificationDataException(Exception):
    __slots__ = ["errors"]

    def __init__(self, errors: List[Issue]):
        self.errors = errors


def validate_employer_being_added(employer: Optional[Employer]) -> None:
    """Validate the Employer a user is attempting to add to their account

    Raises
    ------
    - EmployerRequiresVerificationDataException
    - ValidationException
    """

    if not employer:
        raise ValidationException(
            errors=[
                ValidationErrorDetail(
                    type=IssueType.require_employer, message="Invalid FEIN", field="employer_fein",
                )
            ]
        )

    if not employer.fineos_employer_id:
        raise ValidationException(
            errors=[
                ValidationErrorDetail(
                    type=IssueType.require_contributing_employer,
                    message="Confirm that you have the correct EIN, and that the Employer is contributing to Paid Family and Medical Leave.",
                    field="employer_fein",
                )
            ]
        )

    if employer.has_verification_data is False:
        raise EmployerRequiresVerificationDataException(
            errors=[
                # TODO (CP-1925): Use ValidationErrorDetail instead of Issue
                Issue(
                    type=IssueType.employer_requires_verification_data,
                    message="Employer has no verification data",
                    field="employer_fein",
                )
            ]
        )
