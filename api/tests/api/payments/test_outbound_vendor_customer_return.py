import logging  # noqa: B1
import os
import pathlib

import boto3
import defusedxml.ElementTree as ET

import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    Address,
    CtrDocumentIdentifier,
    EmployeeReferenceFile,
    GeoState,
    ReferenceFileType,
    State,
    StateLog,
    TaxIdentifier,
)
from massgov.pfml.db.models.factories import (
    EmployeeFactory,
    ReferenceFileFactory,
    TaxIdentifierFactory,
)
from massgov.pfml.payments.outbound_vendor_customer_return import (
    VcDocAdData,
    check_dependencies,
    handle_xml_syntax_error,
    move_processed_file,
    process_ams_document,
    process_outbound_vendor_customer_return,
    update_employee_data,
    validate_ams_document,
)
from massgov.pfml.payments.payments_util import ValidationContainer, ValidationReason

TEST_FOLDER = pathlib.Path(__file__).parent
TEST_FILE_PATH = os.path.join(
    TEST_FOLDER,
    "test_files",
    "outbound_vendor_customer_returns",
    "test_outbound_vendor_customer_return.xml",
)
XML_ROOT = ET.parse(TEST_FILE_PATH)

# Mock S3 settings
SOURCE_FILE_NAME = "test_file.xml"
SOURCE_FOLDER = "ctr/inbound/received"
SOURCE_KEY = f"{SOURCE_FOLDER}/{SOURCE_FILE_NAME}"
RECEIVED_FOLDER = (
    f"s3://test_bucket/{SOURCE_FOLDER}"  # test_bucket should be the mock_s3_bucket name
)
RECEIVED_S3_PATH = f"{RECEIVED_FOLDER}/{SOURCE_FILE_NAME}"
PROCESSED_FOLDER = RECEIVED_FOLDER.replace("received", "processed")
PROCESSED_S3_PATH = f"{PROCESSED_FOLDER}/{SOURCE_FILE_NAME}"
ERROR_FOLDER = RECEIVED_FOLDER.replace("received", "error")
ERROR_S3_PATH = f"{ERROR_FOLDER}/{SOURCE_FILE_NAME}"


def get_ams_document(description="valid"):
    """
    The test file in the TEST_FILE_PATH contains multiple AMS_DOCUMENT elements, tagged with "DESCRIPTION" fields that
    allow the test runner to select a specific case to test.

    Cases:
    "valid": All VC_DOC_VCUST fields are valid
    "all_fields_invalid": All VC_DOC_VCUST fields contain validation errors
    "missing_fields": All VC_DOC_VCUST are missing
    "multiple_addresses": This element has two VC_DOC_AD entries with AD_ID == "PA" and AD_ID == "AD010"
    "missing_doc_id": This VC_DOC_VCUST has a "null" DOC_ID on the parent element
    "missing_vc_doc_vcust": This element does not have a VC_DOC_VCUST element
    "missing_city": The VC_DOC_AD with AD_ID == "PA" and AD_ID == "AD010" has a "null" "CITY_NM" value

    """
    return XML_ROOT.findall(f".//AMS_DOCUMENT[@DESCRIPTION='{description}']")[0]


def create_ovr_dependencies(
    ams_document_id, TIN, test_db_session,
) -> [CtrDocumentIdentifier, EmployeeReferenceFile, EmployeeFactory, ReferenceFileFactory]:
    """
    Successful processing of an AMS Document within an OVR file requires multiple dependencies:
    - An employee
    - A CtrDocumentIdentifier the "ctr_document_identifier" field matching the DOC_ID in the AMS_DOCUMENT
    - A ReferenceFile of type VCC
    - An EmployeeReferenceFile that connects the above Employee, VCC ReferenceFile and CtrDocumentIdentifier

    The test xml file used for these tests contain multiple AMS_DOCUMENT objects. To test processing a specific AMS_DOCUMENT,
    create just the dependencies for that AMS_DOCUMENT by passing in the DOC_ID and TIN values from that AMS_DOCUMENT.

    All the other AMS_DOCUMENTS will fail the validation steps, since their depdencies won't exist.
    """

    tax_identifier = TaxIdentifier(tax_identifier=TIN)
    vcc_reference_file = ReferenceFileFactory.create(
        reference_file_type_id=ReferenceFileType.VCC.reference_file_type_id
    )
    employee = EmployeeFactory(mailing_address=Address(), tax_identifier=tax_identifier)

    ctr_document_identifer = CtrDocumentIdentifier(
        ctr_document_identifier=ams_document_id, document_date="2021-01-01", document_counter=1
    )
    test_db_session.add(ctr_document_identifer)
    test_db_session.commit()

    employee_reference_file = EmployeeReferenceFile(
        employee_id=employee.employee_id,
        reference_file_id=vcc_reference_file.reference_file_id,
        ctr_document_identifier_id=ctr_document_identifer.ctr_document_identifier_id,
    )

    employee.reference_files = [employee_reference_file]

    test_db_session.add(employee_reference_file)
    test_db_session.add(employee)
    test_db_session.commit()

    return ctr_document_identifer, employee_reference_file, employee


