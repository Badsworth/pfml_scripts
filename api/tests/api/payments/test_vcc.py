from xml.dom.minidom import Document

import pytest
from freezegun import freeze_time

import massgov.pfml.payments.vcc as vcc
from tests.api.payments import validate_attributes, validate_elements

base_data = {
    "first_name": "Jane",
    "middle_name": "Abigail",
    "last_name": "Doe",
    "payee_soc_number": "123456789",
    "payee_aba_number": "345345345",
    "payee_account_type": "Saving",
    "payee_account_number": "000111222333",
    "payment_address_1": "123 Foo St.",
    "payment_address_2": "Apt #123",
    "payment_address_4": "Chicago",
    "payment_address_6": "IL",
    "payment_post_code": "12345",
    "payee_payment_method": "ACH",
}


@freeze_time("2020-01-01")
def test_build_individual_vcc_document():
    document = vcc.build_individual_vcc_document(Document(), base_data.copy(), 1)

    # Doc ID is generated randomly every run, but appears in many sub values.
    doc_id = document._attrs["DOC_ID"].value
    assert doc_id == "INTFDFML010120200001"

    # Verify the root of the document
    assert document.tagName == "AMS_DOCUMENT"
    expected_doc_attributes = {"DOC_ID": doc_id}
    expected_doc_attributes.update(vcc.ams_doc_attributes.copy())
    expected_doc_attributes.update(vcc.generic_attributes.copy())
    validate_attributes(document, expected_doc_attributes)
    assert len(document.childNodes) == 8

    # Validate the VCC_DOC_HDR section
    vcc_doc_hdr = document.childNodes[0]
    assert vcc_doc_hdr.tagName == "VCC_DOC_HDR"
    validate_attributes(vcc_doc_hdr, {"AMSDataObject": "Y"})

    expected_hdr_subelements = {"DOC_ID": doc_id}
    expected_hdr_subelements.update(vcc.generic_attributes.copy())
    validate_elements(vcc_doc_hdr, expected_hdr_subelements)

    # Validate the VCC_DOC_VCUST section
    vcc_doc_vcust = document.childNodes[1]
    assert vcc_doc_vcust.tagName == "VCC_DOC_VCUST"
    validate_attributes(vcc_doc_vcust, {"AMSDataObject": "Y"})

    expected_vcust_subelements = {
        "DOC_ID": doc_id,
        "FRST_NM": "Jane",
        "MID_NM": "Abigail",
        "LAST_NM": "Doe",
        "TIN": "123456789",
        "ABA_NO": "345345345",
        "ACCT_TYP": "1",
        "ACCT_NO_VIEW": "000111222333",
        "EFT_STA": "1",
    }
    expected_vcust_subelements.update(vcc.generic_attributes.copy())
    expected_vcust_subelements.update(vcc.vcc_doc_vcust_attributes.copy())
    validate_elements(vcc_doc_vcust, expected_vcust_subelements)

    # Validate the PA VCC_DOC_AD section
    vcc_doc_ad_pa = document.childNodes[2]
    assert vcc_doc_ad_pa.tagName == "VCC_DOC_AD"
    validate_attributes(vcc_doc_ad_pa, {"AMSDataObject": "Y"})

    expected_doc_1_subelements = {
        "DOC_ID": doc_id,
        "STR_1_NM": "123 Foo St.",
        "STR_2_NM": "Apt #123",
        "CITY_NM": "Chicago",
        "ST": "IL",
        "ZIP": "12345",
    }
    expected_doc_1_subelements.update(vcc.generic_attributes.copy())
    expected_doc_1_subelements.update(vcc.vcc_doc_ad_attributes.copy())
    expected_doc_1_subelements.update(vcc.vcc_doc_ad_attributes_pa.copy())
    validate_elements(vcc_doc_ad_pa, expected_doc_1_subelements)

    # Validate the second VCC_DOC_AD section
    vcc_doc_ad_pr = document.childNodes[3]
    assert vcc_doc_ad_pr.tagName == "VCC_DOC_AD"
    validate_attributes(vcc_doc_ad_pr, {"AMSDataObject": "Y"})

    expected_doc_2_subelements = {
        "DOC_ID": doc_id,
        "STR_1_NM": "123 Foo St.",
        "STR_2_NM": "Apt #123",
        "CITY_NM": "Chicago",
        "ST": "IL",
        "ZIP": "12345",
    }
    expected_doc_2_subelements.update(vcc.generic_attributes.copy())
    expected_doc_2_subelements.update(vcc.vcc_doc_ad_attributes.copy())
    expected_doc_2_subelements.update(vcc.vcc_doc_ad_attributes_pr.copy())
    validate_elements(vcc_doc_ad_pr, expected_doc_2_subelements)

    # Validate the VCC_DOC_1099 section
    vcc_doc_1099 = document.childNodes[4]
    assert vcc_doc_1099.tagName == "VCC_DOC_1099"
    validate_attributes(vcc_doc_1099, {"AMSDataObject": "Y"})

    expected_1099_subelements = {
        "DOC_ID": doc_id,
        "TIN_AD": "123 Foo St. Apt #123",
        "TIN_CITY_NM": "Chicago",
        "TIN_ST": "IL",
        "TIN_ZIP": "12345",
    }
    expected_1099_subelements.update(vcc.generic_attributes.copy())
    expected_1099_subelements.update(vcc.vcc_doc_1099_attributes.copy())
    validate_elements(vcc_doc_1099, expected_1099_subelements)

    # Validate the W9 VCC_DOC_BUS section
    vcc_doc_bus_w9 = document.childNodes[5]
    assert vcc_doc_bus_w9.tagName == "VCC_DOC_BUS"
    validate_attributes(vcc_doc_bus_w9, {"AMSDataObject": "Y"})

    expected_doc_bus_w9_subelements = {"DOC_ID": doc_id, "CERT_STRT_DT": "2020-01-01"}
    expected_doc_bus_w9_subelements.update(vcc.generic_attributes.copy())
    expected_doc_bus_w9_subelements.update(vcc.vcc_doc_bus_attributes.copy())
    expected_doc_bus_w9_subelements.update(vcc.vcc_doc_bus_attributes_w9.copy())
    validate_elements(vcc_doc_bus_w9, expected_doc_bus_w9_subelements)

    # Validate the EFT VCC_DOC_BUS section
    vcc_doc_bus_eft = document.childNodes[6]
    assert vcc_doc_bus_eft.tagName == "VCC_DOC_BUS"
    validate_attributes(vcc_doc_bus_eft, {"AMSDataObject": "Y"})

    expected_doc_bus_eft_subelements = {"DOC_ID": doc_id, "CERT_STRT_DT": "2020-01-01"}
    expected_doc_bus_eft_subelements.update(vcc.generic_attributes.copy())
    expected_doc_bus_eft_subelements.update(vcc.vcc_doc_bus_attributes.copy())
    expected_doc_bus_eft_subelements.update(vcc.vcc_doc_bus_attributes_eft.copy())
    validate_elements(vcc_doc_bus_eft, expected_doc_bus_eft_subelements)

    # Validate the VCC_DOC_1099 section
    vcc_doc_cert = document.childNodes[7]
    assert vcc_doc_cert.tagName == "VCC_DOC_CERT"
    validate_attributes(vcc_doc_cert, {"AMSDataObject": "Y"})

    expected_cert_subelements = {
        "DOC_ID": doc_id,
    }
    expected_cert_subelements.update(vcc.generic_attributes.copy())
    expected_cert_subelements.update(vcc.vcc_doc_cert_attributes.copy())
    validate_elements(vcc_doc_cert, expected_cert_subelements)


