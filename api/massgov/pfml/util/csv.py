import dataclasses
import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, Optional, Type, Union
from uuid import UUID


def isoformat(o: Union[datetime.date, datetime.time]) -> str:
    return o.isoformat()


Encoders = Dict[Type[Any], Callable[[Any], str]]

ENCODERS_BY_TYPE: Encoders = {
    bytes: lambda o: o.decode(),
    datetime.date: isoformat,
    datetime.datetime: isoformat,
    datetime.time: isoformat,
    datetime.timedelta: lambda td: td.total_seconds(),
    Decimal: str,
    Enum: lambda o: o.value,
    UUID: str,
    str: str,
    type(None): lambda _: "",
    int: str,
    float: str,
}


def encode_row(obj: Any, encoders: Optional[Encoders] = None) -> Dict[str, str]:
    if dataclasses.is_dataclass(obj):
        result = {}
        for f in dataclasses.fields(obj):
            value = encode_value(getattr(obj, f.name), encoders)
            result[f.name] = value
        return result

    if isinstance(dict, obj):
        return {k: encode_value(v, encoders) for k, v in obj.items()}

    raise TypeError(f"Object of type '{obj.__class__.__name__}' is not a dataclass or dictionary")


def encode_value(obj: Any, encoders: Optional[Encoders] = None) -> str:
    if encoders is None:
        encoders = {}

    try:
        # try the provided encoders (if any)
        return _encode_value(obj, encoders)
    except TypeError:
        # failing that, fall back to defaults
        return _encode_value(obj, ENCODERS_BY_TYPE)


def _encode_value(obj: Any, encoders: Encoders) -> str:
    for base in obj.__class__.__mro__[:-1]:
        try:
            encoder = encoders[base]
        except KeyError:
            continue
        return encoder(obj)
    else:  # We have exited the for loop without finding a suitable encoder
        raise TypeError(f"Object of type '{obj.__class__.__name__}' is not CSV serializable")
