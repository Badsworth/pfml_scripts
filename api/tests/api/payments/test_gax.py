from datetime import datetime

import massgov.pfml.payments.gax as gax


def validate_elements(element, expected_elements):
    """
    Utility method for easily validating the inner most elements of a gax document.
    Note that expected elements is a map of: attribute tag -> value
    This method also checks a few other static values
    """

    # len(element) returns the number of subelements
    assert len(element) == len(expected_elements)

    for tag, text in expected_elements.items():
        subelement = element.find(tag)
        assert subelement.tag == tag
        assert subelement.text == f"<![CDATA[{text}]]>"
        assert subelement.attrib == {"Attribute": "Y"}


def test_get_fiscal_year():
    # Fiscal year matches calendar year for first six months
    assert gax.get_fiscal_year(datetime(2020, 1, 1)) == 2020
    assert gax.get_fiscal_year(datetime(2020, 2, 1)) == 2020
    assert gax.get_fiscal_year(datetime(2020, 3, 1)) == 2020
    assert gax.get_fiscal_year(datetime(2020, 4, 1)) == 2020
    assert gax.get_fiscal_year(datetime(2020, 5, 1)) == 2020
    assert gax.get_fiscal_year(datetime(2020, 6, 1)) == 2020
    # And then is incremented by 1 starting in July
    assert gax.get_fiscal_year(datetime(2020, 7, 1)) == 2021
    assert gax.get_fiscal_year(datetime(2020, 8, 1)) == 2021
    assert gax.get_fiscal_year(datetime(2020, 9, 1)) == 2021
    assert gax.get_fiscal_year(datetime(2020, 10, 1)) == 2021
    assert gax.get_fiscal_year(datetime(2020, 11, 1)) == 2021
    assert gax.get_fiscal_year(datetime(2020, 12, 1)) == 2021


def test_get_fiscal_month():
    # Fiscal month is 6 months ahead
    assert gax.get_fiscal_month(datetime(2020, 1, 1)) == 7
    assert gax.get_fiscal_month(datetime(2020, 2, 1)) == 8
    assert gax.get_fiscal_month(datetime(2020, 3, 1)) == 9
    assert gax.get_fiscal_month(datetime(2020, 4, 1)) == 10
    assert gax.get_fiscal_month(datetime(2020, 5, 1)) == 11
    assert gax.get_fiscal_month(datetime(2020, 6, 1)) == 12
    assert gax.get_fiscal_month(datetime(2020, 7, 1)) == 1
    assert gax.get_fiscal_month(datetime(2020, 8, 1)) == 2
    assert gax.get_fiscal_month(datetime(2020, 9, 1)) == 3
    assert gax.get_fiscal_month(datetime(2020, 10, 1)) == 4
    assert gax.get_fiscal_month(datetime(2020, 11, 1)) == 5
    assert gax.get_fiscal_month(datetime(2020, 12, 1)) == 6


def test_build_individual_gax_document():
    document = gax.build_individual_gax_document(
        {
            "leave_type": "Bonding Leave",
            "payment_date": datetime(2020, 7, 1),
            "vendor_customer_code": "abc1234",
            "vendor_address_id": "xyz789",
            "amount_monamt": "1200.00",
            "claim_number": "NTN-1234",
            "paymentstartp": datetime(2020, 8, 1),
            "paymentendper": datetime(2020, 12, 1),
        }
    )

    # Doc ID is generated randomly every run, but appears in many sub values.
    doc_id = document.attrib["DOC_ID"]
    assert doc_id

    # Verify the root of the document
    assert document.tag == "AMS_DOCUMENT"
    expected_doc_attributes = {"DOC_ID": doc_id}
    expected_doc_attributes.update(gax.ams_doc_attributes.copy())
    expected_doc_attributes.update(gax.generic_attributes.copy())
    assert document.attrib == expected_doc_attributes
    assert len(document) == 3  # len of an element gives number of subelements

    # Validate the ABS_DOC_HDR section
    abs_doc_hdr = document[0]
    assert abs_doc_hdr.tag == "ABS_DOC_HDR"
    assert abs_doc_hdr.attrib == {"AMSDataObject": "Y"}

    expected_hdr_subelements = {
        "DOC_ID": doc_id,
        "DOC_BFY": "2021",
        "DOC_FY_DC": "2021",
        "DOC_PER_DC": "1",
    }
    expected_hdr_subelements.update(gax.generic_attributes.copy())
    validate_elements(abs_doc_hdr, expected_hdr_subelements)

    # Validate the ABS_DOC_VEND section
    abs_doc_vend = document[1]
    assert abs_doc_vend.tag == "ABS_DOC_VEND"
    assert abs_doc_vend.attrib == {"AMSDataObject": "Y"}

    expected_vend_subelements = {"DOC_ID": doc_id, "VEND_CUST_CD": "abc1234", "AD_ID": "xyz789"}
    expected_vend_subelements.update(gax.generic_attributes.copy())
    expected_vend_subelements.update(gax.abs_doc_vend_attributes.copy())
    validate_elements(abs_doc_vend, expected_vend_subelements)

    # Validate the ABS_DOC_ACTG section
    abs_doc_actg = document[2]
    assert abs_doc_actg.tag == "ABS_DOC_ACTG"
    assert abs_doc_actg.attrib == {"AMSDataObject": "Y"}

    expected_actg_subelements = {
        "DOC_ID": doc_id,
        "EVNT_TYP_ID": "7246",
        "LN_AM": "1200.00",
        "BFY": "2021",
        "FY_DC": "2021",
        "PER_DC": "1",
        "VEND_INV_NO": "NTN-1234_2020-07-01",
        "VEND_INV_DT": "2020-07-01",
        "RFED_DOC_ID": "PFML0000000070030632",
        "SVC_FRM_DT": "2020-08-01",
        "SVC_TO_DT": "2020-12-01",
    }
    expected_actg_subelements.update(gax.generic_attributes.copy())
    expected_actg_subelements.update(gax.abs_doc_actg_attributes.copy())
    validate_elements(abs_doc_actg, expected_actg_subelements)
