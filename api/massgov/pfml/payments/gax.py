import random
import string
from datetime import datetime
from typing import Any, Dict
from xml.etree.ElementTree import Element, SubElement

# Mappings of attributes to their static values
# These generic ones are reused by each element type
generic_attributes = {
    "DOC_CAT": "ABS",
    "DOC_TYP": "ABS",
    "DOC_CD": "GAX",
    "DOC_DEPT_CD": "EOL",
    "DOC_UNIT_CD": "8700",
    "DOC_VERS_NO": "1",
}

ams_doc_attributes = {"DOC_IMPORT_MODE": "OE"}

abs_doc_vend_attributes = {"DOC_VEND_LN_NO": "1"}

abs_doc_actg_attributes = {
    "DOC_VEND_LN_NO": "1",
    "DOC_ACTG_LN_NO": "1",
    "VEND_INV_LN_NO": "1",
    "RFED_DOC_CD": "GAE",
    "RFED_DOC_DEPT_CD": "EOL",
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
    if leave_type == "Bonding Leave":
        return "7246"
    if leave_type == "Medical Leave":
        return "7247"

    raise Exception(f"Leave type {leave_type} not found")


def get_rfed_doc_id(leave_type: str) -> str:
    # TODO: The type on the leave type object here will probably be changed when we have the models.
    if leave_type == "Bonding Leave":
        return "PFML0000000070030632"
    if leave_type == "Medical Leave":
        return "PFML1000000070030632"

    raise Exception(f"Leave type {leave_type} not found")


def add_cdata_elements(parent: Element, elements: Dict[str, Any]) -> None:
    for key, val in elements.items():
        elem = SubElement(parent, key, {"Attribute": "Y"})
        # Anything in the CDATA tag is passed directly and markup ignored
        elem.text = f"<![CDATA[{val}]]>"


# Note, doc_data is going to be replaced with an actual db model object(s?).
# The migrations necessary for that are forthcoming in other PRs, for simplicity,
# I'm just using a simple dictionary instead.
def build_individual_gax_document(doc_data: Dict[str, Any]) -> Element:
    # Everything in this block will need to pull from the actual object models
    # They have been conveniently sectioned together to make the switch easier.
    leave_type = doc_data["leave_type"]
    payment_date = doc_data["payment_date"]
    fiscal_year = get_fiscal_year(payment_date)
    doc_period = get_fiscal_month(payment_date)
    vendor_customer_code = doc_data["vendor_customer_code"]
    vendor_address_id = doc_data["vendor_address_id"]
    monetary_amount = doc_data["amount_monamt"]
    claim_number = doc_data["claim_number"]
    start_date = doc_data["paymentstartp"]
    end_date = doc_data["paymentendper"]

    doc_id = "INTF" + "".join(random.choices(string.ascii_letters + string.digits, k=16))
    event_type_id = get_event_type_id(leave_type)
    rfed_doc_id = get_rfed_doc_id(leave_type)

    payment_date_str = payment_date.strftime("%Y-%m-%d")
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    vendor_invoice_number = f"{claim_number}_{payment_date_str}"

    # Create the root of the document
    ams_document_attributes = {"DOC_ID": doc_id}
    ams_document_attributes.update(ams_doc_attributes.copy())
    ams_document_attributes.update(generic_attributes.copy())
    root = Element("AMS_DOCUMENT", ams_document_attributes)

    # Add the ABS_DOC_HDR
    abs_doc_hdr = SubElement(root, "ABS_DOC_HDR", {"AMSDataObject": "Y"})
    # Add the individual ABS_DOC_HDR values
    abs_doc_hdr_elements = {
        "DOC_ID": doc_id,
        "DOC_BFY": fiscal_year,
        "DOC_FY_DC": fiscal_year,
        "DOC_PER_DC": doc_period,
    }
    abs_doc_hdr_elements.update(generic_attributes.copy())
    add_cdata_elements(abs_doc_hdr, abs_doc_hdr_elements)

    # Add the ABS_DOC_VEND
    abs_doc_vend = SubElement(root, "ABS_DOC_VEND", {"AMSDataObject": "Y"})
    # Add the individual ABS_DOC_VEND values
    abs_doc_vend_elements = {
        "DOC_ID": doc_id,
        "VEND_CUST_CD": vendor_customer_code,
        "AD_ID": vendor_address_id,
    }
    abs_doc_vend_elements.update(abs_doc_vend_attributes.copy())
    abs_doc_vend_elements.update(generic_attributes.copy())
    add_cdata_elements(abs_doc_vend, abs_doc_vend_elements)

    # Add the ABS_DOC_ACTG
    abs_doc_actg = SubElement(root, "ABS_DOC_ACTG", {"AMSDataObject": "Y"})

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
    add_cdata_elements(abs_doc_actg, abs_doc_actg_elements)

    return root
