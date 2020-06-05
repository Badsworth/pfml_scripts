#
# File format utility class for character length formatted files
#

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Sequence


@dataclass
class FieldFormat:
    property_name: str
    length: int
    conversion_function: Optional[Callable] = None


class FileFormat:
    def __init__(self, format: Sequence[FieldFormat]):
        self.format = format

    def parse_line(self, line: str) -> Dict:
        object = {}
        start_index = 0
        for column_format in self.format:
            property_name = column_format.property_name
            end_index = start_index + column_format.length

            column_value = line[start_index:end_index].strip()

            conversion_function = column_format.conversion_function
            if conversion_function is None:
                object[property_name] = column_value
            else:
                object[property_name] = conversion_function(column_value)

            start_index = end_index

        return object

    def get_line_length(self):
        length = 0
        for column_format in self.format:
            length = length + column_format.length
        return length
