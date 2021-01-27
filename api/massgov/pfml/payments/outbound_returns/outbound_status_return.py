from dataclasses import dataclass
from typing import Optional, Set, Union, cast
from xml.etree.ElementTree import Element

import defusedxml.ElementTree as ET

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    Employee,
    Payment,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.payments.payments_util import Constants

logger = logging.get_logger(__name__)

ACCEPTABLE_AMS_DOC_CODES = ["GAX", "VCC"]
EMPLOYEE_STR = "Employee"
PAYMENT_STR = "Payment"


@dataclass
class AmsDocResult:
    item: Optional[Union[Employee, Payment]] = None
    validation_container: Optional[payments_util.ValidationContainer] = None
    state_log: Optional[StateLog] = None


class AmsDocData:
    doc_id: Optional[str]
    doc_cd: Optional[str]
    tran_cd: Optional[str]
    unit_cd: Optional[str]
    doc_unit_cd: Optional[str]
    dept_cd: Optional[str]
    doc_dept_cd: Optional[str]
    doc_phase_cd: Optional[str]
    errors: Optional[str] = None
    validation_container: payments_util.ValidationContainer

    def __init__(self, ams_doc):
        self.validation_container = payments_util.ValidationContainer("")

        self.doc_id = payments_util.validate_xml_input(
            "DOC_ID", ams_doc, self.validation_container, required=True
        )
        self.doc_cd = payments_util.validate_xml_input(
            "DOC_CD",
            ams_doc,
            self.validation_container,
            required=True,
            acceptable_values=ACCEPTABLE_AMS_DOC_CODES,
        )
        self.tran_cd = payments_util.validate_xml_input(
            "TRAN_CD",
            ams_doc,
            self.validation_container,
            find_attribute=True,
            required=True,
            acceptable_values=[cast(str, self.doc_cd)],
        )
        self.unit_cd = payments_util.validate_xml_input(
            "UNIT_CD",
            ams_doc,
            self.validation_container,
            find_attribute=True,
            required=True,
            acceptable_values=[Constants.COMPTROLLER_UNIT_CODE],
        )
        self.doc_unit_cd = payments_util.validate_xml_input(
            "DOC_UNIT_CD",
            ams_doc,
            self.validation_container,
            required=True,
            acceptable_values=[Constants.COMPTROLLER_UNIT_CODE],
        )
        self.dept_cd = payments_util.validate_xml_input(
            "DEPT_CD",
            ams_doc,
            self.validation_container,
            find_attribute=True,
            required=True,
            acceptable_values=[Constants.COMPTROLLER_DEPT_CODE],
        )
        self.doc_dept_cd = payments_util.validate_xml_input(
            "DOC_DEPT_CD",
            ams_doc,
            self.validation_container,
            required=True,
            acceptable_values=[Constants.COMPTROLLER_DEPT_CODE],
        )
        self.doc_phase_cd = payments_util.validate_xml_input(
            "DOC_PHASE_CD", ams_doc, self.validation_container, required=True
        )
        self.errors = payments_util.validate_xml_input(
            "ERRORS", ams_doc, self.validation_container, required=True
        )

        # Handle self.error_list
        self._validate_errors(ams_doc)

        # Validate DOC_PHASE_CD
        self._validate_doc_phase_cd(ams_doc)

        # Set record_key
        self.validation_container.record_key = cast(str, self.doc_id)

    def _validate_errors(self, ams_doc: Element) -> None:
        """Builds self.error_list"""

        # If there is no ERRORS element, return
        if self.errors is None:
            return

        errors_elem = ams_doc.find("ERRORS")
        if errors_elem:
            # Picky linter
            error_count = int(cast(str, errors_elem.get("NO_OF_ERRORS")))

            if error_count > 0:
                self.validation_container.add_validation_issue(
                    payments_util.ValidationReason.OUTBOUND_STATUS_ERROR, "ERRORS"
                )

    def _validate_doc_phase_cd(self, ams_doc: Element) -> None:
        if self.doc_phase_cd != Constants.DOC_PHASE_CD_FINAL_STATUS:
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.INVALID_VALUE, "DOC_PHASE_CD"
            )


