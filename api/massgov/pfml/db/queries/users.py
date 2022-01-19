from typing import Optional

import massgov.pfml.api.app as app
from massgov.pfml import db
from massgov.pfml.db.models.employees import User


def get_user_by_email(db_session: Optional[db.Session], email: str) -> Optional[User]:
    if db_session is not None:
        return _get_user_by_email_query(db_session, email)

    with app.db_session() as db_session:
        return _get_user_by_email_query(db_session, email)


def _get_user_by_email_query(db_session: db.Session, email: str) -> Optional[User]:
    return db_session.query(User).filter(User.email_address == email).one_or_none()
