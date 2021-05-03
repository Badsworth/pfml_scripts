import os
import pathlib
import re
import uuid
import xml.dom.minidom as minidom
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast
from xml.etree.ElementTree import Element

import boto3
import botocore
import pytz
import smart_open
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import ColumnProperty, class_mapper
from sqlalchemy.orm.exc import MultipleResultsFound

import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.lookup import LookupTable
from massgov.pfml.db.models import base
from massgov.pfml.db.models.employees import (
    Address,
    Claim,
    ClaimType,
    CtrBatchIdentifier,
    CtrDocumentIdentifier,
    Employee,
    EmployeeReferenceFile,
    ExperianAddressPair,
    LkClaimType,
    LkReferenceFileType,
    Payment,
    PaymentReferenceFile,
    PubEft,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.db.models.payments import (
    FineosExtractEmployeeFeed,
    FineosExtractVbiRequestedAbsence,
    FineosExtractVbiRequestedAbsenceSom,
    FineosExtractVpei,
    FineosExtractVpeiClaimDetails,
    FineosExtractVpeiPaymentDetails,
)
from massgov.pfml.util.csv import CSVSourceWrapper

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
    S3_INBOUND_SKIPPED_DIR = "skipped"
    S3_INBOUND_ERROR_DIR = "error"

    FILE_NAME_PUB_NACHA = "EOLWD-DFML-NACHA"
    FILE_NAME_PUB_EZ_CHECK = "EOLWD-DFML-EZ-CHECK"
    FILE_NAME_PUB_POSITIVE_PAY = "EOLWD-DFML-POSITIVE-PAY"
    FILE_NAME_PAYMENT_AUDIT_REPORT = "Payment-Audit-Report"

    NACHA_FILE_FORMAT = f"%Y-%m-%d-%H-%M-%S-{FILE_NAME_PUB_NACHA}"

    # When processing payments, certain states
    # are allowed to be restarted (mainly error states)
    # If we receive a payment record from FINEOS while
    # a payment is in ANY other states, the new payment record should
    # immediately go into the payment error report
    #
    # How do you know if something should go in this list?
    #   1. The payment associated with the state has reached an end state and will never change again
    #   2. The state is an error state and someone will be notified (eg. Program Integrity) via a report
    #   3. We expect, and want, to receive the payment again when the issue is corrected via the FINEOS extract
    #   4. The payment has not already been sent to PUB - even if it's an error state
    #   5. The state is in the DELEGATED_PAYMENT flow
    RESTARTABLE_PAYMENT_STATES = frozenset(
        [
            State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
            State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
            State.PAYMENT_FAILED_ADDRESS_VALIDATION,
        ]
    )
    RESTARTABLE_PAYMENT_STATE_IDS = frozenset(
        [state.state_id for state in RESTARTABLE_PAYMENT_STATES]
    )

    # States that we wait in while waiting for the reject file
    # If any payments are still in this state when the extract
    # task runs, we'll move them to an error state.
    REJECT_FILE_PENDING_STATES = [
        State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_NOT_SAMPLED,
        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_OVERPAYMENT,
        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_ZERO_PAYMENT,
        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_CANCELLATION,
        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_EMPLOYER_REIMBURSEMENT,
    ]


class Regexes:
    MONETARY_AMOUNT = (
        r"^\d*\.\d\d$"  # Decimal fields must include 2 digits following the decimal point.
    )
    STATE_ABBREVIATION = r"^[A-Z]{2}$"  # State abbreviations should be exactly 2 uppercase letters.
    COUNTRY_ABBREVIATION = (
        r"^[A-Z]{2}$"  # Country abbreviations should be exactly 2 uppercase letters.
    )
    ZIP_CODE = r"^\d{5}(-\d{4})?$"  # Zip codes must contain 5 digits and may contain +4 identifier.


class ValidationReason(str, Enum):
    MISSING_FIELD = "MissingField"
    MISSING_DATASET = "MissingDataset"
    MISSING_IN_DB = "MissingInDB"
    FIELD_TOO_SHORT = "FieldTooShort"
    FIELD_TOO_LONG = "FieldTooLong"
    INVALID_LOOKUP_VALUE = "InvalidLookupValue"
    INVALID_VALUE = "InvalidValue"
    INVALID_TYPE = "InvalidType"
    MULTIPLE_VALUES_FOUND = "MultipleValuesFound"
    VALUE_NOT_FOUND = "ValueNotFound"
    NON_NULLABLE = "NonNullable"
    EXCEPTION_OCCURRED = "ExceptionOccurred"
    OUTBOUND_STATUS_ERROR = "OutboundStatusError"
    MISMATCHED_DATA = "MismatchedData"
    UNUSABLE_STATE = "UnusableState"
    RECEIVED_PAYMENT_CURRENTLY_BEING_PROCESSED = "ReceivedPaymentCurrentlyBeingProcessed"
    UNEXPECTED_PAYMENT_TRANSACTION_TYPE = "UnexpectedPaymentTransactionType"
    EFT_PRENOTE_PENDING = "EFTPending"
    EFT_PRENOTE_REJECTED = "EFTRejected"
    CLAIMANT_MISMATCH = "ClaimantMismatch"
    CLAIM_NOT_ID_PROOFED = "ClaimNotIdProofed"


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


class ValidationIssueException(Exception):
    __slots__ = ["issues", "message"]

    def __init__(self, issues: List[ValidationIssue], message: str):
        self.issues = issues
        self.message = message


def get_now() -> datetime:
    # Note that this uses Eastern time (not UTC)
    tz = pytz.timezone("America/New_York")
    return datetime.now(tz)


def get_date_folder(current_time: Optional[datetime] = None) -> str:
    if not current_time:
        current_time = get_now()

    return current_time.strftime("%Y-%m-%d")


def build_archive_path(
    prefix: str, file_status: str, file_name: str, current_time: Optional[datetime] = None
) -> str:
    """
    Construct the path to a file. In the format: prefix / file_status / current_time as date / file_name
    If no current_time specified, will use get_now() method.
    For example:

    build_archive_path("s3://bucket/path/archive", Constants.S3_INBOUND_RECEIVED_DIR, "2021-01-01-12-00-00-example-file.csv", datetime.datetime(2021, 1, 1, 12, 0, 0))
    produces
    "s3://bucket/path/archive/received/2021-01-01/2021-01-01-12-00-00-example-file.csv"

    Parameters
    -----------
    prefix: str
      The beginning of the path, likely based on a s3 path configured by an env var
    file_status: str
      The state the file is in, should be one of constants defined above that start with S3_INBOUND or S3_OUTBOUND
    file_name: str
      name of the file - will not be modified
    current_time: Optional[datetime]
      An optional datetime for use in the path, will be formatted as %Y-%m-%d
    """

    return os.path.join(prefix, file_status, get_date_folder(current_time), file_name)


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


def zip_code_validator(zip_code: str) -> Optional[ValidationReason]:
    if not re.match(Regexes.ZIP_CODE, zip_code):
        return ValidationReason.INVALID_VALUE
    return None


def validate_csv_input(
    key: str,
    data: Dict[str, str],
    errors: ValidationContainer,
    required: Optional[bool] = False,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    custom_validator_func: Optional[Callable[[str], Optional[ValidationReason]]] = None,
) -> Optional[str]:
    value = data.get(key)
    if value == "Unknown":
        value = None  # Effectively treating "" and "Unknown" the same

    if required and not value:
        errors.add_validation_issue(ValidationReason.MISSING_FIELD, key)
        return None

    validation_issues = []
    # Check the length only if it is defined/not empty
    if value:
        if min_length and len(value) < min_length:
            validation_issues.append(ValidationReason.FIELD_TOO_SHORT)
        if max_length and len(value) > max_length:
            validation_issues.append(ValidationReason.FIELD_TOO_LONG)

        # Also only bother with custom validation if the value exists
        if custom_validator_func:
            reason = custom_validator_func(value)
            if reason:
                validation_issues.append(reason)

    if required:

        for validation_issue in validation_issues:
            # Any non-missing error types add the value to the error details
            # Note that this means these reports will contain PII data
            errors.add_validation_issue(validation_issue, f"{key}: {value}")

    # If any of the specific validations hit an error, don't return the value
    # This is true even if the field is not required as we may still use the field.
    if len(validation_issues) > 0:
        return None

    return value


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


def validate_xml_input(
    key: str,
    element: Element,
    errors: ValidationContainer,
    find_attribute: bool = False,
    required: Optional[bool] = False,
    acceptable_values: Optional[List[str]] = None,
) -> Optional[str]:
    """Validate XML input

    Primarily used to validate XML input from CTR Outbound Return files
    """
    if find_attribute:
        value = get_xml_attribute(element, key)
    else:
        value = get_xml_subelement(element, key)

    # If this attribute is required and it is either not present or set to
    # "null", then add a validation issue and return None
    if required and value is None:
        errors.add_validation_issue(ValidationReason.MISSING_FIELD, key)
        return None

    # If this attribute can only be within a set of acceptable values, then
    # add a validation issue if it isn't one of those values
    if acceptable_values and value not in acceptable_values:
        errors.add_validation_issue(ValidationReason.INVALID_VALUE, key)

    return value


def get_xml_attribute(element: Element, key: str) -> Optional[str]:
    """Get an attribute from an XML element

    Returns:
        None: if the attribute is missing
    """
    if key in element.attrib:
        return element.attrib[key]
    else:
        return None


def get_xml_subelement(element: Element, key: str) -> Optional[str]:
    """Get a subelement from an XML element

    Returns:
        None: if the subelement is missing or is set to "null"
    """
    sub_elem = element.find(key)
    if sub_elem is not None and sub_elem.text and sub_elem.text.lower() != "null":
        return sub_elem.text.strip("\n")
    else:
        return None


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
        value = v if v else "null"
        element.setAttribute(k, value)


def add_cdata_elements(
    parent: minidom.Element,
    document: minidom.Document,
    elements: Dict[str, Any],
    add_y_attribute: bool = True,
) -> None:
    for key, val in elements.items():
        elem = document.createElement(key)
        if add_y_attribute:
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
        ctr_batch_identifier_id=uuid.uuid4(),
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
        reference_file_id=uuid.uuid4(),
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
    processed_path = os.path.join(
        payments_config.get_s3_config().pfml_fineos_extract_archive_path,
        Constants.S3_INBOUND_PROCESSED_DIR,
        get_date_group_folder_name(date_group, export_type),
    )

    skipped_path = os.path.join(
        payments_config.get_s3_config().pfml_fineos_extract_archive_path,
        Constants.S3_INBOUND_SKIPPED_DIR,
        get_date_group_folder_name(date_group, export_type),
    )
    reference_file = (
        db_session.query(ReferenceFile)
        .filter(ReferenceFile.reference_file_type_id == export_type.reference_file_type_id)
        .filter(
            (ReferenceFile.file_location == processed_path)
            | (ReferenceFile.file_location == skipped_path)
        )
        .first()
    )
    return reference_file is not None


def get_fineos_max_history_date(export_type: LkReferenceFileType) -> datetime:
    """Returns a max history datetime for a given ReferenceFileType

    Only accepts:
        - ReferenceFileType.FINEOS_CLAIMANT_EXTRACT
        - ReferenceFileType.FINEOS_PAYMENT_EXTRACT

    Raises:
        ValueError: An unacceptable ReferenceFileType or a bad datestring was
                    provided by get_date_config()
    """
    date_config = payments_config.get_date_config()

    if (
        export_type.reference_file_type_id
        == ReferenceFileType.FINEOS_CLAIMANT_EXTRACT.reference_file_type_id
    ):
        datestring = date_config.fineos_claimant_extract_max_history_date

    elif (
        export_type.reference_file_type_id
        == ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id
    ):
        datestring = date_config.fineos_payment_extract_max_history_date

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
        s3_config.pfml_fineos_extract_archive_path, Constants.S3_INBOUND_RECEIVED_DIR
    )

    # If get_fineos_max_history_date() raises a ValueError, we have
    # a big problem and it should propagate up.
    max_history_date = get_fineos_max_history_date(export_type)
    max_history_date_str = max_history_date.strftime("%Y-%m-%d")

    logger.debug(
        "Copying expected files from FINEOS folder: %s (%s)",
        ", ".join(expected_file_names),
        export_type.reference_file_type_description,
        extra={
            "src": source_folder,
            "destination": destination_folder,
            "max_history_date": max_history_date_str,
        },
    )

    logger.info(
        f"Copying fineos extract files to pfml received folder starting at {max_history_date}",
        extra={"max_history_date": max_history_date},
    )

    # copy all previously unprocessed files to the received folder
    # keep a mapping of expected to mapped files grouped by date
    copied_file_mapping_by_date: Dict[str, Dict[str, str]] = {}

    def copy_files(files, folder, check_already_processed=False):
        previously_processed_date_group = set()

        logger.debug("Copying files from folder: %s", folder)

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
                logger.warning(
                    "Skipping: FINEOS extract folder named %s is not a parseable date", date_str
                )
                continue

            # If the date of the folder is older than the max_history_date,
            # we skip ahead
            if date_of_folder < max_history_date:
                logger.info(
                    "Skipping: FINEOS extract folder dated %s is prior to max_history_date %s",
                    date_str,
                    max_history_date_str,
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
                        logger.info(
                            f"Skipping: FINEOS extract folder dated {date_str} was previously processed"
                        )
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
                            f"Error while copying fineos extracts - duplicate files found for {expected_file_name}: {existing_expected_file} and {source_file}"
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
                    "Skipping FINEOS extract folder dated %s as it is prior to %s",
                    date_folder,
                    max_history_date_str,
                )
                continue
        except ValueError:
            # There are folders named config and logs that we don't want to process
            logger.warning(
                "Skipping FINEOS extract folder named %s as it is not a parseable date", date_folder
            )
            continue

        if payment_extract_reference_file_exists_by_date_group(
            db_session, date_folder, export_type
        ):
            logger.info(
                f"Skipping: FINEOS extract folder dated {date_folder} was previously processed"
            )
            continue

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
        message = f"Error while copying fineos extracts - The following expected files were not found {','.join(missing_files)}"
        logger.info(message)
        raise Exception(message)

    logger.debug(
        "Successfully copied expected files from FINEOS folder: %s (%s)",
        expected_file_names,
        export_type.reference_file_type_description,
        extra={
            "src": source_folder,
            "destination": destination_folder,
            "max_history_date": max_history_date_str,
            "copied_files": copied_file_mapping_by_date,
        },
    )

    return copied_file_mapping_by_date


