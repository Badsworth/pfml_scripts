import csv
import dataclasses
import datetime
import os
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
)
from uuid import UUID

import smart_open

from massgov.pfml.util import files as file_util
from massgov.pfml.util import logging

logger = logging.get_logger(__name__)


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

    if isinstance(obj, dict):
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


_DictRow = Mapping[str, Any]
_DialectLike = Union[str, csv.Dialect, Type[csv.Dialect]]


class EncodingDictWriter(csv.DictWriter):
    encoders: Optional[Encoders]

    def __init__(
        self,
        f: Any,
        fieldnames: Sequence[str],
        restval: Optional[Any] = "",
        extrasaction: str = "raise",
        dialect: _DialectLike = "excel",
        encoders: Optional[Encoders] = None,
        *args: Any,
        **kwds: Any,
    ) -> None:
        self.encoders = encoders

        super().__init__(f, fieldnames, restval, extrasaction, dialect, *args, **kwds)

    def writerow(self, rowdict: _DictRow) -> Any:
        return super().writerow(encode_row(rowdict, self.encoders))

    def writerows(self, rowdicts: Iterable[_DictRow]) -> Any:
        return super().writerows(map(lambda d: encode_row(d, self.encoders), rowdicts))


class CSVSourceWrapper:
    """Simple wrapper for reading dicts out of CSV files"""

    def __init__(self, file_path: str, transport_params: Optional[Dict[str, Any]] = None):
        self._file_path = file_path
        self._transport_params = transport_params

    def __iter__(self) -> Generator[Dict[Any, Any], Any, Any]:
        with smart_open.open(
            self._file_path, "r", transport_params=self._transport_params
        ) as csvfile:
            dict_reader = csv.DictReader(csvfile, delimiter=",", restkey="other_fields")
            for row in dict_reader:
                yield row


def download_and_parse_csv(s3_path: str, download_directory: str) -> CSVSourceWrapper:
    file_name = os.path.basename(s3_path)
    download_location = os.path.join(download_directory, file_name)
    logger.debug("Download file: %s, to: %s", s3_path, download_location)

    try:
        if s3_path.startswith("s3:/"):
            file_util.download_from_s3(s3_path, download_location)
        else:
            file_util.copy_file(s3_path, download_location)
    except Exception as e:
        logger.exception(
            "Error downloading file: %s",
            s3_path,
            extra={"src": s3_path, "destination": download_directory},
        )
        raise e

    return CSVSourceWrapper(download_location)
