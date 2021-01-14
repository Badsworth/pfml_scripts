import decimal
from dataclasses import dataclass
from typing import Optional, Set, cast
from xml.etree.ElementTree import Element

import defusedxml.ElementTree as ET

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    CtrDocumentIdentifier,
    Payment,
    PaymentMethod,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)

logger = logging.get_logger(__name__)

ACCEPTABLE_PY_CD = "GAX"


@dataclass
class PaymentReturnResult:
    payment: Optional[Payment] = None
    validation_container: Optional[payments_util.ValidationContainer] = None
    state_log: Optional[StateLog] = None


class PaymentReturnDocData:
    py_cd: Optional[str]
    py_id: Optional[str]
    py_dept: Optional[str]
    vend_cd: Optional[str]
    chk_am: Optional[str]
    chk_no: Optional[str]
    chk_eft_iss_dt: Optional[str]
    validation_container: payments_util.ValidationContainer

    def __init__(self, pymt_retn_doc):
        # Setting validation_container.record_key to "" is an ugly hack
        # We set it at the end of the __init__
        self.validation_container = payments_util.ValidationContainer("")

        self.py_id = payments_util.validate_xml_input(
            "PY_ID", pymt_retn_doc, self.validation_container, required=True
        )
        self.py_cd = payments_util.validate_xml_input(
            "PY_CD",
            pymt_retn_doc,
            self.validation_container,
            required=True,
            acceptable_values=[ACCEPTABLE_PY_CD],
        )
        self.py_dept = payments_util.validate_xml_input(
            "PY_DEPT",
            pymt_retn_doc,
            self.validation_container,
            required=True,
            acceptable_values=[payments_util.Constants.COMPTROLLER_DEPT_CODE],
        )
        self.vend_cd = payments_util.validate_xml_input(
            "VEND_CD", pymt_retn_doc, self.validation_container, required=True
        )
        self.chk_am = payments_util.validate_xml_input(
            "CHK_AM", pymt_retn_doc, self.validation_container, required=True
        )
        self.chk_no = payments_util.validate_xml_input(
            "CHK_NO", pymt_retn_doc, self.validation_container, required=True
        )
        self.chk_eft_iss_dt = payments_util.validate_xml_input(
            "CHK_EFT_ISS_DT", pymt_retn_doc, self.validation_container, required=True
        )

        # Set the record key to be the PY_ID
        # Cast for the picky linter
        self.validation_container.record_key = cast(str, self.py_id)


def update_payment(
    db_session: db.Session,
    ref_file: ReferenceFile,
    payment: Payment,
    ctr_document_identifier_model: CtrDocumentIdentifier,
    payment_return_doc_data: PaymentReturnDocData,
) -> None:
    """Update the payment and create the PaymentReferenceFile

    Be sure to check that there is not already a PaymentReferenceFile for
    this payment + reference file (e.g. the same payment appears multiple
    times in this Outboun Payment Return). Otherwise, this function can halt the
    processing of the Outbound Payment Return.
    """
    payment.disb_check_eft_issue_date = payments_util.datetime_str_to_date(
        payment_return_doc_data.chk_eft_iss_dt
    )
    payment.disb_check_eft_number = payment_return_doc_data.chk_no
    # Cast for the picky linter
    payment.disb_amount = decimal.Decimal(cast(str, payment_return_doc_data.chk_am))

    if "A" in cast(str, payment_return_doc_data.chk_no):
        payment.disb_method_id = PaymentMethod.ACH.payment_method_id
    else:
        payment.disb_method_id = PaymentMethod.CHECK.payment_method_id
    db_session.add(payment)

    # Create a new row in the PaymentReferenceFile table to link the payment
    # to Outbound Payment Return
    payments_util.create_model_reference_file(
        db_session, ref_file, payment, ctr_document_identifier_model
    )


