#
# ACH file reader.
#

import dataclasses
import decimal
import enum
from typing import Any, Dict, List, Optional, Sequence, TextIO

import massgov.pfml.util.logging
from massgov.pfml.util.files.file_format import FieldFormat, FileFormat, LineParseError

logger = massgov.pfml.util.logging.get_logger(__name__)


class TypeCode(enum.IntEnum):
    FILE_HEADER = 1
    BATCH_HEADER = 5
    ENTRY_DETAIL = 6
    ADDENDA = 7
    BATCH_CONTROL = 8
    FILE_CONTROL = 9

    ADDENDA_NOTIFICATION_OF_CHANGE = 98
    ADDENDA_RETURN = 99


ENTRY_DETAIL_FORMAT = FileFormat(
    (
        FieldFormat("record_type_code", 1, int),
        FieldFormat("transaction_code", 2, int),
        FieldFormat("receiving_dfi_id", 8),
        FieldFormat("check_digit", 1, int),
        FieldFormat("dfi_account_number", 17),
        FieldFormat("amount", 10, int),
        FieldFormat("id_number", 15),
        FieldFormat("individual_name", 22),
        FieldFormat("discretionary_data", 2),
        FieldFormat("addenda_indicator", 1, int),
        FieldFormat("trace_number", 15, int),
    )
)

ADDENDA_DETAIL_FORMAT = FileFormat(
    (
        FieldFormat("record_type_code", 1, int),
        FieldFormat("addenda_type_code", 2, int),
        FieldFormat("return_reason_code", 3),
        FieldFormat("original_trace_number", 15, int),
        FieldFormat("date_of_death", 6),
        FieldFormat("original_dfi_id", 8),
        FieldFormat("addenda_information", 44),
        FieldFormat("addenda_trace_number", 15, int),
    )
)

FILE_CONTROL_FORMAT = FileFormat(
    (
        FieldFormat("record_type_code", 1, int),
        FieldFormat("batch_count", 6, int),
        FieldFormat("block_count", 6, int),
        FieldFormat("entry_count", 8, int),
        FieldFormat("entry_hash", 10, int),
        FieldFormat("total_debit_amount", 12, int),
        FieldFormat("total_credit_amount", 12, int),
        FieldFormat("reserved", 39),
    )
)


class ACHFatalParseError(Exception):
    """A unrecoverable error in the ACH file."""


@dataclasses.dataclass
class RawRecord:
    type_code: TypeCode
    line_number: int
    data: str


@dataclasses.dataclass
class ACHReturn:
    id_number: str
    return_reason_code: str
    original_dfi_id: str  # Routing number
    dfi_account_number: str  # Account number
    amount: decimal.Decimal
    name: str
    line_number: int
    raw_record: RawRecord

    def is_change_notification(self):
        return False

    def get_details_for_log(self) -> Dict[str, Any]:
        return {
            "type_code": self.raw_record.type_code.value,
            "ach_id_number": self.id_number,
            "reason_code": self.return_reason_code,
        }

    def get_details_for_error(self) -> Dict[str, Any]:
        return {
            "ach_id_number": self.id_number,
            "reason_code": self.return_reason_code,
        }


@dataclasses.dataclass
class ACHChangeNotification(ACHReturn):
    addenda_information: str

    def is_change_notification(self):
        return True


@dataclasses.dataclass
class ACHWarning:
    raw_record: RawRecord
    warning: str

    def get_details_for_log(self) -> Dict[str, Any]:
        return {
            "type_code": self.raw_record.type_code.value,
            "raw_data": self.raw_record.data,
        }


