import os
import pathlib
from datetime import datetime, timedelta
from xml.dom.minidom import Document

import defusedxml.ElementTree as ET
import pytest
import smart_open
from freezegun import freeze_time
from sqlalchemy import func

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.payments.outbound_status_return as outbound_status_return
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.payments.vcc as vcc
from massgov.pfml.db.models.employees import (
    BankAccountType,
    CtrDocumentIdentifier,
    EmployeeReferenceFile,
    GeoState,
    PaymentMethod,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.db.models.factories import (
    AddressFactory,
    CtrAddressPairFactory,
    CtrDocumentIdentifierFactory,
    EftFactory,
    EmployeeFactory,
    EmployeeReferenceFileFactory,
    ReferenceFileFactory,
    TaxIdentifierFactory,
)
from tests.api.payments import validate_attributes, validate_elements

TEST_FOLDER = pathlib.Path(__file__).parent


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
    ctr_address_pair = CtrAddressPairFactory(fineos_address=mailing_address)
    employee = EmployeeFactory.create(
        first_name="Jane",
        last_name="Doe",
        tax_identifier=tax_identifier,
        eft=eft,
        ctr_address_pair=ctr_address_pair,
        payment_method_id=PaymentMethod.ACH.payment_method_id,
    )
    return employee


def _create_ctr_document_identifier(
    now: datetime, doc_counter: int, db_session: db.Session
) -> CtrDocumentIdentifier:
    ctr_doc_id = CtrDocumentIdentifierFactory(
        ctr_document_identifier=vcc.get_doc_id(now, doc_counter),
        document_date=now.date(),
        document_counter=doc_counter,
    )
    ref_file = ReferenceFileFactory(
        reference_file_type_id=ReferenceFileType.VCC.reference_file_type_id,
    )
    emp_ref_file = EmployeeReferenceFileFactory(
        reference_file=ref_file, ctr_document_identifier=ctr_doc_id,
    )
    db_session.add(emp_ref_file)
    db_session.commit()

    return ctr_doc_id


@freeze_time("2020-01-01 12:00:00")
def test_build_individual_vcc_document(initialize_factories_session):
    now = datetime.now()
    employee = get_base_employee()
    document = vcc.build_individual_vcc_document(Document(), employee, now, vcc.get_doc_id(now, 1))

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
        "FRST_NM": "JANE",
        "LAST_NM": "DOE",
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
        "STR_1_NM": "123 FOO ST.",
        "STR_2_NM": "APT #123",
        "CITY_NM": "CHICAGO",
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
        "STR_1_NM": "123 FOO ST.",
        "STR_2_NM": "APT #123",
        "CITY_NM": "CHICAGO",
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
        "TIN_AD": "123 FOO ST. APT #123",
        "TIN_CITY_NM": "CHICAGO",
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
    now = datetime.now()
    employee = get_base_employee(add_eft=False)
    employee.payment_method_id = PaymentMethod.CHECK.payment_method_id
    document = vcc.build_individual_vcc_document(Document(), employee, now, vcc.get_doc_id(now, 45))
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
        "FRST_NM": "JANE",
        "LAST_NM": "DOE",
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
    now = datetime.now()

    employee = get_base_employee()
    employee.first_name = "A" * 20
    employee.last_name = "C" * 40
    employee.ctr_address_pair.fineos_address.address_line_one = "D" * 80
    employee.ctr_address_pair.fineos_address.address_line_two = "E" * 80
    employee.ctr_address_pair.fineos_address.city = "F" * 65

    document = vcc.build_individual_vcc_document(Document(), employee, now, vcc.get_doc_id(now, 1))
    doc_id = document._attrs["DOC_ID"].value
    # Just checking that the above values were properly truncated

    # Validate the VCC_DOC_VCUST section
    vcc_doc_vcust = document.childNodes[1]
    assert vcc_doc_vcust.tagName == "VCC_DOC_VCUST"

    expected_vcust_subelements = {
        "DOC_ID": doc_id,
        "FRST_NM": "A" * 14,
        "LAST_NM": "C" * 30,
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
        "STR_1_NM": "D" * 75,
        "STR_2_NM": "E" * 75,
        "CITY_NM": "F" * 60,
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
        "TIN_AD": "D" * 40,  # Only address 1 ends up present
        "TIN_CITY_NM": "F" * 30,
        "TIN_ST": "IL",
        "TIN_ZIP": "12345",
    }
    expected_1099_subelements.update(vcc.generic_attributes.copy())
    expected_1099_subelements.update(vcc.vcc_doc_1099_attributes.copy())
    validate_elements(vcc_doc_1099, expected_1099_subelements)


@freeze_time("2020-01-01 12:00:00")
def test_build_vcc_files(initialize_factories_session, test_db_session, mock_s3_bucket):
    employees = [get_base_employee(), get_base_employee(use_random_tin=True)]
    for employee in employees:
        state_log = state_log_util.create_state_log(
            start_state=State.IDENTIFY_MMARS_STATUS,
            associated_model=employee,
            db_session=test_db_session,
        )
        state_log_util.finish_state_log(
            state_log=state_log,
            end_state=State.ADD_TO_VCC,
            outcome=state_log_util.build_outcome("success"),
            db_session=test_db_session,
        )

    ctr_outbound_path = f"s3://{mock_s3_bucket}/path/to/dir"
    (dat_filepath, inf_filepath) = vcc.build_vcc_files(test_db_session, ctr_outbound_path)

    # Confirm that we created a database row for each employee we created a document for.
    assert test_db_session.query(
        func.count(CtrDocumentIdentifier.ctr_document_identifier_id)
    ).scalar() == len(employees)
    assert test_db_session.query(
        func.count(EmployeeReferenceFile.ctr_document_identifier_id)
    ).scalar() == len(employees)

    # Confirm that we created a single VCC record.
    ref_files = (
        test_db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.reference_file_type_id == ReferenceFileType.VCC.reference_file_type_id
        )
        .all()
    )
    assert len(ref_files) == 1

    # Confirm that the ReferenceFile is correctly associated with Employee models through the
    # EmployeeReferenceFile table.
    ref_file = ref_files[0]
    assert len(ref_file.employees) == len(employees)

    # Confirm that the INF data is being saved to the database properly.
    assert ref_file.ctr_batch_identifier.inf_data.get("NewMmarsTransCode") == "VCC"

    with smart_open.open(inf_filepath) as inf_file:
        assert os.path.basename(inf_filepath) == "EOL0101VCC10.INF"
        inf_file_contents = "".join(line for line in inf_file)
        assert inf_file_contents == (
            "NewMmarsBatchID = EOL0101VCC10;\n"
            "NewMmarsBatchDeptCode = EOL;\n"
            "NewMmarsUnitCode = 8770;\n"
            "NewMmarsImportDate = 2020-01-01;\n"
            "NewMmarsTransCode = VCC;\n"
            "NewMmarsTableName = ;\n"
            "NewMmarsTransCount = 2;\n"
            "NewMmarsTransDollarAmount = ;\n"
        )

    with smart_open.open(dat_filepath) as dat_file:
        assert os.path.basename(dat_filepath) == "EOL0101VCC10.DAT"
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
        assert len(root) == len(employees)  # For the two documents passed in
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


