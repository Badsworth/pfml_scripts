from typing import List, Optional, Union

import defusedxml.ElementTree as ET

import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    CtrDocumentIdentifier,
    PaymentReferenceFile,
    ReferenceFile,
)
from massgov.pfml.payments.payments_util import Constants

logger = logging.get_logger(__name__)


class AmsDocData:
    doc_id: Optional[str]
    doc_cd: Optional[str]
    tran_cd: Optional[str]
    unit_cd: Optional[str]
    dept_cd: Optional[str]
    validation_container: payments_util.ValidationContainer

    def __init__(self, ams_doc, doc_id_value, tran_cd_value):
        attributes = ams_doc.attrib
        doc_cd = ams_doc.find("DOC_CD")

        self.doc_id = doc_id_value
        self.doc_cd = doc_cd.text if doc_cd is not None else None
        self.tran_cd = tran_cd_value
        self.unit_cd = attributes["UNIT_CD"] if "UNIT_CD" in attributes else None
        self.dept_cd = attributes["DEPT_CD"] if "DEPT_CD" in attributes else None
        self.validation_container = payments_util.ValidationContainer(doc_id_value)


def get_payment_validation_issues(ams_doc, doc_id_value, tran_cd_value):
    ams_doc_data = AmsDocData(ams_doc, doc_id_value, tran_cd_value)
    validation_container = ams_doc_data.validation_container

    if tran_cd_value is None:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.MISSING_FIELD, "TRAN_CD"
        )
        return ams_doc_data

    if tran_cd_value not in ["GAX", "VCC"]:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.INVALID_VALUE, "TRAN_CD"
        )
        return ams_doc_data

    if ams_doc_data.doc_id is None:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.MISSING_FIELD, "DOC_ID"
        )

    if ams_doc_data.doc_cd is None:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.MISSING_FIELD, "DOC_CD"
        )
    elif ams_doc_data.doc_cd not in ["GAX", "VCC"]:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.INVALID_VALUE, "DOC_CD"
        )

    if ams_doc_data.dept_cd is None:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.MISSING_FIELD, "DEPT_CD"
        )
    elif ams_doc_data.dept_cd != Constants.COMPTROLLER_DEPT_CODE:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.INVALID_VALUE, "DEPT_CD"
        )

    if ams_doc_data.unit_cd is None:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.MISSING_FIELD, "UNIT_CD"
        )
    elif ams_doc_data.unit_cd != Constants.COMPTROLLER_UNIT_CODE:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.INVALID_VALUE, "UNIT_CD"
        )

    # check to see if TRAN_CD is None has already been performed so this
    # is just a check of its value
    if ams_doc_data.tran_cd != ams_doc_data.doc_cd:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.INVALID_VALUE, "TRAN_CD and DOC_CD"
        )

    return ams_doc_data


def get_emp_or_pay_ref_file(
    db_session: db.Session, doc_id: str, tran_cd: str
) -> Union[PaymentReferenceFile, None]:
    if tran_cd == "GAX":
        payment_reference_file = (
            db_session.query(PaymentReferenceFile)
            .join(PaymentReferenceFile.ctr_document_identifier)
            .filter(CtrDocumentIdentifier.ctr_document_identifier == doc_id)
            .first()
        )

        return payment_reference_file
    return None


def process_outbound_status_return(db_session: db.Session, ref_file: ReferenceFile) -> List:
    validation_issues = []

    try:
        file_location = ref_file.file_location
        file = file_util.read_file(file_location)
    except Exception as e:
        logger.exception("Unable to open file:", extra={"error": e})
        raise e

    try:
        root = ET.fromstring(file)
    except Exception as e:
        logger.exception("XML is not properly formatted", extra={"error": e})
        payments_util.move_file_and_update_ref_file(
            db_session, ref_file.file_location.replace("received", "error"), ref_file
        )
        db_session.add(ref_file)
        db_session.commit()
        raise e

    for ams_doc in root:
        # query PaymentReferenceFile for matching DOC_ID
        doc_id = ams_doc.find("DOC_ID")
        doc_id_value = doc_id.text if doc_id is not None else None

        tran_cd_value = ams_doc.attrib["TRAN_CD"] if "TRAN_CD" in ams_doc.attrib else None

        # validate ams_doc values:
        ams_doc_data = get_payment_validation_issues(ams_doc, doc_id_value, tran_cd_value)

        validation_container = ams_doc_data.validation_container

        if validation_container.has_validation_issues():
            validation_issues.append(validation_container)
            continue

        if ams_doc_data.tran_cd == "GAX":
            payment_reference_file = get_emp_or_pay_ref_file(
                db_session, doc_id_value, tran_cd_value
            )

            if payment_reference_file is None:
                validation_container.add_validation_issue(
                    payments_util.ValidationReason.MISSING_IN_DB, "PaymentReferenceFile"
                )
                validation_issues.append(validation_container)
                continue

            # Create a new row in the PaymentReferenceFile table to link the payment to Outbound Status Return
            pay_ref_outbound_status_return = PaymentReferenceFile(
                payment_id=payment_reference_file.payment_id,
                reference_file_id=ref_file.reference_file_id,
                ctr_document_identifier_id=payment_reference_file.ctr_document_identifier.ctr_document_identifier_id,
            )
            db_session.add(pay_ref_outbound_status_return)

            # TODO: check if NO_ERRORS is not 0, create row in StateLog if not
            # num_of_errors = ams_doc.find("ERRORS").attrib["NO_OF_ERRORS"]
            # if num_of_errors != "0":
            #     create_state_log_entry()

    # TODO: create a row in the StateLog table for the ReferenceFile and set the state to Processed

    # move the file within the agency transfer S3 bucket to ctr/inbound/processed
    payments_util.move_file_and_update_ref_file(
        db_session, ref_file.file_location.replace("received", "processed"), ref_file
    )
    db_session.add(ref_file)
    db_session.commit()
    return validation_issues
