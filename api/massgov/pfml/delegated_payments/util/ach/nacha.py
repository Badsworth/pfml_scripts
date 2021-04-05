import decimal
import random
from datetime import datetime, timedelta
from math import floor
from typing import Any

NACHA_EOL = b"\r\n"


# Define constants here.
class Constants:
    # ODFI ID: The ID of the Originating Depository Financial Institution (ODFI)
    # ODFI is a banking term in the US in connection with ACH.
    odfi_id = "22117218"
    ref_code = ""
    modifier = "A"
    destination = "221172186"
    destination_name = "People'sUnitedBankNA"
    origin = "P046002284"
    origin_name = "MA DFML"
    originator_code = "1"
    service_code = "220"
    class_code = "PPD"
    company_name = "MA DFML"
    description = "MA PFML"
    company_id = "P046002284"
    blocking_factor = "10"
    format_code = "1"

    priority_code = "01"
    file_control_record_type = "9"
    batch_header_record_type = "5"
    batch_control_record_type = "8"
    entry_record_type = "6"
    addenda_record_indicator = "0"

    # 94 bytes specified by the format.
    record_size = "094"

    checking_return_trans_code = "21"
    checking_deposit_trans_code = "22"
    checking_prenote_trans_code = "23"
    savings_return_trans_code = "31"
    savings_deposit_trans_code = "32"
    savings_prenote_trans_code = "33"

    batch_number = "0000001"  # We will only send 1 batch per day

    addendum_record_type = "7"
    addendum_type_return = "99"
    addendum_type_notification_change = "98"

    # "C" codes documented here: https://www.vericheck.com/ach-notification-of-change-noc-codes/
    addendum_change_reason_codes = [
        "C01",
        "C02",
        "C03",
        "C04",
        "C05",
        "C06",
        "C07",
        "C09",
        "C10",
        "C11",
        "C12",
    ]

    # "R" codes documented here: https://www.vericheck.com/ach-return-codes/
    addendum_return_reason_codes = [
        "R01",
        "R02",
        "R03",
        "R04",
        "R05",
        "R06",
        "R07",
        "R08",
        "R09",
        "R10",
        "R11",
        "R12",
        "R13",
        "R14",
        "R15",
        "R16",
        "R17",
        "R20",
        "R21",
        "R22",
        "R23",
        "R24",
        "R29",
        "R31",
        "R33",
    ]

    addendum_return_types = ["98", "99"]


class NachaFile:
    def __init__(self):

        # Initialize the batches list
        self.batches = []

        # Initialize the nine_fill
        self.nine_fill = b""

        # Create the File Header and File Control records
        self.file_header = NachaFileHeader()

    def add_batch(self, batch):
        self.batches.append(batch)

    def finalize(self):

        for batch in self.batches:
            batch.finalize()

        # Get the totals from all the batches
        entry_count = 0
        entry_hash = 0
        debit_amount = 0
        credit_amount = 0
        for batch in self.batches:
            entry_count += int(batch.batch_control.get_value("entry_count"))
            entry_hash += int(batch.batch_control.get_value("entry_hash"))
            debit_amount += int(batch.batch_control.get_value("debit_amount"))
            credit_amount += int(batch.batch_control.get_value("credit_amount"))
        # Set the entry_count
        # Obtain the rightmost 10 digits of the hash
        entry_hash = entry_hash % 10000000000

        # Calculate and set the Block Count
        # There are 2 records for the file (File Header and File Control)
        # There are 2 records for each batch (Batch Header and Batch Control)
        blocking_factor = int(self.file_header.get_value("blocking_factor"))
        record_count = 2 + (len(self.batches) * 2) + entry_count
        block_count = int(floor(record_count / blocking_factor))
        block_mod = record_count % blocking_factor
        if block_mod != 0:
            block_count += 1
            self.nine_fill = NACHA_EOL.join([("9" * 94).encode()] * (blocking_factor - block_mod))

        self.file_control = NachaFileControl(
            entry_count=entry_count,
            entry_hash=entry_hash,
            debit_amount=debit_amount,
            credit_amount=credit_amount,
            block_count=block_count,
            batch_count=len(self.batches),
        )

    def to_bytes(self):
        for batch in self.batches:
            batch.finalize()

        self.finalize()

        header = self.file_header.data
        control = self.file_control.data
        batches = NACHA_EOL.join(batch.to_bytes() for batch in self.batches)
        return NACHA_EOL.join([header, batches, control, self.nine_fill])