def test_build_individual_vcc_document_missing_required_values(initialize_factories_session):
    now = datetime.now()

    no_first_name_data = get_base_employee(use_random_tin=True)
    no_first_name_data.first_name = ""
    with pytest.raises(Exception, match="Value for first_name is required to generate document."):
        vcc.build_individual_vcc_document(
            Document(), no_first_name_data, now, vcc.get_doc_id(now, 1)
        )

    no_last_name_data = get_base_employee(use_random_tin=True)
    no_last_name_data.last_name = ""
    with pytest.raises(Exception, match="Value for last_name is required to generate document."):
        vcc.build_individual_vcc_document(
            Document(), no_last_name_data, now, vcc.get_doc_id(now, 1)
        )

    no_ssn_data = get_base_employee(use_random_tin=True)
    no_ssn_data.tax_identifier.tax_identifier = ""
    with pytest.raises(
        Exception, match="Value for tax_identifier is required to generate document."
    ):
        vcc.build_individual_vcc_document(Document(), no_ssn_data, now, vcc.get_doc_id(now, 1))

    no_address1_data = get_base_employee(use_random_tin=True)
    no_address1_data.ctr_address_pair.fineos_address.address_line_one = ""
    with pytest.raises(
        Exception, match="Value for address_line_one is required to generate document."
    ):
        vcc.build_individual_vcc_document(Document(), no_address1_data, now, vcc.get_doc_id(now, 1))

    no_city_data = get_base_employee(use_random_tin=True)
    no_city_data.ctr_address_pair.fineos_address.city = ""
    with pytest.raises(Exception, match="Value for city is required to generate document."):
        vcc.build_individual_vcc_document(Document(), no_city_data, now, vcc.get_doc_id(now, 1))

    no_state_data = get_base_employee(use_random_tin=True)
    no_state_data.ctr_address_pair.fineos_address.geo_state = None
    with pytest.raises(Exception, match="Value for geo_state is required to generate document."):
        vcc.build_individual_vcc_document(Document(), no_state_data, now, vcc.get_doc_id(now, 1))

    no_zip_data = get_base_employee(use_random_tin=True)
    no_zip_data.ctr_address_pair.fineos_address.zip_code = ""
    with pytest.raises(Exception, match="Value for zip_code is required to generate document."):
        vcc.build_individual_vcc_document(Document(), no_zip_data, now, vcc.get_doc_id(now, 1))