def get_ovr_reference_file():
    return ReferenceFileFactory(
        reference_file_type_id=ReferenceFileType.OUTBOUND_VENDOR_CUSTOMER_RETURN.reference_file_type_id,
        file_location=RECEIVED_S3_PATH,
    )


def setup_mock_update_employee_data(monkeypatch):
    def mock_update_employee_data(ams_document, ams_document_id, vc_doc_vcust, employee):
        mock_update_employee_data.times_called = mock_update_employee_data.times_called + 1

    mock_update_employee_data.times_called = 0

    monkeypatch.setattr(
        "massgov.pfml.payments.outbound_vendor_customer_return.update_employee_data",
        mock_update_employee_data,
    )
    return mock_update_employee_data


def setup_mock_s3_bucket(mock_s3_bucket):
    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key=SOURCE_KEY, Body=file_util.read_file(TEST_FILE_PATH))


def test_validate_ams_document_valid_doc(test_db_session, initialize_factories_session):
    ams_document = get_ams_document()
    ams_document_id = ams_document.get("DOC_ID")
    validation_container = ValidationContainer(ams_document_id)
    vc_doc_vcust = ams_document.find("VC_DOC_VCUST")

    tax_identifier = TaxIdentifierFactory.create(tax_identifier="517467495")
    employee = EmployeeFactory.create(tax_identifier=tax_identifier)

    validation_container, validated_address_data = validate_ams_document(
        ams_document, ams_document_id, vc_doc_vcust, employee, validation_container
    )

    assert validation_container.has_validation_issues() is False


def test_validate_ams_document_with_invalid_fields(test_db_session, initialize_factories_session):
    ams_document = get_ams_document("all_fields_invalid")
    ams_document_id = ams_document.get("DOC_ID")
    validation_container = ValidationContainer(ams_document_id)
    vc_doc_vcust = ams_document.find("VC_DOC_VCUST")

    tax_identifier = TaxIdentifier(tax_identifier="590764658")
    employee = EmployeeFactory.create(tax_identifier=tax_identifier)

    validation_container, validated_address_data = validate_ams_document(
        ams_document, ams_document_id, vc_doc_vcust, employee, validation_container
    )

    field_to_reason_mapping = {
        "DOC_ID": ValidationReason.INVALID_VALUE,
        "DOC_CAT": ValidationReason.INVALID_VALUE,
        "DOC_TYP": ValidationReason.INVALID_VALUE,
        "DOC_CD": ValidationReason.INVALID_VALUE,
        "DOC_DEPT_CD": ValidationReason.INVALID_VALUE,
        "DOC_UNIT_CD": ValidationReason.INVALID_VALUE,
        "ORG_TYP": ValidationReason.INVALID_VALUE,
        "TIN_TYP": ValidationReason.INVALID_VALUE,
        "TIN": ValidationReason.INVALID_VALUE,
        "VC_DOC_AD": ValidationReason.VALUE_NOT_FOUND,
        "VEND_CUST_CD": ValidationReason.NON_NULLABLE,
        "ORG_VEND_CUST_CD": ValidationReason.NON_NULLABLE,
    }

    for issue in validation_container.validation_issues:
        assert issue.reason == field_to_reason_mapping[issue.details]

    assert len(validation_container.validation_issues) == 12
    assert len(validation_container.errors) == 0


