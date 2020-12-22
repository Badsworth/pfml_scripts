import decimal
import random
import string
import xml.dom.minidom as minidom
from datetime import datetime
from typing import Any, Dict, List, Tuple, cast

import massgov.pfml.payments.payments_util as payments_util
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

abs_doc_vend_attributes = {"DOC_VEND_LN_NO": "1"}

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


def get_event_type_id(leave_type: str) -> str:
    # TODO: The type on the leave type object here will probably be changed when we have the models.
    if leave_type == "Bonding Leave" or leave_type == "Military Leave":
        return "7246"
    if leave_type == "Medical Leave":
        return "7247"

    raise Exception(f"Leave type {leave_type} not found")


def get_rfed_doc_id(leave_type: str) -> str:
    # TODO: The type on the leave type object here will probably be changed when we have the models.
    # Note: the RFED_DOC_ID changes at the beginning of each fiscal year
    if leave_type == "Bonding Leave" or leave_type == "Military Leave":
        return "PFMLFAMFY2170030632"
    if leave_type == "Medical Leave":
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


# Note, doc_data is going to be replaced with an actual db model object(s?).
# The migrations necessary for that are forthcoming in other PRs, for simplicity,
# I'm just using a simple dictionary instead.
def build_individual_gax_document(
    xml_document: minidom.Document, doc_data: Dict[str, Any]
) -> minidom.Element:
    # Everything in this block will need to pull from the actual object models
    # They have been conveniently sectioned together to make the switch easier.
    leave_type = doc_data["leave_type"]
    payment_date = doc_data["payment_date"]
    fiscal_year = get_fiscal_year(payment_date)
    doc_period = get_fiscal_month(payment_date)
    vendor_customer_code = doc_data["vendor_customer_code"]
    vendor_address_id = doc_data["vendor_address_id"]
    monetary_amount = doc_data["amount_monamt"]
    absence_case_id = doc_data["absence_case_id"]
    start_date = doc_data["paymentstartp"]
    end_date = doc_data["paymentendper"]
    disbursement_format = get_disbursement_format(doc_data["payment_method"])

    doc_id = get_doc_id()
    event_type_id = get_event_type_id(leave_type)
    rfed_doc_id = get_rfed_doc_id(leave_type)

    payment_date_str = payment_date.strftime("%Y-%m-%d")
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    vendor_invoice_number = f"{absence_case_id}_{payment_date_str}"

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
        "AD_ID": vendor_address_id,
        "DFLT_DISB_FRMT": disbursement_format,
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
        "VEND_INV_DT": payment_date_str,
        "RFED_DOC_ID": rfed_doc_id,
        "SVC_FRM_DT": start_date_str,
        "SVC_TO_DT": end_date_str,
    }
    abs_doc_actg_elements.update(abs_doc_actg_attributes.copy())
    abs_doc_actg_elements.update(generic_attributes.copy())
    payments_util.add_cdata_elements(abs_doc_actg, xml_document, abs_doc_actg_elements)

    return root


def build_gax_dat(doc_data: List[Dict[str, Any]]) -> minidom.Document:
    # xml_document represents the overall XML object
    xml_document = minidom.Document()

    # Document root contains all of the GAX documents
    document_root = xml_document.createElement("AMS_DOC_XML_IMPORT_FILE")
    payments_util.add_attributes(document_root, {"VERSION": "1.0"})
    xml_document.appendChild(document_root)

    for data in doc_data:
        # gax_document refers to individual documents which contain payment data
        gax_document = build_individual_gax_document(xml_document, data)
        document_root.appendChild(gax_document)

    return xml_document


def build_gax_inf(doc_data: List[Dict[str, Any]], now: datetime, count: int) -> Dict[str, str]:
    total_dollar_amount = cast(
        decimal.Decimal, sum(decimal.Decimal(data["amount_monamt"]) for data in doc_data)
    )

    return {
        "NewMmarsBatchID": f"{Constants.COMPTROLLER_DEPT_CODE}{now.strftime('%m%d')}GAX{count}",  # eg. EOL0101GAX24
        "NewMmarsBatchDeptCode": Constants.COMPTROLLER_DEPT_CODE,
        "NewMmarsUnitCode": Constants.COMPTROLLER_UNIT_CODE,
        "NewMmarsImportDate": now.strftime("%Y-%m-%d"),
        "NewMmarsTransCode": "GAX",
        "NewMmarsTableName": "",
        "NewMmarsTransCount": str(len(doc_data)),
        "NewMmarsTransDollarAmount": str(total_dollar_amount.quantize(TWOPLACES)),
    }


def build_gax_files(doc_data: List[Dict[str, Any]], directory: str, count: int) -> Tuple[str, str]:
    if count < 10:
        raise Exception("Gax file count must be greater than 10")
    now = payments_util.get_now()

    filename = f"{Constants.COMPTROLLER_DEPT_CODE}{now.strftime('%Y%m%d')}GAX{count}"
    dat_xml_document = build_gax_dat(doc_data)
    inf_dict = build_gax_inf(doc_data, now, count)

    return payments_util.create_files(directory, filename, dat_xml_document, inf_dict)
