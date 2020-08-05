from pydantic import UUID4

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
from massgov.pfml.api.authorization.flask import READ, ensure
from massgov.pfml.db.models.employees import Employer
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.sqlalchemy import get_or_404


class EmployerResponse(PydanticBaseModel):
    # Only return these fields in the API for now.
    employer_id: UUID4
    employer_fein: str
    employer_dba: str


def employers_get(employer_id):
    with app.db_session() as db_session:
        employer = get_or_404(db_session, Employer, employer_id)
        ensure(READ, employer)
        return response_util.success_response(
            message="Successfully retrieved employer",
            data=EmployerResponse.from_orm(employer).dict(),
        ).to_api_response()