def test_validate_ams_document_with_missing_fields(test_db_session, initialize_factories_session):
    ams_document = get_ams_document("missing_fields")
    ams_document_id = ams_document.get("DOC_ID")
    validation_container = ValidationContainer(ams_document_id)
    vc_doc_vcust = ams_document.find("VC_DOC_VCUST")

    tax_identifier = TaxIdentifier(tax_identifier="590764658")
    employee = EmployeeFactory.create(tax_identifier=tax_identifier)

    validation_container, validated_address_data = validate_ams_document(
        ams_document, ams_document_id, vc_doc_vcust, employee, validation_container
    )

    field_to_reason_mapping = {
        "DOC_CAT": ValidationReason.MISSING_FIELD,
        "DOC_TYP": ValidationReason.MISSING_FIELD,
        "DOC_CD": ValidationReason.MISSING_FIELD,
        "DOC_DEPT_CD": ValidationReason.MISSING_FIELD,
        "DOC_UNIT_CD": ValidationReason.MISSING_FIELD,
        "ORG_TYP": ValidationReason.MISSING_FIELD,
        "TIN_TYP": ValidationReason.MISSING_FIELD,
        "TIN": ValidationReason.MISSING_FIELD,
        "VC_DOC_AD": ValidationReason.VALUE_NOT_FOUND,
        "VEND_CUST_CD": ValidationReason.NON_NULLABLE,
        "ORG_VEND_CUST_CD": ValidationReason.NON_NULLABLE,
    }

    for issue in validation_container.validation_issues:
        assert issue.reason == field_to_reason_mapping[issue.details]

    assert len(validation_container.validation_issues) == 11
    assert len(validation_container.errors) == 0


def test_validate_ams_document_with_multiple_addresses(
    test_db_session, initialize_factories_session
):
    ams_document = get_ams_document("multiple_addresses")
    ams_document_id = ams_document.get("DOC_ID")
    validation_container = ValidationContainer(ams_document_id)
    vc_doc_vcust = ams_document.find("VC_DOC_VCUST")

    tax_identifier = TaxIdentifier(tax_identifier="579313283")
    employee = EmployeeFactory.create(tax_identifier=tax_identifier)

    validation_container, validated_address_data = validate_ams_document(
        ams_document, ams_document_id, vc_doc_vcust, employee, validation_container
    )

    assert len(validation_container.validation_issues) == 1
    assert len(validation_container.errors) == 0
    validation_issue = validation_container.validation_issues[0]
    assert validation_issue.reason == ValidationReason.MULTIPLE_VALUES_FOUND
    assert validation_issue.details == "VC_DOC_AD"
    assert validated_address_data is None