def group_s3_files_by_date(expected_file_names: List[str]) -> Dict[str, List[str]]:
    s3_config = payments_config.get_s3_config()
    source_folder = os.path.join(
        s3_config.pfml_fineos_extract_archive_path, Constants.S3_INBOUND_RECEIVED_DIR
    )
    logger.info("Grouping files by date in path: %s", source_folder)

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


def compare_address_fields(first: Address, second: Address, field: str) -> bool:
    value1 = getattr(first, field)
    value2 = getattr(second, field)

    if field == "zip_code":
        value1 = value1.strip()[:5] if value1 else None
        value2 = value2.strip()[:5] if value2 else None

    if type(value1) is str:
        value1 = value1.strip().lower()
    if type(value2) is str:
        value2 = value2.strip().lower()

    if value1 is None:
        value1 = ""
    if value2 is None:
        value2 = ""

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


def find_existing_address_pair(
    employee: Optional[Employee], new_address: Address, db_session: db.Session
) -> Optional[ExperianAddressPair]:
    if not employee:
        return None

    subquery = (
        db_session.query(Payment.payment_id)
        .join(Claim)
        .filter(Claim.employee_id == employee.employee_id)
    )
    experian_address_pairs = (
        db_session.query(ExperianAddressPair)
        .join(Payment, Payment.experian_address_pair_id == ExperianAddressPair.fineos_address_id)
        .filter(Payment.payment_id.in_(subquery))
        .all()
    )

    # TODO
    for experian_address_pair in experian_address_pairs:

        existing_fineos_address = experian_address_pair.fineos_address
        existing_experian_address = experian_address_pair.experian_address

        if existing_fineos_address and is_same_address(new_address, existing_fineos_address):
            return experian_address_pair

        if existing_experian_address and is_same_address(new_address, existing_experian_address):
            return experian_address_pair

    return None