@freeze_time("2020-01-01")
def test_build_individual_vcc_document_no_eft():
    data = base_data.copy()
    del data["payee_aba_number"]
    del data["payee_account_type"]
    del data["payee_account_number"]
    data["payee_payment_method"] = "Check"
    document = vcc.build_individual_vcc_document(Document(), data, 45)
    # Doc ID is generated randomly every run, but appears in many sub values.
    doc_id = document._attrs["DOC_ID"].value
    assert doc_id == "INTFDFML010120200045"

    # Only going to validate the differences from the base test
    # The EFT vcc_doc_bus section won't be present
    # A few elements won't be present in vcc_doc_vcust
    assert len(document.childNodes) == 7

    vcc_doc_vcust = document.childNodes[1]
    expected_vcust_subelements = {
        "DOC_ID": doc_id,
        "FRST_NM": "Jane",
        "MID_NM": "Abigail",
        "LAST_NM": "Doe",
        "TIN": "123456789",
        # Extra fields not present
    }
    expected_vcust_subelements.update(vcc.generic_attributes.copy())
    expected_vcust_subelements.update(vcc.vcc_doc_vcust_attributes.copy())
    validate_elements(vcc_doc_vcust, expected_vcust_subelements)

    vcc_doc_bus_w9 = document.childNodes[5]
    expected_doc_bus_w9_subelements = {"DOC_ID": doc_id, "CERT_STRT_DT": "2020-01-01"}
    expected_doc_bus_w9_subelements.update(vcc.generic_attributes.copy())
    expected_doc_bus_w9_subelements.update(vcc.vcc_doc_bus_attributes.copy())
    expected_doc_bus_w9_subelements.update(vcc.vcc_doc_bus_attributes_w9.copy())
    validate_elements(vcc_doc_bus_w9, expected_doc_bus_w9_subelements)


