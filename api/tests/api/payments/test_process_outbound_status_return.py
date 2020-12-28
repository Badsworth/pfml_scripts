import os

import boto3
import defusedxml.ElementTree as ET
import pytest

import massgov.pfml.payments.outbound_status_return as process_outbound_status_return
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.factories import (
    CtrDocumentIdentifierFactory,
    PaymentReferenceFileFactory,
    ReferenceFileFactory,
)
from massgov.pfml.payments.payments_util import ValidationReason

file_with_no_errors = "mock_status_return.dat"
file_with_errors = "mock_status_return_2.dat"


def get_paths(mock_s3_bucket, file_name):
    s3 = boto3.resource("s3")
    folder_name = "ctr/inbound/received"
    key = "{}/{}".format(folder_name, file_name)

    test_file_path = os.path.join(os.path.dirname(__file__), "test_files", file_name)
    full_path = "s3://{}/{}".format(mock_s3_bucket, key)

    s3.Object(mock_s3_bucket, key).put(Body=open(test_file_path, "rb"))
    return full_path, test_file_path


def payment_reference_file_setup(test_db_session, initialize_factories_session):
    ctr_doc_id = "INTFDFMLGYLDEZWTZYCP"
    ctr_document_identifier = CtrDocumentIdentifierFactory.create(
        ctr_document_identifier=ctr_doc_id
    )
    PaymentReferenceFileFactory.create(ctr_document_identifier=ctr_document_identifier)

    ctr_doc_id_2 = "INTFDFMLLNILNPSWAVCB"
    ctr_document_identifier_2 = CtrDocumentIdentifierFactory.create(
        ctr_document_identifier=ctr_doc_id_2
    )
    PaymentReferenceFileFactory.create(ctr_document_identifier=ctr_document_identifier_2)


def test_get_validation_issues_no_issues():
    file_location = os.path.join(os.path.dirname(__file__), "test_files", file_with_no_errors)
    file = file_util.read_file(file_location)

    mock_xml_data = ET.fromstring(file)
    single_status_return_doc = mock_xml_data[0]

    status_return_doc_data = process_outbound_status_return.get_payment_validation_issues(
        single_status_return_doc, "INTFDFMLGYLDEZWTZYCP", "GAX"
    )
    validation_container = status_return_doc_data.validation_container

    assert validation_container.record_key == "INTFDFMLGYLDEZWTZYCP"
    assert len(validation_container.validation_issues) == 0
    assert len(validation_container.errors) == 0

    assert status_return_doc_data.doc_id == "INTFDFMLGYLDEZWTZYCP"
    assert status_return_doc_data.doc_cd == "GAX"
    assert status_return_doc_data.dept_cd == "EOL"
    assert status_return_doc_data.unit_cd == "8770"
    assert status_return_doc_data.tran_cd == "GAX"


def test_get_validation_issues_with_issues():
    mock_invalid_status_return_doc = """<?xml version="1.0" ?>
    <AMS_IC_STATUS>
        <AMS_DOCUMENT BATCH_ID="EOL1217GAX20" IMP_DT="2020-12-17" TRAN_CD="GAX">
            <DOC_CD><![CDATA[WRONG]]></DOC_CD>
        </AMS_DOCUMENT>
    </AMS_IC_STATUS>"""

    mock_invalid_xml_data = ET.fromstring(mock_invalid_status_return_doc)
    single_invalid_status_return_doc = mock_invalid_xml_data[0]

    status_return_doc_data = process_outbound_status_return.get_payment_validation_issues(
        single_invalid_status_return_doc, None, "GAX"
    )
    validation_container = status_return_doc_data.validation_container

    assert status_return_doc_data.doc_id is None
    assert status_return_doc_data.doc_cd == "WRONG"
    assert status_return_doc_data.dept_cd is None
    assert status_return_doc_data.tran_cd == "GAX"
    assert status_return_doc_data.unit_cd is None
    assert any(
        issue.reason == ValidationReason.MISSING_FIELD and issue.details == "DOC_ID"
        for issue in validation_container.validation_issues
    )
    assert any(
        issue.reason == ValidationReason.MISSING_FIELD and issue.details == "DEPT_CD"
        for issue in validation_container.validation_issues
    )
    assert any(
        issue.reason == ValidationReason.MISSING_FIELD and issue.details == "UNIT_CD"
        for issue in validation_container.validation_issues
    )
    assert any(
        issue.reason == ValidationReason.INVALID_VALUE and issue.details == "DOC_CD"
        for issue in validation_container.validation_issues
    )
    assert any(
        issue.reason == ValidationReason.INVALID_VALUE and issue.details == "TRAN_CD and DOC_CD"
        for issue in validation_container.validation_issues
    )

    assert validation_container.record_key is None
    assert len(validation_container.validation_issues) == 5
    assert len(validation_container.errors) == 0


