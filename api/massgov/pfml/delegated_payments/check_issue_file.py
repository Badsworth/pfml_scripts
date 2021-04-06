import decimal
from typing import Any

from massgov.pfml.delegated_payments.delegated_payments_util import (
    ValidationIssue,
    ValidationIssueException,
    ValidationReason,
)

EOL = b"\r\n"


# Define constants here.
class Constants:
    # These values are undocumented in PUB's docs, therefore labeling them generically.
    CWMA_static_field_1 = 6
    CWMA_static_field_2 = 11
    CWMA_static_field_3 = 3037

    # TODO: This value is from their example file. Should it always be used?
    bfc_code = "CLMNT"


class CheckIssueFile:
    def __init__(self):
        self.entries = []

    def add_entry(self, entry):
        self.entries.append(entry)

    def to_bytes(self):
        return EOL.join(entry.to_bytes() for entry in self.entries)


class CheckIssueRecord:
    def __init__(self, fields):
        self.fields = fields

    def field_to_bytes(self, field):
        return field.data().encode()

    def to_bytes(self):
        return b"".join(map(self.field_to_bytes, self.fields))


class CheckIssueField:
    name: str
    description: str
    length: int
    value: Any

    def __init__(self, name, length, value, truncate_on_overflow=False):
        self.name = name
        self.length = length
        self.value = str(value)

        if len(str(value)) > self.length and not truncate_on_overflow:
            details = f"Value '{value}' for field '{name}' is longer than max length of {self.length}: {len(value)}"

            issue = ValidationIssue(reason=ValidationReason.FIELD_TOO_LONG, details=details)
            raise ValidationIssueException(issues=[issue], message=details)

        if len(str(value)) > self.length and truncate_on_overflow:
            self.value = self.value[0 : self.length]

    def data(self) -> str:
        return self.value


class NumericCheckIssueField(CheckIssueField):
    int_value: int

    def __init__(self, name, length, int_value, truncate_on_overflow=False):
        self.int_value = int(int_value)
        CheckIssueField.__init__(self, name, length, int(int_value), truncate_on_overflow)

    def data(self) -> str:
        return self.value.rjust(self.length, "0")


class AlphanumericCheckIssueField(CheckIssueField):
    def data(self) -> str:
        return self.value.ljust(self.length, " ")


class BlankCheckIssueField(CheckIssueField):
    def __init__(self, name, length):
        CheckIssueField.__init__(self, name, length, "")

    def data(self) -> str:
        return self.length * " "


class CheckIssueEntry(CheckIssueRecord):
    def __init__(
        self, status_code, account_number, check_number, amount, issue_date, payee_id, payee_name
    ):
        # Strip any periods from decimal
        amount = int(decimal.Decimal(amount) * decimal.Decimal(100))
        issue_date = issue_date.strftime("%y%m%d")

        fields = (
            NumericCheckIssueField("CWMA1", 1, Constants.CWMA_static_field_1),
            AlphanumericCheckIssueField("Status Code", 1, status_code),
            NumericCheckIssueField("CWMA2", 2, Constants.CWMA_static_field_2),
            BlankCheckIssueField("Filler 1", 4),  # Static filler
            CheckIssueField("CWMA3", 4, Constants.CWMA_static_field_3),
            BlankCheckIssueField("Filler 2", 10),  # Static filler
            NumericCheckIssueField("CWMA Account #", 17, account_number),
            NumericCheckIssueField("Check #", 10, check_number),
            NumericCheckIssueField("Amount", 10, amount),
            CheckIssueField("Issue Date", 6, issue_date),
            AlphanumericCheckIssueField("Payee ID", 10, payee_id),
            CheckIssueField("BFC Code", 5, Constants.bfc_code),
            AlphanumericCheckIssueField("Trace Number", 40, payee_name),
        )

        CheckIssueRecord.__init__(self, fields)