def test_build_individual_vcc_document_truncated_values():
    data = base_data.copy()
    data["first_name"] = "a" * 20
    data["middle_name"] = "b" * 20
    data["last_name"] = "c" * 40
    data["payment_address_1"] = "d" * 80  # Address 1
    data["payment_address_2"] = "e" * 80  # Address 2
    data["payment_address_4"] = "f" * 65  # City

    document = vcc.build_individual_vcc_document(Document(), data, 1)
    doc_id = document._attrs["DOC_ID"].value
    # Just checking that the above values were properly truncated

    # Validate the VCC_DOC_VCUST section
    vcc_doc_vcust = document.childNodes[1]
    assert vcc_doc_vcust.tagName == "VCC_DOC_VCUST"

    expected_vcust_subelements = {
        "DOC_ID": doc_id,
        "FRST_NM": "a" * 14,
        "MID_NM": "b" * 14,
        "LAST_NM": "c" * 30,
        "TIN": "123456789",
        "ABA_NO": "345345345",
        "ACCT_TYP": "1",
        "ACCT_NO_VIEW": "000111222333",
        "EFT_STA": "1",
    }
    expected_vcust_subelements.update(vcc.generic_attributes.copy())
    expected_vcust_subelements.update(vcc.vcc_doc_vcust_attributes.copy())
    validate_elements(vcc_doc_vcust, expected_vcust_subelements)

    vcc_doc_ad = document.childNodes[2]
    assert vcc_doc_ad.tagName == "VCC_DOC_AD"

    expected_doc_ad_subelements = {
        "DOC_ID": doc_id,
        "STR_1_NM": "d" * 75,
        "STR_2_NM": "e" * 75,
        "CITY_NM": "f" * 60,
        "ST": "IL",
        "ZIP": "12345",
    }
    expected_doc_ad_subelements.update(vcc.generic_attributes.copy())
    expected_doc_ad_subelements.update(vcc.vcc_doc_ad_attributes.copy())
    expected_doc_ad_subelements.update(vcc.vcc_doc_ad_attributes_pa.copy())
    validate_elements(vcc_doc_ad, expected_doc_ad_subelements)

    # Validate the VCC_DOC_1099 section
    vcc_doc_1099 = document.childNodes[4]
    assert vcc_doc_1099.tagName == "VCC_DOC_1099"
    validate_attributes(vcc_doc_1099, {"AMSDataObject": "Y"})

    expected_1099_subelements = {
        "DOC_ID": doc_id,
        "TIN_AD": "d" * 40,  # Only address 1 ends up present
        "TIN_CITY_NM": "f" * 30,
        "TIN_ST": "IL",
        "TIN_ZIP": "12345",
    }
    expected_1099_subelements.update(vcc.generic_attributes.copy())
    expected_1099_subelements.update(vcc.vcc_doc_1099_attributes.copy())
    validate_elements(vcc_doc_1099, expected_1099_subelements)


