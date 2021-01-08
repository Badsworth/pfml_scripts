from typing import List, Optional

import defusedxml.ElementTree as ET

import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    CtrDocumentIdentifier,
    PaymentMethod,
    PaymentReferenceFile,
    ReferenceFile,
)
from massgov.pfml.payments.payments_util import Constants

logger = logging.get_logger(__name__)


class PaymentReturnDocData:
    py_cd: Optional[str]
    py_id: Optional[str]
    py_dept: Optional[str]
    vend_cd: Optional[str]
    chk_am: Optional[str]
    chk_no: Optional[str]
    chk_eft_iss_dt: Optional[str]
    validation_container: payments_util.ValidationContainer

    def __init__(self, payment_return_doc, py_id_value):
        py_cd = payment_return_doc.find("PY_CD")
        py_dept = payment_return_doc.find("PY_DEPT")
        vend_cd = payment_return_doc.find("VEND_CD")
        chk_am = payment_return_doc.find("CHK_AM")
        chk_no = payment_return_doc.find("CHK_NO")
        chk_eft_iss_dt = payment_return_doc.find("CHK_EFT_ISS_DT")

        self.py_id = py_id_value
        self.py_cd = py_cd.text if py_cd is not None else None
        self.py_dept = py_dept.text if py_dept is not None else None
        self.vend_cd = vend_cd.text if vend_cd is not None else None
        self.chk_am = chk_am.text if chk_am is not None else None
        self.chk_no = chk_no.text if chk_no is not None else None
        self.chk_eft_iss_dt = chk_eft_iss_dt.text if chk_eft_iss_dt is not None else None
        self.validation_container = payments_util.ValidationContainer(py_id_value)


def get_validation_issues(pymt_retn_doc, py_id_value):
    payment_return_doc_data = PaymentReturnDocData(pymt_retn_doc, py_id_value)
    validation_container = payment_return_doc_data.validation_container

    if payment_return_doc_data.py_id is None:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.MISSING_FIELD, "PY_ID"
        )

    if payment_return_doc_data.vend_cd is None:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.MISSING_FIELD, "VEND_CD"
        )

    if payment_return_doc_data.chk_am is None:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.MISSING_FIELD, "CHK_AM"
        )

    if payment_return_doc_data.chk_no is None:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.MISSING_FIELD, "CHK_NO"
        )

    if payment_return_doc_data.chk_eft_iss_dt is None:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.MISSING_FIELD, "CHK_EFT_ISS_DT"
        )

    if payment_return_doc_data.py_dept is None:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.MISSING_FIELD, "PY_DEPT"
        )
    elif payment_return_doc_data.py_dept != Constants.COMPTROLLER_DEPT_CODE:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.INVALID_VALUE, "PY_DEPT"
        )

    if payment_return_doc_data.py_cd is None:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.MISSING_FIELD, "PY_CD"
        )
    elif payment_return_doc_data.py_cd != "GAX":
        validation_container.add_validation_issue(
            payments_util.ValidationReason.INVALID_VALUE, "PY_CD"
        )

    return payment_return_doc_data


def get_payment_reference_file(
    db_session: db.Session, py_id: str
) -> Optional[PaymentReferenceFile]:
    payment_reference_file = (
        db_session.query(PaymentReferenceFile)
        .join(PaymentReferenceFile.ctr_document_identifier)
        .filter(CtrDocumentIdentifier.ctr_document_identifier == py_id)
        .first()
    )

    return payment_reference_file


def process_outbound_payment_return(db_session: db.Session, ref_file: ReferenceFile) -> List:
    validation_issues = []

    try:
        file_location = ref_file.file_location
        file = file_util.read_file(file_location)
    except Exception as e:
        logger.exception("Unable to open file", extra={"file_location": ref_file.file_location})
        raise e

    try:
        root = ET.fromstring(file)
    except Exception as e:
        logger.exception(
            "XML is not properly formatted", extra={"file_location": ref_file.file_location}
        )
        # TODO: Create a row in the StateLog table for the ReferenceFile and set the state
        # to Outbound Payment Return syntax error
        payments_util.move_file_and_update_ref_file(
            db_session, ref_file.file_location.replace("received", "error"), ref_file
        )
        db_session.add(ref_file)
        db_session.commit()
        raise e

    for pymt_retn_doc in root:
        py_id = pymt_retn_doc.find("PY_ID")
        py_id_value = py_id.text if py_id is not None else None

        payment_return_doc_data = get_validation_issues(pymt_retn_doc, py_id_value)
        validation_container = payment_return_doc_data.validation_container

        if validation_container.has_validation_issues():
            validation_issues.append(validation_container)
            continue

        # query PaymentReferenceFile for matching PY_ID
        payment_reference_file = get_payment_reference_file(
            db_session, payment_return_doc_data.py_id
        )

        if not payment_reference_file:
            validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_IN_DB, "PaymentReferenceFile"
            )
            validation_issues.append(validation_container)
            continue

        payment = payment_reference_file.payment

        if payment_return_doc_data.vend_cd != payment.claim.employee.ctr_vendor_customer_code:
            validation_container.add_validation_issue(
                payments_util.ValidationReason.INVALID_VALUE, "VEND_CD"
            )
            validation_issues.append(validation_container)
            continue

        payment.disb_amount = payment_return_doc_data.chk_am
        payment.disb_check_eft_issue_date = payment_return_doc_data.chk_eft_iss_dt
        payment.disb_check_eft_number = payment_return_doc_data.chk_no

        if "A" in payment_return_doc_data.chk_no:
            payment.disb_method_id = PaymentMethod.ACH.payment_method_id
        else:
            payment.disb_method_id = PaymentMethod.CHECK.payment_method_id

        # Create a new row in the PaymentReferenceFile table to link the payment to Outbound Payment Return
        pay_ref_outbound_payment_return = PaymentReferenceFile(
            payment_id=payment_reference_file.payment_id,
            reference_file_id=ref_file.reference_file_id,
            ctr_document_identifier_id=payment_reference_file.ctr_document_identifier.ctr_document_identifier_id,
        )
        db_session.add(payment)
        db_session.add(pay_ref_outbound_payment_return)

    # move the file within the agency transfer S3 bucket to ctr/inbound/processed
    payments_util.move_file_and_update_ref_file(
        db_session, ref_file.file_location.replace("received", "processed"), ref_file
    )
    db_session.add(ref_file)
    db_session.commit()
    return validation_issues
