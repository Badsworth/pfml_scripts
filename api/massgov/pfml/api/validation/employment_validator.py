from typing import Optional

import massgov.pfml.db as db
import massgov.pfml.util.logging
from massgov.pfml.api.validation.exceptions import IssueRule, IssueType, ValidationErrorDetail
from massgov.pfml.db.models.employees import (
    Employee,
    Employer,
    TaxIdentifier,
    WagesAndContributions,
)

logger = massgov.pfml.util.logging.get_logger(__name__)


def get_contributing_employer_or_employee_issue(
    db_session: db.Session,
    maybe_employer_fein: Optional[str],
    maybe_tax_identifier: Optional[TaxIdentifier],
) -> Optional[ValidationErrorDetail]:
    """Validate an Employer exists and a specific Employee works there"""

    # Requiring an EIN be present is handled by a separate validation rule
    logger.warning("IN FUNC")
    if maybe_employer_fein is not None:
        employer = (
            db_session.query(Employer)
            .filter(Employer.employer_fein == maybe_employer_fein)
            .one_or_none()
        )

        # Employer was not in DOR data, or we haven't yet created the corresponding record in FINEOS
        # if employer is None or employer.fineos_employer_id is None:
        if employer is None:
            logger.warning("emp is none or fineos id is none")
            return ValidationErrorDetail(
                field="employer_fein",
                type=IssueType.require_contributing_employer,
                message="Confirm that you have the correct EIN, and that the Employer is contributing to Paid Family and Medical Leave.",
            )

        # The DOR doesn't currently provide employee wages for employers that
        # are exempt.
        if employer.family_exemption and employer.medical_exemption:
            logger.warning("emp is exempt")
            return ValidationErrorDetail(
                field="employer_fein",
                type=IssueType.require_non_exempt_employer,
                message="The employer you entered is exempt in our system.",
            )

        # Requiring a tax identifier be present is handled by a separate validation rule.
        if maybe_tax_identifier is not None and not employee_has_wages_from_employer(
            db_session, employer, maybe_tax_identifier
        ):
            # If we have no record of wages for this Employee, then we don't send the
            # employee to FINEOS in the eligibility feed file for the employer, which
            # means FINEOS has no connection between the employee and employer. Attempting
            # to register the employee/employer combo in Fineos during claim creation
            # will therefore fail with a "not found" error.
            return ValidationErrorDetail(
                rule=IssueRule.require_employee,
                # TODO is this error message so specific that it's wrong?
                # If the employee itself is not found, then it isn't correct to
                # say that the association is not found.
                message="We couldn't find an assocation between you and the employer you entered in our system.",
                type=IssueType.pfml,
            )

    return None


def employee_has_wages_from_employer(
    db_session: db.Session, employer: Employer, tax_identifier: TaxIdentifier
) -> bool:
    employee = (
        db_session.query(Employee)
        .join(TaxIdentifier)
        .filter(TaxIdentifier.tax_identifier == tax_identifier.tax_identifier)
        .one_or_none()
    )

    if employee is None:
        return False

    wage_count = (
        db_session.query(WagesAndContributions)
        .filter(
            WagesAndContributions.employee_id == employee.employee_id,
            WagesAndContributions.employer_id == employer.employer_id,
        )
        .limit(1)
        .count()
    )

    return wage_count > 0
