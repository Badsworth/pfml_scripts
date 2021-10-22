from typing import Type, TypeVar
from uuid import UUID

from werkzeug.exceptions import NotFound

import massgov.pfml.db as db

_T = TypeVar("_T")


def get_or_404(db_session: db.Session, model: Type[_T], id: UUID) -> _T:
    """Like get() but throws a NotFound exception if result is None"""
    result = db_session.query(model).get(id)

    if result is None:
        raise NotFound(description="Could not find {} with ID {}".format(model.__name__, id))

    return result