def test_build_individual_vcc_document_too_long_values(initialize_factories_session):
    now = datetime.now()

    long_ssn_data = get_base_employee(use_random_tin=True)
    long_ssn_data.tax_identifier.tax_identifier = "0" * 25
    with pytest.raises(
        Exception, match="Value for tax_identifier is longer than allowed length of 9."
    ):
        vcc.build_individual_vcc_document(Document(), long_ssn_data, now, vcc.get_doc_id(now, 1))

    long_aba_num_data = get_base_employee(use_random_tin=True)
    long_aba_num_data.eft.routing_nbr = "0" * 25
    with pytest.raises(
        Exception, match="Value for routing_nbr is longer than allowed length of 9."
    ):
        vcc.build_individual_vcc_document(
            Document(), long_aba_num_data, now, vcc.get_doc_id(now, 1)
        )

    long_acct_num_data = get_base_employee(use_random_tin=True)
    long_acct_num_data.eft.account_nbr = "0" * 45
    with pytest.raises(
        Exception, match="Value for account_nbr is longer than allowed length of 40."
    ):
        vcc.build_individual_vcc_document(
            Document(), long_acct_num_data, now, vcc.get_doc_id(now, 1)
        )

    long_zip_data = get_base_employee(use_random_tin=True)
    long_zip_data.ctr_address_pair.fineos_address.zip_code = "01234-56789"
    with pytest.raises(Exception, match="Value for zip_code is longer than allowed length of 10."):
        vcc.build_individual_vcc_document(Document(), long_zip_data, now, vcc.get_doc_id(now, 1))


def test_build_individual_vcc_document_missing_eft(initialize_factories_session):
    now = datetime.now()
    employee = get_base_employee(add_eft=False)
    # Note that this employee has the employee method set to EFT still which is an issue
    with pytest.raises(Exception, match="ACH parameters missing when payment method is ACH"):
        vcc.build_individual_vcc_document(Document(), employee, now, vcc.get_doc_id(now, 1))


def test_get_vcc_doc_counter_offset_for_today_first_today(test_db_session):
    offset = vcc.get_vcc_doc_counter_offset_for_today(datetime.now(), test_db_session)
    assert offset == 0, "First doc_counter offset today does not start with expected value"


def test_get_vcc_doc_counter_offset_for_today_with_existing_values(
    initialize_factories_session, test_db_session
):
    now = datetime.now()
    yesterday = datetime.now() - timedelta(days=1)

    # Add several batches for today. range() does not include the stop value.
    # https://docs.python.org/3.8/library/stdtypes.html#ranges
    next_doc_counter = 8
    for doc_counter in range(next_doc_counter):
        _create_ctr_document_identifier(now, doc_counter, test_db_session)

    # Add more batches for yesterday so that there are batch_counters larger than the one we
    # will be inserting.
    for doc_counter in range(2 * next_doc_counter):
        _create_ctr_document_identifier(yesterday, doc_counter, test_db_session)

    offset = vcc.get_vcc_doc_counter_offset_for_today(now, test_db_session)
    assert offset == next_doc_counter


def get_validation_container(ams_doc):
    if ams_doc.get("TRAN_CD") is None and ams_doc.find("DOC_ID") is None:
        return outbound_status_return.get_payment_validation_issues(ams_doc, None, None)
    elif ams_doc.get("TRAN_CD") is not None and ams_doc.find("DOC_ID") is None:
        return outbound_status_return.get_payment_validation_issues(
            ams_doc, None, ams_doc.get("TRAN_CD")
        )
    elif ams_doc.get("TRAN_CD") is not None and ams_doc.find("DOC_ID") is None:
        return outbound_status_return.get_payment_validation_issues(
            ams_doc, ams_doc.find("DOC_ID").text, None
        )

    tran_cd = ams_doc.get("TRAN_CD")
    doc_id = ams_doc.find("DOC_ID").text

    return outbound_status_return.get_payment_validation_issues(ams_doc, doc_id, tran_cd)


def test_vcc_outbound_status_errors(initialize_factories_session):

    file_path = os.path.join(TEST_FOLDER, "test_files", "test_vcc_status_return.xml")

    root = ET.parse(file_path).getroot()

    doc_count = 0
    for ams_doc in root:
        ams_doc_data = get_validation_container(ams_doc)
        validation_container = ams_doc_data.validation_container

        if doc_count == 0:  # Good doc
            assert validation_container.has_validation_issues() is False
        if doc_count == 1:  # Missing DOC_ID
            assert validation_container.has_validation_issues() is True
            assert (
                validation_container.validation_issues[0].reason
                == payments_util.ValidationReason.MISSING_FIELD
                and validation_container.validation_issues[0].details == "DOC_ID"
            )
        elif doc_count == 2:  # Missing NO_ERRORS, default to '0', but bad DOC_PHASE_CD
            assert validation_container.has_validation_issues() is True
            assert (
                validation_container.validation_issues[0].reason
                == payments_util.ValidationReason.INVALID_VALUE
                and validation_container.validation_issues[0].details
                == "DOC_PHASE_CD (2 - Not Final)"
            )
        elif doc_count == 3:  # Has ERRORS set
            assert validation_container.has_validation_issues() is True
            assert (
                validation_container.validation_issues[0].reason
                == payments_util.ValidationReason.OUTBOUND_STATUS_ERROR
            )

        doc_count += 1
