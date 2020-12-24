import os
import xml.dom.minidom as minidom
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

import pytz

import massgov.pfml.util.logging as logging
from massgov.pfml.db.lookup import LookupTable

logger = logging.get_logger(__package__)


class Constants:
    COMPTROLLER_UNIT_CODE = "8770"
    COMPTROLLER_DEPT_CODE = "EOL"


@dataclass
class PaymentsS3Config:
    # S3 paths (eg. s3://bucket/path/to/folder/)
    # Vars prefixed with fineos are buckets owned by fineos
    # Vars prefixed by pfml are owned by us

    # FINEOS generates data export files for PFML API to pick up
    # This is where FINEOS makes those files available to us
    fineos_data_export_path: str
    # PFML API stores a copy of all files that FINEOS generates for us
    # This is where we store that copy
    pfml_fineos_inbound_path: str
    # PFML API generates files for FINEOS to process
    # This is where FINEOS picks up files from us
    fineos_data_import_path: str
    ## PFML API stores a copy of all files that we generate for FINEOS
    ## This is where we store that copy
    pfml_fineos_outbound_path: str


def get_s3_config() -> PaymentsS3Config:
    return PaymentsS3Config(
        fineos_data_export_path=str(os.environ.get("FINEOS_DATA_EXPORT_PATH")),
        pfml_fineos_inbound_path=str(os.environ.get("PFML_FINEOS_INBOUND_PATH")),
        fineos_data_import_path=str(os.environ.get("FINEOS_DATA_IMPORT_PATH")),
        pfml_fineos_outbound_path=str(os.environ.get("PFML_FINEOS_OUTBOUND_PATH")),
    )


class ValidationReason(str, Enum):
    MISSING_FIELD = "MissingField"
    MISSING_DATASET = "MissingDataset"
    MISSING_IN_DB = "MissingInDB"
    FIELD_TOO_SHORT = "FieldTooShort"
    FIELD_TOO_LONG = "FieldTooLong"
    INVALID_LOOKUP_VALUE = "InvalidLookupValue"


@dataclass(frozen=True, eq=True)
class ValidationIssue:
    reason: ValidationReason
    details: str


@dataclass
class ValidationContainer:
    # Keeping this simple for now, will likely be expanded in the future.
    record_key: str
    validation_issues: List[ValidationIssue] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def add_validation_issue(self, reason: ValidationReason, details: str) -> None:
        self.validation_issues.append(ValidationIssue(reason, details))

    def add_error_msg(self, message: str) -> None:
        self.errors.append(message)

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
            cdata = document.createCDATASection(str(val))
        elem.appendChild(cdata)


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


def datetime_str_to_date(datetime_str: Optional[str]) -> Optional[date]:
    if not datetime_str:
        return None
    return datetime.fromisoformat(datetime_str).date()
