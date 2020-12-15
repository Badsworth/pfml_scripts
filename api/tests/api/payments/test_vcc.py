import tempfile
from datetime import datetime
from xml.dom.minidom import Document

import defusedxml.ElementTree as ET
import pytest
from freezegun import freeze_time

import massgov.pfml.payments.vcc as vcc
from massgov.pfml.db.models.employees import BankAccountType, GeoState, PaymentMethod
from massgov.pfml.db.models.factories import (
    AddressFactory,
    EftFactory,
    EmployeeFactory,
    TaxIdentifierFactory,
)
from tests.api.payments import validate_attributes, validate_elements


def get_base_employee(add_eft=True, use_random_tin=False):
    # Create a generic employee that tests can use

    if use_random_tin:
        tax_identifier = TaxIdentifierFactory()
    else:
        tax_identifier = TaxIdentifierFactory(tax_identifier="123456789")

    eft = None
    if add_eft:
        eft = EftFactory.create(
            routing_nbr="345345345",
            account_nbr="000111222333",
            bank_account_type_id=BankAccountType.SAVINGS.bank_account_type_id,
        )
    mailing_address = AddressFactory(
        address_line_one="123 Foo St.",
        address_line_two="Apt #123",
        city="Chicago",
        geo_state_id=GeoState.IL.geo_state_id,
        zip_code="12345",
    )
    employee = EmployeeFactory.create(
        first_name="Jane",
        last_name="Doe",
        tax_identifier=tax_identifier,
        eft=eft,
        mailing_address=mailing_address,
        payment_method_id=PaymentMethod.ACH.payment_method_id,
    )
    return employee


@freeze_time("2020-01-01 12:00:00")
def test_build_individual_vcc_document(initialize_factories_session):
    employee = get_base_employee()
    document = vcc.build_individual_vcc_document(Document(), employee, datetime.now(), 1)

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


@freeze_time("2020-01-01 12:00:00")
def test_build_individual_vcc_document_no_eft(initialize_factories_session):
    employee = get_base_employee(add_eft=False)
    employee.payment_method = PaymentMethod.CHECK
    document = vcc.build_individual_vcc_document(Document(), employee, datetime.now(), 45)
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


