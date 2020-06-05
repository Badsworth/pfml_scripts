from datetime import date
from decimal import Decimal
from typing import Any, Dict

from pydantic import UUID4

import massgov.pfml.api.app as app
from massgov.pfml.db.models.employees import WagesAndContributions
from massgov.pfml.util.pydantic import PydanticBaseModel


class WagesAndContributionsResponse(PydanticBaseModel):
    """Response object for a given WagesAndContributions result."""

    filing_period: date
    employee_id: UUID4
    employer_id: UUID4
    is_independent_contractor: bool
    is_opted_in: bool
    employee_ytd_wages: Decimal
    employee_qtr_wages: Decimal
    employee_med_contribution: Decimal
    employer_med_contribution: Decimal
    employee_fam_contribution: Decimal
    employer_fam_contribution: Decimal


def wages_get(employee_id, filing_period=None):
    with app.db_session() as db_session:
        query = db_session.query(WagesAndContributions).filter_by(employee_id=employee_id)

        if filing_period is not None:
            query = query.filter_by(filing_period=filing_period)

        wages = query.all()

    return list(map(build_response, wages))


def build_response(obj: WagesAndContributions) -> Dict[Any, Any]:
    """Helper method to create a response from an ORM model."""
    return WagesAndContributionsResponse.from_orm(obj).dict()
