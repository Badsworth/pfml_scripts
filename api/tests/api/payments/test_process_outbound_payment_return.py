import os

import boto3
import defusedxml.ElementTree as ET
import pytest

import massgov.pfml.payments.process_outbound_payment_return as process_outbound_payment_return
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.factories import (
    CtrDocumentIdentifierFactory,
    PaymentReferenceFileFactory,
    ReferenceFileFactory,
)
from massgov.pfml.payments.payments_util import ValidationReason

file_with_no_errors = "mock_payment_return.dat"
file_with_errors = "mock_payment_return_2.dat"


def get_paths(mock_s3_bucket, file_name):
    s3 = boto3.resource("s3")
    folder_name = "ctr/inbound/received"
    key = "{}/{}".format(folder_name, file_name)

    test_file_path = os.path.join(os.path.dirname(__file__), "test_files", file_name)
    full_path = "s3://{}/{}".format(mock_s3_bucket, key)

    s3.Object(mock_s3_bucket, key).put(Body=open(test_file_path, "rb"))
    return full_path, test_file_path


def payment_reference_file_setup(test_db_session, initialize_factories_session):
    ctr_doc_id = "INTFDFMLN50LINES0001"
    ctr_document_identifier = CtrDocumentIdentifierFactory.create(
        ctr_document_identifier=ctr_doc_id
    )
    pay_ref_1 = PaymentReferenceFileFactory.create(ctr_document_identifier=ctr_document_identifier)

    ctr_doc_id_2 = "INTFDFMLGYLDEZWTZYCP"
    ctr_document_identifier_2 = CtrDocumentIdentifierFactory.create(
        ctr_document_identifier=ctr_doc_id_2
    )
    pay_ref_2 = PaymentReferenceFileFactory.create(
        ctr_document_identifier=ctr_document_identifier_2
    )

    return pay_ref_1, pay_ref_2


def test_get_validation_issues_no_issues():
    file_location = os.path.join(os.path.dirname(__file__), "test_files", file_with_no_errors)
    file = file_util.read_file(file_location)
    mock_xml_data = ET.fromstring(file)

    single_payment_return_doc = mock_xml_data[0]

    payment_return_doc_data = process_outbound_payment_return.get_validation_issues(
        single_payment_return_doc, "INTFDFMLN50LINES0001"
    )
    validation_container = payment_return_doc_data.validation_container

    assert validation_container.record_key == "INTFDFMLN50LINES0001"
    assert len(validation_container.validation_issues) == 0
    assert len(validation_container.errors) == 0

    assert payment_return_doc_data.py_id == "INTFDFMLN50LINES0001"
    assert payment_return_doc_data.py_cd == "GAX"
    assert payment_return_doc_data.py_dept == "EOL"
    assert payment_return_doc_data.vend_cd == "VC0001201168"
    assert payment_return_doc_data.chk_no == "00002493873"
    assert payment_return_doc_data.chk_am == "50.00"
    assert payment_return_doc_data.chk_eft_iss_dt == "2020-12-17"


