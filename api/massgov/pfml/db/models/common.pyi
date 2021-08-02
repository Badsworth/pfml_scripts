from enum import Enum
from typing import Any, Type, TypeVar

import sqlalchemy.types as types

from massgov.pfml.types import Fein, TaxId

_E = TypeVar("_E", bound=Enum)

class StrEnum(types.TypeDecorator[_E]):
    def __init__(self, enum_type: Type[_E], *args: Any, **kwargs: Any) -> None: ...

class TaxIdColumn(types.TypeDecorator[TaxId]): ...
class FeinColumn(types.TypeDecorator[Fein]): ...