def test_check_dependencies(test_db_session, initialize_factories_session):
    # The dependencies are checked in order, so the ordering of these statements matter
    # missing DOC_ID
    ams_document = get_ams_document("missing_doc_id")
    ams_document_id = ams_document.get("DOC_ID")
    reference_file = ReferenceFileFactory.create()
    dependencies = check_dependencies(ams_document, test_db_session, reference_file)

    assert dependencies.ams_document_id is None
    assert dependencies.ctr_document_identifier is None
    assert dependencies.employee is None
    assert dependencies.vc_doc_vcust is None

    # VC_DOC_VCUST not in AMS_DOCUMENT

    ams_document = get_ams_document("missing_vc_doc_vcust")
    ams_document_id = ams_document.get("DOC_ID")
    dependencies = check_dependencies(ams_document, test_db_session, reference_file)

    assert dependencies.ams_document_id == ams_document_id
    assert dependencies.vc_doc_vcust is None
    assert dependencies.ctr_document_identifier is None
    assert dependencies.employee is None

    # ctr_document_identifier is not found

    ams_document = get_ams_document()
    vc_doc_vcust = ams_document.find("VC_DOC_VCUST")
    ams_document_id = ams_document.get("DOC_ID")
    dependencies = check_dependencies(ams_document, test_db_session, reference_file)

    assert dependencies.ams_document_id == ams_document_id
    assert dependencies.vc_doc_vcust == vc_doc_vcust
    assert dependencies.ctr_document_identifier is None
    assert dependencies.employee is None

    # create a valid CtrDocumentIdentifier for the next test
    ctr_document_identifer = CtrDocumentIdentifier(
        ctr_document_identifier=ams_document_id, document_date="2021-01-01", document_counter=1
    )
    test_db_session.add(ctr_document_identifer)
    test_db_session.commit()

    # Employee not found
    dependencies = check_dependencies(ams_document, test_db_session, reference_file)

    assert dependencies.ams_document_id == ams_document_id
    assert dependencies.vc_doc_vcust == vc_doc_vcust
    assert dependencies.ctr_document_identifier == ctr_document_identifer
    assert dependencies.employee is None

    # create an Employee and EmployeeReferenceFile linked to the above CtrDocumentIdentifier to complete all dependencies
    employee = EmployeeFactory()

    employee_reference_file = EmployeeReferenceFile(
        employee_id=employee.employee_id,
        reference_file_id=reference_file.reference_file_id,
        ctr_document_identifier_id=ctr_document_identifer.ctr_document_identifier_id,
    )

    employee.reference_files = [employee_reference_file]

    test_db_session.add(employee_reference_file)
    test_db_session.add(employee)
    test_db_session.commit()

    # all dependencies met:
    dependencies = check_dependencies(ams_document, test_db_session, reference_file)

    assert dependencies.ams_document_id == ams_document_id
    assert dependencies.vc_doc_vcust == vc_doc_vcust
    assert dependencies.ctr_document_identifier == ctr_document_identifer
    assert dependencies.employee == employee


def test_update_employee_data(test_db_session, initialize_factories_session):
    ams_document = get_ams_document()
    ams_document_id = ams_document.get("DOC_ID")
    vc_doc_vcust = ams_document.find("VC_DOC_VCUST")
    vc_doc_ad = ams_document.find("VC_DOC_AD")  # address data
    vc_doc_ad_data = VcDocAdData(vc_doc_ad)

    employee = EmployeeFactory.create()

    # give the employee a mailing address with all None values
    new_address = Address()
    employee.mailing_address = new_address
    test_db_session.add(new_address)
    test_db_session.add(employee)
    test_db_session.commit()

    test_db_session.refresh(employee)

    assert employee.mailing_address.address_line_one is None
    assert employee.mailing_address.address_line_two is None
    assert employee.mailing_address.city is None
    assert employee.mailing_address.geo_state_id is None
    assert employee.mailing_address.zip_code is None

    update_employee_data(vc_doc_ad_data, ams_document_id, vc_doc_vcust, employee)

    assert employee.mailing_address.address_line_one == vc_doc_ad.find("STR_1_NM").text
    assert employee.mailing_address.address_line_two is None
    assert employee.mailing_address.city == vc_doc_ad.find("CITY_NM").text
    assert employee.mailing_address.zip_code == vc_doc_ad.find("ZIP").text
    assert employee.mailing_address.geo_state_id == GeoState.get_id(vc_doc_ad.find("ST").text)


def test_move_processed_file(test_db_session, initialize_factories_session, mock_s3_bucket):
    setup_mock_s3_bucket(mock_s3_bucket)
    reference_file = ReferenceFileFactory.create(file_location=RECEIVED_S3_PATH)
    move_processed_file(reference_file)
    assert reference_file.file_location == PROCESSED_S3_PATH

    processed_files = file_util.list_files(PROCESSED_FOLDER)
    received_files = file_util.list_files(RECEIVED_FOLDER)
    assert processed_files == ["test_file.xml"]
    assert received_files == []


def test_update_employee_data_when_missing_data(test_db_session, initialize_factories_session):
    ams_document = get_ams_document("missing_city")
    ams_document_id = ams_document.get("DOC_ID")
    TIN = ams_document.find("VC_DOC_VCUST").find("TIN").text

    (ctr_document_identifier, employee_reference_file, employee) = create_ovr_dependencies(
        ams_document_id, TIN, test_db_session
    )

    # give the employee a mailing address with all None values
    new_address = Address()
    employee.mailing_address = new_address
    test_db_session.add(new_address)
    test_db_session.add(employee)
    test_db_session.commit()

    test_db_session.refresh(employee)

    assert employee.mailing_address.address_line_one is None
    assert employee.mailing_address.address_line_two is None
    assert employee.mailing_address.city is None
    assert employee.mailing_address.geo_state_id is None
    assert employee.mailing_address.zip_code is None

    ovr_reference_file = get_ovr_reference_file()

    process_ams_document(ams_document, test_db_session, ovr_reference_file)

    test_db_session.refresh(employee)
    assert employee.mailing_address.address_line_one is None
    assert employee.mailing_address.address_line_two is None
    assert employee.mailing_address.city is None
    assert employee.mailing_address.geo_state_id is None
    assert employee.mailing_address.zip_code is None