def process_pymt_retn_doc(
    db_session: db.Session,
    ref_file: ReferenceFile,
    pymt_retn_doc: Element,
    processed_payments: Set[Payment],
) -> PaymentReturnResult:
    """Process a single PYMT_RETN_DOC XML element"""

    # Skip ahead if the element is the wrong tag type
    if pymt_retn_doc.tag and pymt_retn_doc.tag.upper() != "PYMT_RETN_DOC":
        logger.info(
            "Skipping element: tag is %s instead of PYMT_RETN_DOC",
            pymt_retn_doc.tag,
            extra={"file_location": ref_file.file_location},
        )
        return PaymentReturnResult()

    # Parse the element
    payment_return_doc_data = PaymentReturnDocData(pymt_retn_doc)

    # If the element has no PY_ID, it's malformed.
    if payment_return_doc_data.py_id is None:
        # This is a malformed Outbound Payment Return.
        # We should notify CTR
        logger.error(
            "PYMT_RETN_DOC is missing PY_ID value in file %s",
            ref_file.file_location,
            extra={"file_location": ref_file.file_location},
        )
        return PaymentReturnResult(
            validation_container=payment_return_doc_data.validation_container
        )

    # Query for existing Payment by looking for a PaymentReferenceFile with
    # matching PY_ID: this is the GAX that initiated this Outbound Payment
    # Return
    try:
        payment, ctr_document_identifier_model = payments_util.get_payment_by_doc_id(
            db_session, payment_return_doc_data.py_id
        )
    except ValueError:
        # This should never happen, but if it does:
        # 1. CTR has sent us a DOC_ID we never sent them OR
        # 2. Our db lost a DOC_ID that we previously sent to CTR in a GAX
        # Resolution: Grep all the GAXs in the PFML agency transfer bucket for
        #             this DOC_ID to see whether this is a bug in our code or an
        #             error in MMARS
        logger.exception(
            "Failed to find a payment for the specified CTR Document Identifier %s",
            payment_return_doc_data.py_id,
            extra={
                "file_location": ref_file.file_location,
                "ctr_document_identifier": payment_return_doc_data.py_id,
            },
        )
        return PaymentReturnResult(
            validation_container=payment_return_doc_data.validation_container
        )

    # If there are validation issues, create a state log and add this payment
    # to the GAX error report
    if payment_return_doc_data.validation_container.has_validation_issues():
        logger.info(
            "Validation issues found for payment with PY_ID %s",
            payment_return_doc_data.py_id,
            extra={
                "file_location": ref_file.file_location,
                "ctr_document_identifier": payment_return_doc_data.py_id,
            },
        )
        state_log = state_log_util.create_finished_state_log(
            associated_model=payment,
            start_state=State.GAX_SENT,
            end_state=State.ADD_TO_GAX_ERROR_REPORT,
            outcome=state_log_util.build_outcome(
                "Validation issues found", payment_return_doc_data.validation_container
            ),
            db_session=db_session,
        )
        return PaymentReturnResult(payment, payment_return_doc_data.validation_container, state_log)

    # Validate that the MMARS Vendor Customer Code matches
    try:
        db_vendor_customer_code = payment.claim.employee.ctr_vendor_customer_code
    except Exception:
        # There might be an error where the payment, claim, or employee
        # attribute is empty.
        logger.exception(
            "Was unable to get the ctr_vendor_customer_code for the employee associated with payment %s",
            payment.payment_id,
            extra={
                "file_location": ref_file.file_location,
                "ctr_document_identifier": payment_return_doc_data.py_id,
            },
        )
        return PaymentReturnResult(
            validation_container=payment_return_doc_data.validation_container
        )

    if payment_return_doc_data.vend_cd != db_vendor_customer_code:
        # This should never happen, but if it does it means that the MMARS
        # vendor customer code associated with this PYMT_RETN_DOC does not
        # match what we have on file in the employee table.
        # We should contact CTR
        logger.error(
            "Skipped record: PYMT_RETN_DOC has vendor customer code %s, but the database shows that this employee should have vendor customer code %s",
            payment_return_doc_data.vend_cd,
            db_vendor_customer_code,
            extra={
                "file_location": ref_file.file_location,
                "ctr_document_identifier": payment_return_doc_data.py_id,
            },
        )
        return PaymentReturnResult(
            validation_container=payment_return_doc_data.validation_container
        )

    # This should never happen, but if the same payment appears in the
    # Outbound Payment Return more than once, we should log an error
    if payment in processed_payments:
        logger.error(
            "The payment with PY_ID %s has already been processed from this Outbound Payment Return",
            payment_return_doc_data.py_id,
            extra={
                "file_location": ref_file.file_location,
                "ctr_document_identifier": payment_return_doc_data.py_id,
            },
        )
        return PaymentReturnResult()

    # Everything has gone smoothly. Now, we update the payment and create a
    # PaymentReferenceFile and StateLog
    update_payment(
        db_session, ref_file, payment, ctr_document_identifier_model, payment_return_doc_data
    )
    success_message = f"Successfully processed payment with PY_ID {payment_return_doc_data.py_id} from Outbound Payment Return"
    state_log = state_log_util.create_finished_state_log(
        associated_model=payment,
        start_state=State.GAX_SENT,
        end_state=State.SEND_PAYMENT_DETAILS_TO_FINEOS,
        outcome=state_log_util.build_outcome(success_message),
        db_session=db_session,
    )
    logger.info(
        success_message,
        extra={
            "file_location": ref_file.file_location,
            "ctr_document_identifier": payment_return_doc_data.py_id,
        },
    )
    return PaymentReturnResult(payment, payment_return_doc_data.validation_container, state_log)