def is_same_eft(first: PubEft, second: PubEft) -> bool:
    """Returns true if all EFT fields match"""
    if (
        first.routing_nbr == second.routing_nbr
        and first.account_nbr == second.account_nbr
        and first.bank_account_type_id == second.bank_account_type_id
    ):
        return True
    else:
        return False


def find_existing_eft(employee: Optional[Employee], new_eft: PubEft) -> Optional[PubEft]:
    if not employee:
        return None

    for pub_eft_pair in employee.pub_efts.all():
        if is_same_eft(pub_eft_pair.pub_eft, new_eft):
            return pub_eft_pair.pub_eft

    return None


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
            # convert to Dict from sql alchemy JSON data type which has type Union[Dict, List]
            return cast(Dict, ctr_batch.inf_data)
    except SQLAlchemyError as e:
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


def get_fineos_vendor_customer_numbers_from_reference_file(reference: ReferenceFile) -> List[Dict]:
    return [
        {
            "fineos_customer_number": emp.employee.fineos_customer_number,
            "ctr_vendor_customer_code": emp.employee.ctr_vendor_customer_code,
        }
        for emp in reference.employees
    ]


def read_reference_file(ref_file: ReferenceFile, ref_file_type: LkReferenceFileType) -> str:
    """ Reads a ReferenceFile

    Must have a file_location and a matching file_type

    Raises:
        ValueError: if the file_type is wrong or if the file_location is missing
        Also: various errors from actually reading the file
    """

    if ref_file.file_location is None:
        raise ValueError(f"ReferenceFile {ref_file.reference_file_id} is missing a file_location")
    elif ref_file.reference_file_type_id != ref_file_type.reference_file_type_id:
        raise ValueError(
            f"ReferenceFile {ref_file.reference_file_id} is not of the expected ReferenceFileType {ref_file_type.reference_file_type_description}"
        )
    else:
        return file_util.read_file(ref_file.file_location)  # May raise file handling errors


