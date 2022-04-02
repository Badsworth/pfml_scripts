from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from pydantic.types import UUID4
from sqlalchemy.orm.query import Query
from werkzeug.exceptions import NotFound

import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.api.eligibility import wage
from massgov.pfml.api.eligibility.benefit_year_dates import get_benefit_year_dates
from massgov.pfml.api.eligibility.wage import WageCalculator, get_retroactive_base_period
from massgov.pfml.db.models.absences import AbsenceStatus
from massgov.pfml.db.models.employees import (
    BenefitYear,
    BenefitYearContribution,
    Claim,
    Employee,
    TaxIdentifier,
)
from massgov.pfml.util.pydantic import PydanticBaseModel

logger = massgov.pfml.util.logging.get_logger(__name__)

# any other statuses we should include?
ABSENCE_STATUSES_WITH_BENEFIT_YEAR = [
    AbsenceStatus.IN_REVIEW.absence_status_id,
    AbsenceStatus.APPROVED.absence_status_id,
    AbsenceStatus.COMPLETED.absence_status_id,
]


class CreateBenefitYearContribution(PydanticBaseModel):
    employer_id: UUID4
    average_weekly_wage: Decimal

    @staticmethod
    def from_wage_quarters(
        wage_calculator: WageCalculator,
    ) -> "List[CreateBenefitYearContribution]":
        contribtuons = []
        for employer_id in wage_calculator.employer_average_weekly_wage:
            average_weekly_wage = wage_calculator.get_employer_average_weekly_wage(
                employer_id, default=Decimal("0"), should_round=True
            )
            contribtuons.append(
                CreateBenefitYearContribution(
                    employer_id=employer_id, average_weekly_wage=average_weekly_wage
                )
            )
        return contribtuons


def _find_employee_by_ssn(db_session: db.Session, tax_identifier: str) -> Employee:
    return (
        db_session.query(Employee)
        .join(TaxIdentifier, Employee.tax_identifier_id == TaxIdentifier.tax_identifier_id)
        .filter(TaxIdentifier.tax_identifier == tax_identifier)
        .one_or_none()
    )


