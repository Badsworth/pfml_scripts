import csv
from dataclasses import dataclass
from typing import Dict, List, TextIO

import massgov.pfml.util.logging
from massgov.pfml.delegated_payments.pub.pub_util import IteratorKeepingLastItem
from massgov.pfml.util.strings import remove_unicode_replacement_char

logger = massgov.pfml.util.logging.get_logger(__name__)


@dataclass
class ManualPubParseLineError:
    """A parsing problem with one line in the CSV."""

    line_number: int
    raw_line: str
    field_name: str
    warning: str


class LineParseError(Exception):
    """Internal exception used to handle a parsing problem with one line."""


class FileParseError(Exception):
    """A unrecoverable error in the CSV manual PUB reject parser"""


@dataclass
class ManualPubReject:
    """A manual PUB reject that was parsed from a line in the CSV return file."""

    line_number: int
    raw_line: str
    record_id: str
    notes: str


class ManualPubRejectFileParser:
    """
    A reader for a PUB manual reject file parser

    File is expected to contain an ID and Notes column
    See https://lwd.atlassian.net/wiki/spaces/API/pages/2241855513/Rejecting+PUB+Payments+Manually+ACH
    for further details on how this is used.
    """

    RECORD_ID_COLUMN = "ID"
    NOTES_COLUMN = "Notes"

    EXPECTED_FIELD_NAMES = {RECORD_ID_COLUMN, NOTES_COLUMN}

    def __init__(self, f: TextIO):
        self.stream_iterator = IteratorKeepingLastItem(f)
        self.name = getattr(f, "name", repr(f))
        self.manual_pub_rejects: List[ManualPubReject] = []
        self.line_errors: List[ManualPubParseLineError] = []
        self.logging_extra = {"manual_pub_reject_parser.name": self.name}

        self.parse_manual_pub_reject_file()

    def get_line_errors(self) -> List[ManualPubParseLineError]:
        """Return a list of single line parse errors in the stream."""
        return self.line_errors

    def get_manual_pub_rejects(self) -> List[ManualPubReject]:
        """Return a list of the manual PUB rejects successfully parsed from the stream."""
        return self.manual_pub_rejects

    def add_line_error(self, line_number: int, field_name: str, warning: str) -> None:
        """Add a line parse error to the internal list."""
        self.line_errors.append(
            ManualPubParseLineError(
                line_number, self.stream_iterator.current_item, field_name, warning
            )
        )

    def parse_manual_pub_reject_file(self) -> None:
        logger.info("Parsing manual PUB reject file", extra=self.logging_extra)
        csv_reader = csv.DictReader(self.stream_iterator)

        self.validate_field_names(csv_reader)

        for line in csv_reader:
            try:
                self.parse_csv_line(csv_reader.line_num, line)
            except LineParseError as err:
                self.add_line_error(csv_reader.line_num, err.args[0], err.args[1])

        self.logging_extra["manual_pub_reject_parser.record_count"] = len(self.manual_pub_rejects)
        self.logging_extra["manual_pub_reject_parser.line_error_count"] = len(self.line_errors)
        logger.info("Finished parsing manual PUB reject file", extra=self.logging_extra)

    def validate_field_names(self, csv_reader: csv.DictReader) -> None:
        if csv_reader.fieldnames is None:
            raise FileParseError("No header row in Manual PUB reject CSV file - empty file")

        field_names = set(csv_reader.fieldnames)

        if not self.EXPECTED_FIELD_NAMES <= field_names:
            raise FileParseError("Expected field names not present in manual PUB reject CSV file")

    def parse_csv_line(self, line_number: int, line: Dict[str, str]) -> None:
        """Parse a single csv line"""

        # Similar to the payment reject report we get back from the PI team
        # filter this odd character out to keep notes clean.
        notes = remove_unicode_replacement_char(line[self.NOTES_COLUMN])

        manual_pub_reject = ManualPubReject(
            line_number=line_number,
            raw_line=self.stream_iterator.current_item,
            record_id=line[self.RECORD_ID_COLUMN],
            notes=notes,
        )

        self.manual_pub_rejects.append(manual_pub_reject)