def move_reference_file(
    db_session: db.Session, ref_file: ReferenceFile, src_dir: str, dest_dir: str
) -> None:
    """ Moves a ReferenceFile

    Renames the actual S3 file (copies and deletes) and updates the reference_file.file_location
    """
    if ref_file.file_location is None:
        raise ValueError(f"ReferenceFile {ref_file.reference_file_id} is missing a file_location")

    old_location = ref_file.file_location

    # Verify that the file_locations contains the src directory. Ex: Constants.S3_INBOUND_RECEIVED_DIR
    # This will raise a ValueError if the src directory is not found
    old_location.rindex(src_dir)

    # Replace src directory with the dest directory. Ex: Constants.S3_INBOUND_ERROR_DIR
    new_location = old_location.replace(src_dir, dest_dir)

    # Rename the file
    # This may raise S3-related errors
    file_util.rename_file(old_location, new_location)

    # Update reference_file.file_location
    try:
        ref_file.file_location = new_location
        db_session.add(ref_file)
        db_session.commit()
        logger.info(
            "Successfully moved Reference File",
            extra={
                "file_location": ref_file.file_location,
                "src_dir": src_dir,
                "dest_dir": dest_dir,
            },
        )
    except SQLAlchemyError:
        # Rollback the database transaction
        db_session.rollback()
        # Rollback the file move
        file_util.rename_file(new_location, old_location)
        # Log the exception
        logger.exception(
            "Unable to move ReferenceFile",
            extra={
                "file_location": ref_file.file_location,
                "src_dir": src_dir,
                "dest_dir": dest_dir,
            },
        )
        raise


