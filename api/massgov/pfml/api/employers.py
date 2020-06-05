from pydantic import UUID4
from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
from massgov.pfml.db.models.employees import Employer
from massgov.pfml.util.pydantic import PydanticBaseModel


class EmployerResponse(PydanticBaseModel):
    # Only return these fields in the API for now.
    employer_id: UUID4
    employer_fein: str
    employer_dba: str


def employers_get(employer_id):
    with app.db_session() as db_session:
        employer = db_session.query(Employer).get(employer_id)

    if employer is None:
        raise NotFound()

    response = EmployerResponse.from_orm(employer)
    return response.dict()