def test_state_log_creation_with_no_validation_issues(
    test_db_session, initialize_factories_session
):
    ams_document = get_ams_document()
    ams_document_id = ams_document.get("DOC_ID")
    TIN = ams_document.find("VC_DOC_VCUST").find("TIN").text

    (ctr_document_identifier, employee_reference_file, employee,) = create_ovr_dependencies(
        ams_document_id, TIN, test_db_session
    )

    ovr_reference_file = get_ovr_reference_file()

    validation_container, state_log = process_ams_document(
        ams_document, test_db_session, ovr_reference_file
    )

    assert validation_container.has_validation_issues() is False
    assert state_log.start_state_id == State.VCC_SENT.state_id
    assert state_log.employee == employee
    assert state_log.payment is None
    assert state_log.reference_file is None


def test_state_log_creation_with_dependency_issues(test_db_session, initialize_factories_session):
    ams_document = get_ams_document()
    ovr_reference_file = get_ovr_reference_file()

    validation_container, state_log = process_ams_document(
        ams_document, test_db_session, ovr_reference_file
    )

    assert validation_container is None
    assert state_log is None


def test_state_log_with_validation_issues(test_db_session, initialize_factories_session):
    ams_document = get_ams_document("all_fields_invalid")
    ams_document_id = ams_document.get("DOC_ID")
    TIN = ams_document.find("VC_DOC_VCUST").find("TIN").text

    (ctr_document_identifier, employee_reference_file, employee,) = create_ovr_dependencies(
        ams_document_id, TIN, test_db_session
    )

    ovr_reference_file = get_ovr_reference_file()

    validation_container, state_log = process_ams_document(
        ams_document, test_db_session, ovr_reference_file
    )

    assert validation_container.has_validation_issues() is True
    assert state_log.start_state_id == State.VCC_SENT.state_id
    assert state_log.employee == employee
    assert state_log.payment is None
    assert state_log.reference_file is None


def test_process_ams_document_with_validation_issues(
    test_db_session, initialize_factories_session, monkeypatch
):
    # with validation issues, update_employee_data should not be called
    mock_update_employee_data = setup_mock_update_employee_data(monkeypatch)
    ams_document = get_ams_document("all_fields_invalid")
    ams_document_id = ams_document.get("DOC_ID")
    TIN = ams_document.find("VC_DOC_VCUST").find("TIN").text

    (ctr_document_identifier, employee_reference_file, employee,) = create_ovr_dependencies(
        ams_document_id, TIN, test_db_session
    )

    ovr_reference_file = get_ovr_reference_file()

    validation_container, state_log = process_ams_document(
        ams_document, test_db_session, ovr_reference_file
    )

    assert validation_container.has_validation_issues() is True
    assert mock_update_employee_data.times_called == 0
    assert state_log is not None


def test_process_ams_document_with_no_validation_issues(
    test_db_session, initialize_factories_session, monkeypatch
):
    # with no validation issues, update_employee_data should be called
    mock_update_employee_data = setup_mock_update_employee_data(monkeypatch)
    ams_document = get_ams_document()
    ams_document_id = ams_document.get("DOC_ID")
    TIN = ams_document.find("VC_DOC_VCUST").find("TIN").text

    (
        ctr_document_identifier,  # noqa
        employee_reference_file,  # noqa
        employee,  # noqa
    ) = create_ovr_dependencies(ams_document_id, TIN, test_db_session)

    ovr_reference_file = get_ovr_reference_file()

    validation_container, state_log = process_ams_document(
        ams_document, test_db_session, ovr_reference_file
    )

    assert validation_container.has_validation_issues() is False
    assert mock_update_employee_data.times_called == 1
    assert state_log is not None