def test_build_individual_vcc_document_missing_required_values():
    no_first_name_data = base_data.copy()
    del no_first_name_data["first_name"]
    with pytest.raises(Exception, match="Value for first_name is required to generate document."):
        vcc.build_individual_vcc_document(Document(), no_first_name_data, 1)

    no_last_name_data = base_data.copy()
    del no_last_name_data["last_name"]
    with pytest.raises(Exception, match="Value for last_name is required to generate document."):
        vcc.build_individual_vcc_document(Document(), no_last_name_data, 1)

    no_ssn_data = base_data.copy()
    del no_ssn_data["payee_soc_number"]
    with pytest.raises(
        Exception, match="Value for payee_soc_number is required to generate document."
    ):
        vcc.build_individual_vcc_document(Document(), no_ssn_data, 1)

    no_address1_data = base_data.copy()
    del no_address1_data["payment_address_1"]
    with pytest.raises(
        Exception, match="Value for payment_address_1 is required to generate document."
    ):
        vcc.build_individual_vcc_document(Document(), no_address1_data, 1)

    no_city_data = base_data.copy()
    del no_city_data["payment_address_4"]
    with pytest.raises(
        Exception, match="Value for payment_address_4 is required to generate document."
    ):
        vcc.build_individual_vcc_document(Document(), no_city_data, 1)

    no_state_data = base_data.copy()
    del no_state_data["payment_address_6"]
    with pytest.raises(
        Exception, match="Value for payment_address_6 is required to generate document."
    ):
        vcc.build_individual_vcc_document(Document(), no_state_data, 1)

    no_zip_data = base_data.copy()
    del no_zip_data["payment_post_code"]
    with pytest.raises(
        Exception, match="Value for payment_post_code is required to generate document."
    ):
        vcc.build_individual_vcc_document(Document(), no_zip_data, 1)


def test_build_individual_vcc_document_too_long_values():
    long_ssn_data = base_data.copy()
    long_ssn_data["payee_soc_number"] = "0" * 25
    with pytest.raises(
        Exception, match="Value for payee_soc_number is longer than allowed length of 9."
    ):
        vcc.build_individual_vcc_document(Document(), long_ssn_data, 1)

    long_aba_num_data = base_data.copy()
    long_aba_num_data["payee_aba_number"] = "0" * 25
    with pytest.raises(
        Exception, match="Value for payee_aba_number is longer than allowed length of 9."
    ):
        vcc.build_individual_vcc_document(Document(), long_aba_num_data, 1)

    long_acct_num_data = base_data.copy()
    long_acct_num_data["payee_account_number"] = "0" * 45
    with pytest.raises(
        Exception, match="Value for payee_account_number is longer than allowed length of 40."
    ):
        vcc.build_individual_vcc_document(Document(), long_acct_num_data, 1)

    long_state_data = base_data.copy()
    long_state_data["payment_address_6"] = "abc"
    with pytest.raises(
        Exception, match="Value for payment_address_6 is longer than allowed length of 2."
    ):
        vcc.build_individual_vcc_document(Document(), long_state_data, 1)

    long_zip_data = base_data.copy()
    long_zip_data["payment_post_code"] = "01234-56789"
    with pytest.raises(
        Exception, match="Value for payment_post_code is longer than allowed length of 10."
    ):
        vcc.build_individual_vcc_document(Document(), long_zip_data, 1)


def test_build_individual_vcc_document_invalid_acct_type():
    bad_acct_type_data = base_data.copy()
    bad_acct_type_data["payee_account_type"] = "NotReal"
    with pytest.raises(Exception, match="Account type NotReal not found"):
        vcc.build_individual_vcc_document(Document(), bad_acct_type_data, 1)


def test_build_individual_vcc_document_missing_eft():
    data = base_data.copy()
    del data["payee_aba_number"]
    del data["payee_account_type"]
    del data["payee_account_number"]
    with pytest.raises(Exception, match="ACH parameters missing when payment method is ACH"):
        vcc.build_individual_vcc_document(Document(), data, 1)