def process_ams_document(
    db_session: db.Session,
    ref_file: ReferenceFile,
    ams_document: Element,
    processed_models: Set[Union[Employee, Payment]],
) -> AmsDocResult:

    # Skip ahead if the element is the wrong tag type
    if ams_document.tag and ams_document.tag.upper() != "AMS_DOCUMENT":
        logger.info(
            "Skipping element: tag is %s instead of AMS_DOCUMENT",
            ams_document.tag,
            extra={"file_location": ref_file.file_location},
        )
        return AmsDocResult()

    # validate ams_doc values:
    ams_doc_data = AmsDocData(ams_document)

    # If the element has no DOC_ID, it's malformed.
    if ams_doc_data.doc_id is None:
        # This is a malformed Outbound Payment Return.
        # We should notify CTR
        logger.error(
            "AMS_DOCUMENT is missing DOC_ID value in file %s",
            ref_file.file_location,
            extra={"file_location": ref_file.file_location},
        )
        return AmsDocResult(validation_container=ams_doc_data.validation_container)

    # Query for existing Payment or Employee by looking for a
    # PaymentReferenceFile or EmployeeReferenceFile with matching DOC_ID: this
    # is the GAX that initiated this Outbound Status Return
    try:
        found_model, ctr_document_identifier_model = payments_util.get_model_by_doc_id(
            db_session, ams_doc_data.doc_id
        )
        if isinstance(found_model, Payment):
            found_model_type = PAYMENT_STR
        elif isinstance(found_model, Employee):
            found_model_type = EMPLOYEE_STR
        else:
            raise ValueError("get_model_by_doc_id() returned an invalid model")
    except ValueError:
        # This should never happen, but if it does:
        # 1. CTR has sent us a DOC_ID we never sent them OR
        # 2. Our db lost a DOC_ID that we previously sent to CTR in a GAX
        # Resolution: Grep all the GAXs & VCCs in the PFML agency transfer
        #             bucket for this DOC_ID to see whether this is a bug in
        #             our code or an error in MMARS
        logger.exception(
            "Failed to find a payment or employee for the specified CTR Document Identifier %s",
            ams_doc_data.doc_id,
            extra={
                "file_location": ref_file.file_location,
                "ctr_document_identifier": ams_doc_data.doc_id,
            },
        )
        return AmsDocResult(validation_container=ams_doc_data.validation_container)

    # If there are validation issues, create a state log. If this is in
    # response to a GAX, add the payment to the GAX error report. If this is
    # in response to a VCC, add the employee to the VCC error report.
    if ams_doc_data.validation_container.has_validation_issues():
        if found_model_type == PAYMENT_STR:
            state_log = state_log_util.create_finished_state_log(
                associated_model=found_model,
                end_state=State.ADD_TO_GAX_ERROR_REPORT,
                outcome=state_log_util.build_outcome(
                    "Validation issues found", ams_doc_data.validation_container
                ),
                db_session=db_session,
            )
        else:
            state_log = state_log_util.create_finished_state_log(
                associated_model=found_model,
                end_state=State.ADD_TO_VCC_ERROR_REPORT,
                outcome=state_log_util.build_outcome(
                    "Validation issues found", ams_doc_data.validation_container
                ),
                db_session=db_session,
            )
        logger.info(
            "Validation issues found for %s with DOC_ID %s",
            found_model_type,
            ams_doc_data.doc_id,
            extra={
                "file_location": ref_file.file_location,
                "ctr_document_identifier": ams_doc_data.doc_id,
            },
        )
        return AmsDocResult(found_model, ams_doc_data.validation_container, state_log)

    # This should never happen, but if the same payment or employee appears in
    # the Outbound Status Return more than once, we should log an error
    if found_model in processed_models:
        logger.error(
            "The %s with DOC_ID %s has already been processed from this Outbound Status Return",
            found_model_type,
            ams_doc_data.doc_id,
            extra={
                "file_location": ref_file.file_location,
                "ctr_document_identifier": ams_doc_data.doc_id,
            },
        )
        return AmsDocResult()

    # Everything has gone smoothly. Now, we update the payment and create a
    # StateLog and a PaymentReferenceFile or an EmployeeReferenceFile
    success_message = f"Successfully processed {found_model_type} with DOC_ID {ams_doc_data.doc_id} from Outbound Status Return"
    if found_model_type == PAYMENT_STR:
        state_log = state_log_util.create_finished_state_log(
            associated_model=found_model,
            end_state=State.CONFIRM_PAYMENT,
            outcome=state_log_util.build_outcome(success_message),
            db_session=db_session,
        )
    else:
        state_log = state_log_util.create_finished_state_log(
            associated_model=found_model,
            end_state=State.VCC_SENT,  # For VCCs, we rely on Data Mart to update state
            outcome=state_log_util.build_outcome(success_message),
            db_session=db_session,
        )

    payments_util.create_model_reference_file(
        db_session, ref_file, found_model, ctr_document_identifier_model
    )
    logger.info(
        success_message,
        extra={
            "file_location": ref_file.file_location,
            "ctr_document_identifier": ams_doc_data.doc_id,
        },
    )
    return AmsDocResult(found_model, ams_doc_data.validation_container, state_log)


