import xml.dom.minidom as minidom
from datetime import datetime
from typing import Any, Dict, List

import massgov.pfml.payments.payments_util as payments_util
from massgov.pfml.payments.payments_util import Constants

generic_attributes = {
    "DOC_CAT": "VCUST",
    "DOC_TYP": "VCC",
    "DOC_CD": "VCC",
    "DOC_DEPT_CD": Constants.COMPTROLLER_DEPT_CODE,
    "DOC_UNIT_CD": Constants.COMPTROLLER_UNIT_CODE,
    "DOC_VERS_NO": "1",
}

ams_doc_attributes = {"DOC_IMPORT_MODE": "OE"}

vcc_doc_vcust_attributes = {"DOC_VCUST_LN_NO": "1", "ORG_TYP": "1", "ORG_CLS": "1", "TIN_TYP": "2"}

vcc_doc_ad_attributes = {
    "DOC_VCUST_LN_NO": "1",
    "DFLT_AD_TYP": "True",
    "CNTAC_NO": "PC001",
    "PRIN_CNTAC": "NONE PROVIDED",
    "CNTAC_PH_NO": "NONE PROVIDED",
    "AD_ID": "AD010",
}

# We add two of these sections with the only difference being static values
vcc_doc_ad_attributes_pa = {"AD_TYP": "PA", "DOC_AD_LN_NO": "1"}

vcc_doc_ad_attributes_pr = {"AD_TYP": "PR", "DOC_AD_LN_NO": "2"}

vcc_doc_1099_attributes = {"DOC_VCUST_LN_NO": "1", "DOC_1099_LN_NO": "1", "RPT_1099_FL": "True"}

vcc_doc_bus_attributes = {"DOC_VCUST_LN_NO": "1", "CERT_NO": "DFMLCertified"}

# If EFT data is present, we'll add a second vcc_doc_bus section with different static attributes
vcc_doc_bus_attributes_w9 = {"DOC_BUS_LN_NO": "1", "BUS_TYP": "W9"}

vcc_doc_bus_attributes_eft = {"DOC_BUS_LN_NO": "2", "BUS_TYP": "EFT"}

vcc_doc_cert_attributes = {
    "DOC_VCUST_LN_NO": "1",
    "DOC_CERT_LN_NO": "1",
    "VEND_ACT_STA": "2",
    "VEND_APRV_STA": "3",
}


def get_doc_id(now: datetime, count: int) -> str:
    return f"INTFDFML{now.strftime('%d%m%Y')}{count:04}"


def get_acct_type_num(acct_type: str) -> str:
    if acct_type == "Saving":
        return "1"
    if acct_type == "Checking":
        return "2"

    raise Exception(f"Account type {acct_type} not found")


