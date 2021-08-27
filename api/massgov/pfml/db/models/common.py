import uuid
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Type, TypeVar, cast

import sqlalchemy.types as types
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.engine.interfaces import Dialect

# All type information in this file is provided for reference, because a
# corresponding stub file exists at `common.pyi`, the types there are what's
# actually used by the type checker.
#
# This is because there's some issue with the generic argument with
# TypeDecorator class getting handled correctly when doing it as laid out in
# this file (gating the generic argument in the TYPE_CHECKING block).

_E = TypeVar("_E", bound=Enum)

if TYPE_CHECKING:
    StrEnumType = types.TypeDecorator[_E]
else:
    StrEnumType = types.TypeDecorator

# (PostgreSQLUUID) https://github.com/dropbox/sqlalchemy-stubs/issues/94
PostgreSQLUUID = cast("types.TypeEngine[uuid.UUID]", UUID(as_uuid=True),)


class StrEnum(StrEnumType):
    """Represent the Enum in the database by it's string value, as opposed to
    it's name, which a bare Enum used as column type will do.

    For more details on how this class works, see the SQLAlchemy docs:
    https://docs.sqlalchemy.org/en/13/core/custom_types.html#augmenting-existing-types
    """

    impl = types.Text

    def __init__(self, enum_type: Type[_E], *args: Any, **kwargs: Any) -> None:
        super(StrEnum, self).__init__(*args, **kwargs)
        self._enum_type = enum_type

    # Called when this value is used in a query, e.g.:
    #
    # app value (an Enum) -> db value (a string)
    def process_bind_param(self, value: Optional[_E], dialect: Dialect) -> Optional[str]:
        if value is None:
            return None

        return value.value

    # Called when this column is loaded from the database, e.g.:
    #
    # db value (a string) -> app value (an Enum)
    def process_result_value(self, value: Optional[Any], dialect: Dialect) -> Optional[_E]:
        if value is None:
            return None

        return self._enum_type(value)