class NachaBatch:
    def __init__(self, effective_date, today):
        # Initialize the entries list
        self.entries = []

        self.addenda = []

        # We only need 1 batch
        self.batch_number = Constants.batch_number

        # Create Header and Control records
        self.batch_header = NachaBatchHeader(effective_date, today)

    def add_entry(self, entry, addendum=None):
        trace_number = Constants.odfi_id + str(len(self.entries) + 1).rjust(7, "0")
        entry.set_value("trace_number", trace_number)

        if addendum is not None:
            entry.set_value("addenda", "1")

            addendum.set_value("original_trace_number", trace_number)
            addendum.set_value("trace_number", trace_number)
            addendum.set_value("original_receiving_dfi_id", entry.get_value("receiving_dfi_id"))

        self.entries.append(entry)

        if addendum is not None:
            self.entries.append(addendum)

    def finalize(self):
        # Calculate and set the Entry Hash
        entry_hash = 0
        debit_amount = 0
        credit_amount = 0
        for entry in self.entries:
            if entry.get_value("record_type") != Constants.entry_record_type:
                continue

            entry_hash += int(entry.get_value("receiving_dfi_id"))
            # Currently we do not support debits, but this is here anyway
            if Constants.service_code in (
                NachaBatchHeader.DEBITS_ONLY_SERVICE,
                NachaBatchHeader.MIXED_SERVICE,
            ):
                debit_amount += int(entry.get_value("amount"))
            if Constants.service_code in (
                NachaBatchHeader.CREDITS_ONLY_SERVICE,
                NachaBatchHeader.MIXED_SERVICE,
            ):
                credit_amount += int(entry.get_value("amount"))

        # Obtain the rightmost 10 digits of the entry_hash
        entry_hash = entry_hash % 10000000000

        self.batch_control = NachaBatchControl(
            entry_count=len(self.entries),
            entry_hash=entry_hash,
            debit_amount=debit_amount,
            credit_amount=credit_amount,
        )

    def to_bytes(self):
        header = self.batch_header.data
        control = self.batch_control.data
        entries = NACHA_EOL.join(entry.to_bytes() for entry in self.entries)

        return NACHA_EOL.join([header, entries, control])


class NachaRecord:
    def __init__(self, fields):
        self.fields = fields
        self.data = bytearray(b" " * 94)

        for field_name in fields:
            self.set_value(field_name, fields[field_name].data())

    def set_value(self, field_name, value):
        if field_name in self.fields:
            field = self.fields[field_name]
            start = field.start
            end = field.end

            # Insert the value into the data string.
            # Do not exceed the allowed length of the field
            self.data[start:end] = str.encode(str(value)[0 : end - start])
        else:
            raise NachaError(field_name + " isn't defined in " + self.__class__.__name__ + ".")

    def get_value(self, field_name):
        if field_name in self.fields:
            field = self.fields[field_name]
            start = field.start
            end = field.end
            return str(self.data[start:end].decode())
        else:
            raise NachaError(field_name + " isn't defined in " + self.__class__.__name__ + ".")

    def to_bytes(self):
        return self.data


class NachaField:
    name: str
    description: str
    start: int
    end: int
    length: int
    value: Any

    def __init__(self, name, start, end, value, truncate_on_overflow=False):
        self.name = name
        # decrement start by 1 for zero-based indexing in the field.
        self.start = start - 1
        self.length = end - self.start
        self.end = end
        self.value = str(value)

        if len(str(value)) > self.length and not truncate_on_overflow:
            raise NachaError(
                f"Value '{value}' for field '{name}' is longer than max length of {self.length}: {len(value)}"
            )

        if len(str(value)) > self.length and truncate_on_overflow:
            self.value = self.value[0 : self.length]

    def data(self) -> str:
        return self.value


class NumericNachaField(NachaField):
    int_value: int

    def __init__(self, name, start, end, int_value, truncate_on_overflow=False):
        self.int_value = int(int_value)
        NachaField.__init__(self, name, start, end, int(int_value), truncate_on_overflow)

    def data(self) -> str:
        return self.value.rjust(self.length, "0")


