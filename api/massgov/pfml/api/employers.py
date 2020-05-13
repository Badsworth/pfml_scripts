from dataclasses import dataclass

from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
from massgov.pfml.db.models.employees import Employer


def employers_get(employer_id):
    with app.db_session() as db_session:
        employer = db_session.query(Employer).get(employer_id)

    if employer is None:
        raise NotFound()

    return emp_response(employer)


@dataclass
class Response:
    employer_id: str
    employer_fein: str
    employer_dba: str


def emp_response(employer: Employer) -> Response:
    return Response(
        employer_id=employer.employer_id,
        employer_fein=employer.employer_fein,
        employer_dba=employer.employer_dba,
    )
