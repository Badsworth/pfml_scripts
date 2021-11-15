#
# Parse "outstanding issue" and "paid checks" files from People's United Bank (PUB).
#

import csv
import dataclasses
import datetime
import decimal
import enum
from typing import List, Optional, TextIO

import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)


class PaidStatus(enum.Enum):
    PAID = "Paid"
    OUTSTANDING = "Outstanding"
    FUTURE = "Future"
    VOID = "Void"
    STALE = "Stale"
    STOP = "Stop"


@dataclasses.dataclass
class CheckPayment:
    """A check payment response that was parsed from a line in the CSV return file."""

    line_number: int
    raw_line: str
    check_number: str
    payee_name: str
    status: PaidStatus = PaidStatus.OUTSTANDING
    issued_date: Optional[datetime.date] = None
    paid_date: Optional[datetime.date] = None
    amount: decimal.Decimal = decimal.Decimal(0)


@dataclasses.dataclass
class CheckParseLineError:
    """A parsing problem with one line in the CSV."""

    line_number: int
    raw_line: str
    field_name: str
    warning: str


class LineParseError(Exception):
    """Internal exception used to handle a parsing problem with one line."""


class CheckParseError(Exception):
    """A unrecoverable error in the CSV return file."""


class IteratorKeepingLastItem:
    """An iterator that keeps a copy of the last item that was yielded."""

    def __init__(self, it):
        self.it = it

    def __next__(self):
        self.last_item = next(self.it)
        return self.last_item

    def __iter__(self):
        return self


class CheckReader:
    """A reader for PUB CSV return files.

    Handles both the "Outstanding Issues" and "Paid Checks" formats (these are almost identical)."""

    def __init__(self, f: TextIO):
        self.stream_iterator = IteratorKeepingLastItem(f)
        self.name = getattr(f, "name", repr(f))
        self.check_payments: List[CheckPayment] = []
        self.line_errors: List[CheckParseLineError] = []
        self.is_outstanding_issues = False
        self.is_paid_checks = False
        self.logging_extra = {"check_return.reader.name": self.name}

        self.parse_check_file()

    def get_check_payments(self) -> List[CheckPayment]:
        """Return a list of payments that were parsed from the stream."""
        return self.check_payments

    def get_line_errors(self) -> List[CheckParseLineError]:
        """Return a list of single line parse errors in the stream."""
        return self.line_errors

    def add_line_error(self, line_number: int, field_name: str, warning: str) -> None:
        """Add a line parse error to the internal list."""
        self.line_errors.append(
            CheckParseLineError(line_number, self.stream_iterator.last_item, field_name, warning)
        )

    def parse_check_file(self) -> None:
        """Parse a check return CSV stream in one of the two formats."""
        csv_reader = csv.DictReader(self.stream_iterator)
        self.validate_field_names(csv_reader)
        for line in csv_reader:
            try:
                self.parse_csv_line(csv_reader.line_num, line)
            except LineParseError as err:
                self.add_line_error(csv_reader.line_num, err.args[0], err.args[1])

        self.logging_extra["check_return.reader.payment_count"] = len(self.check_payments)
        self.logging_extra["check_return.reader.line_error_count"] = len(self.line_errors)
        logger.info("parse file done", extra=self.logging_extra)

    def parse_csv_line(self, line_number, line):
        """Parse a single csv line."""
        logging_extra = {**self.logging_extra, "check_return.reader.line_number": line_number}
        check_payment = CheckPayment(
            line_number=line_number,
            raw_line=self.stream_iterator.last_item,
            check_number=line["Check Number"],
            payee_name=line["Payee Name"],
        )
        if self.is_outstanding_issues:
            try:
                check_payment.status = PaidStatus(line["Type Detail"])
            except ValueError:
                raise LineParseError("Type Detail", "invalid status")
            check_payment.issued_date = parse_date(line["Issued Date"], "Issued Date")
            check_payment.amount = parse_decimal(line["Issued Amount"], "Issued Amount")
            if check_payment.amount <= 0:
                logger.warning("check payment amount is not positive", extra=logging_extra)
                check_payment.amount = abs(check_payment.amount)
        elif self.is_paid_checks:
            check_payment.status = PaidStatus.PAID
            check_payment.paid_date = parse_date(line["Posted Date"], "Posted Date")
            # Posted amounts are negative in the "Paid Checks" file, but we want positive for
            # consistency with "Outstanding Issues" file.
            check_payment.amount = parse_decimal(line["Posted Amount"], "Posted Amount")
            if check_payment.amount < 0:
                check_payment.amount = abs(check_payment.amount)
            else:
                logger.warning("check posted amount is not negative", extra=logging_extra)
        self.check_payments.append(check_payment)

    COMMON_FIELDS = {"Type", "Type Detail", "Check Number", "Payee Name"}
    OUTSTANDING_ISSUES_FIELDS = {"Issued Date", "Issued Amount"}
    PAID_CHECKS_FIELDS = {"Posted Date", "Posted Amount"}

    def validate_field_names(self, csv_reader: csv.DictReader) -> None:
        """Confirm that the CSV contains the expected columns."""
        if csv_reader.fieldnames is None:
            raise CheckParseError("no header row in CSV file (empty file)")
        field_names = set(csv_reader.fieldnames)
        if not self.COMMON_FIELDS <= field_names:
            raise CheckParseError("common fields not present in CSV header")
        if self.OUTSTANDING_ISSUES_FIELDS <= field_names:
            self.is_outstanding_issues = True
            logger.info("detected file type: outstanding issues", extra=self.logging_extra)
        elif self.PAID_CHECKS_FIELDS <= field_names:
            self.is_paid_checks = True
            logger.info("detected file type: paid checks", extra=self.logging_extra)
        else:
            raise CheckParseError("required fields for either format not present in CSV header")


def parse_date(string, field_name):
    """Parse a date in MM/DD/YYYY format."""
    try:
        return datetime.datetime.strptime(string, "%m/%d/%Y").date()
    except ValueError:
        logger.warning("failed to parse date in field %s", field_name)
        raise LineParseError(field_name, "invalid date")


def parse_decimal(string, field_name):
    """Parse a decimal value."""
    try:
        return decimal.Decimal(string)
    except decimal.InvalidOperation:
        logger.warning("failed to parse decimal in field %s", field_name)
        raise LineParseError(field_name, "invalid decimal")