def test_get_validation_issues_with_issues():
    mock_invalid_payment_return_doc = """<?xml version="1.0" encoding="ISO-8859-1"?>
    <AMS_DOC_XML_EXPORT_FILE>
        <PYMT_RETN_DOC>
            <PY_CD Attribute="Y"><![CDATA[WRONG]]></PY_CD>
        </PYMT_RETN_DOC>
    </AMS_DOC_XML_EXPORT_FILE>"""

    mock_invalid_xml_data = ET.fromstring(mock_invalid_payment_return_doc)

    single_invalid_payment_return_doc = mock_invalid_xml_data[0]

    payment_return_doc_data = process_outbound_payment_return.get_validation_issues(
        single_invalid_payment_return_doc, None
    )

    validation_container = payment_return_doc_data.validation_container

    assert payment_return_doc_data.py_id is None
    assert payment_return_doc_data.py_cd == "WRONG"
    assert payment_return_doc_data.py_dept is None
    assert payment_return_doc_data.vend_cd is None
    assert payment_return_doc_data.chk_no is None
    assert payment_return_doc_data.chk_am is None
    assert payment_return_doc_data.chk_eft_iss_dt is None

    assert any(
        issue.reason == ValidationReason.MISSING_FIELD and issue.details == "PY_ID"
        for issue in validation_container.validation_issues
    )
    assert any(
        issue.reason == ValidationReason.MISSING_FIELD and issue.details == "VEND_CD"
        for issue in validation_container.validation_issues
    )
    assert any(
        issue.reason == ValidationReason.MISSING_FIELD and issue.details == "CHK_AM"
        for issue in validation_container.validation_issues
    )
    assert any(
        issue.reason == ValidationReason.MISSING_FIELD and issue.details == "CHK_NO"
        for issue in validation_container.validation_issues
    )
    assert any(
        issue.reason == ValidationReason.MISSING_FIELD and issue.details == "CHK_EFT_ISS_DT"
        for issue in validation_container.validation_issues
    )
    assert any(
        issue.reason == ValidationReason.INVALID_VALUE and issue.details == "PY_CD"
        for issue in validation_container.validation_issues
    )
    assert any(
        issue.reason == ValidationReason.MISSING_FIELD and issue.details == "PY_DEPT"
        for issue in validation_container.validation_issues
    )

    assert validation_container.record_key is None
    assert len(validation_container.validation_issues) == 7
    assert len(validation_container.errors) == 0


def test_process_outbound_payment_return_success(
    test_db_session, mock_s3_bucket, initialize_factories_session
):
    full_path, test_file_path = get_paths(mock_s3_bucket, file_with_no_errors)
    payment_reference_file_setup(test_db_session, initialize_factories_session)

    ref_file = ReferenceFileFactory.create(file_location=full_path)
    result = process_outbound_payment_return.process_outbound_payment_return(
        test_db_session, ref_file
    )
    assert len(result) == 0

    test_db_session.refresh(ref_file)
    assert (
        ref_file.file_location == "s3://test_bucket/ctr/inbound/processed/mock_payment_return.dat"
    )


def test_payment_obj_updates(test_db_session, mock_s3_bucket, initialize_factories_session):
    full_path, test_file_path = get_paths(mock_s3_bucket, file_with_no_errors)
    pay_ref_1, pay_ref_2 = payment_reference_file_setup(
        test_db_session, initialize_factories_session
    )

    payment_1 = pay_ref_1.payment
    payment_2 = pay_ref_2.payment

    ref_file = ReferenceFileFactory.create(file_location=full_path)
    result = process_outbound_payment_return.process_outbound_payment_return(
        test_db_session, ref_file
    )
    assert len(result) == 0

    # test that after outbound payment return has been processed, payment object is updated
    # with values from the xml file
    test_db_session.refresh(payment_1)
    payment_1.disb_amount == "50.00"
    payment_1.disb_check_eft_issue_date == "2020-12-17"
    payment_1.disb_check_eft_number == "00002493873"
    payment_1.disb_method.payment_method_description == "Check"

    test_db_session.refresh(payment_2)
    payment_2.disb_amount == "75.00"
    payment_2.disb_check_eft_issue_date == "2020-12-17"
    payment_2.disb_check_eft_number == "0000249123A"
    payment_2.disb_method.payment_method_description == "ACH"


