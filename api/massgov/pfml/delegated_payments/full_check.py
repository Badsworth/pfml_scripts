import csv
import io
import re
from datetime import date
from decimal import Decimal
from itertools import chain
from typing import Any, List, Optional, TextIO, Tuple, Type

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
from massgov.pfml.util.decimals import round_nearest_hundredth

DATE_FORMAT = "%m/%d/%Y"


class FullCheckField:
    description: str
    max_length: int
    value: Any
    value_type: Optional[Type[Any]] = None
    as_string: str = ""
    pattern: Optional[str] = None
    validation_issues: List[payments_util.ValidationIssue] = []

    def __init__(self, description: str, max_length: int, value: Any) -> None:
        self.description = description
        self.max_length = max_length
        self.value = value
        self.validation_issues = []

        # Only attempt to format the input value and do additional validations if the input value
        # has the correct type.
        if self.validate_type():
            self.as_string = self.format_value()
            self.validate_length()
            self.validate_pattern()

    def __str__(self) -> str:
        if len(self.validation_issues) > 0:
            raise payments_util.ValidationIssueException(
                message="Cannot stringify field because there are validation_issues",
                issues=self.validation_issues,
            )

        return self.as_string

    def add_validation_issue(self, reason: payments_util.ValidationReason, details: str) -> None:
        self.validation_issues.append(payments_util.ValidationIssue(reason, details))

    def validate_type(self) -> bool:
        if self.value_type is not None and not isinstance(self.value, self.value_type):
            msg = "Expected value for field '{}' to have type '{}', found type '{}'".format(
                self.description, self.value_type.__name__, type(self.value).__name__
            )
            self.add_validation_issue(payments_util.ValidationReason.INVALID_TYPE, msg)
            return False

        return True

    def format_value(self) -> str:
        return str(self.value or "")

    def validate_length(self) -> None:
        if len(self.as_string) > self.max_length:
            msg = "Length of field '{}' exceeded maximum length of {}: {}".format(
                self.description, self.max_length, len(self.as_string)
            )
            self.add_validation_issue(payments_util.ValidationReason.FIELD_TOO_LONG, msg)

    def validate_pattern(self) -> None:
        if self.pattern is not None and not re.match(self.pattern, self.as_string):
            msg = "Expected value for field '{}' to match pattern '{}'".format(
                self.description, self.pattern
            )
            self.add_validation_issue(payments_util.ValidationReason.INVALID_VALUE, msg)


class FullCheckIntegerField(FullCheckField):
    value: int
    value_type = int


class FullCheckDecimalField(FullCheckField):
    value: Decimal
    value_type = Decimal
    pattern = payments_util.Regexes.MONETARY_AMOUNT

    def format_value(self) -> str:
        # Force the value to have a two digit decimal part.
        return str(round_nearest_hundredth(self.value))


class FullCheckDateField(FullCheckField):
    value: date
    value_type = date

    def format_value(self) -> str:
        return self.value.strftime(DATE_FORMAT)


# Same as FullCheckCountryAbbreviationField, separate classes for clarity.
class FullCheckStateAbbreviationField(FullCheckField):
    pattern = payments_util.Regexes.STATE_ABBREVIATION

    def format_value(self) -> str:
        return self.value.upper()


# Same as FullCheckStateAbbreviationField, separate classes for clarity.
class FullCheckCountryAbbreviationField(FullCheckField):
    pattern = payments_util.Regexes.COUNTRY_ABBREVIATION

    def format_value(self) -> str:
        return self.value.upper()


class FullCheckZipCodeField(FullCheckField):
    pattern = payments_util.Regexes.ZIP_CODE


