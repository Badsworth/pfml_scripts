import copy
import random
from typing import Any, Dict, List

import faker

random.seed(1111)

fake = faker.Faker()
fake.seed_instance(1212)

# Define some errors for testing purposes.
ERR_MISSING_REQUIRED_FIELD_DB = {
    "error_number": "0035",
    "column_name": "Field Name",
    "description": "Error 35 - Missing required field based on database settings",
}

ERR_MISSING_REQUIRED_FIELD_PREV_FIELD = {
    "error_number": "0036",
    "column_name": "Field Name",
    "description": "Error 36 - Missing required field based on previous field settings",
}

ERR_DATA_NOT_NUMERIC = {
    "error_number": "0030",
    "column_name": "Field Name",
    "description": "Error 30 - Data is not numeric",
}


def get_record_count(records: List[Any], field: str, param: Any) -> int:
    """ Utility function for getting a count of the number of records that meet a condition
        For example, passing in (field="was_processed",param=True) will give all processed records.
    """
    return sum(map(lambda record: record[field] is param, records))


def get_error_count(records: List[Any]) -> int:
    return sum(map(lambda record: len(record["errors"]) if record["errors"] else 0, records))


def construct_general_params(override_values: Dict[str, str]) -> Dict[str, str]:
    """Get default parameters for the files"""
    if override_values is None:
        params = {}
    else:
        params = copy.deepcopy(override_values)

    params.setdefault("client_identifier", "PRC123")
    params.setdefault("product_identifier", "PPC")
    params.setdefault("file_type", "CRDORD")
    params.setdefault("function", "ORDER")
    params.setdefault("creation_date_time", fake.date(pattern="%Y%m%d%H%M%S"))  # YYYYMMDDHHMMSS
    params.setdefault("client_control_id", "ABCD13052901")
    params.setdefault("sub_client_id", "SC384-9092")
    params.setdefault("card_program", "CP384-T03-020")

    return params


def create_buyer_record(
    override_values: Dict[str, str], errors: List[Dict[str, str]]
) -> Dict[str, str]:
    """Create a buyer record - this is mostly values from the ECOF (input) file. Note not every possible param is instantiated here. """
    if override_values is None:
        record = {}
    else:
        record = copy.deepcopy(override_values)

    record["record_type"] = "B"
    record["errors"] = errors
    record["was_processed"] = errors is None
    record.setdefault("card_program_type", "3")  # 3 = Payroll
    record.setdefault("card_program_identifier", "CP123-T00-000")
    record.setdefault("sub_client_identifier", "SC384-1000")
    record.setdefault(
        "buyer_type", "1"
    )  # 1 = Company, should always be 1 if card_program_type = payroll
    record.setdefault("registered_company_indicator", "Y")
    record.setdefault("card_activation_indicator", "N")
    record.setdefault("card_activation_code_type", "0")
    record.setdefault("card_ship_to_type", "1")  # 1 = Each card shipped individually to cardholder.
    record.setdefault("card_shipping_process", "2")  # 2 = Standard mail (First Class Mail)
    record.setdefault("company_account_number", "123456789")
    record.setdefault("order_delivery_fee_waived", "Y")
    record.setdefault("order_delivery_fee_amount", "0.00")
    record.setdefault("order_purchase_fee_waived", "Y")
    record.setdefault("order_purchase_fee_ammount", "0.00")

    return record


def format_buyer_record(record: Dict[str, Any]) -> str:
    """Format a buyer record, which is a comma-separate row containing 63 elements """
    fields = [
        "" for i in range(64)
    ]  # Initialize it to one extra as the specs start counting from 1, not 0

    fields[1] = record["record_type"]
    fields[2] = record["card_program_type"]
    fields[3] = record["card_program_identifier"]
    fields[4] = record["sub_client_identifier"]
    fields[5] = record["buyer_type"]
    fields[6] = record["registered_company_indicator"]
    fields[7] = record["card_activation_indicator"]
    fields[8] = record["card_activation_code_type"]
    fields[10] = record["card_ship_to_type"]
    fields[11] = record["card_shipping_process"]
    fields[14] = record["company_account_number"]
    fields[48] = record["order_delivery_fee_waived"]
    fields[50] = record["order_delivery_fee_amount"]
    fields[52] = record["order_purchase_fee_waived"]
    fields[54] = record["order_purchase_fee_ammount"]

    return ",".join(fields[1:])  # Return the fields without the first (empty) field.


