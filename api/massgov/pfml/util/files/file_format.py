#
# File format utility class for character length formatted files
#

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Sequence


class LineParseError(Exception):
    """An error when parsing a FileFormat line."""


def parse_empty_as_none(str: str) -> Optional[str]:
    if not str:
        return None

    return str


@dataclass
class FieldFormat:
    property_name: str
    length: int
    conversion_function: Optional[Callable[[str], Any]] = None


class FileFormat:
    def __init__(self, format: Sequence[FieldFormat]):
        self.format = format
        self.line_length = sum(map(lambda field: field.length, format))

    def parse_line(self, line: str) -> Dict:
        line = line.rstrip("\r\n")
        if len(line) != self.line_length:
            raise LineParseError(
                "invalid line length %i (expected %i)" % (len(line), self.line_length)
            )

        object = {}
        start_index = 0
        for column_format in self.format:
            property_name = column_format.property_name
            end_index = start_index + column_format.length

            column_value = line[start_index:end_index].strip()

            conversion_function = column_format.conversion_function

            # if no conversion function is provided, ensure empty strings are parsed as None
            if conversion_function is None:
                object[property_name] = parse_empty_as_none(column_value)
            else:
                try:
                    object[property_name] = conversion_function(column_value)
                except ValueError:
                    raise LineParseError("failed to parse field " + property_name)

            start_index = end_index

        return object

    def get_line_length(self):
        return self.line_length
