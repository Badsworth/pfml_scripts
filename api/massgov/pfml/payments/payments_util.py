import csv
import json
import os
import pathlib
import re
import tempfile
import xml.dom.minidom as minidom
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, cast
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
    ClaimType,
    CtrBatchIdentifier,
    LkClaimType,
    LkReferenceFileType,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.util.aws.ses import EmailRecipient, send_email

logger = logging.get_logger(__package__)


class Constants:
    COMPTROLLER_UNIT_CODE = "8770"
    COMPTROLLER_DEPT_CODE = "EOL"
    COMPTROLLER_AD_ID = "AD010"
    COMPTROLLER_AD_TYPE = "PA"
    DOC_PHASE_CD_FINAL_STATUS = "3 - Final"

    BATCH_ID_TEMPLATE = COMPTROLLER_DEPT_CODE + "{}{}{}"  # Date, GAX/VCC, batch number.
    MMARS_FILE_SKIPPED = "Did not create file for MMARS because there was no work to do"

    S3_OUTBOUND_READY_DIR = "ready"
    S3_OUTBOUND_SENT_DIR = "sent"
    S3_OUTBOUND_ERROR_DIR = "error"
    S3_INBOUND_RECEIVED_DIR = "received"
    S3_INBOUND_PROCESSED_DIR = "processed"
    S3_INBOUND_ERROR_DIR = "error"

    RESTARTABLE_EMPLOYEE_STATES = [
        State.VENDOR_CHECK_INITIATED_BY_VENDOR_EXPORT.state_id,
        State.VENDOR_EXPORT_ERROR_REPORT_SENT.state_id,
        State.VENDOR_CHECK_INITIATED_BY_PAYMENT_EXPORT.state_id,
        State.MMARS_STATUS_CONFIRMED.state_id,
        State.VCM_REPORT_SENT.state_id,
        State.VENDOR_ALLOWABLE_TIME_IN_STATE_EXCEEDED.state_id,
        State.ADD_TO_VCC_ERROR_REPORT.state_id,
    ]


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
    lookup_table_clazz: Type[LookupTable], disallowed_lookup_values: Optional[List[str]] = None
) -> Callable[[str], Optional[ValidationReason]]:
    def validator_func(raw_value: str) -> Optional[ValidationReason]:
        # In certain scenarios, a value might be in our lookup table, but not be
        # valid for a particular scenario, this lets you skip those scenarios
        if disallowed_lookup_values and raw_value in disallowed_lookup_values:
            return ValidationReason.INVALID_LOOKUP_VALUE

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

    # Check the length only if it is defined/not empty
    if value:
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
    ctr_batch_id_pattern = Constants.BATCH_ID_TEMPLATE.format(
        now.strftime("%m%d"), file_type_descr, "%"
    )
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

    batch_id = Constants.BATCH_ID_TEMPLATE.format(
        now.strftime("%m%d"), file_type_descr, batch_counter
    )
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
) -> Tuple[CtrBatchIdentifier, ReferenceFile, pathlib.Path]:
    ctr_batch_id = create_next_batch_id(
        now, file_type.reference_file_type_description or "", db_session
    )

    s3_path = os.path.join(ctr_outbound_path, Constants.S3_OUTBOUND_READY_DIR)
    batch_filename = pathlib.Path(
        Constants.BATCH_ID_TEMPLATE.format(
            now.strftime("%Y%m%d"),
            file_type.reference_file_type_description,
            ctr_batch_id.batch_counter,
        )
    )
    dir_path = os.path.join(s3_path, batch_filename)

    ref_file = ReferenceFile(
        file_location=dir_path,
        reference_file_type_id=file_type.reference_file_type_id,
        ctr_batch_identifier=ctr_batch_id,
    )
    db_session.add(ref_file)

    return (ctr_batch_id, ref_file, batch_filename)


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


def get_date_group_str_from_path(path: str) -> Optional[str]:
    # E.g. For a file path s3://bucket/folder/2020-12-01-file-name.csv return 2020-12-01
    match = re.search("\\d{4}-\\d{2}-\\d{2}-\\d{2}-\\d{2}-\\d{2}", path)
    date_group_str = match[0] if match else None

    return date_group_str


def get_date_group_folder_name(date_group: str, reference_file_type: LkReferenceFileType) -> str:
    if (
        not reference_file_type.reference_file_type_description
    ):  # TODO remove when lookup descriptions are non nullable
        return ""

    reference_file_type_folder_postfix = reference_file_type.reference_file_type_description.lower().replace(
        " ", "-"
    )

    date_group_folder = f"{date_group}-{reference_file_type_folder_postfix}"
    return date_group_folder