def create_cardholder_record(
    override_values: Dict[str, str], errors: List[Dict[str, str]]
) -> Dict[str, str]:
    if override_values is None:
        record = {}
    else:
        record = copy.deepcopy(override_values)

    record["record_type"] = "C"  # Not overrideable.
    record["errors"] = errors
    record["was_processed"] = errors is None

    record.setdefault("client_tracking_id", "0035678123")
    record.setdefault("card_class", "03")
    record.setdefault("card_stock_id", "384CS736")
    record.setdefault("cardholder_first_name", fake.first_name().upper())
    record.setdefault("cardholder_middle_initial", fake.random_letter().upper())
    record.setdefault("cardholder_last_name", fake.last_name().upper())
    record.setdefault(
        "address_line_1",
        "{} {} {}".format(fake.building_number(), fake.street_name(), fake.street_suffix()),
    )  # fake.street_address() gives line 1 and 2, need to build it ourselves.
    record.setdefault("address_line_2", "Apt. {}".format(fake.building_number()))
    record.setdefault("cardholder_city", fake.city().upper())
    record.setdefault("cardholder_state", fake.state_abbr().upper())
    record.setdefault("cardholder_postal_code", fake.zipcode_plus4().replace("-", ""))
    record.setdefault("cardholder_country_code", "USA")
    record.setdefault("cardholder_phone_type", "1")  # 1 = work phone
    record.setdefault("cardholder_phone", "008405777")
    record.setdefault("cardholder_government_id_type", "001")  # SSN
    record.setdefault("cardholder_government_id", fake.ssn().replace("-", ""))
    record.setdefault("cardholder_date_of_birth", fake.date(pattern="%Y%m%d"))
    record.setdefault("employee_id", "0035679780")
    record.setdefault("card_value", "0.00")
    if record["was_processed"]:
        record.setdefault("primary_account_number", "511560XXXXXX7785")
        record.setdefault("routing_and_transit_number", "051000101")
        record.setdefault("dda", "5070000033386")
        record.setdefault("expiration_date", fake.date(pattern="%Y%m"))

    return record


def format_cardholder_record(record: Dict[str, Any]) -> str:
    """ Format a cardholder record which is a comma-seperated row containing 42-46 elements - processed records have 4 additional fields """
    fields = ["" for i in range(44)]

    fields[1] = record["record_type"]
    fields[2] = record["client_tracking_id"]
    fields[3] = record["card_class"]
    fields[4] = record["card_stock_id"]
    fields[6] = record["cardholder_first_name"]
    fields[7] = record["cardholder_middle_initial"]
    fields[8] = record["cardholder_last_name"]
    fields[11] = record["address_line_1"]
    fields[12] = record["address_line_2"]
    fields[14] = record["cardholder_city"]
    fields[15] = record["cardholder_state"]
    fields[16] = record["cardholder_postal_code"]
    fields[17] = record["cardholder_country_code"]
    fields[18] = record["cardholder_phone_type"]
    fields[19] = record["cardholder_phone"]
    fields[20] = record["cardholder_government_id_type"]
    fields[21] = record["cardholder_government_id"]
    fields[24] = record["cardholder_date_of_birth"]
    fields[26] = record["employee_id"]
    fields[27] = record["card_value"]
    if record["was_processed"]:
        fields.extend(["", "", "", ""])  # Extend by 4 elements
        fields[43] = record["primary_account_number"].ljust(19)
        fields[44] = record["routing_and_transit_number"]
        fields[45] = record["dda"].ljust(28)
        fields[46] = record["expiration_date"]

    return ",".join(fields[1:])  # Return the fields without the first (empty) field.


def format_error_record(
    record: Dict[str, str], general_params: Dict[str, str], err: Dict[str, str], row_number: int
) -> str:
    """Format an error record, which is a comma separated 11 element row"""
    # Two more than the actual size. One so the trailing comma is present, one so the indexing matches the spec.
    fields = ["" for i in range(13)]

    fields[1] = "E"
    fields[2] = "{:06d}".format(row_number)
    fields[3] = "001"  # This is the column number of the error
    fields[4] = record["record_type"]
    fields[5] = general_params["sub_client_id"]
    fields[6] = general_params["card_program"]
    if record["record_type"] == "C":
        fields[7] = record["cardholder_last_name"]
        fields[8] = record["client_tracking_id"]
    fields[9] = err["error_number"]
    fields[10] = err["column_name"]
    fields[11] = err["description"]

    return ",".join(fields[1:])