def test_process_outbound_payment_return_with_issues(
    test_db_session, mock_s3_bucket, initialize_factories_session
):
    full_path, test_file_path = get_paths(mock_s3_bucket, file_with_errors)
    payment_reference_file_setup(test_db_session, initialize_factories_session)

    ref_file = ReferenceFileFactory.create(file_location=full_path)
    result = process_outbound_payment_return.process_outbound_payment_return(
        test_db_session, ref_file
    )

    assert len(result) == 7

    test_db_session.refresh(ref_file)
    assert (
        ref_file.file_location == "s3://test_bucket/ctr/inbound/processed/mock_payment_return_2.dat"
    )

    for container in result:
        any(
            container.record_key == "INTFDFMLN50LINES0001"
            and issue.reason == ValidationReason.INVALID_VALUE
            and issue.details == "PY_CD"
            for issue in container.validation_issues
        )
        any(
            container.record_key == "INTFDFMLGYLDEZWTZYCP"
            and issue.reason == ValidationReason.INVALID_VALUE
            and issue.details == "PY_DEPT"
            for issue in container.validation_issues
        )
        any(
            container.record_key == "INTFDFMLN50LINESABCD"
            and issue.reason == ValidationReason.MISSING_FIELD
            and issue.details == "VEND_CD"
            for issue in container.validation_issues
        )
        any(
            container.record_key == "INTFDFMLGYLDEZWTEFG"
            and issue.reason == ValidationReason.INVALID_VALUE
            and issue.details == "CHK_AM"
            for issue in container.validation_issues
        )
        any(
            container.record_key == "INTFDFMLN50LINESHIJK"
            and issue.reason == ValidationReason.INVALID_VALUE
            and issue.details == "CHK_NO"
            for issue in container.validation_issues
        )
        any(
            container.record_key == "INTFDFMLN50LINESLMNO"
            and issue.reason == ValidationReason.MISSING_FIELD
            and issue.details == "DOC_ID"
            for issue in container.validation_issues
        )
        any(
            container.record_key == "None"
            and issue.reason == ValidationReason.MISSING_FIELD
            and issue.details == "PY_ID"
            for issue in container.validation_issues
        )


def test_process_outbound_payment_return_no_pay_ref(
    test_db_session, mock_s3_bucket, initialize_factories_session
):
    full_path, test_file_path = get_paths(mock_s3_bucket, file_with_no_errors)

    ref_file = ReferenceFileFactory.create(file_location=full_path)
    result = process_outbound_payment_return.process_outbound_payment_return(
        test_db_session, ref_file
    )

    assert len(result) == 2

    test_db_session.refresh(ref_file)
    assert (
        ref_file.file_location == "s3://test_bucket/ctr/inbound/processed/mock_payment_return.dat"
    )

    validation_container_1 = result[0]
    errors_1 = validation_container_1.errors
    issues_1 = validation_container_1.validation_issues

    assert len(errors_1) == 0
    assert validation_container_1.record_key == "INTFDFMLN50LINES0001"
    assert issues_1[0].reason == ValidationReason.MISSING_IN_DB
    assert issues_1[0].details == "PaymentReferenceFile"

    validation_container_2 = result[1]
    errors_2 = validation_container_2.errors
    issues_2 = validation_container_2.validation_issues

    assert len(errors_2) == 0
    assert validation_container_2.record_key == "INTFDFMLGYLDEZWTZYCP"
    assert issues_2[0].reason == ValidationReason.MISSING_IN_DB
    assert issues_2[0].details == "PaymentReferenceFile"


def test_process_outbound_payment_return_invalid_path(
    test_db_session, mock_s3_bucket, initialize_factories_session
):
    ref_file = ReferenceFileFactory.create(file_location="not a valid path")

    with pytest.raises(Exception):
        process_outbound_payment_return.process_outbound_payment_return(test_db_session, ref_file)


def test_process_outbound_payment_return_invalid_xml(
    test_db_session, mock_s3_bucket, initialize_factories_session
):
    full_path, test_file_path = get_paths(mock_s3_bucket, "leave_plan.csv")

    ref_file = ReferenceFileFactory.create(file_location=full_path)

    with pytest.raises(Exception):
        process_outbound_payment_return.process_outbound_payment_return(test_db_session, ref_file)

    test_db_session.refresh(ref_file)
    assert ref_file.file_location == "s3://test_bucket/ctr/inbound/error/leave_plan.csv"
