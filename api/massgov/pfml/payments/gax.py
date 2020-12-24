import decimal
import random
import string
import xml.dom.minidom as minidom
from datetime import datetime
from typing import Dict, List, Tuple, cast

import massgov.pfml.payments.payments_util as payments_util
from massgov.pfml.db.models.employees import ClaimType, Payment
from massgov.pfml.payments.payments_util import Constants

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
    xml_document: minidom.Document, payment: Payment
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

    now_datetime = datetime.now()
    start_datetime = cast(datetime, payment.period_start_date)
    end_datetime = cast(datetime, payment.period_end_date)
    if end_datetime > now_datetime or start_datetime > end_datetime:
        raise Exception(
            f"Payment period start ({start_datetime}) and end ({end_datetime}) dates are invalid. Both need to be before now ({now_datetime})."
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


def build_gax_dat(payments: List[Payment]) -> minidom.Document:
    # xml_document represents the overall XML object
    xml_document = minidom.Document()

    # Document root contains all of the GAX documents
    document_root = xml_document.createElement("AMS_DOC_XML_IMPORT_FILE")
    payments_util.add_attributes(document_root, {"VERSION": "1.0"})
    xml_document.appendChild(document_root)

    for payment in payments:
        # gax_document refers to individual documents which contain payment data
        gax_document = build_individual_gax_document(xml_document, payment)
        document_root.appendChild(gax_document)

    return xml_document


def build_gax_inf(payments: List[Payment], now: datetime, count: int) -> Dict[str, str]:
    total_dollar_amount = decimal.Decimal(sum(payment.amount for payment in payments))

    return {
        "NewMmarsBatchID": f"{Constants.COMPTROLLER_DEPT_CODE}{now.strftime('%m%d')}GAX{count}",  # eg. EOL0101GAX24
        "NewMmarsBatchDeptCode": Constants.COMPTROLLER_DEPT_CODE,
        "NewMmarsUnitCode": Constants.COMPTROLLER_UNIT_CODE,
        "NewMmarsImportDate": now.strftime("%Y-%m-%d"),
        "NewMmarsTransCode": "GAX",
        "NewMmarsTableName": "",
        "NewMmarsTransCount": str(len(payments)),
        "NewMmarsTransDollarAmount": str(total_dollar_amount.quantize(TWOPLACES)),
    }


def build_gax_files(payments: List[Payment], directory: str, count: int) -> Tuple[str, str]:
    if count < 10:
        raise Exception("Gax file count must be greater than 10")
    now = payments_util.get_now()

    filename = f"{Constants.COMPTROLLER_DEPT_CODE}{now.strftime('%Y%m%d')}GAX{count}"
    dat_xml_document = build_gax_dat(payments)
    inf_dict = build_gax_inf(payments, now, count)

    return payments_util.create_files(directory, filename, dat_xml_document, inf_dict)
