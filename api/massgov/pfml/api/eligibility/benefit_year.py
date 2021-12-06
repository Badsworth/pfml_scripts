from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic.types import UUID4
from sqlalchemy.orm.query import Query
from werkzeug.exceptions import NotFound

import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.api.eligibility.benefit_year_dates import get_benefit_year_dates
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    BenefitYear,
    BenefitYearContribution,
    Claim,
    Employee,
    TaxIdentifier,
)
from massgov.pfml.util.pydantic import PydanticBaseModel

logger = massgov.pfml.util.logging.get_logger(__name__)

# any other statuses we should include?
AbsenceStatusesWithBenefitYear = [
    AbsenceStatus.APPROVED.absence_status_id,
    AbsenceStatus.COMPLETED.absence_status_id,
]


class CreateBenefitYearContribution(PydanticBaseModel):
    employer_id: UUID4
    average_weekly_wage: Decimal


def _query_approved_or_completed_claims_by_employee_id(
    db_session: db.Session, employee_id: UUID4
) -> "Query[Claim]":
    query = (
        db_session.query(Claim)
        .join(Employee, Claim.employee_id == Employee.employee_id)
        .filter(
            Employee.employee_id == employee_id,
            Claim.fineos_absence_status_id.in_(AbsenceStatusesWithBenefitYear),
        )
    )
    return query


def _get_persisted_benefit_year_for_date(
    db_session: db.Session, employee_id: UUID4, leave_start_date: date
) -> Optional[BenefitYear]:
    dates = get_benefit_year_dates(leave_start_date)
    found_benefit_year: "Optional[BenefitYear]" = (
        db_session.query(BenefitYear)
        .join(Employee, BenefitYear.employee_id == Employee.employee_id)
        .filter(
            Employee.employee_id == employee_id,
            BenefitYear.start_date <= dates.start_date,
            dates.start_date <= BenefitYear.end_date,
        )
        .one_or_none()
    )

    return found_benefit_year


def _get_benefit_year_contribution_from_claim(
    claim: Claim,
) -> Optional[CreateBenefitYearContribution]:

    absence_periods = claim.absence_periods if claim and claim.absence_periods else []
    for absence_period in absence_periods:
        if absence_period.fineos_average_weekly_wage is None:
            continue

        return CreateBenefitYearContribution(
            employer_id=claim.employer_id,
            average_weekly_wage=absence_period.fineos_average_weekly_wage,
        )

    logger.info(
        "Cannot find fineos_average_weekly_wage on claim.",
        extra={
            "claim_id": claim.claim_id,
            "employee_id": claim.employee_id,
            "employer_id": claim.employer_id,
        },
    )

    return None


def _get_benefit_year_dates_from_previous_leave_absence(
    db_session: db.Session, employee_id: UUID4, leave_start_date: date
) -> Optional[BenefitYear]:

    claims = (
        _query_approved_or_completed_claims_by_employee_id(db_session, employee_id)
        .order_by(Claim.absence_period_start_date)
        .all()
    )

    if len(claims) == 0:
        logger.info(
            "Cannot get Benefit Year from previous leave absence, there are no claims.",
            extra={"leave_start_date": leave_start_date, "employee_id": employee_id},
        )
        return None

    benefit_years: List[BenefitYear] = []

    for claim in claims:
        if not claim.absence_period_start_date:
            continue

        if len(benefit_years) == 0 or (
            claim.absence_period_start_date > benefit_years[-1].end_date
        ):
            employer_contributions = _get_benefit_year_contribution_from_claim(claim)
            benefit_year = _create_benefit_year_by_employee_id(
                db_session,
                employee_id,
                claim.absence_period_start_date,
                total_wages=None,
                employer_contributions=[employer_contributions] if employer_contributions else None,
            )
            if benefit_year:
                benefit_years.append(benefit_year)

    for benefit_year in benefit_years:
        if (
            leave_start_date >= benefit_year.start_date
            and leave_start_date <= benefit_year.end_date
        ):
            return benefit_year

    return None


def _find_employee_by_ssn(db_session: db.Session, tax_identifier: str) -> Employee:
    return (
        db_session.query(Employee)
        .join(TaxIdentifier, Employee.tax_identifier_id == TaxIdentifier.tax_identifier_id)
        .filter(TaxIdentifier.tax_identifier == tax_identifier)
        .one_or_none()
    )


def _get_benefit_year_by_employee_id(
    db_session: db.Session, employee_id: UUID4, leave_start_date: date
) -> Optional[BenefitYear]:

    return _get_persisted_benefit_year_for_date(
        db_session, employee_id, leave_start_date
    ) or _get_benefit_year_dates_from_previous_leave_absence(
        db_session, employee_id, leave_start_date
    )


def get_benefit_year_by_ssn(
    db_session: db.Session, tax_identifier: str, leave_start_date: date
) -> Optional[BenefitYear]:

    found_employee = _find_employee_by_ssn(db_session, tax_identifier)
    if not found_employee:
        raise NotFound("Cannot find employee with provided tax identifer.")

    return _get_benefit_year_by_employee_id(
        db_session, found_employee.employee_id, leave_start_date
    )


def _create_benefit_year_by_employee_id(
    db_session: db.Session,
    employee_id: UUID4,
    leave_start_date: date,
    total_wages: Optional[Decimal],
    employer_contributions: Optional[List[CreateBenefitYearContribution]],
) -> Optional[BenefitYear]:
    found_benefit_year = _get_persisted_benefit_year_for_date(
        db_session, employee_id, leave_start_date
    )
    if found_benefit_year:
        logger.info(
            "Cannot create a Benefit Year over period with existing Benefit Year.",
            extra={"leave_start_date": leave_start_date, "employee_id": employee_id},
        )
        return None

    date_range = get_benefit_year_dates(leave_start_date)
    benefit_year = BenefitYear()
    benefit_year.employee_id = employee_id
    benefit_year.start_date = date_range.start_date
    benefit_year.end_date = date_range.end_date

    if total_wages:
        benefit_year.total_wages = total_wages

    benefit_year.contributions = []
    if employer_contributions:
        for employer_contribution in employer_contributions:
            contribution = BenefitYearContribution()
            contribution.employee_id = employee_id
            contribution.employer_id = employer_contribution.employer_id
            contribution.average_weekly_wage = employer_contribution.average_weekly_wage
            benefit_year.contributions.append(contribution)

    db_session.add(benefit_year)
    return benefit_year


def create_benefit_year_by_ssn(
    db_session: db.Session,
    tax_identifier: str,
    leave_start_date: date,
    total_wages: Optional[Decimal],
    employer_contributions: Optional[List[CreateBenefitYearContribution]],
) -> Optional[BenefitYear]:

    found_employee = _find_employee_by_ssn(db_session, tax_identifier)
    if not found_employee:
        raise NotFound("Cannot find employee with provided tax identifer.")

    found_benefit_year = _get_benefit_year_by_employee_id(
        db_session, found_employee.employee_id, leave_start_date
    )
    if found_benefit_year:
        raise ValueError("Cannot create a Benefit Year over period with existing Benefit Year.")

    return _create_benefit_year_by_employee_id(
        db_session,
        found_employee.employee_id,
        leave_start_date,
        total_wages,
        employer_contributions,
    )