class ACHReader:
    """A reader for ACH format files."""

    def __init__(self, f: TextIO):
        self.f = f
        self.name = getattr(self.f, "name", repr(self.f))
        self.ach_returns: List[ACHReturn] = []
        self.change_notifications: List[ACHChangeNotification] = []
        self.warnings: List[ACHWarning] = []
        self.batch_count = 0
        self.entry_count = 0

        self.parse_ach_file()

    def get_ach_returns(self) -> List[ACHReturn]:
        return self.ach_returns

    def get_change_notifications(self) -> List[ACHChangeNotification]:
        return self.change_notifications

    def get_warnings(self) -> List[ACHWarning]:
        return self.warnings

    def add_warning(self, raw_record: RawRecord, warning: str) -> None:
        self.warnings.append(ACHWarning(raw_record=raw_record, warning=warning))

    def parse_ach_file(self):
        """Parse [file header record, ...batches..., file control record]."""
        raw_records = self.parse_raw()
        if not raw_records:
            raise ACHFatalParseError("empty file")

        if raw_records[0].type_code != TypeCode.FILE_HEADER:
            raise ACHFatalParseError(
                "unexpected type for first record (expected FILE_HEADER)", raw_records[0].type_code
            )

        file_control = None
        last_raw_record = raw_records[-1]
        if last_raw_record.type_code == TypeCode.FILE_CONTROL:
            raw_records.pop()
            try:
                file_control = FILE_CONTROL_FORMAT.parse_line(last_raw_record.data)
            except LineParseError as err:
                self.add_warning(last_raw_record, str(err))
        else:
            self.add_warning(last_raw_record, "missing FILE_CONTROL at end of file")

        self.parse_batches(raw_records[1:])

        self.validate_file_control_record(file_control, last_raw_record)

        logger.info(
            "parse file done",
            extra={
                "ach.reader.name": self.name,
                "ach.reader.ach_return_count": len(self.ach_returns),
                "ach.reader.change_notification_count": len(self.change_notifications),
                "ach.reader.warning_count": len(self.warnings),
            },
        )

    def validate_file_control_record(
        self, file_control: Optional[dict], raw_record: RawRecord
    ) -> None:
        """Validate counts in file control record, if one was present (it is required)."""
        if not file_control:
            return

        if self.batch_count != file_control["batch_count"]:
            self.add_warning(
                raw_record,
                "batch count mismatch (found %i, control %i)"
                % (self.batch_count, file_control["batch_count"]),
            )
        if self.entry_count != file_control["entry_count"]:
            self.add_warning(
                raw_record,
                "entry count mismatch (found %i, control %i)"
                % (self.entry_count, file_control["entry_count"]),
            )

    def parse_raw(self) -> List[RawRecord]:
        """Parse stream of lines to RawRecord objects."""
        raw_records = []
        for line_number, data in enumerate(self.f, start=1):
            data = data.rstrip("\r\n")
            try:
                record_type = TypeCode(int(data[0]))
            except ValueError:
                raise ACHFatalParseError("invalid type code %r" % data[0])
            if data == "9" * 94:
                # Padding line
                continue
            raw_record = RawRecord(type_code=record_type, line_number=line_number, data=data)
            raw_records.append(raw_record)
        return raw_records

    def parse_batches(self, raw_records: Sequence[RawRecord]) -> None:
        """Parse repeatedly [batch header record, ...entries..., batch control record]."""
        batches = partition_by_type_code(raw_records, TypeCode.BATCH_HEADER)
        self.batch_count = len(batches)

        for batch in batches:
            batch_first, batch_last = batch[0], batch[-1]

            if batch_first.type_code == TypeCode.BATCH_HEADER:
                batch.pop(0)
            else:
                self.add_warning(batch_first, "missing BATCH_HEADER at start of batch")

            if batch_last.type_code == TypeCode.BATCH_CONTROL:
                batch.pop()
            else:
                self.add_warning(batch_last, "missing BATCH_CONTROL at end of batch")

            self.parse_entries(batch)

    def parse_entries(self, raw_records: Sequence[RawRecord]) -> None:
        """Parse a batch of entries, each with attached addenda."""
        entries = partition_by_type_code(raw_records, TypeCode.ENTRY_DETAIL)
        self.entry_count += len(raw_records)

        for entry in entries:
            self.parse_entry_and_addenda(entry)

    def parse_entry_and_addenda(self, raw_records: Sequence[RawRecord]) -> None:
        """Parse a single entry with an addenda line."""
        record_types = tuple(map(lambda rr: rr.type_code, raw_records))
        if record_types != (TypeCode.ENTRY_DETAIL, TypeCode.ADDENDA):
            self.add_warning(
                raw_records[0],
                "unexpected types %r (expected ENTRY_DETAIL, ADDENDA)" % (record_types,),
            )
            return

        raw_entry_detail, raw_addenda = raw_records

        errors = 0
        try:
            entry = ENTRY_DETAIL_FORMAT.parse_line(raw_entry_detail.data)
        except LineParseError as err:
            self.add_warning(raw_entry_detail, str(err))
            errors += 1

        try:
            addenda = ADDENDA_DETAIL_FORMAT.parse_line(raw_addenda.data)
        except LineParseError as err:
            self.add_warning(raw_addenda, str(err))
            errors += 1

        if errors:
            return

        if entry["addenda_indicator"] != 1:
            self.add_warning(raw_entry_detail, "expected addenda indicator")
            return

        self.process_entry({**entry, **addenda}, raw_entry_detail, raw_addenda)

    def process_entry(
        self, entry: dict, raw_entry_detail: RawRecord, raw_addenda: RawRecord
    ) -> None:
        if entry["addenda_type_code"] == TypeCode.ADDENDA_RETURN:
            ach_return = ACHReturn(
                id_number=entry["id_number"],
                return_reason_code=entry["return_reason_code"],
                original_dfi_id=entry["original_dfi_id"],
                dfi_account_number=entry["dfi_account_number"],
                amount=decimal.Decimal(entry["amount"]) / decimal.Decimal(100),
                name=entry["individual_name"],
                line_number=raw_entry_detail.line_number,
                raw_record=raw_entry_detail,
            )
            self.ach_returns.append(ach_return)
        elif entry["addenda_type_code"] == TypeCode.ADDENDA_NOTIFICATION_OF_CHANGE:
            change_notification = ACHChangeNotification(
                id_number=entry["id_number"],
                return_reason_code=entry["return_reason_code"],
                original_dfi_id=entry["original_dfi_id"],
                dfi_account_number=entry["dfi_account_number"],
                amount=decimal.Decimal(entry["amount"]) / decimal.Decimal(100),
                name=entry["individual_name"],
                addenda_information=entry["addenda_information"],
                line_number=raw_entry_detail.line_number,
                raw_record=raw_entry_detail,
            )
            self.change_notifications.append(change_notification)
        else:
            self.add_warning(
                raw_addenda, "unexpected addenda type code %i" % entry["addenda_type_code"]
            )


def partition_by_type_code(
    raw_records: Sequence[RawRecord], type_code: TypeCode
) -> List[List[RawRecord]]:
    """Split a list of raw records into sub-lists, splitting at records with the given type code."""
    partitions = []
    current: List[RawRecord] = []
    for raw_record in raw_records:
        if raw_record.type_code == type_code:
            if current:
                partitions.append(current)
            current = [raw_record]
        else:
            current.append(raw_record)
    if current:
        partitions.append(current)
    return partitions
