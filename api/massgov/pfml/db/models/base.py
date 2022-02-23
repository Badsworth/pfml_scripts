import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import TIMESTAMP, Column, inspect
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm import deferred
from sqlalchemy.sql.functions import now as sqlnow

from massgov.pfml.util.datetime import utcnow


def same_as_created_at(context):
    return context.get_current_parameters()["created_at"]


# This ensures that deprecated columns won't be read or included as part of an INSERT on the table
def deprecated_column(type: Any, *args: Any, **kwargs: Any) -> Column:
    if not callable(type):
        return deferred(Column(type.evaluates_none(), *args, **kwargs))
    else:
        return deferred(Column(type().evaluates_none(), *args, **kwargs))


@as_declarative()
class Base:
    def dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}

    def for_json(self):
        json_valid_dict = {}
        dictionary = self.dict()
        for key, value in dictionary.items():
            if isinstance(value, UUID) or isinstance(value, Decimal):
                json_valid_dict[key] = str(value)
            elif isinstance(value, date) or isinstance(value, datetime):
                json_valid_dict[key] = value.isoformat()
            else:
                json_valid_dict[key] = value

        return json_valid_dict

    def __rich_repr__(self):
        """Rich repr for interactive console.

        See https://rich.readthedocs.io/en/latest/pretty.html#rich-repr-protocol
        """
        return self.dict().items()

    def model_lookup_by_table_name(self, table_name):
        # _decl_class_registry won't exist as of 1.4.x. Instead,
        # Base.registry.mappers or similar can be used. See https://github.com/sqlalchemy/sqlalchemy/issues/6080
        for model in self._decl_class_registry.values():  # type: ignore[attr-defined]
            if hasattr(model, "__tablename__") and model.__tablename__ == table_name:
                return model


def uuid_gen() -> uuid.UUID:
    return uuid.uuid4()


def utc_timestamp_gen():
    """ Generate a tz-aware timestamp pinned to UTC """
    return utcnow()


# This is annotated as a @declarative_mixin when we upgrade to SQLAlchemy 1.4
class TimestampMixin:
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        server_default=sqlnow(),
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=same_as_created_at,
        onupdate=utc_timestamp_gen,
        server_default=sqlnow(),
    )