def get_payment_by_doc_id(
    db_session: db.Session, doc_id: str
) -> Tuple[Payment, CtrDocumentIdentifier]:
    """Return the payment associated with the given DOC_ID"""
    payment_ref_file = (
        db_session.query(PaymentReferenceFile)
        .join(PaymentReferenceFile.ctr_document_identifier)
        .filter(CtrDocumentIdentifier.ctr_document_identifier == doc_id)
        .first()
    )
    if payment_ref_file is None or payment_ref_file.payment is None:
        raise ValueError("No payment was found")
    else:
        return (payment_ref_file.payment, payment_ref_file.ctr_document_identifier)


def get_model_by_doc_id(
    db_session: db.Session, doc_id: str
) -> Tuple[Union[Employee, Payment], CtrDocumentIdentifier]:
    """Return the payment or employee associated with the given DOC_ID"""
    try:
        return get_payment_by_doc_id(db_session, doc_id)
    except ValueError:
        # If no payment was found, look for an employee
        employee_ref_file = (
            db_session.query(EmployeeReferenceFile)
            .join(EmployeeReferenceFile.ctr_document_identifier)
            .filter(CtrDocumentIdentifier.ctr_document_identifier == doc_id)
            .first()
        )
        if employee_ref_file is None or employee_ref_file.employee is None:
            raise ValueError("No employee or payment was found")
        else:
            return (employee_ref_file.employee, employee_ref_file.ctr_document_identifier)