class CcorGenerator:
    """
      A generator for making mock text for the responses we get from Bank of America.

      CCOR = Consolidated Card Order Response

      Usage:
        import massgov.pfml.bofa.generate as generate

        builder = generate.CcorGenerator()

        # Add a valid buyer record
        builder.add_buyer_record()
        # Add a non-processed buyer record with an error.
        builder.add_buyer_record(errors=[generate.ERR_DATA_NOT_NUMERIC])

        # Add a valid cardholder record
        builder.add_cardholder_record()
        # Add a non-processed cardholder record with an error.
        builder.add_cardholder_record(errors=[generate.ERR_MISSING_REQUIRED_FIELD_DB])
        ccor = builder.build_ccor()

        Note when using add_buyer_record or add_cardholder_record, you can pass in an optional record_details dict
        to override the default/generated values of the builder.

        You can also override some global params (mainly used in header/trailer) by passing a general_params dict
        into the constructor.
    """

    general_params: Dict[str, str]
    buyer_records: List[Any]
    cardholder_records: List[Any]

    def __init__(self, general_param_overrides=None):
        """ Constructor """
        self.general_params = construct_general_params(general_param_overrides)
        self.buyer_records = []
        self.cardholder_records = []

    def add_buyer_record(
        self, record_overrides: Dict[str, str] = None, errors: List[Dict[str, str]] = None
    ) -> None:
        """ Add a buyer record - if errors are provided, it is considered a nonprocessed record """
        record = create_buyer_record(record_overrides, errors)
        self.buyer_records.append(record)

    def add_cardholder_record(
        self, record_overrides: Dict[str, str] = None, errors: List[Dict[str, str]] = None
    ) -> None:
        """ Add a cardholder record - if errors are provided, it is considered a nonprocessed record """
        record = create_cardholder_record(record_overrides, errors)
        self.cardholder_records.append(record)

    def build_ccor_header(self) -> str:
        return "DPSHEADER ,{},{},{},{},{},{},{},".format(
            self.general_params["client_identifier"],
            self.general_params["product_identifier"],
            self.general_params["file_type"],
            self.general_params["function"],
            self.general_params["creation_date_time"],
            self.general_params["client_control_id"],
            self.general_params["sub_client_id"],
        )

    def build_ccor_processed_rows(self) -> List[str]:
        lines = []

        for record in self.buyer_records:
            if not record["was_processed"]:
                continue

            # Add the buyer record
            lines.append(format_buyer_record(record))

        for record in self.cardholder_records:
            if not record["was_processed"]:
                continue

            lines.append(format_cardholder_record(record))

        return lines

    def build_ccor_processed_trailer(self) -> str:
        buyer_record_count = get_record_count(self.buyer_records, "was_processed", True)
        cardholder_record_count = get_record_count(self.cardholder_records, "was_processed", True)
        total_count = buyer_record_count + cardholder_record_count

        return "BT-PROCESSED,{:08d},{:08d},{:08d},".format(
            buyer_record_count, cardholder_record_count, total_count
        )

    def build_ccor_non_processed_rows(self) -> List[str]:
        # The errors have a counter that point to the record number from the input file
        # We don't have an input file, but we can approximate it here using the total count of processed records.
        buyer_record_count = get_record_count(self.buyer_records, "was_processed", True)
        cardholder_record_count = get_record_count(self.cardholder_records, "was_processed", True)
        counter = (
            buyer_record_count + cardholder_record_count + 1
        )  # Add 1 to initialize to the first error index
        lines = []

        for record in self.buyer_records:
            if record["was_processed"]:
                continue

            # Add the buyer record
            lines.append(format_buyer_record(record))
            # Add the error records
            for err in record["errors"]:
                lines.append(format_error_record(record, self.general_params, err, counter))
            counter += 1

        for record in self.cardholder_records:
            if record["was_processed"]:
                continue

            # Add the cardholder record
            lines.append(format_cardholder_record(record))
            # Add the error records
            for err in record["errors"]:
                lines.append(format_error_record(record, self.general_params, err, counter))
            counter += 1

        return lines

    def build_ccor_nonprocessed_trailer(self) -> str:
        buyer_record_count = get_record_count(self.buyer_records, "was_processed", False)
        cardholder_record_count = get_record_count(self.cardholder_records, "was_processed", False)
        error_count = get_error_count(self.buyer_records + self.cardholder_records)
        total_count = buyer_record_count + cardholder_record_count + error_count

        return "BT-NONPROCESSED,{:08d},{:08d},{:08d},{:08d},".format(
            buyer_record_count, cardholder_record_count, error_count, total_count
        )

    def build_ccor_trailer(self) -> str:
        count_buyer_records = len(self.buyer_records)
        count_cardholder_records = len(self.cardholder_records)
        error_count = get_error_count(self.buyer_records + self.cardholder_records)
        total_count = count_buyer_records + count_cardholder_records + error_count

        return "DPSTRAILER,{},{},{:08d},{:08d},{:08d},{:08d},".format(
            self.general_params["client_identifier"],
            self.general_params["client_control_id"],
            count_buyer_records,
            count_cardholder_records,
            error_count,
            total_count,
        )

    def build_ccor(self) -> str:
        """Build the Consolidated Card Order Response file/text (CCOR)"""
        lines = []

        # Add the header
        lines.append(self.build_ccor_header())

        # Add processed records
        lines.append("BH-PROCESSED,")  # Processed header is static
        lines.extend(self.build_ccor_processed_rows())
        lines.append(self.build_ccor_processed_trailer())
        # Add non-processed records
        lines.append("BH-NONPROCESSED,")  # Non-processed header is static
        lines.extend(self.build_ccor_non_processed_rows())
        lines.append(self.build_ccor_nonprocessed_trailer())
        # Add the trailer
        lines.append(self.build_ccor_trailer())

        return "\n".join(lines)
