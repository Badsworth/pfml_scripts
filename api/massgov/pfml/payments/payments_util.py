import csv
import json
import os
import tempfile
import xml.dom.minidom as minidom
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from xml.etree.ElementTree import Element

import boto3
import botocore
import pytz
import smart_open
from sqlalchemy import func
from sqlalchemy.orm.exc import MultipleResultsFound

import massgov.pfml.payments.config as payments_config
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.lookup import LookupTable
from massgov.pfml.db.models.employees import (
    Address,
    CtrBatchIdentifier,
    LkReferenceFileType,
    ReferenceFile,
)
from massgov.pfml.util.aws.ses import EmailRecipient, send_email, send_email_with_attachment

logger = logging.get_logger(__package__)


class Constants:
    COMPTROLLER_UNIT_CODE = "8770"
    COMPTROLLER_DEPT_CODE = "EOL"
    COMPTROLLER_AD_ID = "AD010"
    COMPTROLLER_AD_TYPE = "PA"
    DOC_PHASE_CD_FINAL_STATUS = "3 - Final"


BATCH_ID_TEMPLATE = Constants.COMPTROLLER_DEPT_CODE + "{}{}{}"  # Date, GAX/VCC, batch number.
MMARS_FILE_SKIPPED = "Did not create file for MMARS because there was no work to do"


class ValidationReason(str, Enum):
    MISSING_FIELD = "MissingField"
    MISSING_DATASET = "MissingDataset"
    MISSING_IN_DB = "MissingInDB"
    FIELD_TOO_SHORT = "FieldTooShort"
    FIELD_TOO_LONG = "FieldTooLong"
    INVALID_LOOKUP_VALUE = "InvalidLookupValue"
    INVALID_VALUE = "InvalidValue"
    MULTIPLE_VALUES_FOUND = "MultipleValuesFound"
    VALUE_NOT_FOUND = "ValueNotFound"
    NON_NULLABLE = "NonNullable"
    EXCEPTION_OCCURRED = "ExceptionOccurred"
    OUTBOUND_STATUS_ERROR = "OutboundStatusError"
    MISMATCHED_DATA = "MismatchedData"
    UNUSABLE_STATE = "UnusableState"


@dataclass(frozen=True, eq=True)
class ValidationIssue:
    reason: ValidationReason
    details: str


@dataclass
class ValidationContainer:
    # Keeping this simple for now, will likely be expanded in the future.
    record_key: str
    validation_issues: List[ValidationIssue] = field(default_factory=list)

    def add_validation_issue(self, reason: ValidationReason, details: str) -> None:
        self.validation_issues.append(ValidationIssue(reason, details))

    def has_validation_issues(self) -> bool:
        return len(self.validation_issues) != 0


def lookup_validator(
    lookup_table_clazz: Type[LookupTable],
) -> Callable[[str], Optional[ValidationReason]]:
    def validator_func(raw_value: str) -> Optional[ValidationReason]:
        # description_to_db_instance is used by the get_id method
        # If the value passed into this method is set as a key in that, it's valid
        if raw_value not in lookup_table_clazz.description_to_db_instance:
            return ValidationReason.INVALID_LOOKUP_VALUE
        return None

    return validator_func


def validate_csv_input(
    key: str,
    data: Dict[str, str],
    errors: ValidationContainer,
    required: Optional[bool] = False,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    custom_validator_func: Optional[Callable[[str], Optional[ValidationReason]]] = None,
) -> Optional[str]:
    # Don't write out the actual value in the messages, these can be SSNs, routing #s, and other PII
    value = data.get(key)
    if required and not value or value == "Unknown":
        errors.add_validation_issue(ValidationReason.MISSING_FIELD, key)
        return None  # Effectively treating "" and "Unknown" the same

    # Check the length only if it is defined
    if value is not None:
        if min_length and len(value) < min_length:
            errors.add_validation_issue(ValidationReason.FIELD_TOO_SHORT, key)
        if max_length and len(value) > max_length:
            errors.add_validation_issue(ValidationReason.FIELD_TOO_LONG, key)

        # Also only bother with custom validation if the value exists
        if custom_validator_func:
            reason = custom_validator_func(value)
            if reason:
                errors.add_validation_issue(reason, key)

    return value