def process_outbound_status_return_xml(
    db_session: db.Session, ref_file: ReferenceFile, root: Element
) -> None:
    """Loop through all the elements in the XML root"""
    processed_models: Set[Union[Employee, Payment]] = set()
    for ams_document in root:
        results = process_ams_document(db_session, ref_file, ams_document, processed_models)
        # TODO:
        # Payments are only returned if they have been successfully
        # processed to either:
        # - Happy path: SEND_PAYMENT_DETAILS_TO_FINEOS
        # - Unhappy path: ADD_TO_GAX_ERROR_REPORT
        #
        # Everything else is skipped, which means that, in the extremely
        # unlikely case that a payment is included multiple times in the
        # same Outbound Status Return AND the first entry has issues AND
        # the second entry does not, then the second entry will
        # successfully process. This may or may not be the desired
        # behavior.
        if results.item is not None:
            processed_models.add(results.item)


def process_outbound_status_return(db_session: db.Session, ref_file: ReferenceFile) -> None:
    # Read the ReferenceFile to string
    # Raise an error if the ReferenceFile is not readable
    try:
        xml_string = payments_util.read_reference_file(
            ref_file, ReferenceFileType.OUTBOUND_STATUS_RETURN
        )
    except Exception:
        logger.exception("Unable to process ReferenceFile")
        raise

    # Parse file as XML Document
    # Using .fromstring because file_util.read_file returns the file as a string, not a File object
    try:
        root = ET.fromstring(xml_string)
    except Exception:
        logger.exception("Unable to parse XML", extra={"file_location": ref_file.file_location})
        payments_util.move_reference_file(
            db_session,
            ref_file,
            payments_util.Constants.S3_INBOUND_RECEIVED_DIR,
            payments_util.Constants.S3_INBOUND_ERROR_DIR,
        )
        raise

    # Process each AMS_DOCUMENT in the XML Document
    # Move the file to the processed folder
    try:
        process_outbound_status_return_xml(db_session, ref_file, root)

        # Note: this function calls db_session.commit(), so no need to
        # explicitly call it again.
        payments_util.move_reference_file(
            db_session,
            ref_file,
            payments_util.Constants.S3_INBOUND_RECEIVED_DIR,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
        )
    except Exception:
        # Rollback the db
        db_session.rollback()
        # Something forced us to halt processing
        logger.exception(
            "Unable to process ReferenceFile", extra={"file_location": ref_file.file_location}
        )
        raise
