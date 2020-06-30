from enum import Enum
from typing import Any, Optional, Union

import massgov.pfml.db as db


def by_value(db_session: db.Session, model_cls: Any, value: Union[str, Enum]) -> Optional[Any]:
    if isinstance(value, Enum):
        value = value.value

    model_table_name = model_cls.__tablename__

    column_name = "".join([model_table_name.replace("lk_", "", 1), "_description"])

    lookup_model = (
        db_session.query(model_cls).filter(getattr(model_cls, column_name) == value).one_or_none()
    )

    return lookup_model