def get_now() -> datetime:
    # Note that this uses Eastern time (not UTC)
    tz = pytz.timezone("America/New_York")
    return datetime.now(tz)


def validate_db_input(
    key: str,
    db_object: Any,
    required: bool,
    max_length: int,
    truncate: bool,
    func: Optional[Callable[[Any], Optional[str]]] = None,
) -> Optional[str]:
    value = getattr(db_object, key, None)

    if required and not value:
        raise Exception(f"Value for {key} is required to generate document.")
    elif not required and not value:
        return None

    if func is not None:
        value_str = func(value)
    else:
        value_str = str(value)  # Everything else should be safe to convert to string

    if value_str and len(value_str) > max_length:
        if truncate:
            return value_str[:max_length]
        # Don't add the value itself, these can include SSNs and other PII
        raise Exception(f"Value for {key} is longer than allowed length of {max_length}.")

    return value_str


def validate_input(
    key: str,
    doc_data: Dict[str, Any],
    required: bool,
    max_length: int,
    truncate: bool,
    func: Optional[Callable[[Any], str]] = None,
) -> Optional[str]:
    # This will need to be adjusted to use getattr once doc_data is a db model
    value = doc_data.get(key)

    if required and not value:
        raise Exception(f"Value for {key} is required to generate document.")
    elif not required and not value:
        return None

    if func is not None:
        value_str = func(value)
    else:
        value_str = str(value)  # Everything else should be safe to convert to string

    if len(value_str) > max_length:
        if truncate:
            return value_str[:max_length]
        # Don't add the value itself, these can include SSNs and other PII
        raise Exception(f"Value for {key} is longer than allowed length of {max_length}.")

    return value_str


def add_attributes(element: minidom.Element, attributes: Dict[str, str]) -> None:
    for k, v in attributes.items():
        element.setAttribute(k, v)


def add_cdata_elements(
    parent: minidom.Element, document: minidom.Document, elements: Dict[str, Any]
) -> None:
    for key, val in elements.items():
        elem = document.createElement(key)
        add_attributes(elem, {"Attribute": "Y"})
        parent.appendChild(elem)

        if val is None:
            cdata = document.createCDATASection("null")
        else:
            # Anything in the CDATA tag is passed directly and markup ignored
            # CTR wants DFML to send all values in as uppercase
            cdata = document.createCDATASection(str(val).upper())
        elem.appendChild(cdata)


def create_next_batch_id(
    now: datetime, file_type_descr: str, db_session: db.Session
) -> CtrBatchIdentifier:
    ctr_batch_id_pattern = BATCH_ID_TEMPLATE.format(now.strftime("%m%d"), file_type_descr, "%")
    max_batch_id_today = (
        db_session.query(func.max(CtrBatchIdentifier.batch_counter))
        .filter(
            CtrBatchIdentifier.batch_date == now.date(),
            CtrBatchIdentifier.ctr_batch_identifier.like(ctr_batch_id_pattern),
        )
        .scalar()
    )

    # Start batch counters at 10.
    # Other agencies use suffixes 1-7 (for days of the week). We start our suffixes at 10 so we
    # don't conflict with their batch IDs and have a logical starting point (10 instead of 8).
    batch_counter = 10
    if max_batch_id_today:
        batch_counter = max_batch_id_today + 1

    batch_id = BATCH_ID_TEMPLATE.format(now.strftime("%m%d"), file_type_descr, batch_counter)
    ctr_batch_id = CtrBatchIdentifier(
        ctr_batch_identifier=batch_id,
        year=now.year,
        batch_date=now.date(),
        batch_counter=batch_counter,
    )
    db_session.add(ctr_batch_id)

    return ctr_batch_id