def process_outbound_payment_return_xml(
    db_session: db.Session, ref_file: ReferenceFile, root: Element
) -> None:
    """Loop through all the elements in the XML root"""
    processed_payments: Set[Payment] = set()
    for pymt_retn_doc in root:
        results = process_pymt_retn_doc(db_session, ref_file, pymt_retn_doc, processed_payments)
        # TODO:
        # Payments are only returned if they have been successfully
        # processed to either:
        # - Happy path: SEND_PAYMENT_DETAILS_TO_FINEOS
        # - Unhappy path: ADD_TO_GAX_ERROR_REPORT
        #
        # Everything else is skipped, which means that, in the extremely
        # unlikely case that a payment is included multiple times in the
        # same Outbound Payment Return AND the first entry has issues AND
        # the second entry does not, then the second entry will
        # successfully process. This may or may not be the desired
        # behavior.
        if results.payment is not None:
            processed_payments.add(results.payment)


def process_outbound_payment_return(db_session: db.Session, ref_file: ReferenceFile) -> None:
    """Process a single Outbound Payment Return file"""

    # Read the ReferenceFile to string
    # Raise an error if the ReferenceFile is not readable
    try:
        xml_string = payments_util.read_reference_file(
            ref_file, ReferenceFileType.OUTBOUND_PAYMENT_RETURN
        )
    except Exception:
        # There was an issue attempting to read the reference file
        logger.exception(
            "Unable to read ReferenceFile", extra={"file_location": ref_file.file_location}
        )
        raise

    # Parse file as XML Document
    # Using .fromstring because file_util.read_file returns the file as a string, not a File object
    # If there is an error, move the file to the error folder
    try:
        root = ET.fromstring(xml_string)
    except Exception:
        # XML parsing issue
        logger.exception("Unable to parse XML", extra={"file_location": ref_file.file_location})
        payments_util.move_reference_file(
            db_session,
            ref_file,
            payments_util.Constants.S3_INBOUND_RECEIVED_DIR,
            payments_util.Constants.S3_INBOUND_ERROR_DIR,
        )
        raise

    # Process each PYMT_RETN_DOC in the XML Document
    # Move the file to the processed folder
    try:
        process_outbound_payment_return_xml(db_session, ref_file, root)

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
