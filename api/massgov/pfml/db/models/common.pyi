import uuid
from enum import Enum
from typing import Any, Type, TypeVar

import sqlalchemy.types as types

_E = TypeVar("_E", bound=Enum)

class StrEnum(types.TypeDecorator[_E]):
    def __init__(self, enum_type: Type[_E], *args: Any, **kwargs: Any) -> None: ...

PostgreSQLUUID = types.TypeEngine[uuid.UUID]
