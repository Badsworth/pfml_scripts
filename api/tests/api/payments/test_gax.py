import tempfile
from datetime import datetime
from typing import List
from xml.dom.minidom import Document

import defusedxml.ElementTree as ET
import pytest
from freezegun import freeze_time

import massgov.pfml.payments.gax as gax
from massgov.pfml.db.models.employees import ClaimType, Payment
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
    PaymentFactory,
)
from tests.api.payments import validate_attributes, validate_elements


def get_payment(
    fineos_absence_id: str,
    claim_type_id: int,
    ctr_vendor_code: str,
    amount: float,
    payment_date: datetime,
    start_date: datetime,
    end_date: datetime,
) -> Payment:
    employee = EmployeeFactory(ctr_vendor_customer_code=ctr_vendor_code)
    employer = EmployerFactory()

    return PaymentFactory(
        payment_date=payment_date,
        period_start_date=start_date,
        period_end_date=end_date,
        amount=amount,
        claim=ClaimFactory(
            employee=employee,
            employer_id=employer.employer_id,
            claim_type_id=claim_type_id,
            fineos_absence_id=fineos_absence_id,
        ),
    )


def get_payments() -> List[Payment]:
    return [
        get_payment(
            fineos_absence_id="NTN-1234-ABS-01",
            claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
            ctr_vendor_code="abc1234",
            amount=1200.00,
            payment_date=datetime(2020, 7, 1),
            start_date=datetime(2020, 8, 1),
            end_date=datetime(2020, 12, 1),
        ),
        get_payment(
            fineos_absence_id="NTN-1234-ABS-02",
            claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
            ctr_vendor_code="12345678",
            amount=1300.00,
            payment_date=datetime(2020, 1, 15),
            start_date=datetime(2020, 2, 15),
            end_date=datetime(2020, 4, 15),
        ),
    ]


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


def test_get_disbursement_format():
    assert gax.get_disbursement_format("ACH") == "EFT"
    assert gax.get_disbursement_format("Check") == "REGW"


def test_gax_doc_id():
    doc_id = gax.get_doc_id()
    assert doc_id[:8] == "INTFDFML"
    assert len(doc_id) == 20


def test_build_individual_gax_document(initialize_factories_session):
    document = gax.build_individual_gax_document(
        Document(),
        get_payment(
            fineos_absence_id="NTN-1234-ABS-01",
            payment_date=datetime(2020, 7, 1),
            ctr_vendor_code="abc1234",
            amount=1200.00,
            claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
            start_date=datetime(2020, 8, 1),
            end_date=datetime(2020, 12, 1),
        ),
    )
    # Doc ID is generated randomly every run, but appears in many sub values.
    doc_id = document._attrs["DOC_ID"].value
    assert doc_id

    # Verify the root of the document
    assert document.tagName == "AMS_DOCUMENT"
    expected_doc_attributes = {"DOC_ID": doc_id}
    expected_doc_attributes.update(gax.ams_doc_attributes.copy())
    expected_doc_attributes.update(gax.generic_attributes.copy())
    validate_attributes(document, expected_doc_attributes)
    assert len(document.childNodes) == 3

    # Validate the ABS_DOC_HDR section
    abs_doc_hdr = document.childNodes[0]
    assert abs_doc_hdr.tagName == "ABS_DOC_HDR"
    validate_attributes(abs_doc_hdr, {"AMSDataObject": "Y"})

    expected_hdr_subelements = {
        "DOC_ID": doc_id,
        "DOC_BFY": "2021",
        "DOC_FY_DC": "2021",
        "DOC_PER_DC": "1",
    }
    expected_hdr_subelements.update(gax.generic_attributes.copy())
    validate_elements(abs_doc_hdr, expected_hdr_subelements)

    # Validate the ABS_DOC_VEND section
    abs_doc_vend = document.childNodes[1]

    assert abs_doc_vend.tagName == "ABS_DOC_VEND"
    validate_attributes(abs_doc_vend, {"AMSDataObject": "Y"})

    expected_vend_subelements = {
        "DOC_ID": doc_id,
        "VEND_CUST_CD": "abc1234",
        "AD_ID": "xyz789",
        # "DFLT_DISB_FRMT": "EFT", # TODO: uncomment this when disbursement_format is set
    }
    expected_vend_subelements.update(gax.generic_attributes.copy())
    expected_vend_subelements.update(gax.abs_doc_vend_attributes.copy())
    validate_elements(abs_doc_vend, expected_vend_subelements)

    # Validate the ABS_DOC_ACTG section
    abs_doc_actg = document.childNodes[2]
    assert abs_doc_actg.tagName == "ABS_DOC_ACTG"
    validate_attributes(abs_doc_actg, {"AMSDataObject": "Y"})

    expected_actg_subelements = {
        "DOC_ID": doc_id,
        "EVNT_TYP_ID": "7246",
        "LN_AM": "1200.00",
        "BFY": "2021",
        "FY_DC": "2021",
        "PER_DC": "1",
        "VEND_INV_NO": "NTN-1234-ABS-01_2020-07-01",
        "VEND_INV_DT": "2020-07-01",
        "RFED_DOC_ID": "PFMLFAMFY2170030632",
        "SVC_FRM_DT": "2020-08-01",
        "SVC_TO_DT": "2020-12-01",
    }
    expected_actg_subelements.update(gax.generic_attributes.copy())
    expected_actg_subelements.update(gax.abs_doc_actg_attributes.copy())
    validate_elements(abs_doc_actg, expected_actg_subelements)