class FullCheckRecord:
    line_2: Tuple[FullCheckField, ...]
    line_3: Tuple[FullCheckField, ...]

    def __init__(
        self,
        check_number: int,
        check_date: date,
        amount: Decimal,
        memo: str,
        payee_name: str,
        address_line_1: str,
        address_line_2: Optional[str],
        city: str,
        state: str,
        zip_code: Any,
        country: str,
    ):
        # Individual records within an Full check file are represented as 2 rows with comma-separated
        # fields with line indicators 2 and 3 (1 is reserved for the file's header).
        self.line_2 = (
            FullCheckIntegerField("Line indicator", 1, 2),
            FullCheckIntegerField("Check number", 10, check_number),
            FullCheckDateField("Check date", 10, check_date),
            FullCheckDecimalField("Check amount", 14, amount),
            FullCheckField("Memo", 100, memo),
        )
        self.line_3 = (
            FullCheckIntegerField("Line indicator", 1, 3),
            FullCheckField("Payee name line 1", 85, payee_name),
            FullCheckField("Payee name line 2", 85, ""),  # Payee name line 2 will remain empty.
            FullCheckField("Payee address line 1", 85, address_line_1),
            FullCheckField("Payee address line 2", 85, address_line_2),
            FullCheckField("Payee city", 35, city),
            FullCheckStateAbbreviationField("Payee state", 2, state),
            FullCheckZipCodeField("Payee zip code", 10, zip_code),
            FullCheckCountryAbbreviationField("Payee country", 2, country),
        )

        self.validate_lines()

    def __str__(self) -> str:
        s = io.StringIO()
        w = csv.writer(s)
        w.writerow(self.line_2)
        w.writerow(self.line_3)

        return s.getvalue()

    def validate_lines(self) -> None:
        # Collect all validation issues and raise all of them at once.
        lines = self.line_2 + self.line_3

        validation_issues = list(chain.from_iterable([field.validation_issues for field in lines]))
        if len(validation_issues) > 0:
            raise payments_util.ValidationIssueException(
                message="Encountered validation issues when creating Full check record",
                issues=validation_issues,
            )


class FullCheckHeader:
    fields: Tuple[FullCheckField, ...]

    def __init__(
        self,
        name_line_1: str,
        name_line_2: str,
        address_line_1: str,
        address_line_2: str,
        city: str,
        state: str,
        zip_code: Any,
        country: str,
        account_number: int,
        routing_number: int,
    ):
        self.fields = (
            FullCheckIntegerField("Line indicator", 1, 1),
            FullCheckField("Payer name line 1", 85, name_line_1),
            FullCheckField("Payer name line 2", 85, name_line_2),
            FullCheckField("Payer address line 1", 85, address_line_1),
            FullCheckField("Payer address line 2", 85, address_line_2),
            FullCheckField("Payer city", 35, city),
            FullCheckStateAbbreviationField("Payer state", 2, state),
            FullCheckZipCodeField("Payer zip code", 10, zip_code),
            FullCheckCountryAbbreviationField("Payer country", 2, country),
            FullCheckIntegerField("Payer account number", 16, account_number),
            FullCheckIntegerField("Payer routing number", 11, routing_number),
        )
        self.validate_fields()

    def __str__(self) -> str:
        s = io.StringIO()
        w = csv.writer(s)
        w.writerow(self.fields)

        return s.getvalue()

    def validate_fields(self) -> None:
        validation_issues = list(
            chain.from_iterable([field.validation_issues for field in self.fields])
        )
        if len(validation_issues) > 0:
            raise payments_util.ValidationIssueException(
                message="Encountered validation issues when creating EZ check header",
                issues=validation_issues,
            )


class EzCheckFile:
    header: FullCheckHeader
    records: List[FullCheckRecord] = []

    def __init__(self, header: FullCheckHeader):
        if not isinstance(header, FullCheckHeader):
            raise TypeError("is not an FullCheckHeader")

        self.header = header
        self.records = []

    def add_record(self, record: FullCheckRecord) -> None:
        if not isinstance(record, FullCheckRecord):
            raise TypeError("is not an EzCheckRecord")

        self.records.append(record)

    def write_to(self, fout: TextIO) -> None:
        fout.write(str(self.header))
        for record in self.records:
            fout.write(str(record))
