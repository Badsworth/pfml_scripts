from dataclasses import dataclass
from datetime import date

import massgov.pfml.api.app as app
from massgov.pfml.db.models.employees import WagesAndContributions


def wages_get(employee_id, filing_period=None):
    with app.db_session() as db_session:
        wage = db_session.query(WagesAndContributions).filter_by(employee_id=employee_id)
        if filing_period is not None:
            wage = wage.filter_by(filing_period=filing_period)
        results = wage.all()

    return list(map(wage_and_comp_response, results))


@dataclass
class WageResponse:
    filing_period: date
    employee_id: str
    employer_id: str
    is_independent_contractor: bool
    is_opted_in: bool
    employee_ytd_wages: float
    employee_qtr_wages: float
    employee_med_contribution: float
    employer_med_contribution: float
    employee_fam_contribution: float
    employer_fam_contribution: float


def wage_and_comp_response(wage: WagesAndContributions) -> WageResponse:
    return WageResponse(
        filing_period=wage.filing_period,
        employee_id=wage.employee_id,
        employer_id=wage.employer_id,
        is_independent_contractor=wage.is_independent_contractor,
        is_opted_in=wage.is_opted_in,
        employee_ytd_wages=wage.employee_ytd_wages,
        employee_qtr_wages=wage.employee_qtr_wages,
        employee_med_contribution=wage.employee_med_contribution,
        employer_med_contribution=wage.employer_med_contribution,
        employer_fam_contribution=wage.employer_fam_contribution,
        employee_fam_contribution=wage.employee_fam_contribution,
    )