def create_batch_id_and_reference_file(
    now: datetime, file_type: LkReferenceFileType, db_session: db.Session, ctr_outbound_path: str
) -> Tuple[CtrBatchIdentifier, ReferenceFile]:
    ctr_batch_id = create_next_batch_id(
        now, file_type.reference_file_type_description or "", db_session
    )

    s3_path = os.path.join(ctr_outbound_path, "ready")
    batch_filename = BATCH_ID_TEMPLATE.format(
        now.strftime("%Y%m%d"),
        file_type.reference_file_type_description,
        ctr_batch_id.batch_counter,
    )
    dir_path = os.path.join(s3_path, batch_filename)

    ref_file = ReferenceFile(
        file_location=dir_path,
        reference_file_type_id=file_type.reference_file_type_id,
        ctr_batch_identifier=ctr_batch_id,
    )
    db_session.add(ref_file)

    return (ctr_batch_id, ref_file)


def create_files(
    directory: str, filename: str, dat_xml_document: minidom.Document, inf_dict: Dict[str, str]
) -> Tuple[str, str]:
    dat_filepath = os.path.join(directory, f"{filename}.DAT")
    inf_filepath = os.path.join(directory, f"{filename}.INF")

    with open(dat_filepath, "wb") as dat_file:
        dat_file.write(dat_xml_document.toprettyxml(indent="   ", encoding="ISO-8859-1"))

    with open(inf_filepath, "w") as inf_file:
        for k, v in inf_dict.items():
            inf_file.write(f"{k} = {v};\n")

    return (dat_filepath, inf_filepath)


def copy_fineos_data_to_archival_bucket(expected_file_names: List[str]) -> Dict[str, str]:
    s3_config = payments_config.get_s3_config()
    return file_util.copy_s3_files(
        s3_config.fineos_data_export_path, s3_config.pfml_fineos_inbound_path, expected_file_names
    )


def group_s3_files_by_date(expected_file_names: List[str]) -> Dict[str, List[str]]:
    s3_config = payments_config.get_s3_config()
    s3_objects = file_util.list_files(s3_config.pfml_fineos_inbound_path)

    date_to_full_path: Dict = {}

    for s3_object in s3_objects:
        for expected_file_name in expected_file_names:
            if s3_object.endswith(expected_file_name):
                # Grab everything that isn't the suffix of the file name
                date = s3_object[: -len(expected_file_name)]
                fixed_date_str = date.rstrip("-")  # eg. 2020-01-01- becomes 2020-01-01

                if not date_to_full_path.get(fixed_date_str):
                    date_to_full_path[fixed_date_str] = []

                full_path = os.path.join(s3_config.pfml_fineos_inbound_path, s3_object)
                date_to_full_path[fixed_date_str].append(full_path)

    return date_to_full_path


def create_mmars_files_in_s3(
    path: str,
    filename: str,
    dat_xml_document: minidom.Document,
    inf_dict: Dict[str, str],
    session: Optional[boto3.Session] = None,
) -> Tuple[str, str]:
    if not path.startswith("s3:"):
        os.makedirs(path, exist_ok=True)

    dat_filepath = os.path.join(path, f"{filename}.DAT")
    inf_filepath = os.path.join(path, f"{filename}.INF")

    config = botocore.client.Config(retries={"max_attempts": 10, "mode": "standard"})
    transport_params = {
        "session": session or boto3.Session(),
        "resource_kwargs": {"config": config},
    }

    with smart_open.open(dat_filepath, "wb", transport_params=transport_params) as dat_file:
        dat_file.write(dat_xml_document.toprettyxml(indent="   ", encoding="ISO-8859-1"))

    with smart_open.open(inf_filepath, "w", transport_params=transport_params) as inf_file:
        for k, v in inf_dict.items():
            inf_file.write(f"{k} = {v};\n")

    return (dat_filepath, inf_filepath)


def datetime_str_to_date(datetime_str: Optional[str]) -> Optional[date]:
    if not datetime_str:
        return None
    return datetime.fromisoformat(datetime_str).date()


def get_xml_attribute(elem: Element, attr_str: str) -> Optional[str]:
    attr_val = elem.find(attr_str)
    if attr_val is not None and attr_val.text != "null":
        return attr_val.text
    else:
        return None