def test_process_outbound_vendor_customer_return_reference_file_type(
    test_db_session, initialize_factories_session, caplog, mock_s3_bucket
):
    setup_mock_s3_bucket(mock_s3_bucket)

    # skips processing the file if ReferenceFileType is not OutboundVendorCustomerReturn
    caplog.set_level(logging.ERROR)  # noqa: B1
    reference_file = ReferenceFileFactory(file_location=RECEIVED_S3_PATH)
    process_outbound_vendor_customer_return(reference_file, test_db_session)
    assert "Skipping processing file at location" in caplog.text
    assert reference_file.file_location == RECEIVED_S3_PATH
    caplog.clear()

    # update the ReferenceFileType
    reference_file.reference_file_type_id = (
        ReferenceFileType.OUTBOUND_VENDOR_CUSTOMER_RETURN.reference_file_type_id
    )
    process_outbound_vendor_customer_return(reference_file, test_db_session)
    assert reference_file.file_location == PROCESSED_S3_PATH
    assert "Skipping processing file at location" not in caplog.text


def test_finish_state_log_with_validation_issues(
    test_db_session, initialize_factories_session, mock_s3_bucket
):
    # Test case: state log created and finished with "Validation issues found" outcome
    # By setting up dependencies for the "all_invalid_fields" AMS_DOCUMENT in the test file, the AMS_DOCUMENT should make it through the
    # process to the point where the state_log is finished with validation issues found
    setup_mock_s3_bucket(mock_s3_bucket)

    ams_document = get_ams_document("all_fields_invalid")
    ams_document_id = ams_document.get("DOC_ID")
    TIN = ams_document.find("VC_DOC_VCUST").find("TIN").text

    (ctr_document_identifier, employee_reference_file, employee) = create_ovr_dependencies(
        ams_document_id, TIN, test_db_session
    )

    ovr_reference_file = get_ovr_reference_file()

    process_outbound_vendor_customer_return(ovr_reference_file, test_db_session)

    state_log = test_db_session.query(StateLog).filter(StateLog.employee == employee).all()

    assert len(state_log) == 1
    state_log = state_log[0]
    assert state_log.start_state_id == State.VCC_SENT.state_id
    assert state_log.end_state_id == State.VCC_SENT.state_id
    assert state_log.employee_id == employee.employee_id
    assert state_log.outcome == {
        "message": "Validation issues found",
        "validation_container": {
            "record_key": "_INTFDFML161220200011",
            "validation_issues": [
                {"reason": "InvalidValue", "details": "DOC_ID"},
                {"reason": "InvalidValue", "details": "DOC_CAT"},
                {"reason": "InvalidValue", "details": "DOC_TYP"},
                {"reason": "InvalidValue", "details": "DOC_CD"},
                {"reason": "InvalidValue", "details": "DOC_DEPT_CD"},
                {"reason": "InvalidValue", "details": "DOC_UNIT_CD"},
                {"reason": "InvalidValue", "details": "ORG_TYP"},
                {"reason": "InvalidValue", "details": "TIN_TYP"},
                {"reason": "ValueNotFound", "details": "VC_DOC_AD"},
                {"reason": "NonNullable", "details": "VEND_CUST_CD"},
                {"reason": "NonNullable", "details": "ORG_VEND_CUST_CD"},
            ],
            "errors": [],
        },
    }
    assert ovr_reference_file.file_location == PROCESSED_S3_PATH


