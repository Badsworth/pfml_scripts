import decimal
import random
import string
import xml.dom.minidom as minidom
from datetime import datetime
from typing import Dict, List, Tuple, cast

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import (
    ClaimType,
    CtrDocumentIdentifier,
    Payment,
    PaymentReferenceFile,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.payments.payments_util import Constants

logger = massgov.pfml.util.logging.get_logger(__name__)

TWOPLACES = decimal.Decimal(10) ** -2


# Mappings of attributes to their static values
# These generic ones are reused by each element type
generic_attributes = {
    "DOC_CAT": "ABS",
    "DOC_TYP": "ABS",
    "DOC_CD": "GAX",
    "DOC_DEPT_CD": Constants.COMPTROLLER_DEPT_CODE,
    "DOC_UNIT_CD": Constants.COMPTROLLER_UNIT_CODE,
    "DOC_VERS_NO": "1",
}

ams_doc_attributes = {"DOC_IMPORT_MODE": "OE"}

abs_doc_vend_attributes = {"DOC_VEND_LN_NO": "1", "AD_ID": "AD010"}

abs_doc_actg_attributes = {
    "DOC_VEND_LN_NO": "1",
    "DOC_ACTG_LN_NO": "1",
    "VEND_INV_LN_NO": "1",
    "RFED_DOC_CD": "GAE",
    "RFED_DOC_DEPT_CD": Constants.COMPTROLLER_DEPT_CODE,
    "RFED_VEND_LN_NO": "1",
    "RFED_ACTG_LN_NO": "1",
    "RF_TYP": "1",
}


def get_fiscal_year(date_value: datetime) -> int:
    # Fiscal year matches calendar year for the first six months
    # of the year and is incremented by one from July onward.
    if date_value.month > 6:
        return date_value.year + 1
    return date_value.year


def get_fiscal_month(date_value: datetime) -> int:
    # Fiscal month/period is ahead by six months (January = 7, July = 1)
    # If it's the last six months, subtract 6
    if date_value.month > 6:
        return date_value.month - 6
    # Otherwise it's the first six months of the year, add six
    return date_value.month + 6


def get_event_type_id(leave_type: int) -> str:
    if leave_type == ClaimType.FAMILY_LEAVE.claim_type_id:
        return "7246"  # this also covers military leave
    if leave_type == ClaimType.MEDICAL_LEAVE.claim_type_id:
        return "7247"

    raise Exception(f"Leave type {leave_type} not found")


def get_rfed_doc_id(leave_type: int) -> str:
    # Note: the RFED_DOC_ID changes at the beginning of each fiscal year
    if leave_type == ClaimType.FAMILY_LEAVE.claim_type_id:
        return "PFMLFAMFY2170030632"
    if leave_type == ClaimType.MEDICAL_LEAVE.claim_type_id:
        return "PFMLMEDFY2170030632"

    raise Exception(f"Leave type {leave_type} not found")


def get_disbursement_format(payment_method: str) -> str:
    # ACH is coded as "EFT" in MMARS
    if payment_method == "ACH":
        return "EFT"
    # Check is coded as "REGW" in MMARS
    if payment_method == "Check":
        return "REGW"

    raise Exception(f"Payment method {payment_method} not found")


def get_doc_id() -> str:
    return "INTFDFML" + "".join(random.choices(string.ascii_letters + string.digits, k=12))


def get_date_format(date_value: datetime) -> str:
    return date_value.strftime("%Y-%m-%d")


def get_payment_amount(amount: decimal.Decimal) -> str:
    if amount > 0:
        return "{:0.2f}".format(amount)
    else:
        raise ValueError(f"Payment amount needs to be greater than 0: '{amount}'")


def build_individual_gax_document(
    xml_document: minidom.Document, payment: Payment, now: datetime
) -> minidom.Element:
    try:
        claim = payment.claim
        employee = claim.employee
    except Exception as e:
        raise Exception(f"Required payment model not present {str(e)}")

    leave_type = get_rfed_doc_id(claim.claim_type.claim_type_id)
    payment_date = payments_util.validate_db_input(
        key="payment_date",
        db_object=payment,
        required=True,
        truncate=False,
        max_length=10,
        func=get_date_format,
    )
    fiscal_year = get_fiscal_year(cast(datetime, payment.payment_date))
    doc_period = get_fiscal_month(cast(datetime, payment.payment_date))
    vendor_customer_code = payments_util.validate_db_input(
        key="ctr_vendor_customer_code",
        db_object=employee,
        required=True,
        max_length=20,
        truncate=False,
    )
    monetary_amount = payments_util.validate_db_input(
        key="amount",
        db_object=payment,
        required=True,
        truncate=False,
        max_length=10,  # the 10 is not a limitation that comes from MMARS
        func=get_payment_amount,
    )
    absence_case_id = payments_util.validate_db_input(
        key="fineos_absence_id", db_object=claim, required=True, max_length=19, truncate=False
    )

    today = now.date()
    start = cast(datetime, payment.period_start_date)
    end = cast(datetime, payment.period_end_date)

    if end > today or start > end:
        raise Exception(
            f"Payment period start ({start}) and end ({end}) dates are invalid. Both need to be before now ({today})."
        )

    start_date = payments_util.validate_db_input(
        key="period_start_date",
        db_object=payment,
        required=True,
        truncate=False,
        max_length=10,
        func=get_date_format,
    )
    end_date = payments_util.validate_db_input(
        key="period_end_date",
        db_object=payment,
        required=True,
        truncate=False,
        max_length=10,
        func=get_date_format,
    )

    # TODO: uncomment and wire get_disbursement_format with appropriate values
    # disbursement_format = get_disbursement_format(...)

    doc_id = get_doc_id()
    event_type_id = get_event_type_id(claim.claim_type.claim_type_id)
    rfed_doc_id = leave_type

    vendor_invoice_number = f"{absence_case_id}_{payment_date}"

    # Create the root of the document
    ams_document_attributes = {"DOC_ID": doc_id}
    ams_document_attributes.update(ams_doc_attributes.copy())
    ams_document_attributes.update(generic_attributes.copy())
    root = xml_document.createElement("AMS_DOCUMENT")
    payments_util.add_attributes(root, ams_document_attributes)

    # Add the ABS_DOC_HDR
    abs_doc_hdr = xml_document.createElement("ABS_DOC_HDR")
    payments_util.add_attributes(abs_doc_hdr, {"AMSDataObject": "Y"})
    root.appendChild(abs_doc_hdr)

    # Add the individual ABS_DOC_HDR values
    abs_doc_hdr_elements = {
        "DOC_ID": doc_id,
        "DOC_BFY": fiscal_year,
        "DOC_FY_DC": fiscal_year,
        "DOC_PER_DC": doc_period,
    }
    abs_doc_hdr_elements.update(generic_attributes.copy())
    payments_util.add_cdata_elements(abs_doc_hdr, xml_document, abs_doc_hdr_elements)

    # Add the ABS_DOC_VEND
    abs_doc_vend = xml_document.createElement("ABS_DOC_VEND")
    payments_util.add_attributes(abs_doc_vend, {"AMSDataObject": "Y"})
    root.appendChild(abs_doc_vend)
    # Add the individual ABS_DOC_VEND values
    abs_doc_vend_elements = {
        "DOC_ID": doc_id,
        "VEND_CUST_CD": vendor_customer_code,
        # "DFLT_DISB_FRMT": disbursement_format, # TODO: uncomment and set to disbursement_format
    }
    abs_doc_vend_elements.update(abs_doc_vend_attributes.copy())
    abs_doc_vend_elements.update(generic_attributes.copy())
    payments_util.add_cdata_elements(abs_doc_vend, xml_document, abs_doc_vend_elements)

    # Add the ABS_DOC_ACTG
    abs_doc_actg = xml_document.createElement("ABS_DOC_ACTG")
    payments_util.add_attributes(abs_doc_actg, {"AMSDataObject": "Y"})
    root.appendChild(abs_doc_actg)

    # Add the individual ABS_DOC_ACTG values
    abs_doc_actg_elements = {
        "DOC_ID": doc_id,
        "EVNT_TYP_ID": event_type_id,
        "LN_AM": monetary_amount,
        "BFY": fiscal_year,
        "FY_DC": fiscal_year,
        "PER_DC": doc_period,
        "VEND_INV_NO": vendor_invoice_number,
        "VEND_INV_DT": payment_date,
        "RFED_DOC_ID": rfed_doc_id,
        "SVC_FRM_DT": start_date,
        "SVC_TO_DT": end_date,
    }
    abs_doc_actg_elements.update(abs_doc_actg_attributes.copy())
    abs_doc_actg_elements.update(generic_attributes.copy())
    payments_util.add_cdata_elements(abs_doc_actg, xml_document, abs_doc_actg_elements)

    return root


def build_gax_dat(
    payments: List[Payment], now: datetime, ref_file: ReferenceFile, db_session: db.Session
) -> minidom.Document:
    # xml_document represents the overall XML object
    xml_document = minidom.Document()

    # Document root contains all of the GAX documents
    document_root = xml_document.createElement("AMS_DOC_XML_IMPORT_FILE")
    payments_util.add_attributes(document_root, {"VERSION": "1.0"})
    xml_document.appendChild(document_root)

    # Add the index so we can populate the non-nullable ctr_document_identifier.document_counter
    # field with something useful.
    for i, payment in enumerate(payments):
        ctr_doc_id = CtrDocumentIdentifier(
            ctr_document_identifier=get_doc_id(), document_date=now.date(), document_counter=i,
        )
        db_session.add(ctr_doc_id)

        # gax_document refers to individual documents which contain payment data
        gax_document = build_individual_gax_document(xml_document, payment, now)
        document_root.appendChild(gax_document)

        # Add records to the database for the document.
        payment_ref_file = PaymentReferenceFile(
            payment=payment, reference_file=ref_file, ctr_document_identifier=ctr_doc_id,
        )
        db_session.add(payment_ref_file)

    return xml_document


def build_gax_inf(payments: List[Payment], now: datetime, batch_id: str) -> Dict[str, str]:
    total_dollar_amount = decimal.Decimal(sum(payment.amount for payment in payments))

    return {
        "NewMmarsBatchID": batch_id,
        "NewMmarsBatchDeptCode": Constants.COMPTROLLER_DEPT_CODE,
        "NewMmarsUnitCode": Constants.COMPTROLLER_UNIT_CODE,
        "NewMmarsImportDate": now.strftime("%Y-%m-%d"),
        "NewMmarsTransCode": "GAX",
        "NewMmarsTableName": "",
        "NewMmarsTransCount": str(len(payments)),
        "NewMmarsTransDollarAmount": str(total_dollar_amount.quantize(TWOPLACES)),
    }


def get_eligible_payments(db_session: db.Session) -> List[Payment]:
    state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=State.ADD_TO_GAX,
        db_session=db_session,
    )

    return [state_log.payment for state_log in state_logs]


def build_gax_files(db_session: db.Session, ctr_outbound_path: str) -> Tuple[str, str]:
    try:
        now = payments_util.get_now()

        ctr_batch_id, ref_file = payments_util.create_batch_id_and_reference_file(
            now, ReferenceFileType.GAX, db_session, ctr_outbound_path
        )

        payments = get_eligible_payments(db_session)

        dat_xml_document = build_gax_dat(payments, now, ref_file, db_session)
        inf_dict = build_gax_inf(payments, now, ctr_batch_id.ctr_batch_identifier)
        ctr_batch_id.inf_data = inf_dict

        db_session.commit()

        return payments_util.create_mmars_files_in_s3(
            ref_file.file_location, ctr_batch_id.ctr_batch_identifier, dat_xml_document, inf_dict,
        )
    except Exception as e:
        logger.exception("Unable to create GAX:", str(e))
        db_session.rollback()

    return ("", "")


def build_gax_files_for_s3(db_session: db.Session) -> Tuple[str, str]:
    return build_gax_files(db_session, payments_util.get_s3_config().pfml_ctr_outbound_path)