def test_process_outbound_status_return_success(
    test_db_session, mock_s3_bucket, initialize_factories_session
):
    full_path, test_file_path = get_paths(mock_s3_bucket, file_with_no_errors)
    payment_reference_file_setup(test_db_session, initialize_factories_session)

    ref_file = ReferenceFileFactory.create(file_location=full_path)
    result = process_outbound_status_return.process_outbound_status_return(
        test_db_session, ref_file
    )
    assert len(result) == 0

    test_db_session.refresh(ref_file)
    assert ref_file.file_location == "s3://test_bucket/ctr/inbound/processed/mock_status_return.dat"


def test_process_outbound_status_return_with_issues(
    test_db_session, mock_s3_bucket, initialize_factories_session
):
    full_path, test_file_path = get_paths(mock_s3_bucket, file_with_errors)
    payment_reference_file_setup(test_db_session, initialize_factories_session)

    ref_file = ReferenceFileFactory.create(file_location=full_path)
    result = process_outbound_status_return.process_outbound_status_return(
        test_db_session, ref_file
    )

    assert len(result) == 7

    test_db_session.refresh(ref_file)
    assert (
        ref_file.file_location == "s3://test_bucket/ctr/inbound/processed/mock_status_return_2.dat"
    )

    for container in result:
        any(
            container.record_key == "'INTFDFMLGYLDEZWTZYCP"
            and issue.reason == ValidationReason.INVALID_VALUE
            and issue.details == "TRAN_CD and DOC_CD"
            for issue in container.validation_issues
        )
        any(
            container.record_key == "INTFDFMLLNILNPSWAVAB"
            and issue.reason == ValidationReason.INVALID_VALUE
            and issue.details == "UNIT_CD"
            for issue in container.validation_issues
        )
        any(
            container.record_key == "INTFDFMLLNILNPSWAVCD"
            and issue.reason == ValidationReason.MISSING_FIELD
            and issue.details == "UNIT_CD"
            for issue in container.validation_issues
        )
        any(
            container.record_key == "INTFDFMLLNILNPSWAVEF"
            and issue.reason == ValidationReason.INVALID_VALUE
            and issue.details == "DEPT_CD"
            for issue in container.validation_issues
        )
        any(
            container.record_key == "INTFDFMLLNILNPSWAVGH"
            and issue.reason == ValidationReason.INVALID_VALUE
            and issue.details == "TRAN_CD"
            for issue in container.validation_issues
        )
        any(
            container.record_key == "INTFDFMLLNILNPSWAVIJ"
            and issue.reason == ValidationReason.MISSING_FIELD
            and issue.details == "TRAN_CD"
            for issue in container.validation_issues
        )
        any(
            container.record_key == "None"
            and issue.reason == ValidationReason.MISSING_FIELD
            and issue.details == "DOC_ID"
            for issue in container.validation_issues
        )


def test_process_outbound_status_return_no_pay_ref(
    test_db_session, mock_s3_bucket, initialize_factories_session
):
    full_path, test_file_path = get_paths(mock_s3_bucket, file_with_no_errors)

    ref_file = ReferenceFileFactory.create(file_location=full_path)
    result = process_outbound_status_return.process_outbound_status_return(
        test_db_session, ref_file
    )

    assert len(result) == 2

    test_db_session.refresh(ref_file)
    assert ref_file.file_location == "s3://test_bucket/ctr/inbound/processed/mock_status_return.dat"

    validation_container_1 = result[0]
    errors_1 = validation_container_1.errors
    issues_1 = validation_container_1.validation_issues

    assert len(errors_1) == 0
    assert validation_container_1.record_key == "INTFDFMLGYLDEZWTZYCP"
    assert issues_1[0].reason == ValidationReason.MISSING_IN_DB
    assert issues_1[0].details == "PaymentReferenceFile"

    validation_container_2 = result[1]
    errors_2 = validation_container_2.errors
    issues_2 = validation_container_2.validation_issues

    assert len(errors_2) == 0
    assert validation_container_2.record_key == "INTFDFMLLNILNPSWAVCB"
    assert issues_2[0].reason == ValidationReason.MISSING_IN_DB
    assert issues_2[0].details == "PaymentReferenceFile"


def test_process_outbound_status_return_invalid_path(
    test_db_session, mock_s3_bucket, initialize_factories_session
):
    ref_file = ReferenceFileFactory.create(file_location="not a valid path")

    with pytest.raises(Exception):
        process_outbound_status_return.process_outbound_status_return(test_db_session, ref_file)


def test_process_outbound_status_return_invalid_xml(
    test_db_session, mock_s3_bucket, initialize_factories_session
):
    full_path, test_file_path = get_paths(mock_s3_bucket, "leave_plan.csv")

    ref_file = ReferenceFileFactory.create(file_location=full_path)

    with pytest.raises(Exception):
        process_outbound_status_return.process_outbound_status_return(test_db_session, ref_file)

    test_db_session.refresh(ref_file)
    assert ref_file.file_location == "s3://test_bucket/ctr/inbound/error/leave_plan.csv"