def test_finish_state_log_with_no_validation_issues(
    test_db_session, initialize_factories_session, mock_s3_bucket
):
    # Test case: state log created and finished with "No validation issues found" outcome
    # By setting up dependencies for the "valid" AMS_DOCUMENT in the test file, the AMS_DOCUMENT should make it through the
    # process to the point where the state_log is finished with no validation issues
    setup_mock_s3_bucket(mock_s3_bucket)

    ams_document = get_ams_document()
    ams_document_id = ams_document.get("DOC_ID")
    TIN = ams_document.find("VC_DOC_VCUST").find("TIN").text

    (ctr_document_identifier, employee_reference_file, employee) = create_ovr_dependencies(
        ams_document_id, TIN, test_db_session
    )

    assert employee.mailing_address.address_line_one is None
    assert employee.mailing_address.address_line_two is None
    assert employee.mailing_address.city is None
    assert employee.mailing_address.geo_state_id is None
    assert employee.mailing_address.zip_code is None

    ovr_reference_file = get_ovr_reference_file()

    process_outbound_vendor_customer_return(ovr_reference_file, test_db_session)

    state_log = test_db_session.query(StateLog).filter(StateLog.employee == employee).all()

    assert len(state_log) == 1
    state_log = state_log[0]
    assert state_log.start_state_id == State.VCC_SENT.state_id
    assert state_log.end_state_id == State.VCC_SENT.state_id
    assert state_log.employee_id == employee.employee_id
    assert state_log.outcome == {
        "message": "No validation issues found",
        "validation_container": {
            "record_key": "INTFDFML161220200010",
            "validation_issues": [],
            "errors": [],
        },
    }

    address = ams_document.find("VC_DOC_AD")

    assert employee.mailing_address.address_line_one == address.find("STR_1_NM").text
    assert employee.mailing_address.address_line_two is None
    assert employee.mailing_address.city == address.find("CITY_NM").text
    assert employee.mailing_address.geo_state.geo_state_description == address.find("ST").text
    assert employee.mailing_address.zip_code == address.find("ZIP").text
    assert ovr_reference_file.file_location == PROCESSED_S3_PATH


def test_handle_xml_syntax_error_S3_failure(
    test_db_session, initialize_factories_session, caplog, mock_s3_bucket
):
    setup_mock_s3_bucket(mock_s3_bucket)
    exception = Exception()
    caplog.set_level(logging.ERROR)  # noqa: B1
    ovr_reference_file = get_ovr_reference_file()

    # Test S3 failure
    invalid_s3_path = ovr_reference_file.file_location.replace("s3://", "notS3://")
    ovr_reference_file.file_location = invalid_s3_path

    handle_xml_syntax_error(ovr_reference_file, exception, test_db_session)

    test_db_session.refresh(ovr_reference_file)
    test_db_session.flush()

    assert ovr_reference_file.file_location == RECEIVED_S3_PATH
    assert (
        "an error occurred when attempting to move to 'notS3://test_bucket/ctr/inbound/error/test_file.xml'"
        in caplog.text
    )


def test_handle_xml_syntax_error_DB_failure(
    test_db_session, initialize_factories_session, caplog, mock_s3_bucket
):

    setup_mock_s3_bucket(mock_s3_bucket)
    exception = Exception()
    caplog.set_level(logging.ERROR)  # noqa: B1
    ovr_reference_file = get_ovr_reference_file()

    # Test DB failure
    # insert a ReferenceFile already containing the error path, forcing a unique key error in handle_xml_syntax_error
    ReferenceFileFactory(
        file_location=ovr_reference_file.file_location.replace("received", "error")
    )
    handle_xml_syntax_error(ovr_reference_file, exception, test_db_session)

    test_db_session.refresh(ovr_reference_file)
    received_files = file_util.list_files(RECEIVED_FOLDER)
    error_files = file_util.list_files(ERROR_FOLDER)

    assert "an error occurred when saving the new location" in caplog.text
    assert received_files == []
    assert error_files == ["test_file.xml"]
    assert ovr_reference_file.file_location == RECEIVED_S3_PATH


def test_handle_xml_syntax_error_no_issues(
    test_db_session, initialize_factories_session, caplog, mock_s3_bucket
):
    setup_mock_s3_bucket(mock_s3_bucket)
    exception = Exception()
    caplog.set_level(logging.ERROR)  # noqa: B1
    ovr_reference_file = get_ovr_reference_file()

    # No S3 or DB issues
    handle_xml_syntax_error(ovr_reference_file, exception, test_db_session)

    test_db_session.refresh(ovr_reference_file)
    received_files = file_util.list_files(RECEIVED_FOLDER)
    error_files = file_util.list_files(ERROR_FOLDER)

    assert received_files == []
    assert error_files == ["test_file.xml"]
    assert ovr_reference_file.file_location == ERROR_S3_PATH
