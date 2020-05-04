from dataclasses import dataclass

from werkzeug.exceptions import NotFound

import massgov.pfml.api.db as db
from massgov.pfml.api.db.models import WageAndContribution

# this isn't being imported properly so it defaults to the example. hence all the 200s


def wages_get(employee_id, filing_period=None):
    with db.session_scope() as db_session:
        wage = db_session.query(WageAndContribution).filter_by(employee_id=employee_id)
        if filing_period is not None:
            wage = wage.filter_by(filing_period=filing_period)
        results = wage.all()
    if wage is None:
        raise NotFound()
    return [wage_and_comp_response(result) for result in results]


@dataclass
class WageResponse:
    filing_period: str
    employee_id: str
    employer_id: str
    is_independent_contractor: bool
    is_opted_in: bool
    employer_ytd_wages: int
    employer_qtr_wages: int
    employer_med_contribution: int
    employer_fam_contribution: int


def wage_and_comp_response(wage: WageAndContribution) -> WageResponse:
    return WageResponse(
        filing_period=wage.filing_period,
        employee_id=wage.employee_id,
        employer_id=wage.employer_id,
        is_independent_contractor=wage.is_independent_contractor,
        is_opted_in=wage.is_opted_in,
        employer_ytd_wages=wage.employer_ytd_wages,
        employer_qtr_wages=wage.employer_qtr_wages,
        employer_med_contribution=wage.employer_med_contribution,
        employer_fam_contribution=wage.employer_fam_contribution,
    )