class AlphanumericNachaField(NachaField):
    def data(self) -> str:
        return self.value.ljust(self.length, " ")


class RoutingNachaField(NachaField):
    def data(self) -> str:
        return self.value.rjust(self.length, " ")


class NachaFileHeader(NachaRecord):
    def __init__(self):
        fields = {
            "record_type": NumericNachaField("Record Type", 1, 1, 1),
            "priority_code": NachaField("Priority Code", 2, 3, Constants.priority_code),
            "destination": RoutingNachaField("Immediate Destination", 4, 13, Constants.destination),
            "origin": RoutingNachaField("Immediate Origin", 14, 23, Constants.origin),
            "creation_date": NachaField(
                "File Creation Date", 24, 29, datetime.today().strftime("%y%m%d")
            ),
            "creation_time": NachaField(
                "File Creation Time", 30, 33, datetime.today().strftime("%H%M")
            ),
            "file_id_modifier": NachaField("File ID Modifier", 34, 34, Constants.modifier),
            "record_size": NachaField("Record Size", 35, 37, Constants.record_size),
            "blocking_factor": NachaField("Blocking Factor", 38, 39, Constants.blocking_factor),
            "format_code": NachaField("Format Code", 40, 40, Constants.format_code),
            "destination_name": AlphanumericNachaField(
                "Immediate Destination Name", 41, 63, Constants.destination_name
            ),
            "origin_name": AlphanumericNachaField(
                "Immediate Origin Name", 64, 86, Constants.origin_name
            ),
            "ref_code": AlphanumericNachaField("Reference Code", 87, 94, Constants.ref_code),
        }

        NachaRecord.__init__(self, fields)


class NachaFileControl(NachaRecord):
    def __init__(
        self, entry_count, entry_hash, debit_amount, credit_amount, block_count, batch_count
    ):
        # Define the Fields
        fields = {
            "record_type": NachaField("Record Type", 1, 1, Constants.file_control_record_type),
            "batch_count": NumericNachaField("Batch Count", 2, 7, batch_count),
            "block_count": NumericNachaField("Block Count", 8, 13, block_count),
            "entry_count": NumericNachaField("Entry Count", 14, 21, entry_count),
            "entry_hash": NumericNachaField("Entry Hash", 22, 31, entry_hash),
            "debit_amount": NumericNachaField("Total Debit Amount", 32, 43, debit_amount),
            "credit_amount": NumericNachaField("Total Credit Amount", 44, 55, credit_amount),
            "reserved": AlphanumericNachaField("Reserved", 56, 94, ""),
        }

        NachaRecord.__init__(self, fields)


class NachaBatchHeader(NachaRecord):

    PPD_ENTRY = "PPD"

    MIXED_SERVICE = "200"
    CREDITS_ONLY_SERVICE = "220"
    DEBITS_ONLY_SERVICE = "225"

    def __init__(self, effective_date, today):

        while effective_date.weekday() in [5, 6]:
            effective_date += timedelta(days=1)

        fields = {
            "record_type": NachaField("Record Type", 1, 1, Constants.batch_header_record_type),
            "service_code": NachaField("Service Class Code", 2, 4, Constants.service_code),
            "company_name": AlphanumericNachaField("Company Name", 5, 20, Constants.company_name),
            "company_data": AlphanumericNachaField("Company Discretionary Data", 21, 40, ""),
            "company_id": AlphanumericNachaField(
                "Company Identification", 41, 50, Constants.company_id
            ),
            "entry_class_code": AlphanumericNachaField(
                "Standard Entry Class Code", 51, 53, Constants.class_code
            ),
            "entry_description": AlphanumericNachaField(
                "Company Entry Description", 54, 63, Constants.description
            ),
            "descriptive_date": AlphanumericNachaField(
                "Company Descriptive Date", 64, 69, today.strftime("%b %y")
            ),
            "entry_date": NachaField(
                "Effective Entry Date", 70, 75, effective_date.strftime("%y%m%d")
            ),
            "settlement_date": NachaField("Settlement Date", 76, 78, ""),
            "originator_code": NachaField(
                "Originator Status Code", 79, 79, Constants.originator_code
            ),
            "odfi_id": AlphanumericNachaField(
                "Originating DFI Identification", 80, 87, Constants.odfi_id
            ),
            "batch_number": NachaField("Batch Number", 88, 94, Constants.batch_number),
        }

        NachaRecord.__init__(self, fields)