def compare_address_fields(first: Address, second: Address, field: str) -> bool:
    value1 = getattr(first, field)
    value2 = getattr(second, field)

    if field == "zip_code":
        value1 = value1.strip()[:5]
        value2 = value2.strip()[:5]

    if type(value1) is str:
        value1 = value1.strip().lower()
    if type(value2) is str:
        value2 = value2.strip().lower()

    return value1 == value2


def is_same_address(first: Address, second: Address) -> bool:
    if (
        compare_address_fields(first, second, "address_line_one")
        and compare_address_fields(first, second, "city")
        and compare_address_fields(first, second, "zip_code")
        and compare_address_fields(first, second, "geo_state_id")
        and compare_address_fields(first, second, "country_id")
        and compare_address_fields(first, second, "address_line_two")
    ):
        return True
    else:
        return False


def move_file_and_update_ref_file(
    db_session: db.Session, destination: str, ref_file: ReferenceFile
) -> None:
    file_util.rename_file(ref_file.file_location, destination)
    ref_file.file_location = destination


def get_inf_data_from_reference_file(
    reference: ReferenceFile, db_session: db.Session
) -> Optional[Dict]:
    ctr_id = reference.ctr_batch_identifier_id

    try:
        ctr_batch = (
            db_session.query(CtrBatchIdentifier)
            .filter(CtrBatchIdentifier.ctr_batch_identifier_id == ctr_id)
            .one_or_none()
        )

        if ctr_batch and ctr_batch.inf_data:
            return json.loads(str(ctr_batch.inf_data))
    except MultipleResultsFound as e:
        logger.exception(
            "CtrBatchIdentifier query failed: %s",
            type(e),
            extra={"CtrBatchIdentifier.ctr_batch_identifier_id": ctr_id, "error": e},
        )
    return None


def get_inf_data_as_plain_text(inf_data: Dict) -> str:
    text = ""
    for key, value in inf_data.items():
        text += f"{key} = {value}\n"

    return text


def email_inf_data(
    ref_file: ReferenceFile, db_session: db.Session, email: EmailRecipient, subject: str
) -> None:

    inf_data = get_inf_data_from_reference_file(ref_file, db_session)

    if inf_data is None:
        logger.error(
            "Could not find INF data for reference file",
            extra={"reference_file_id": ref_file.reference_file_id},
        )
        return

    payment_config = payments_config.get_email_config()
    data = get_inf_data_as_plain_text(inf_data)
    send_email(
        email,
        subject,
        data,
        payment_config.pfml_email_address,
        payment_config.bounce_forwarding_email_address,
    )


def email_fineos_vendor_customer_numbers(
    ref_file: ReferenceFile, db_session: db.Session, email: EmailRecipient, subject: str
) -> None:

    inf_data = get_inf_data_from_reference_file(ref_file, db_session)

    if inf_data is None:
        logger.error(
            "Could not find INF data for reference file",
            extra={"reference_file_id": ref_file.reference_file_id},
        )
        return

    payment_config = payments_config.get_email_config()
    body_text = get_inf_data_as_plain_text(inf_data)

    fineos_vendor_customer_numbers = get_fineos_vendor_customer_numbers_from_reference_file(
        ref_file
    )
    fieldnames = ["fineos_customer_number", "ctr_vendor_customer_code"]
    csv_data_path = [create_csv_from_list(fineos_vendor_customer_numbers, fieldnames)]

    send_email_with_attachment(
        email, subject, body_text, payment_config.pfml_email_address, csv_data_path
    )


def get_fineos_vendor_customer_numbers_from_reference_file(reference: ReferenceFile) -> List[Dict]:
    return [
        {
            "fineos_customer_number": emp.employee.fineos_customer_number,
            "ctr_vendor_customer_code": emp.employee.ctr_vendor_customer_code,
        }
        for emp in reference.employees
    ]


def create_csv_from_list(customer_data: List[Dict], fieldnames: List[str]) -> str:
    temp_file_name = f"{get_now():%Y-%m-%d}-VCC-BIEVNT-supplement"
    directory = tempfile.mkdtemp()

    csv_filepath = os.path.join(directory, f"{temp_file_name}.csv")

    with open(csv_filepath, mode="w") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()
        for data in customer_data:
            writer.writerow(data)

    return csv_filepath
