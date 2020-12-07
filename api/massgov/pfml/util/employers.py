from typing import Optional, Union

from massgov.pfml import db
from massgov.pfml.db.models.employees import Employer


def lookup_employer(
    db_session: db.Session, employer_fein: Optional[str] = None, employer_id: Optional[str] = None
) -> Union[Employer, None]:
    employer = None

    if employer_id:
        employer = db_session.query(Employer).get(employer_id)
    elif employer_fein:
        employer = (
            db_session.query(Employer).filter(Employer.employer_fein == employer_fein).one_or_none()
        )
    return employer