# "Relevant" here is defined by the list of absence statuses stored in ABSENCE_STATUSES_WITH_BENEFIT_YEAR
def _query_relevant_claims_by_employee_id(
    db_session: db.Session, employee_id: UUID4
) -> "Query[Claim]":
    query = db_session.query(Claim).filter(
        Claim.employee_id == employee_id,
        Claim.fineos_absence_status_id.in_(ABSENCE_STATUSES_WITH_BENEFIT_YEAR),
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

    if found_benefit_year:
        return found_benefit_year

    # Check to see if there's a future beneift year we need to adjust
    future_benefit_year: "Optional[BenefitYear]" = (
        db_session.query(BenefitYear)
        .join(Employee, BenefitYear.employee_id == Employee.employee_id)
        .filter(
            Employee.employee_id == employee_id,
            dates.start_date <= BenefitYear.start_date,
            BenefitYear.start_date <= dates.end_date,
        )
        .one_or_none()
    )

    if future_benefit_year:
        future_benefit_year.start_date = dates.start_date
        future_benefit_year.end_date = dates.end_date
        db_session.commit()

    return future_benefit_year


def _get_benefit_year_contribution_from_claim(
    claim: Claim,
) -> Optional[CreateBenefitYearContribution]:
    if not claim.employer_id:
        logger.warning(
            "Cannot find employer_id on claim.",
            extra={"claim_id": claim.claim_id, "employee_id": claim.employee_id},
        )

        return None

    absence_periods = claim.absence_periods if claim and claim.absence_periods else []
    for absence_period in absence_periods:
        if absence_period.fineos_average_weekly_wage is None:
            continue

        return CreateBenefitYearContribution(
            employer_id=claim.employer_id,
            average_weekly_wage=absence_period.fineos_average_weekly_wage,
        )

    logger.warning(
        "Cannot find fineos_average_weekly_wage on claim.",
        extra={
            "claim_id": claim.claim_id,
            "employee_id": claim.employee_id,
            "employer_id": claim.employer_id,
        },
    )

    return None


def find_employer_benefit_year_contribution(
    benefit_year: BenefitYear, employer_id: UUID4
) -> Optional[BenefitYearContribution]:
    contributions = benefit_year.contributions if benefit_year.contributions else []
    for contribution in contributions:
        if contribution.employer_id == employer_id:
            return contribution

    return None


def find_employer_benefit_year_IAWW_contribution(
    benefit_year: BenefitYear, employer_id: UUID4
) -> Optional[Decimal]:
    contribution = find_employer_benefit_year_contribution(benefit_year, employer_id)
    if not contribution:
        return None

    return contribution.average_weekly_wage


def _create_benefit_year(
    db_session: db.Session,
    employee_id: UUID4,
    leave_start_date: date,
    total_wages: Optional[Decimal],
    employer_contributions: Optional[List[CreateBenefitYearContribution]],
    base_period_dates: Optional[Tuple[date, date]] = None,
) -> Optional[BenefitYear]:
    employer_contributions = employer_contributions if employer_contributions else []

    found_benefit_year = _get_persisted_benefit_year_for_date(
        db_session, employee_id, leave_start_date
    )
    if found_benefit_year:
        logger.warning(
            "Cannot create a Benefit Year over period with existing Benefit Year.",
            extra={"leave_start_date": leave_start_date, "employee_id": employee_id},
        )
        return None

    date_range = get_benefit_year_dates(leave_start_date)
    benefit_year = BenefitYear(
        **date_range.dict(), employee_id=employee_id, total_wages=total_wages
    )
    if base_period_dates:
        benefit_year.base_period_start_date = base_period_dates[0]
        benefit_year.base_period_end_date = base_period_dates[1]

    benefit_year.contributions = []
    for employer_contribution in employer_contributions:
        benefit_year.contributions.append(
            BenefitYearContribution(**employer_contribution.dict(), employee_id=employee_id)
        )

    db_session.add(benefit_year)
    return benefit_year


def _create_benefit_years_from_leave_absence_history(
    db_session: db.Session, employee_id: UUID4
) -> List[BenefitYear]:
    claims = (
        _query_relevant_claims_by_employee_id(db_session, employee_id)
        .order_by(Claim.absence_period_start_date)
        .all()
    )

    if len(claims) == 0:
        logger.warning(
            "Cannot get Benefit Year from previous leave absence, there are no claims.",
            extra={"employee_id": employee_id},
        )
        return []

    benefit_years: List[BenefitYear] = []

    for claim in claims:
        if not claim.absence_period_start_date:
            continue

        if len(benefit_years) == 0 or (
            claim.absence_period_start_date > benefit_years[-1].end_date
        ):
            employer_contributions = _get_benefit_year_contribution_from_claim(claim)
            benefit_year = _create_benefit_year(
                db_session,
                employee_id,
                claim.absence_period_start_date,
                total_wages=None,
                employer_contributions=[employer_contributions] if employer_contributions else None,
            )
            if benefit_year:
                benefit_years.append(benefit_year)

    db_session.add_all(benefit_years)
    return benefit_years


def get_benefit_year_from_leave_absence_history(
    db_session: db.Session, employee_id: UUID4, leave_start_date: date
) -> Optional[BenefitYear]:

    benefit_years = _create_benefit_years_from_leave_absence_history(db_session, employee_id)

    if len(benefit_years) == 0:
        return None

    try:
        db_session.commit()
    except Exception as error:
        logger.error(
            "An error occurred while creating benefit years from previous claims.",
            extra={"employee_id": employee_id, "error_message": str(error)},
        )
        db_session.rollback()

    dates = get_benefit_year_dates(leave_start_date)

    # If the claim start date is within the existing benefit year, return it as is
    # If the claim start date is before the existing benefit year, but within 52 weeks
    # of it, update the start and end date of the existing benefit year based on the new
    # claim, and then return it.
    for benefit_year in benefit_years:
        if (
            dates.start_date >= benefit_year.start_date
            and dates.start_date <= benefit_year.end_date
        ):
            return benefit_year
        elif (
            dates.start_date <= benefit_year.start_date
            and benefit_year.start_date <= dates.end_date
        ):
            benefit_year.start_date = dates.start_date
            benefit_year.end_date = dates.end_date
            db_session.commit()
            return benefit_year

    return None


def get_benefit_year_by_employee_id(
    db_session: db.Session, employee_id: UUID4, leave_start_date: date
) -> Optional[BenefitYear]:
    return _get_persisted_benefit_year_for_date(
        db_session, employee_id, leave_start_date
    ) or get_benefit_year_from_leave_absence_history(db_session, employee_id, leave_start_date)


def get_all_benefit_years_by_employee_id(
    db_session: db.Session, employee_id: UUID4
) -> List[BenefitYear]:
    return db_session.query(BenefitYear).filter(BenefitYear.employee_id == employee_id).all()


def get_benefit_year_by_ssn(
    db_session: db.Session, tax_identifier: str, leave_start_date: date
) -> Optional[BenefitYear]:

    found_employee = _find_employee_by_ssn(db_session, tax_identifier)
    if not found_employee:
        raise NotFound("Cannot find employee with provided tax identifer.")

    return get_benefit_year_by_employee_id(db_session, found_employee.employee_id, leave_start_date)


def create_benefit_year_by_employee_id(
    db_session: db.Session,
    employee_id: UUID4,
    leave_start_date: date,
    total_wages: Optional[Decimal],
    employer_contributions: Optional[List[CreateBenefitYearContribution]],
    base_period_dates: Optional[Tuple[date, date]] = None,
) -> Optional[BenefitYear]:

    try:
        benefit_year = _create_benefit_year(
            db_session,
            employee_id,
            leave_start_date,
            total_wages,
            employer_contributions,
            base_period_dates,
        )
        db_session.commit()
        return benefit_year

    except Exception as error:
        logger.error(
            "An error occurred while creating Benefit Year.",
            extra={"employee_id": employee_id, "error": str(error)},
        )
        db_session.rollback()

    return None


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

    return create_benefit_year_by_employee_id(
        db_session,
        found_employee.employee_id,
        leave_start_date,
        total_wages,
        employer_contributions,
    )


def _get_earliest_claim_in_benefit_year(
    db_session: db.Session, benefit_year: BenefitYear
) -> Optional[Claim]:
    return (
        db_session.query(Claim)
        .filter(Claim.employee_id == benefit_year.employee_id)
        .filter(Claim.absence_period_start_date.isnot(None))
        .filter(
            Claim.absence_period_start_date.between(benefit_year.start_date, benefit_year.end_date)
        )
        .order_by(Claim.absence_period_start_date)
        .first()
    )


def set_base_period_for_benefit_year(
    db_session: db.Session, benefit_year: BenefitYear
) -> Optional[BenefitYear]:
    earilest_claim_in_benefit_year = _get_earliest_claim_in_benefit_year(db_session, benefit_year)

    if earilest_claim_in_benefit_year is None:
        logger.info(
            "Unable to set base period for benefit year. No claims found for benefit year",
            extra={"benefit_year_id": benefit_year.benefit_year_id},
        )
        return None

    application_submitted_date = earilest_claim_in_benefit_year.created_at.date()

    # Choose earliest date
    effective_date = min(application_submitted_date, benefit_year.start_date)

    base_period_qtrs = get_retroactive_base_period(
        db_session, benefit_year.employee_id, effective_date
    )
    base_period_start, base_period_end = base_period_qtrs[-1], base_period_qtrs[0]

    benefit_year.base_period_start_date = base_period_start.start_date()
    benefit_year.base_period_end_date = base_period_end.as_date()

    db_session.add(benefit_year)
    db_session.commit()

    return benefit_year


def create_employer_contribution_for_benefit_year(
    db_session: db.Session,
    benefit_year_id: UUID4,
    employee_id: UUID4,
    employer_id: UUID4,
    average_weekly_wage: Decimal,
) -> Optional[BenefitYearContribution]:

    contribution = BenefitYearContribution(
        benefit_year_id=benefit_year_id,
        employee_id=employee_id,
        employer_id=employer_id,
        average_weekly_wage=average_weekly_wage,
    )

    try:
        db_session.add(contribution)
        db_session.commit()
        return contribution
    except Exception as error:
        logger.error(
            "An error occurred while creating employer contribution for benefit year.",
            extra={
                "benefit_year_id": benefit_year_id,
                "employee_id": employee_id,
                "employer_id": employer_id,
                "error_message": str(error),
            },
        )
        db_session.rollback()
    return None


def get_employer_aww(
    db_session: db.Session,
    benefit_year: BenefitYear,
    employer_id: UUID4,
) -> Optional[Decimal]:
    # Determine base period for benefit year
    base_period = (
        benefit_year.base_period_start_date,
        benefit_year.base_period_end_date,
    )
    # -- Calculate retroactive base period if not currently set
    if base_period[0] is None or base_period[1] is None:
        logger.info(
            "Base period for benefit year was empty.",
            extra={"benefit_year_id": benefit_year.benefit_year_id},
        )
        updated_benefit_year = set_base_period_for_benefit_year(db_session, benefit_year)
        if updated_benefit_year is not None:
            base_period = (
                updated_benefit_year.base_period_start_date,
                updated_benefit_year.base_period_end_date,
            )
            logger.info(
                "Calculated the base period for the benefit year.",
                extra={"benefit_year_id": benefit_year.benefit_year_id, "base_period": base_period},
            )

    # Retrieve or calculate IAWW for benefit year
    employer_average_weekly_wage = find_employer_benefit_year_IAWW_contribution(
        benefit_year, employer_id
    )
    # -- Calculate IAWW using the same base period for the benefit year
    if not employer_average_weekly_wage and base_period[0] is not None:
        base_period_start_date = base_period[0]
        wage_calculator = wage.get_wage_calculator(
            benefit_year.employee_id, base_period_start_date, db_session
        )
        employer_average_weekly_wage = wage_calculator.get_employer_average_weekly_wage(
            employer_id, default=Decimal("0"), should_round=True
        )
        create_employer_contribution_for_benefit_year(
            db_session,
            benefit_year.benefit_year_id,
            benefit_year.employee_id,
            employer_id,
            employer_average_weekly_wage,
        )
        logger.info(
            "Calculated employer average weekly wage for the beneift year.",
            extra={
                "benefit_year_id": benefit_year.benefit_year_id,
                "base_period": base_period,
                "employer_id": employer_id,
                "quarterly_wages": str(dict(wage_calculator.employer_quarter_wage)),
            },
        )

    return employer_average_weekly_wage