@freeze_time("2021-01-01 12:00:00")
def test_build_gax_files(initialize_factories_session):

    with tempfile.TemporaryDirectory() as directory:
        (dat_filepath, inf_filepath) = gax.build_gax_files(get_payments(), directory, 11)

        with open(inf_filepath) as inf_file:
            assert inf_filepath.split("/")[-1] == "EOL20210101GAX11.INF"
            inf_file_contents = "".join(line for line in inf_file)
            assert inf_file_contents == (
                "NewMmarsBatchID = EOL0101GAX11;\n"
                "NewMmarsBatchDeptCode = EOL;\n"
                "NewMmarsUnitCode = 8770;\n"
                "NewMmarsImportDate = 2021-01-01;\n"
                "NewMmarsTransCode = GAX;\n"
                "NewMmarsTableName = ;\n"
                "NewMmarsTransCount = 2;\n"
                "NewMmarsTransDollarAmount = 2500.00;\n"
            )

        with open(dat_filepath) as dat_file:
            assert dat_filepath.split("/")[-1] == "EOL20210101GAX11.DAT"
            dat_file_contents = "".join(line for line in dat_file)

            # This bit doesn't get parsed into the XML objects
            assert dat_file_contents.startswith('<?xml version="1.0" encoding="ISO-8859-1"?>')

            # Make sure cdata fields weren't mistakenly escaped
            assert "&lt;" not in dat_file_contents
            assert "&gt;" not in dat_file_contents
            # Make sure cdata fields were created properly by looking for one
            assert '<BFY Attribute="Y"><![CDATA[2021]]></BFY>' in dat_file_contents

            # We use ET for parsing instead of minidom as minidom makes odd decisions
            # when creating objects (new lines are child nodes?) that is complex.
            # Note that this parser removes the CDATA tags when parsing.
            root = ET.fromstring(dat_file_contents)
            assert len(root) == 2  # For the two documents passed in
            for document in root:
                # Doc ID is generated randomly every run, but appears in many sub values.
                doc_id = document.attrib["DOC_ID"]
                assert doc_id

                assert document.tag == "AMS_DOCUMENT"
                expected_doc_attributes = {"DOC_ID": doc_id}
                expected_doc_attributes.update(gax.ams_doc_attributes.copy())
                expected_doc_attributes.update(gax.generic_attributes.copy())
                assert document.attrib == expected_doc_attributes
                assert len(document) == 3  # len of an element gives number of subelements

                abs_doc_hdr = document[0]
                assert abs_doc_hdr.tag == "ABS_DOC_HDR"
                assert abs_doc_hdr.attrib == {"AMSDataObject": "Y"}

                abs_doc_vend = document[1]
                assert abs_doc_vend.tag == "ABS_DOC_VEND"
                assert abs_doc_vend.attrib == {"AMSDataObject": "Y"}

                abs_doc_actg = document[2]
                assert abs_doc_actg.tag == "ABS_DOC_ACTG"
                assert abs_doc_actg.attrib == {"AMSDataObject": "Y"}


def test_small_count():
    with pytest.raises(Exception, match="Gax file count must be greater than 10"):
        gax.build_gax_files(None, "", 1)