def payment_extract_reference_file_exists_by_date_group(
    db_session: db.Session, date_group: str, export_type: LkReferenceFileType
) -> bool:
    path = os.path.join(
        payments_config.get_s3_config().pfml_fineos_inbound_path,
        Constants.S3_INBOUND_PROCESSED_DIR,
        get_date_group_folder_name(date_group, export_type),
    )
    reference_file = (
        db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.file_location == path,
            ReferenceFile.reference_file_type_id == export_type.reference_file_type_id,
        )
        .first()
    )

    return reference_file is not None


def get_fineos_max_history_date(export_type: LkReferenceFileType) -> datetime:
    """Returns a max history datetime for a given ReferenceFileType

    Only accepts:
        - ReferenceFileType.VENDOR_CLAIM_EXTRACT
        - ReferenceFileType.PAYMENT_EXTRACT

    Raises:
        ValueError: An unacceptable ReferenceFileType or a bad datestring was
                    provided by get_date_config()
    """
    date_config = payments_config.get_date_config()

    if (
        export_type.reference_file_type_id
        == ReferenceFileType.VENDOR_CLAIM_EXTRACT.reference_file_type_id
    ):
        datestring = date_config.fineos_vendor_max_history_date

    elif (
        export_type.reference_file_type_id
        == ReferenceFileType.PAYMENT_EXTRACT.reference_file_type_id
    ):
        datestring = date_config.fineos_payment_max_history_date

    else:
        raise ValueError(f"Incorrect export_type {export_type} provided")

    return datetime.strptime(datestring, "%Y-%m-%d")  # This may raise a ValueError


# TODO: This function should probably get broken down into smaller functions
def copy_fineos_data_to_archival_bucket(
    db_session: db.Session, expected_file_names: List[str], export_type: LkReferenceFileType
) -> Dict[str, Dict[str, str]]:
    # stage source and destination folders
    s3_config = payments_config.get_s3_config()
    source_folder = s3_config.fineos_data_export_path
    destination_folder = os.path.join(
        s3_config.pfml_fineos_inbound_path, Constants.S3_INBOUND_RECEIVED_DIR
    )

    # If get_fineos_max_history_date() raises a ValueError, we have
    # a big problem and it should propagate up.
    max_history_date = get_fineos_max_history_date(export_type)

    # copy all previously unprocessed files to the received folder
    # keep a mapping of expected to mapped files grouped by date
    copied_file_mapping_by_date: Dict[str, Dict[str, str]] = {}

    def copy_files(files, folder, check_already_processed=False):
        previously_processed_date_group = set()

        for file_path in files:
            date_str = get_date_group_str_from_path(file_path)
            # Only copy folders that are newer than a given date
            # Folders are formatted as 2020-12-17-00-00-00; we just care about the day portion
            try:
                # Cast is for picky linter that doesn't want to index an Optional[str]
                # TODO: Better is to refactor get_date_group_str_from_path() to return
                #       str and raise an error if there's an issue
                date_str_str = cast(str, date_str)
                date_of_folder = datetime.strptime(date_str_str[:10], "%Y-%m-%d")
            except (ValueError, TypeError):
                # There are non-timestamped folders that we don't want to
                # process, so we skip ahead
                logger.info(
                    f"Skipping: FINEOS extract folder named {date_str} is not a parseable date"
                )
                continue

            # If the date of the folder is older than the max_history_date,
            # we skip ahead
            if date_of_folder < max_history_date:
                max_history_date_str = max_history_date.strftime("%Y-%m-%d")
                logger.info(
                    f"Skipping: FINEOS extract folder dated {date_str} is prior to max_history_date {max_history_date_str}"
                )
                continue

            for expected_file_name in expected_file_names:
                if file_path.endswith(expected_file_name) and date_str is not None:
                    source_file = os.path.join(source_folder, folder, file_path)

                    if check_already_processed and (
                        date_str in previously_processed_date_group
                        or payment_extract_reference_file_exists_by_date_group(
                            db_session, date_str, export_type
                        )
                    ):
                        previously_processed_date_group.add(date_str)
                        continue

                    file_name = file_util.get_file_name(file_path)
                    destination_file = os.path.join(destination_folder, file_name)

                    if copied_file_mapping_by_date.get(date_str) is None:
                        copied_file_mapping_by_date[date_str] = dict.fromkeys(
                            expected_file_names, ""
                        )

                    # We found two files which end the same, error
                    existing_expected_file = copied_file_mapping_by_date[date_str].get(
                        expected_file_name
                    )
                    if existing_expected_file and existing_expected_file != source_file:
                        raise RuntimeError(
                            f"Duplicate files found for {expected_file_name}: {existing_expected_file} and {source_file}"
                        )

                    file_util.copy_file(source_file, destination_file)
                    copied_file_mapping_by_date[date_str][expected_file_name] = destination_file

    # process top level files
    top_level_files = file_util.list_files(source_folder)
    copy_files(top_level_files, folder="", check_already_processed=True)

    # check archive folders for unprocessed dates
    date_folders = file_util.list_folders(source_folder)
    for date_folder in date_folders:
        # We never want to process anything from before 2020-12-17 in any environment
        # Add a hardcoded-check here to exclude data that is that old
        # Folders are formatted as 2020-12-17-00-00-00, we just care about the day portion
        try:
            date_of_folder = datetime.strptime(date_folder[:10], "%Y-%m-%d")
            if date_of_folder < max_history_date:
                logger.info(
                    f"Skipping FINEOS extract folder dated {date_folder} as it is prior to 12/17/2020"
                )
                continue
        except ValueError:
            # There are folders named config and logs that we don't want to process
            logger.info(
                f"Skipping FINEOS extract folder named {date_folder} as it is not a parseable date"
            )
            continue

        if not payment_extract_reference_file_exists_by_date_group(
            db_session, date_folder, export_type
        ):
            subfolder_path = os.path.join(source_folder, date_folder)
            subfolder_files = file_util.list_files(subfolder_path)
            copy_files(subfolder_files, folder=date_folder, check_already_processed=False)

    # check for missing files in each group
    missing_files = []
    for date_str, copied_file_mapping in copied_file_mapping_by_date.items():
        for expected_file_name, destination in copied_file_mapping.items():
            if not destination:
                missing_files.append(f"{date_str}-{expected_file_name}")

    if missing_files:
        raise Exception(f"The following files were not found in S3 {','.join(missing_files)}")

    return copied_file_mapping_by_date


