import logging  # noqa: B1
import os
import pathlib

import boto3
import defusedxml.ElementTree as ET
import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.outbound_returns.outbound_vendor_customer_return as outbound_vendor_customer_return
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    CtrDocumentIdentifier,
    Employee,
    EmployeeReferenceFile,
    GeoState,
    ReferenceFileType,
    State,
    StateLog,
    TaxIdentifier,
)
from massgov.pfml.db.models.factories import (
    CtrAddressPairFactory,
    CtrDocumentIdentifierFactory,
    EmployeeFactory,
    EmployeeReferenceFileFactory,
    ReferenceFileFactory,
    TaxIdentifierFactory,
)
from massgov.pfml.payments.payments_util import Constants, ValidationContainer, ValidationReason
from massgov.pfml.types import TaxId
from tests.helpers.state_log import AdditionalParams, setup_state_log

# every test in here requires real resources
pytestmark = pytest.mark.integration

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
PROCESSED_FOLDER = RECEIVED_FOLDER.replace(
    Constants.S3_INBOUND_RECEIVED_DIR, Constants.S3_INBOUND_PROCESSED_DIR
)
PROCESSED_S3_PATH = f"{PROCESSED_FOLDER}/{SOURCE_FILE_NAME}"
ERROR_FOLDER = RECEIVED_FOLDER.replace(
    Constants.S3_INBOUND_RECEIVED_DIR, Constants.S3_INBOUND_ERROR_DIR
)
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
    ams_document_id, tin, test_db_session, previous_states=None
) -> [CtrDocumentIdentifier, EmployeeReferenceFile, Employee]:
    """
    Successful processing of an AMS Document within an OVR file requires multiple dependencies:
    - An employee
    - A CtrDocumentIdentifier the "ctr_document_identifier" field matching the DOC_ID in the AMS_DOCUMENT
    - A ReferenceFile of type VCC
    - An EmployeeReferenceFile that connects the above Employee, VCC ReferenceFile and CtrDocumentIdentifier
    - A previous StateLog entry

    The test xml file used for these tests contain multiple AMS_DOCUMENT objects. To test processing a specific AMS_DOCUMENT,
    create just the dependencies for that AMS_DOCUMENT by passing in the DOC_ID and TIN values from that AMS_DOCUMENT.

    All the other AMS_DOCUMENTS will fail the validation steps, since their depdencies won't exist.
    """
    # TIN comes in with an invalid format from the document. Remove leading and trailing _
    tin = tin.replace("_", "")

    if previous_states is None:
        previous_states = [State.VCC_SENT]

    state_log_setup_results = setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_states=previous_states,
        test_db_session=test_db_session,
        additional_params=AdditionalParams(tax_identifier=TaxIdentifier(tax_identifier=tin),),
    )

    employee = state_log_setup_results.associated_model
    ctr_address_pair = CtrAddressPairFactory()
    employee.ctr_address_pair = ctr_address_pair
    ctr_document_identifier = CtrDocumentIdentifierFactory(
        ctr_document_identifier=ams_document_id, document_date="2021-01-01", document_counter=1
    )
    vcc_reference_file = ReferenceFileFactory(
        reference_file_type_id=ReferenceFileType.VCC.reference_file_type_id
    )
    employee_reference_file = EmployeeReferenceFileFactory(
        employee=employee,
        ctr_document_identifier=ctr_document_identifier,
        reference_file=vcc_reference_file,
    )

    return (ctr_document_identifier, employee_reference_file, employee)


def get_ovr_reference_file():
    return ReferenceFileFactory(
        reference_file_type_id=ReferenceFileType.OUTBOUND_VENDOR_CUSTOMER_RETURN.reference_file_type_id,
        file_location=RECEIVED_S3_PATH,
    )


def setup_mock_update_employee_data(monkeypatch):
    def mock_update_employee_data(
        ams_document, ams_document_id, vc_doc_vcust, employee, db_session
    ):
        mock_update_employee_data.times_called = mock_update_employee_data.times_called + 1

    mock_update_employee_data.times_called = 0

    monkeypatch.setattr(
        "massgov.pfml.payments.outbound_returns.outbound_vendor_customer_return.update_employee_data",
        mock_update_employee_data,
    )
    return mock_update_employee_data