def build_individual_vcc_document(
    document: minidom.Document, doc_data: Dict[str, Any], now: datetime, document_count: int
) -> minidom.Element:
    # Everything in this block will need to pull from the actual object models
    # They have been conveniently sectioned together to make the switch easier.
    first_name = payments_util.validate_input(
        key="first_name", doc_data=doc_data, required=True, max_length=14, truncate=True
    )
    middle_name = payments_util.validate_input(
        key="middle_name", doc_data=doc_data, required=False, max_length=14, truncate=True
    )
    last_name = payments_util.validate_input(
        key="last_name", doc_data=doc_data, required=True, max_length=30, truncate=True
    )
    payee_ssn = payments_util.validate_input(
        key="payee_soc_number", doc_data=doc_data, required=True, max_length=9, truncate=False
    )
    payee_aba_num = payments_util.validate_input(
        key="payee_aba_number", doc_data=doc_data, required=False, max_length=9, truncate=False
    )
    payee_acct_type = payments_util.validate_input(
        key="payee_account_type",
        doc_data=doc_data,
        required=False,
        max_length=1,
        truncate=False,
        func=get_acct_type_num,
    )
    payee_acct_num = payments_util.validate_input(
        key="payee_account_number", doc_data=doc_data, required=False, max_length=40, truncate=False
    )
    payment_address_line_1 = payments_util.validate_input(
        key="payment_address_1", doc_data=doc_data, required=True, max_length=75, truncate=True
    )
    payment_address_line_2 = payments_util.validate_input(
        key="payment_address_2", doc_data=doc_data, required=False, max_length=75, truncate=True
    )
    city = payments_util.validate_input(
        key="payment_address_4", doc_data=doc_data, required=True, max_length=60, truncate=True
    )
    state = payments_util.validate_input(
        key="payment_address_6", doc_data=doc_data, required=True, max_length=2, truncate=False
    )
    zip_code = payments_util.validate_input(
        key="payment_post_code", doc_data=doc_data, required=True, max_length=10, truncate=False
    )
    payment_method = doc_data.get("payee_payment_method")

    doc_id = get_doc_id(now, document_count)

    has_eft = payee_aba_num and payee_acct_type and payee_acct_num

    # If the payment method is ACH, all related params must be present
    if payment_method == "ACH" and not (payee_aba_num or payee_acct_type or payee_acct_num):
        raise Exception("ACH parameters missing when payment method is ACH")

    # Create the root of the document
    ams_document_attributes = {"DOC_ID": doc_id}
    ams_document_attributes.update(ams_doc_attributes.copy())
    ams_document_attributes.update(generic_attributes.copy())
    root = document.createElement("AMS_DOCUMENT")
    payments_util.add_attributes(root, ams_document_attributes)

    # Add the VCC_DOC_HDR
    vcc_doc_hdr = document.createElement("VCC_DOC_HDR")
    payments_util.add_attributes(vcc_doc_hdr, {"AMSDataObject": "Y"})
    root.appendChild(vcc_doc_hdr)

    # Add the individual VCC_DOC_HDR values
    vcc_doc_hdr_elements = {
        "DOC_ID": doc_id,
    }
    vcc_doc_hdr_elements.update(generic_attributes.copy())
    payments_util.add_cdata_elements(vcc_doc_hdr, document, vcc_doc_hdr_elements)

    # Add the VCC_DOC_VCUST
    vcc_doc_vcust = document.createElement("VCC_DOC_VCUST")
    payments_util.add_attributes(vcc_doc_vcust, {"AMSDataObject": "Y"})
    root.appendChild(vcc_doc_vcust)

    # Add the individual VCC_DOC_VCUST values
    vcc_doc_vcust_elements = {
        "DOC_ID": doc_id,
        "FRST_NM": first_name,
        "MID_NM": middle_name,
        "LAST_NM": last_name,
        "TIN": payee_ssn,
    }
    vcc_doc_vcust_elements.update(vcc_doc_vcust_attributes.copy())
    vcc_doc_vcust_elements.update(generic_attributes.copy())

    # Only add these attributes if there is EFT information
    if has_eft:
        vcc_doc_vcust_elements.update(
            {
                "ABA_NO": payee_aba_num,
                "ACCT_TYP": payee_acct_type,
                "ACCT_NO_VIEW": payee_acct_num,
                "EFT_STA": "1",
            }
        )

    payments_util.add_cdata_elements(vcc_doc_vcust, document, vcc_doc_vcust_elements)

    # Add the PA VCC_DOC_AD
    vcc_doc_ad_pa = document.createElement("VCC_DOC_AD")
    payments_util.add_attributes(vcc_doc_ad_pa, {"AMSDataObject": "Y"})
    root.appendChild(vcc_doc_ad_pa)

    # Add the PA individual VCC_DOC_AD values
    vcc_doc_ad_pa_elements = {
        "DOC_ID": doc_id,
        "STR_1_NM": payment_address_line_1,
        "STR_2_NM": payment_address_line_2,
        "CITY_NM": city,
        "ST": state,
        "ZIP": zip_code,
    }
    vcc_doc_ad_pa_elements.update(vcc_doc_ad_attributes.copy())
    vcc_doc_ad_pa_elements.update(vcc_doc_ad_attributes_pa.copy())
    vcc_doc_ad_pa_elements.update(generic_attributes.copy())
    payments_util.add_cdata_elements(vcc_doc_ad_pa, document, vcc_doc_ad_pa_elements)

    # Add the PR VCC_DOC_AD
    vcc_doc_ad_pr = document.createElement("VCC_DOC_AD")
    payments_util.add_attributes(vcc_doc_ad_pr, {"AMSDataObject": "Y"})
    root.appendChild(vcc_doc_ad_pr)

    # Add the PR individual VCC_DOC_AD values
    vcc_doc_ad_pr_elements = {
        "DOC_ID": doc_id,
        "STR_1_NM": payment_address_line_1,
        "STR_2_NM": payment_address_line_2,
        "CITY_NM": city,
        "ST": state,
        "ZIP": zip_code,
    }
    vcc_doc_ad_pr_elements.update(vcc_doc_ad_attributes.copy())
    vcc_doc_ad_pr_elements.update(vcc_doc_ad_attributes_pr.copy())
    vcc_doc_ad_pr_elements.update(generic_attributes.copy())
    payments_util.add_cdata_elements(vcc_doc_ad_pr, document, vcc_doc_ad_pr_elements)

    # Add the VCC_DOC_1099
    vcc_doc_1099 = document.createElement("VCC_DOC_1099")
    payments_util.add_attributes(vcc_doc_1099, {"AMSDataObject": "Y"})
    root.appendChild(vcc_doc_1099)

    # Add the individual VCC_DOC_1099 values
    vcc_doc_1099_elements = {
        "DOC_ID": doc_id,
        "TIN_AD": f"{payment_address_line_1} {payment_address_line_2}"[:40],  # Max length of 40
        "TIN_CITY_NM": city[:30],  # This has a max length of 30 despite it being 60 elsewhere
        "TIN_ST": state,
        "TIN_ZIP": zip_code,
    }
    vcc_doc_1099_elements.update(generic_attributes.copy())
    vcc_doc_1099_elements.update(vcc_doc_1099_attributes.copy())
    payments_util.add_cdata_elements(vcc_doc_1099, document, vcc_doc_1099_elements)

    # Add the W9 VCC_DOC_BUS
    vcc_doc_bus_w9 = document.createElement("VCC_DOC_BUS")
    payments_util.add_attributes(vcc_doc_bus_w9, {"AMSDataObject": "Y"})
    root.appendChild(vcc_doc_bus_w9)

    # Add the W9 individual VCC_DOC_BUS values
    vcc_doc_bus_w9_elements = {"DOC_ID": doc_id, "CERT_STRT_DT": now.strftime("%Y-%m-%d")}
    vcc_doc_bus_w9_elements.update(vcc_doc_bus_attributes.copy())
    vcc_doc_bus_w9_elements.update(vcc_doc_bus_attributes_w9.copy())
    vcc_doc_bus_w9_elements.update(generic_attributes.copy())
    payments_util.add_cdata_elements(vcc_doc_bus_w9, document, vcc_doc_bus_w9_elements)

    # An EFT vcc_doc_bus section is needed if there is EFT information
    if has_eft:
        # Add the EFT VCC_DOC_BUS
        vcc_doc_bus_eft = document.createElement("VCC_DOC_BUS")
        payments_util.add_attributes(vcc_doc_bus_eft, {"AMSDataObject": "Y"})
        root.appendChild(vcc_doc_bus_eft)

        # Add the EFT individual VCC_DOC_BUS values
        vcc_doc_bus_eft_elements = {"DOC_ID": doc_id, "CERT_STRT_DT": now.strftime("%Y-%m-%d")}
        vcc_doc_bus_eft_elements.update(vcc_doc_bus_attributes.copy())
        vcc_doc_bus_eft_elements.update(vcc_doc_bus_attributes_eft.copy())
        vcc_doc_bus_eft_elements.update(generic_attributes.copy())
        payments_util.add_cdata_elements(vcc_doc_bus_eft, document, vcc_doc_bus_eft_elements)

    # Add the VCC_DOC_CERT
    vcc_doc_cert = document.createElement("VCC_DOC_CERT")
    payments_util.add_attributes(vcc_doc_cert, {"AMSDataObject": "Y"})
    root.appendChild(vcc_doc_cert)

    # Add the individual VCC_DOC_CERT values
    vcc_doc_cert_elements = {
        "DOC_ID": doc_id,
    }
    vcc_doc_cert_elements.update(vcc_doc_cert_attributes.copy())
    vcc_doc_cert_elements.update(generic_attributes.copy())
    payments_util.add_cdata_elements(vcc_doc_cert, document, vcc_doc_cert_elements)

    return root