# TODO adjust tests and replace with new version
def group_s3_files_by_date(expected_file_names: List[str]) -> Dict[str, List[str]]:
    s3_config = payments_config.get_s3_config()
    source_folder = os.path.join(
        s3_config.pfml_fineos_inbound_path, Constants.S3_INBOUND_RECEIVED_DIR
    )
    logger.info(f"Grouping files by date in {source_folder}")
    s3_objects = file_util.list_files(source_folder)
    s3_objects.sort()

    date_to_full_path: Dict[str, List[str]] = OrderedDict()

    for s3_object in s3_objects:
        fixed_date_str = get_date_group_str_from_path(s3_object)
        for expected_file_name in expected_file_names:
            if s3_object.endswith(expected_file_name) and fixed_date_str is not None:
                if not date_to_full_path.get(fixed_date_str):
                    date_to_full_path[fixed_date_str] = []

                full_path = os.path.join(source_folder, s3_object)
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
            extra={"CtrBatchIdentifier.ctr_batch_identifier_id": ctr_id},
        )
    return None


def get_inf_data_as_plain_text(inf_data: Dict) -> str:
    text = ""
    for key, value in inf_data.items():
        text += f"{key} = {value}\n"

    return text


def email_inf_data(
    ref_file: ReferenceFile, db_session: db.Session, recipient: EmailRecipient, subject: str
) -> None:

    inf_data = get_inf_data_from_reference_file(ref_file, db_session)

    if inf_data is None:
        logger.error(
            "Could not find INF data for reference file",
            extra={"reference_file_id": ref_file.reference_file_id},
        )
        return

    payment_config = payments_config.get_email_config()
    sender = payment_config.pfml_email_address
    data = get_inf_data_as_plain_text(inf_data)
    bounce_forwarding_email_address_arn = payment_config.bounce_forwarding_email_address_arn
    send_email(
        recipient=recipient,
        subject=subject,
        body_text=data,
        sender=sender,
        bounce_forwarding_email_address_arn=bounce_forwarding_email_address_arn,
    )


def get_mapped_claim_type(claim_type_str: str) -> LkClaimType:
    """Given a string from a Vendor Extract, return a LkClaimType

    Raises:
        ValueError: if the string does not match an existing LkClaimType
    """
    if claim_type_str == "Family":
        return ClaimType.FAMILY_LEAVE
    elif claim_type_str == "Employee":
        return ClaimType.MEDICAL_LEAVE
    else:
        raise ValueError("Unknown claim type")


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

    send_email(
        email,
        subject,
        body_text,
        payment_config.pfml_email_address,
        payment_config.bounce_forwarding_email_address_arn,
        csv_data_path,
    )


def get_fineos_vendor_customer_numbers_from_reference_file(reference: ReferenceFile) -> List[Dict]:
    return [
        {
            "fineos_customer_number": emp.employee.fineos_customer_number,
            "ctr_vendor_customer_code": emp.employee.ctr_vendor_customer_code,
        }
        for emp in reference.employees
    ]


def create_csv_from_list(customer_data: List[Dict], fieldnames: List[str]) -> pathlib.Path:
    temp_file_name = f"{get_now():%Y-%m-%d}-VCC-BIEVNT-supplement"
    directory = tempfile.mkdtemp()

    csv_filepath = pathlib.Path(os.path.join(directory, f"{temp_file_name}.csv"))

    with open(csv_filepath, mode="w") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()
        for data in customer_data:
            writer.writerow(data)

    return csv_filepath
