import os
from typing import Optional

import defusedxml.ElementTree as ET
from sqlalchemy.orm.exc import MultipleResultsFound

import massgov.pfml.payments.config as payments_config
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import LkReferenceFileType, ReferenceFile, ReferenceFileType
from massgov.pfml.payments.outbound_status_return import process_outbound_status_return
from massgov.pfml.payments.outbound_vendor_customer_return import (
    process_outbound_vendor_customer_return,
)
from massgov.pfml.payments.process_outbound_payment_return import process_outbound_payment_return

logger = logging.get_logger(__name__)


def handle_unknown_type(source_filepath: str, reference_file: ReferenceFile) -> None:
    error_filepath = source_filepath.replace("/received", "/error")
    try:
        file_util.rename_file(source_filepath, error_filepath)
    except Exception:
        logger.exception(
            "Exception while handling ReferenceFile at %s, could not move to %s",
            source_filepath,
            error_filepath,
            extra={"source_filepath": source_filepath, "error_filepath": error_filepath},
        )
        return
    reference_file.file_location = error_filepath
    logger.error(
        "Incorrect file type, or unparseable file, for file at %s; moved to %s",
        source_filepath,
        error_filepath,
        extra={"source_filepath": source_filepath, "error_filepath": error_filepath},
    )


def read_and_inspect_file(file_location: str) -> Optional[LkReferenceFileType]:
    file_type = None
    try:
        xml_file = file_util.read_file(file_location)
        root = ET.fromstring(xml_file)

        # check for Outbound Status Return
        if root.tag == "AMS_IC_STATUS":
            file_type = ReferenceFileType.OUTBOUND_STATUS_RETURN
        # check for Outbound Vendor Customer Return
        elif root.find("AMS_DOCUMENT") is not None:
            file_type = ReferenceFileType.OUTBOUND_VENDOR_CUSTOMER_RETURN
        # check for Outbound Payment Return
        elif root.find("PYMT_RETN_DOC") is not None:
            file_type = ReferenceFileType.OUTBOUND_PAYMENT_RETURN

        return file_type

    except IOError:
        logger.exception(
            f"Unable to open S3 file: {file_location}", extra={"file_location": file_location}
        )
    except ET.ParseError:
        logger.exception(
            f"Unable to parse file as xml: {file_location}", extra={"file_location": file_location}
        )
    except Exception:
        logger.exception(
            f"Unexpected error handling file: {file_location}",
            extra={"file_location": file_location},
        )
    return file_type


def get_reference_file(source_filepath: str, db_session: db.Session) -> Optional[ReferenceFile]:
    try:
        reference_file = (
            db_session.query(ReferenceFile)
            .filter(ReferenceFile.file_location == source_filepath)
            .one_or_none()
        )
    except MultipleResultsFound:
        logger.exception(
            f"Found more than one ReferenceFile with the same file_location: {source_filepath}",
            extra={"source_filepath": source_filepath},
        )
    except Exception:
        logger.exception(
            f"Error attempting to retrieve ReferenceFile with file_location: {source_filepath}",
            extra={"source_filepath": source_filepath},
        )

    return reference_file


def process_ctr_outbound_returns(db_session: db.Session) -> None:
    # Read files that are in /ctr/inbound/received and append ReferenceFile objects to each list,
    # then call the appropriate handler for elements in each list
    s3_config = payments_config.get_s3_config()
    base_filepath = os.path.join(s3_config.pfml_ctr_inbound_path, "received")
    try:
        ctr_inbound_filenames = file_util.list_files_without_folder(base_filepath)
    except Exception:
        logger.exception(
            f"Error connecting to S3 folder: {base_filepath}",
            extra={"base_filepath": base_filepath},
        )
        return

    outbound_status_return_files = []
    outbound_vendor_customer_return_files = []
    outbound_payment_return_files = []

    if len(ctr_inbound_filenames) == 0:
        logger.warning(
            f"Did not find any files in source S3 directory: {s3_config.pfml_ctr_inbound_path}",
            extra={"pfml_ctr_inbound_path": s3_config.pfml_ctr_inbound_path},
        )
        return

    try:
        for filename in ctr_inbound_filenames:
            source_filepath = os.path.join(base_filepath, filename)

            # retrieve ReferenceFile
            reference_file = get_reference_file(source_filepath, db_session)
            if not reference_file:
                logger.warning(
                    f"Could not find ReferenceFile record in database for file in S3 named: {source_filepath}",
                    extra={"source_filepath": source_filepath},
                )
                continue

            # parse file and determine the type of file
            file_type = read_and_inspect_file(source_filepath)

            if file_type == ReferenceFileType.OUTBOUND_STATUS_RETURN:
                reference_file.reference_file_type_id = (
                    ReferenceFileType.OUTBOUND_STATUS_RETURN.reference_file_type_id
                )
                outbound_status_return_files.append(reference_file)
            elif file_type == ReferenceFileType.OUTBOUND_VENDOR_CUSTOMER_RETURN:
                reference_file.reference_file_type_id = (
                    ReferenceFileType.OUTBOUND_VENDOR_CUSTOMER_RETURN.reference_file_type_id
                )
                outbound_vendor_customer_return_files.append(reference_file)
            elif file_type == ReferenceFileType.OUTBOUND_PAYMENT_RETURN:
                reference_file.reference_file_type_id = (
                    ReferenceFileType.OUTBOUND_PAYMENT_RETURN.reference_file_type_id
                )
                outbound_payment_return_files.append(reference_file)
            else:
                handle_unknown_type(source_filepath, reference_file)

            db_session.add(reference_file)

        # commit ReferenceFile.file_location and .reference_file_type_id changes
        db_session.commit()
    except Exception:
        logger.exception(
            f"An exception occurred processing files in {base_filepath}, database will not be updated",
            extra={"base_filepath": base_filepath},
        )
        db_session.rollback()
        return

    # TODO API-675: Remove the stub function calls and replace with the imported functions
    # Question: Should the functions also accept the opened files, so that we don't have to download twice?
    for reference_file in outbound_status_return_files:
        process_outbound_status_return(db_session, reference_file)
    for reference_file in outbound_vendor_customer_return_files:
        process_outbound_vendor_customer_return(reference_file, db_session)
    for reference_file in outbound_payment_return_files:
        process_outbound_payment_return(db_session, reference_file)