def create_model_reference_file(
    db_session: db.Session,
    ref_file: ReferenceFile,
    associated_model: Union[Payment, Employee],
    ctr_document_identifier_model: CtrDocumentIdentifier,
) -> None:
    """Creates a PaymentReferenceFile or EmployeeReferenceFile for a Payment or Employee

    Raises:
        SQLAlchemyError: if there is an issue creating the db record
    """
    model_ref_file: Union[EmployeeReferenceFile, PaymentReferenceFile]
    try:
        if isinstance(associated_model, Payment):
            model_ref_file = PaymentReferenceFile(
                payment=associated_model,
                reference_file=ref_file,
                ctr_document_identifier=ctr_document_identifier_model,
            )
        elif isinstance(associated_model, Employee):
            model_ref_file = EmployeeReferenceFile(
                employee=associated_model,
                reference_file=ref_file,
                ctr_document_identifier=ctr_document_identifier_model,
            )

        db_session.add(model_ref_file)
    except SQLAlchemyError:
        # It's possible for SQLAlchemy to raise an IntegrityError if we try to
        # add a second PaymentReferenceFile/EmployeeReferenceFile with the
        # same payment + reference_file combination. IntegrityErrors blow up
        # the db transaction and require a rollback. If we rollback, we've
        # broken all processing.
        db_session.rollback()
        logger.exception(
            "Unable to create a <Model>ReferenceFile",
            extra={
                "file_location": ref_file.file_location,
                "ctr_document_identifier": ctr_document_identifier_model.ctr_document_identifier,
            },
        )
        raise


def get_reference_file(source_filepath: str, db_session: db.Session) -> Optional[ReferenceFile]:
    """Returns a ReferenceFile for a given file location

    Raises:
        MultipleResultsFound: if multiple ReferenceFiles have the same file_location
                              This should not happen. The db is broken.
    """
    try:
        return (
            db_session.query(ReferenceFile)
            .filter(ReferenceFile.file_location == source_filepath)
            .one_or_none()
        )
    except MultipleResultsFound:
        logger.exception(
            f"Found more than one ReferenceFile with the same file_location: {source_filepath}",
            extra={"source_filepath": source_filepath},
        )
        raise


def download_and_parse_csv(s3_path: str, download_directory: str) -> CSVSourceWrapper:
    file_name = os.path.basename(s3_path)
    download_location = os.path.join(download_directory, file_name)
    logger.debug("Download file: %s, to: %s", s3_path, download_location)

    try:
        if s3_path.startswith("s3:/"):
            file_util.download_from_s3(s3_path, download_location)
        else:
            file_util.copy_file(s3_path, download_location)
    except Exception as e:
        logger.exception(
            "Error downloading file: %s",
            s3_path,
            extra={"src": s3_path, "destination": download_directory},
        )
        raise e

    return CSVSourceWrapper(download_location)


def make_keys_lowercase(data: Dict[str, Any]) -> Dict[str, Any]:
    return {k.lower(): v for k, v in data.items()}


def get_attribute_names(cls):
    return [
        prop.key
        for prop in class_mapper(cls).iterate_properties
        if isinstance(prop, ColumnProperty)
    ]


def create_staging_table_instance(
    data: Dict,
    db_cls: Union[
        Type[FineosExtractVpei],
        Type[FineosExtractVpeiClaimDetails],
        Type[FineosExtractVpeiPaymentDetails],
        Type[FineosExtractVbiRequestedAbsenceSom],
        Type[FineosExtractEmployeeFeed],
        Type[FineosExtractVbiRequestedAbsence],
    ],
    ref_file: ReferenceFile,
    fineos_extract_import_log_id: Optional[int],
) -> base.Base:
    """ We check if keys from data have a matching class property in staging model db_cls, if data contains
    properties not yet included in cls, we log a warning. We return an instance of cls, with matching properties
    from data and cls.
    Eg:
        class VbiRequestedAbsenceSom(Base):
            __tablename__ = "a"
            absence_casenumber = Column(Text)
            absence_casestatus = Column(Text)
            new_column = Column(Text)

        data = {'absence_casenumber': '123', 'absence_casestatus': 'active','new_column': 'testtest'}

        We will return an instance of class VbiRequestedAbsenceSom, with properties absence_casenumber and
        absence_casestatus. We will log a warning stating property new_column is not included in model
        class VbiRequestedAbsenceSom.
    """

    # check if extracted data types match our db model properties
    known_properties = set(get_attribute_names(db_cls))
    extracted_properties = set(data.keys())
    difference = [prop for prop in extracted_properties if prop not in known_properties]

    if len(difference) > 0:
        logger.warning(f"{db_cls.__name__} does not include properties: {','.join(difference)}")
        [data.pop(diff) for diff in difference]

    return db_cls(
        **data, reference_file=ref_file, fineos_extract_import_log_id=fineos_extract_import_log_id,
    )
