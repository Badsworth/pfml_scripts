import os
from dataclasses import dataclass
from typing import List, Optional

import defusedxml.ElementTree as ET

import massgov.pfml.payments.config as payments_config
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import LkReferenceFileType, ReferenceFile, ReferenceFileType

from . import outbound_payment_return, outbound_status_return, outbound_vendor_customer_return

logger = logging.get_logger(__name__)


OUTBOUND_STATUS_RETURN_XML_DOC_ROOT_ELEMENT = "AMS_IC_STATUS"


@dataclass
class ProcessOutboundReturnsConfig:
    process_outbound_vendor_returns: bool = True
    process_outbound_status_returns: bool = True
    process_outbound_payment_returns: bool = True


class OutboundReturnData:
    db_session: db.Session
    outbound_status_return_files: List[ReferenceFile]
    outbound_vendor_customer_return_files: List[ReferenceFile]
    outbound_payment_return_files: List[ReferenceFile]

    def __init__(self, db_session: db.Session):
        self.db_session = db_session
        self.outbound_status_return_files = []
        self.outbound_vendor_customer_return_files = []
        self.outbound_payment_return_files = []

    def sort_returns(self):
        self.outbound_status_return_files.sort(key=lambda ref_file: ref_file.file_location)
        self.outbound_vendor_customer_return_files.sort(key=lambda ref_file: ref_file.file_location)
        self.outbound_payment_return_files.sort(key=lambda ref_file: ref_file.file_location)


def _identify_outbound_return(ref_file: ReferenceFile) -> LkReferenceFileType:
    """Identify which type of Outbound Return a given file is

    Raises:
        ValueError: if it is not a known Outbound Return type
    """
    xml_file = file_util.read_file(ref_file.file_location)
    root = ET.fromstring(xml_file)

    # check for Outbound Status Return
    if root.tag == OUTBOUND_STATUS_RETURN_XML_DOC_ROOT_ELEMENT:
        return ReferenceFileType.OUTBOUND_STATUS_RETURN
    # check for Outbound Vendor Customer Return
    elif root.find("AMS_DOCUMENT") is not None:
        return ReferenceFileType.OUTBOUND_VENDOR_CUSTOMER_RETURN
    # check for Outbound Payment Return
    elif root.find("PYMT_RETN_DOC") is not None:
        return ReferenceFileType.OUTBOUND_PAYMENT_RETURN
    else:
        raise ValueError("Unknown Outbound Return type")


def _set_outbound_reference_file_type(
    db_session: db.Session, ref_file: ReferenceFile, outbound_return_data: OutboundReturnData
) -> None:
    """Identifies each reference file and sets its type"""
    try:
        file_type = _identify_outbound_return(ref_file)
    except Exception:
        # Handle unkown types
        logger.warning(
            "Unexpected file type at %s",
            ref_file.file_location,
            extra={"file_location": ref_file.file_location},
        )
        # Note: move_reference_file() calls db_session.commit(), but that
        # should be ok; it should not interrupt any in-progress
        # transactions
        payments_util.move_reference_file(
            db_session,
            ref_file,
            payments_util.Constants.S3_INBOUND_RECEIVED_DIR,
            payments_util.Constants.S3_INBOUND_ERROR_DIR,
        )
        return

    logger.info(
        "Identified outbound file type for file: %s, type: %s", ref_file.file_location, file_type
    )

    # Handle Outbound Status Returns
    if file_type == ReferenceFileType.OUTBOUND_STATUS_RETURN:
        ref_file.reference_file_type_id = (
            ReferenceFileType.OUTBOUND_STATUS_RETURN.reference_file_type_id
        )
        outbound_return_data.outbound_status_return_files.append(ref_file)

    # Handle Outbound Vendor Customer Returns
    elif file_type == ReferenceFileType.OUTBOUND_VENDOR_CUSTOMER_RETURN:
        ref_file.reference_file_type_id = (
            ReferenceFileType.OUTBOUND_VENDOR_CUSTOMER_RETURN.reference_file_type_id
        )
        outbound_return_data.outbound_vendor_customer_return_files.append(ref_file)

    # Handle Outbound Payment Returns
    elif file_type == ReferenceFileType.OUTBOUND_PAYMENT_RETURN:
        ref_file.reference_file_type_id = (
            ReferenceFileType.OUTBOUND_PAYMENT_RETURN.reference_file_type_id
        )
        outbound_return_data.outbound_payment_return_files.append(ref_file)