def setup_mock_s3_bucket(mock_s3_bucket):
    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key=SOURCE_KEY, Body=file_util.read_file(TEST_FILE_PATH))


# === TESTS BEGIN ===


def test_validate_ams_document_valid_doc(test_db_session, initialize_factories_session):
    ams_document = get_ams_document()
    ams_document_id = ams_document.get("DOC_ID")
    validation_container = ValidationContainer(ams_document_id)
    vc_doc_vcust = ams_document.find("VC_DOC_VCUST")

    tax_identifier = TaxIdentifierFactory.create(tax_identifier="517467495")
    employee = EmployeeFactory.create(tax_identifier=tax_identifier)

    (
        validation_container,
        validated_address_data,
    ) = outbound_vendor_customer_return.validate_ams_document(
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

    (
        validation_container,
        validated_address_data,
    ) = outbound_vendor_customer_return.validate_ams_document(
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

    assert len(validation_container.validation_issues) == 11


def test_validate_ams_document_with_missing_fields(test_db_session, initialize_factories_session):
    ams_document = get_ams_document("missing_fields")
    ams_document_id = ams_document.get("DOC_ID")
    validation_container = ValidationContainer(ams_document_id)
    vc_doc_vcust = ams_document.find("VC_DOC_VCUST")

    tax_identifier = TaxIdentifier(tax_identifier="590764658")
    employee = EmployeeFactory.create(tax_identifier=tax_identifier)

    (
        validation_container,
        validated_address_data,
    ) = outbound_vendor_customer_return.validate_ams_document(
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


def test_validate_ams_document_with_multiple_addresses(
    test_db_session, initialize_factories_session
):
    ams_document = get_ams_document("multiple_addresses")
    ams_document_id = ams_document.get("DOC_ID")
    validation_container = ValidationContainer(ams_document_id)
    vc_doc_vcust = ams_document.find("VC_DOC_VCUST")

    tax_identifier = TaxIdentifier(tax_identifier="579313283")
    employee = EmployeeFactory.create(tax_identifier=tax_identifier)

    (
        validation_container,
        validated_address_data,
    ) = outbound_vendor_customer_return.validate_ams_document(
        ams_document, ams_document_id, vc_doc_vcust, employee, validation_container
    )

    assert len(validation_container.validation_issues) == 1
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
    dependencies = outbound_vendor_customer_return.check_dependencies(
        ams_document, test_db_session, reference_file
    )

    assert dependencies.ams_document_id is None
    assert dependencies.ctr_document_identifier is None
    assert dependencies.employee is None
    assert dependencies.vc_doc_vcust is None

    # VC_DOC_VCUST not in AMS_DOCUMENT

    ams_document = get_ams_document("missing_vc_doc_vcust")
    ams_document_id = ams_document.get("DOC_ID")
    dependencies = outbound_vendor_customer_return.check_dependencies(
        ams_document, test_db_session, reference_file
    )

    assert dependencies.ams_document_id == ams_document_id
    assert dependencies.vc_doc_vcust is None
    assert dependencies.ctr_document_identifier is None
    assert dependencies.employee is None

    # ctr_document_identifier is not found

    ams_document = get_ams_document()
    vc_doc_vcust = ams_document.find("VC_DOC_VCUST")
    ams_document_id = ams_document.get("DOC_ID")
    dependencies = outbound_vendor_customer_return.check_dependencies(
        ams_document, test_db_session, reference_file
    )

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
    dependencies = outbound_vendor_customer_return.check_dependencies(
        ams_document, test_db_session, reference_file
    )

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
    dependencies = outbound_vendor_customer_return.check_dependencies(
        ams_document, test_db_session, reference_file
    )

    assert dependencies.ams_document_id == ams_document_id
    assert dependencies.vc_doc_vcust == vc_doc_vcust
    assert dependencies.ctr_document_identifier == ctr_document_identifer
    assert dependencies.employee == employee


def test_update_employee_data(test_db_session, initialize_factories_session):
    ams_document = get_ams_document()
    ams_document_id = ams_document.get("DOC_ID")
    vc_doc_vcust = ams_document.find("VC_DOC_VCUST")
    vc_doc_ad = ams_document.find("VC_DOC_AD")  # address data
    vc_doc_ad_data = outbound_vendor_customer_return.VcDocAdData(vc_doc_ad)

    employee = EmployeeFactory.create()

    # give the employee a CtrAddressPair without a ctr_address
    ctr_address_pair = CtrAddressPairFactory()
    employee.ctr_address_pair = ctr_address_pair
    test_db_session.add(employee)
    test_db_session.commit()

    test_db_session.refresh(employee)

    assert employee.ctr_address_pair.ctr_address is None

    outbound_vendor_customer_return.update_employee_data(
        vc_doc_ad_data, ams_document_id, vc_doc_vcust, employee, test_db_session
    )

    assert employee.ctr_address_pair.ctr_address.address_line_one == vc_doc_ad.find("STR_1_NM").text
    assert employee.ctr_address_pair.ctr_address.address_line_two is None
    assert employee.ctr_address_pair.ctr_address.city == vc_doc_ad.find("CITY_NM").text
    assert employee.ctr_address_pair.ctr_address.zip_code == vc_doc_ad.find("ZIP").text
    assert employee.ctr_address_pair.ctr_address.geo_state_id == GeoState.get_id(
        vc_doc_ad.find("ST").text
    )


def test_update_employee_data_when_missing_data(test_db_session, initialize_factories_session):
    ams_document = get_ams_document("missing_city")
    ams_document_id = ams_document.get("DOC_ID")
    tin = ams_document.find("VC_DOC_VCUST").find("TIN").text

    (ctr_document_identifier, employee_reference_file, employee) = create_ovr_dependencies(
        ams_document_id, tin, test_db_session
    )

    # give the employee a mailing address with all None values
    employee.ctr_address_pair = CtrAddressPairFactory()
    test_db_session.add(employee)
    test_db_session.commit()

    test_db_session.refresh(employee)

    assert employee.ctr_address_pair.ctr_address is None

    ovr_reference_file = get_ovr_reference_file()

    outbound_vendor_customer_return.process_ams_document(
        ams_document, test_db_session, ovr_reference_file
    )

    test_db_session.refresh(employee)
    assert employee.ctr_address_pair.ctr_address is None


def test_state_log_creation_with_no_validation_issues(
    test_db_session, initialize_factories_session
):
    ams_document = get_ams_document()
    ams_document_id = ams_document.get("DOC_ID")
    tin = ams_document.find("VC_DOC_VCUST").find("TIN").text

    (ctr_document_identifier, employee_reference_file, employee) = create_ovr_dependencies(
        ams_document_id, tin, test_db_session
    )

    ovr_reference_file = get_ovr_reference_file()

    validation_container, state_log = outbound_vendor_customer_return.process_ams_document(
        ams_document, test_db_session, ovr_reference_file
    )

    assert validation_container.has_validation_issues() is False
    assert state_log.employee == employee
    assert state_log.payment is None
    assert state_log.reference_file is None
    assert state_log.end_state_id == State.VCC_SENT.state_id


def test_state_log_creation_with_dependency_issues(test_db_session, initialize_factories_session):
    ams_document = get_ams_document()
    ovr_reference_file = get_ovr_reference_file()

    validation_container, state_log = outbound_vendor_customer_return.process_ams_document(
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

    validation_container, state_log = outbound_vendor_customer_return.process_ams_document(
        ams_document, test_db_session, ovr_reference_file
    )

    assert validation_container.has_validation_issues() is True
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

    validation_container, state_log = outbound_vendor_customer_return.process_ams_document(
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

    validation_container, state_log = outbound_vendor_customer_return.process_ams_document(
        ams_document, test_db_session, ovr_reference_file
    )

    assert validation_container.has_validation_issues() is False
    assert mock_update_employee_data.times_called == 1
    assert state_log is not None


def test_process_outbound_vendor_customer_return_reference_file_type(
    test_db_session, initialize_factories_session, caplog, mock_s3_bucket
):
    setup_mock_s3_bucket(mock_s3_bucket)

    # skips processing the file because ReferenceFileType is not
    # OUTBOUND_VENDOR_CUSTOMER_RETURN
    caplog.set_level(logging.ERROR)  # noqa: B1
    reference_file = ReferenceFileFactory(file_location=RECEIVED_S3_PATH)
    with pytest.raises(ValueError):
        outbound_vendor_customer_return.process_outbound_vendor_customer_return(
            test_db_session, reference_file
        )
    assert reference_file.file_location == RECEIVED_S3_PATH
    assert "Unable to process ReferenceFile" in caplog.text
    caplog.clear()

    # set the ReferenceFileType to OUTBOUND_VENDOR_CUSTOMER_RETURN
    reference_file.reference_file_type_id = (
        ReferenceFileType.OUTBOUND_VENDOR_CUSTOMER_RETURN.reference_file_type_id
    )
    outbound_vendor_customer_return.process_outbound_vendor_customer_return(
        test_db_session, reference_file
    )
    assert reference_file.file_location == PROCESSED_S3_PATH
    assert "Unable to process ReferenceFile" not in caplog.text


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

    outbound_vendor_customer_return.process_outbound_vendor_customer_return(
        test_db_session, ovr_reference_file
    )

    state_log = (
        test_db_session.query(StateLog)
        .filter(StateLog.employee == employee)
        .order_by(StateLog.ended_at)
        .all()
    )

    assert len(state_log) == 2
    # First StateLog is the initial state
    # Second StateLog is the new state with the error
    state_log = state_log[1]
    assert state_log.end_state_id == State.VCC_SENT.state_id
    assert state_log.employee_id == employee.employee_id
    assert state_log.outcome == {
        "message": "Processed Outbound Vendor Return: Validation issues found",
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

    assert employee.ctr_address_pair.ctr_address is None
    ovr_reference_file = get_ovr_reference_file()

    outbound_vendor_customer_return.process_outbound_vendor_customer_return(
        test_db_session, ovr_reference_file
    )

    state_log = (
        test_db_session.query(StateLog)
        .filter(StateLog.employee == employee)
        .order_by(StateLog.ended_at)
        .all()
    )

    assert len(state_log) == 2
    # First StateLog is the initial state
    # Second StateLog is the new state
    state_log = state_log[1]
    assert state_log.end_state_id == State.VCC_SENT.state_id
    assert state_log.employee_id == employee.employee_id
    assert state_log.outcome == {
        "message": "Processed Outbound Vendor Return: No validation issues found"
    }

    address = ams_document.find("VC_DOC_AD")

    assert employee.ctr_address_pair.ctr_address.address_line_one == address.find("STR_1_NM").text
    assert employee.ctr_address_pair.ctr_address.address_line_two is None
    assert employee.ctr_address_pair.ctr_address.city == address.find("CITY_NM").text
    assert (
        employee.ctr_address_pair.ctr_address.geo_state.geo_state_description
        == address.find("ST").text
    )
    assert employee.ctr_address_pair.ctr_address.zip_code == address.find("ZIP").text
    assert ovr_reference_file.file_location == PROCESSED_S3_PATH


def test_finish_state_log_with_alternate_previous_state(
    test_db_session, initialize_factories_session, mock_s3_bucket
):
    # Test case: state log created and finished with "No validation issues found" outcome
    # By setting up dependencies for the "valid" AMS_DOCUMENT in the test file, the AMS_DOCUMENT should make it through the
    # process to the point where the state_log is finished with no validation issues
    setup_mock_s3_bucket(mock_s3_bucket)

    ams_document = get_ams_document()
    ams_document_id = ams_document.get("DOC_ID")
    tin = ams_document.find("VC_DOC_VCUST").find("TIN").text

    (ctr_document_identifier, employee_reference_file, employee) = create_ovr_dependencies(
        ams_document_id, tin, test_db_session, previous_states=[State.IDENTIFY_MMARS_STATUS]
    )

    ovr_reference_file = get_ovr_reference_file()

    outbound_vendor_customer_return.process_outbound_vendor_customer_return(
        test_db_session, ovr_reference_file
    )

    state_log = (
        test_db_session.query(StateLog)
        .filter(StateLog.employee == employee)
        .order_by(StateLog.ended_at)
        .all()
    )

    assert len(state_log) == 2
    # First StateLog is the initial state
    # Second StateLog is the new state
    state_log = state_log[1]
    assert state_log.end_state_id == State.IDENTIFY_MMARS_STATUS.state_id