class NachaBatchControl(NachaRecord):
    def __init__(self, entry_count, entry_hash, debit_amount, credit_amount):
        fields = {
            "record_type": NachaField("Record Type", 1, 1, Constants.batch_control_record_type),
            "service_code": NumericNachaField("Service Class Code", 2, 4, Constants.service_code),
            "entry_count": NumericNachaField("Entry/Addenda Count", 5, 10, entry_count),
            "entry_hash": NumericNachaField("Entry Hash", 11, 20, entry_hash),
            "debit_amount": NumericNachaField(
                "Total Debit Entry Dollar Amount", 21, 32, debit_amount
            ),
            "credit_amount": NumericNachaField(
                "Total Credit Entry Dollar Amount", 33, 44, credit_amount
            ),
            "company_id": AlphanumericNachaField(
                "Company Identification", 45, 54, Constants.company_id
            ),
            "auth_code": AlphanumericNachaField("Message Authentication Code", 55, 73, ""),
            "reserved": NachaField("Reserved", 74, 79, ""),
            "odfi_id": NachaField("Originating DFI Identification", 80, 87, Constants.odfi_id),
            "batch_number": NachaField("Batch Number", 88, 94, Constants.batch_number),
        }

        NachaRecord.__init__(self, fields)


class NachaEntry(NachaRecord):
    def __init__(self, trans_code, receiving_dfi_id, dfi_act_num, amount, id, name):
        # Strip any periods from decimal
        amount = int(decimal.Decimal(amount) * decimal.Decimal(100))

        fields = {
            "record_type": NachaField("Record Type", 1, 1, Constants.entry_record_type),
            "transaction_code": NachaField("Transaction Code", 2, 3, trans_code),
            "receiving_dfi_id": NachaField(
                "Receiving DFI Identification", 4, 11, receiving_dfi_id[:-1]
            ),
            "check_digit": NumericNachaField("Check Digit", 12, 12, str(receiving_dfi_id)[-1]),
            "dfi_account_number": AlphanumericNachaField("DFI Account Number", 13, 29, dfi_act_num),
            "amount": NumericNachaField("Amount", 30, 39, amount),
            "id_number": AlphanumericNachaField("Individual Identification Number", 40, 54, id),
            "name": AlphanumericNachaField(
                "Individual Name", 55, 76, name, truncate_on_overflow=True
            ),
            "data": AlphanumericNachaField("Discretionary Data", 77, 78, ""),
            "addenda": NumericNachaField(
                "Addenda Record Indicator", 79, 79, Constants.addenda_record_indicator
            ),
            "trace_number": NachaField("Trace Number", 80, 94, ""),
        }

        NachaRecord.__init__(self, fields)


class NachaAddendumResponse(NachaRecord):
    def __init__(self, date_of_death, return_type, return_reason_code):

        fields = {
            "record_type": NachaField("Record Type", 1, 1, Constants.addendum_record_type),
            "type_code": NachaField("Addenda Type Code", 2, 3, return_type),
            "return_reason_code": NachaField(
                "Return reason code", 4, 6, return_reason_code  # TODO: Fix
            ),
            "original_trace_number": NumericNachaField(
                "Original trace number", 7, 21, 0
            ),  # This is filled in later
            "date_of_death": AlphanumericNachaField("Date of death", 22, 27, date_of_death),
            "original_receiving_dfi_id": NumericNachaField(
                "Original receiving DFI identification", 28, 35, 0
            ),  # This is filled in later
            "addenda_information": AlphanumericNachaField("Addenda information", 36, 79, ""),
            "trace_number": NachaField("Trace Number", 80, 94, ""),
        }

        NachaRecord.__init__(self, fields)

    @classmethod
    def random_return_type(cls):
        return random.choice(Constants.addendum_return_types)

    @classmethod
    def random_reason(cls):
        return random.choice(Constants.addendum_return_reason_codes)


class NachaError(Exception):
    pass