def _process_outbound_returns(
    outbound_return_data: OutboundReturnData,
    process_returns: Optional[ProcessOutboundReturnsConfig] = None,
) -> None:
    """Process Outbound Return files in order.

    Any exceptions raised deeper in the process that haven't been caught are
    propagated up here.

    TODO: Bring bulk of each process_outbound_<type>_return function into this
          module and leave the process_outbound_<type>_return_xml functions in
          their individual modules
    """

    # Process oldest returns first
    outbound_return_data.sort_returns()
    db_session = outbound_return_data.db_session

    # Determine with Outbound Returns to process
    if process_returns is None:
        process_returns = ProcessOutboundReturnsConfig()

    # 1. Outbound Vendor Customer Returns
    if process_returns.process_outbound_vendor_returns:
        for ref_file in outbound_return_data.outbound_vendor_customer_return_files:
            try:
                outbound_vendor_customer_return.process_outbound_vendor_customer_return(
                    db_session, ref_file
                )
            except Exception:
                logger.exception(
                    "Fatal error while processing Outbound Vendor Return %s",
                    ref_file.file_location,
                    extra={"file_location", ref_file.file_location},
                )
                raise

    # 2. Outbound Status Returns
    if process_returns.process_outbound_status_returns:
        for ref_file in outbound_return_data.outbound_status_return_files:
            try:
                outbound_status_return.process_outbound_status_return(db_session, ref_file)
            except Exception:
                logger.exception(
                    "Fatal error while processing Outbound Status Return %s",
                    ref_file.file_location,
                    extra={"file_location", ref_file.file_location},
                )
                raise

    # 3. Outbound Payment Returns
    if process_returns.process_outbound_payment_returns:
        for ref_file in outbound_return_data.outbound_payment_return_files:
            try:
                outbound_payment_return.process_outbound_payment_return(db_session, ref_file)
            except Exception:
                logger.exception(
                    "Fatal error while processing Outbound Payment Return %s",
                    ref_file.file_location,
                    extra={"file_location", ref_file.file_location},
                )
                raise


def process_outbound_returns(
    db_session: db.Session, process_returns: Optional[ProcessOutboundReturnsConfig] = None
) -> None:
    """Top level function for handling CTR Outbound Return files

    Read files that are in /ctr/inbound/received and append ReferenceFile objects to each list,
    then call the appropriate handler for elements in each list
    """

    logger.info("Processing outbound return files")

    # Do setup
    s3_config = payments_config.get_s3_config()
    base_filepath = os.path.join(
        s3_config.pfml_ctr_inbound_path, payments_util.Constants.S3_INBOUND_RECEIVED_DIR
    )
    # Get the filenames
    try:
        ctr_inbound_filenames = file_util.list_files_without_folder(base_filepath)
    except Exception:
        logger.exception("Error connecting to S3 folder: %s", base_filepath)
        raise

    # If we retrieved nothing, exit early
    if not ctr_inbound_filenames:
        logger.warning(
            "Did not find any files in source S3 directory: %s",
            s3_config.pfml_ctr_inbound_path,
            extra={"pfml_ctr_inbound_path": s3_config.pfml_ctr_inbound_path},
        )
        return

    logger.info(
        "Found outbound files for processing at path: %s, files: %s",
        base_filepath,
        ", ".join(ctr_inbound_filenames),
    )

    # Identify each file by opening it up and inspecting it
    try:
        outbound_return_data = OutboundReturnData(db_session)
        for filename in ctr_inbound_filenames:
            source_filepath = os.path.join(base_filepath, filename)

            # Retrieve ReferenceFile
            # TODO add documentation about why we expect an existing reference file here
            ref_file = payments_util.get_reference_file(source_filepath, db_session)
            if ref_file is None:
                logger.warning(
                    f"Could not find ReferenceFile record in database for file in S3 named: {source_filepath}",
                    extra={"source_filepath": source_filepath},
                )
                continue

            # Parse file and determine the type of file
            _set_outbound_reference_file_type(db_session, ref_file, outbound_return_data)

        db_session.commit()
    except Exception:
        db_session.rollback()
        logger.exception(
            f"An exception occurred processing files in {base_filepath}, database will not be updated"
        )
        raise

    # Process each file
    _process_outbound_returns(outbound_return_data, process_returns)

    logger.info("Successfully processed outbound return files")