def test_build_individual_vcc_document_truncated_values(initialize_factories_session):
    employee = get_base_employee()
    employee.first_name = "a" * 20
    employee.last_name = "c" * 40
    employee.mailing_address.address_line_one = "d" * 80
    employee.mailing_address.address_line_two = "e" * 80
    employee.mailing_address.city = "f" * 65

    document = vcc.build_individual_vcc_document(Document(), employee, datetime.now(), 1)
    doc_id = document._attrs["DOC_ID"].value
    # Just checking that the above values were properly truncated

    # Validate the VCC_DOC_VCUST section
    vcc_doc_vcust = document.childNodes[1]
    assert vcc_doc_vcust.tagName == "VCC_DOC_VCUST"

    expected_vcust_subelements = {
        "DOC_ID": doc_id,
        "FRST_NM": "a" * 14,
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


@freeze_time("2020-01-01 12:00:00")
def test_build_vcc_files(initialize_factories_session):
    data = [get_base_employee(), get_base_employee(use_random_tin=True)]

    with tempfile.TemporaryDirectory() as directory:
        (dat_filepath, inf_filepath) = vcc.build_vcc_files(data, directory, 11)

        with open(inf_filepath) as inf_file:
            assert inf_filepath.split("/")[-1] == "EOL20200101VCC11.INF"
            inf_file_contents = "".join(line for line in inf_file)
            assert inf_file_contents == (
                "NewMmarsBatchID = EOL0101VCC11;\n"
                "NewMmarsBatchDeptCode = EOL;\n"
                "NewMmarsUnitCode = 8770;\n"
                "NewMmarsImportDate = 2020-01-01;\n"
                "NewMmarsTransCode = VCC;\n"
                "NewMmarsTableName = ;\n"
                "NewMmarsTransCount = 2;\n"
                "NewMmarsTransDollarAmount = ;\n"
            )

        with open(dat_filepath) as dat_file:
            assert dat_filepath.split("/")[-1] == "EOL20200101VCC11.DAT"
            dat_file_contents = "".join(line for line in dat_file)

            # This bit doesn't get parsed into the XML objects
            assert dat_file_contents.startswith('<?xml version="1.0" encoding="ISO-8859-1"?>')

            # Make sure cdata fields weren't mistakenly escaped
            assert "&lt;" not in dat_file_contents
            assert "&gt;" not in dat_file_contents
            # Make sure cdata fields were created properly by looking for one
            assert (
                '<ACCT_NO_VIEW Attribute="Y"><![CDATA[000111222333]]></ACCT_NO_VIEW>'
                in dat_file_contents
            )

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
                expected_doc_attributes.update(vcc.ams_doc_attributes.copy())
                expected_doc_attributes.update(vcc.generic_attributes.copy())
                assert document.attrib == expected_doc_attributes
                assert len(document) == 8  # len of an element gives number of subelements

                vcc_doc_hdr = document[0]
                assert vcc_doc_hdr.tag == "VCC_DOC_HDR"
                assert vcc_doc_hdr.attrib == {"AMSDataObject": "Y"}

                vcc_doc_vcust = document[1]
                assert vcc_doc_vcust.tag == "VCC_DOC_VCUST"
                assert vcc_doc_vcust.attrib == {"AMSDataObject": "Y"}

                vcc_doc_ad1 = document[2]
                assert vcc_doc_ad1.tag == "VCC_DOC_AD"
                assert vcc_doc_ad1.attrib == {"AMSDataObject": "Y"}

                vcc_doc_ad2 = document[3]
                assert vcc_doc_ad2.tag == "VCC_DOC_AD"
                assert vcc_doc_ad2.attrib == {"AMSDataObject": "Y"}

                vcc_doc_1099 = document[4]
                assert vcc_doc_1099.tag == "VCC_DOC_1099"
                assert vcc_doc_1099.attrib == {"AMSDataObject": "Y"}

                vcc_doc_bus1 = document[5]
                assert vcc_doc_bus1.tag == "VCC_DOC_BUS"
                assert vcc_doc_bus1.attrib == {"AMSDataObject": "Y"}

                vcc_doc_bus2 = document[6]
                assert vcc_doc_bus2.tag == "VCC_DOC_BUS"
                assert vcc_doc_bus2.attrib == {"AMSDataObject": "Y"}

                vcc_doc_cert = document[7]
                assert vcc_doc_cert.tag == "VCC_DOC_CERT"
                assert vcc_doc_cert.attrib == {"AMSDataObject": "Y"}


def test_small_count():
    with pytest.raises(Exception, match="VCC file count must be greater than 10"):
        vcc.build_vcc_files(None, "", 1)


def test_build_individual_vcc_document_missing_required_values(initialize_factories_session):
    no_first_name_data = get_base_employee(use_random_tin=True)
    no_first_name_data.first_name = ""
    with pytest.raises(Exception, match="Value for first_name is required to generate document."):
        vcc.build_individual_vcc_document(Document(), no_first_name_data, datetime.now(), 1)

    no_last_name_data = get_base_employee(use_random_tin=True)
    no_last_name_data.last_name = ""
    with pytest.raises(Exception, match="Value for last_name is required to generate document."):
        vcc.build_individual_vcc_document(Document(), no_last_name_data, datetime.now(), 1)

    no_ssn_data = get_base_employee(use_random_tin=True)
    no_ssn_data.tax_identifier.tax_identifier = ""
    with pytest.raises(
        Exception, match="Value for tax_identifier is required to generate document."
    ):
        vcc.build_individual_vcc_document(Document(), no_ssn_data, datetime.now(), 1)

    no_address1_data = get_base_employee(use_random_tin=True)
    no_address1_data.mailing_address.address_line_one = ""
    with pytest.raises(
        Exception, match="Value for address_line_one is required to generate document."
    ):
        vcc.build_individual_vcc_document(Document(), no_address1_data, datetime.now(), 1)

    no_city_data = get_base_employee(use_random_tin=True)
    no_city_data.mailing_address.city = ""
    with pytest.raises(Exception, match="Value for city is required to generate document."):
        vcc.build_individual_vcc_document(Document(), no_city_data, datetime.now(), 1)

    no_state_data = get_base_employee(use_random_tin=True)
    no_state_data.mailing_address.geo_state = None
    with pytest.raises(Exception, match="Value for geo_state is required to generate document."):
        vcc.build_individual_vcc_document(Document(), no_state_data, datetime.now(), 1)

    no_zip_data = get_base_employee(use_random_tin=True)
    no_zip_data.mailing_address.zip_code = ""
    with pytest.raises(Exception, match="Value for zip_code is required to generate document."):
        vcc.build_individual_vcc_document(Document(), no_zip_data, datetime.now(), 1)


def test_build_individual_vcc_document_too_long_values(initialize_factories_session):
    long_ssn_data = get_base_employee(use_random_tin=True)
    long_ssn_data.tax_identifier.tax_identifier = "0" * 25
    with pytest.raises(
        Exception, match="Value for tax_identifier is longer than allowed length of 9."
    ):
        vcc.build_individual_vcc_document(Document(), long_ssn_data, datetime.now(), 1)

    long_aba_num_data = get_base_employee(use_random_tin=True)
    long_aba_num_data.eft.routing_nbr = "0" * 25
    with pytest.raises(
        Exception, match="Value for routing_nbr is longer than allowed length of 9."
    ):
        vcc.build_individual_vcc_document(Document(), long_aba_num_data, datetime.now(), 1)

    long_acct_num_data = get_base_employee(use_random_tin=True)
    long_acct_num_data.eft.account_nbr = "0" * 45
    with pytest.raises(
        Exception, match="Value for account_nbr is longer than allowed length of 40."
    ):
        vcc.build_individual_vcc_document(Document(), long_acct_num_data, datetime.now(), 1)

    long_zip_data = get_base_employee(use_random_tin=True)
    long_zip_data.mailing_address.zip_code = "01234-56789"
    with pytest.raises(Exception, match="Value for zip_code is longer than allowed length of 10."):
        vcc.build_individual_vcc_document(Document(), long_zip_data, datetime.now(), 1)


def test_build_individual_vcc_document_missing_eft(initialize_factories_session):
    employee = get_base_employee(add_eft=False)
    # Note that this employee has the employee method set to EFT still which is an issue
    with pytest.raises(Exception, match="ACH parameters missing when payment method is ACH"):
        vcc.build_individual_vcc_document(Document(), employee, datetime.now(), 1)