def build_vcc_dat(doc_data: List[Dict[str, Any]], now: datetime) -> minidom.Document:
    # xml_document represents the overall XML object
    xml_document = minidom.Document()

    # Document root contains all of the VCC documents
    document_root = xml_document.createElement("AMS_DOC_XML_IMPORT_FILE")
    payments_util.add_attributes(document_root, {"VERSION": "1.0"})
    xml_document.appendChild(document_root)

    for count, data in enumerate(doc_data):
        # vcc_document refers to individual documents which contain payment data
        vcc_document = build_individual_vcc_document(xml_document, data, now, count)
        document_root.appendChild(vcc_document)

    return xml_document


def build_vcc_inf(doc_data: List[Dict[str, Any]], now: datetime, count: int) -> Dict[str, str]:
    return {
        "NewMmarsBatchID": f"{Constants.COMPTROLLER_DEPT_CODE}{now.strftime('%m%d')}VCC{count}",  # eg. EOL0101VCC24
        "NewMmarsBatchDeptCode": Constants.COMPTROLLER_DEPT_CODE,
        "NewMmarsUnitCode": Constants.COMPTROLLER_UNIT_CODE,
        "NewMmarsImportDate": now.strftime("%Y-%m-%d"),
        "NewMmarsTransCode": "VCC",
        "NewMmarsTableName": "",
        "NewMmarsTransCount": str(len(doc_data)),
        "NewMmarsTransDollarAmount": "",
    }


def build_vcc_files(doc_data: List[Dict[str, Any]], directory: str, count: int) -> (str, str):
    if count < 10:
        raise Exception("VCC file count must be greater than 10")
    now = payments_util.get_now()

    filename = f"{Constants.COMPTROLLER_DEPT_CODE}{now.strftime('%Y%m%d')}VCC{count}"
    dat_xml_document = build_vcc_dat(doc_data, now)
    inf_dict = build_vcc_inf(doc_data, now, count)

    return payments_util.create_files(directory, filename, dat_xml_document, inf_dict)
