import logging  # noqa: B1
import os

import boto3
import defusedxml.ElementTree as ET
import pytest

import massgov.pfml.payments.outbound_returns.outbound_status_return as outbound_status_return
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    EmployeeReferenceFile,
    PaymentReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import (
    CtrDocumentIdentifierFactory,
    EmployeeReferenceFileFactory,
    PaymentReferenceFileFactory,
    ReferenceFileFactory,
)
from massgov.pfml.payments.payments_util import Constants, ValidationReason

# every test in here requires real resources
pytestmark = pytest.mark.integration

file_with_no_errors = "mock_status_return.dat"
file_with_errors = "mock_status_return_2.dat"


def get_paths(mock_s3_bucket, file_name, parent_dir="outbound_status_returns"):
    s3 = boto3.resource("s3")
    folder_name = "ctr/inbound/received"
    key = "{}/{}".format(folder_name, file_name)

    test_file_path = os.path.join(os.path.dirname(__file__), "test_files", parent_dir, file_name)
    full_path = "s3://{}/{}".format(mock_s3_bucket, key)

    s3.Object(mock_s3_bucket, key).put(Body=open(test_file_path, "rb"))
    return full_path, test_file_path


def model_reference_file_setup(test_db_session, initialize_factories_session):
    ctr_doc_id = "INTFDFMLGYLDEZWTZYCP"
    ctr_document_identifier = CtrDocumentIdentifierFactory.create(
        ctr_document_identifier=ctr_doc_id
    )
    pay_ref_1 = PaymentReferenceFileFactory.create(ctr_document_identifier=ctr_document_identifier)

    ctr_doc_id_2 = "INTFDFMLLNILNPSWAVCB"
    ctr_document_identifier_2 = CtrDocumentIdentifierFactory.create(
        ctr_document_identifier=ctr_doc_id_2
    )
    pay_ref_2 = PaymentReferenceFileFactory.create(
        ctr_document_identifier=ctr_document_identifier_2
    )

    ctr_doc_id_3 = "INTFDFML161220200012"
    ctr_document_identifier_3 = CtrDocumentIdentifierFactory.create(
        ctr_document_identifier=ctr_doc_id_3
    )
    emp_ref_1 = EmployeeReferenceFileFactory.create(
        ctr_document_identifier=ctr_document_identifier_3
    )

    return (pay_ref_1, pay_ref_2, emp_ref_1)


# === TESTS BEGIN ===


def test_get_validation_issues_no_issues():
    file_location = os.path.join(
        os.path.dirname(__file__), "test_files", "outbound_status_returns", file_with_no_errors
    )
    file = file_util.read_file(file_location)
    mock_xml_data = ET.fromstring(file)
    single_status_return_doc = mock_xml_data[0]

    status_return_doc_data = outbound_status_return.AmsDocData(single_status_return_doc)
    validation_container = status_return_doc_data.validation_container

    assert validation_container.record_key == "INTFDFMLGYLDEZWTZYCP"
    assert len(validation_container.validation_issues) == 0

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

    status_return_doc_data = outbound_status_return.AmsDocData(single_invalid_status_return_doc)
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
        issue.reason == ValidationReason.INVALID_VALUE and issue.details == "DOC_CD"
        for issue in validation_container.validation_issues
    )
    assert any(
        issue.reason == ValidationReason.INVALID_VALUE and issue.details == "TRAN_CD"
        for issue in validation_container.validation_issues
    )
    assert any(
        issue.reason == ValidationReason.MISSING_FIELD and issue.details == "UNIT_CD"
        for issue in validation_container.validation_issues
    )
    assert any(
        issue.reason == ValidationReason.MISSING_FIELD and issue.details == "DOC_UNIT_CD"
        for issue in validation_container.validation_issues
    )
    assert any(
        issue.reason == ValidationReason.MISSING_FIELD and issue.details == "DEPT_CD"
        for issue in validation_container.validation_issues
    )
    assert any(
        issue.reason == ValidationReason.MISSING_FIELD and issue.details == "DOC_DEPT_CD"
        for issue in validation_container.validation_issues
    )
    assert any(
        issue.reason == ValidationReason.MISSING_FIELD and issue.details == "DOC_PHASE_CD"
        for issue in validation_container.validation_issues
    )
    assert any(
        issue.reason == ValidationReason.INVALID_VALUE and issue.details == "DOC_PHASE_CD"
        for issue in validation_container.validation_issues
    )
    assert any(
        issue.reason == ValidationReason.MISSING_FIELD and issue.details == "ERRORS"
        for issue in validation_container.validation_issues
    )

    assert validation_container.record_key is None
    assert len(validation_container.validation_issues) == 10


def test_process_outbound_status_return_success(
    test_db_session, mock_s3_bucket, initialize_factories_session
):
    # Do setup
    full_path, test_file_path = get_paths(mock_s3_bucket, file_with_no_errors)
    pay_ref_1, pay_ref_2, emp_ref_1 = model_reference_file_setup(
        test_db_session, initialize_factories_session
    )
    ref_file = ReferenceFileFactory.create(
        file_location=full_path,
        reference_file_type_id=ReferenceFileType.OUTBOUND_STATUS_RETURN.reference_file_type_id,
    )

    # Run the process
    outbound_status_return.process_outbound_status_return(test_db_session, ref_file)

    # Toss anything that wasn't committed in the db transaction
    test_db_session.expire_all()

    # Verify all the state logs
    all_state_logs = test_db_session.query(StateLog).all()
    assert len(all_state_logs) == 3

    # Verify first payment's state log
    payment_1 = pay_ref_1.payment
    state_logs = test_db_session.query(StateLog).filter(StateLog.payment == payment_1).all()

    assert len(state_logs) == 1
    state_log_1 = state_logs[0]
    assert state_log_1.end_state_id == State.CONFIRM_PAYMENT.state_id
    assert state_log_1.payment_id == payment_1.payment_id
    assert state_log_1.outcome == {
        "message": f"Successfully processed Payment with DOC_ID {pay_ref_1.ctr_document_identifier.ctr_document_identifier} from Outbound Status Return"
    }

    # Verify second payment's state log
    payment_2 = pay_ref_2.payment
    state_logs = test_db_session.query(StateLog).filter(StateLog.payment == payment_2).all()

    assert len(state_logs) == 1
    state_log_2 = state_logs[0]
    assert state_log_2.end_state_id == State.CONFIRM_PAYMENT.state_id
    assert state_log_2.payment_id == payment_2.payment_id
    assert state_log_2.outcome == {
        "message": f"Successfully processed Payment with DOC_ID {pay_ref_2.ctr_document_identifier.ctr_document_identifier} from Outbound Status Return"
    }

    # Verify employee's state log
    employee_1 = emp_ref_1.employee
    state_logs = test_db_session.query(StateLog).filter(StateLog.employee == employee_1).all()

    assert len(state_logs) == 1
    state_log_3 = state_logs[0]
    assert state_log_3.end_state_id == State.VCC_SENT.state_id
    assert state_log_3.employee_id == employee_1.employee_id
    assert state_log_3.outcome == {
        "message": f"Successfully processed Employee with DOC_ID {emp_ref_1.ctr_document_identifier.ctr_document_identifier} from Outbound Status Return"
    }

    # Verify the Outbound Payment Return has the new file location
    assert ref_file.file_location == full_path.replace(
        Constants.S3_INBOUND_RECEIVED_DIR, Constants.S3_INBOUND_PROCESSED_DIR
    )

    # Verify the new PaymentReferenceFiles were created correctly
    new_pay_ref_1 = (
        test_db_session.query(PaymentReferenceFile)
        .filter(
            PaymentReferenceFile.payment == payment_1,
            PaymentReferenceFile.reference_file == ref_file,
        )
        .all()
    )
    assert len(new_pay_ref_1) == 1
    assert new_pay_ref_1[0].ctr_document_identifier == pay_ref_1.ctr_document_identifier

    new_pay_ref_2 = (
        test_db_session.query(PaymentReferenceFile)
        .filter(
            PaymentReferenceFile.payment == payment_2,
            PaymentReferenceFile.reference_file == ref_file,
        )
        .all()
    )
    assert len(new_pay_ref_2) == 1
    assert new_pay_ref_2[0].ctr_document_identifier == pay_ref_2.ctr_document_identifier

    new_emp_ref_1 = (
        test_db_session.query(EmployeeReferenceFile)
        .filter(
            EmployeeReferenceFile.employee == employee_1,
            EmployeeReferenceFile.reference_file == ref_file,
        )
        .all()
    )
    assert len(new_emp_ref_1) == 1
    assert new_emp_ref_1[0].ctr_document_identifier == emp_ref_1.ctr_document_identifier


def test_process_outbound_status_return_with_issues(
    test_db_session, mock_s3_bucket, initialize_factories_session, caplog
):
    # Do setup
    full_path, test_file_path = get_paths(mock_s3_bucket, file_with_errors)
    pay_ref_1, pay_ref_2, emp_ref_1 = model_reference_file_setup(
        test_db_session, initialize_factories_session
    )
    ref_file = ReferenceFileFactory.create(
        file_location=full_path,
        reference_file_type_id=ReferenceFileType.OUTBOUND_STATUS_RETURN.reference_file_type_id,
    )
    caplog.set_level(logging.ERROR)  # noqa: B1

    # Run the process
    outbound_status_return.process_outbound_status_return(test_db_session, ref_file)

    # Toss anything that wasn't committed in the db transaction
    test_db_session.expire_all()

    # Verify that the file is processed, even though all the records had errors
    assert (
        ref_file.file_location == "s3://test_bucket/ctr/inbound/processed/mock_status_return_2.dat"
    )

    # Verify state logs
    # TODO: clean up this test, very inflexible at the moment
    state_logs = test_db_session.query(StateLog).all()
    assert len(state_logs) == 3

    # TODO: The 4 cases should get PaymentReferenceFiles so we can
    # explicitly test these other cases
    assert len(caplog.records) == 6
    for i, record in enumerate(caplog.records):
        if i == 5:
            assert "AMS_DOCUMENT is missing DOC_ID value in file" in record.msg
        else:
            assert (
                "Failed to find a payment or employee for the specified CTR Document Identifier"
                in record.msg
            )

    for state_log in state_logs:
        assert state_log.outcome["message"] == "Validation issues found"

        if state_log.payment_id == pay_ref_1.payment.payment_id:
            validation_issues = state_log.outcome["validation_container"]["validation_issues"]
            assert len(validation_issues) == 1
            assert state_log.end_state_id == State.ADD_TO_GAX_ERROR_REPORT.state_id
            assert validation_issues[0]["details"] == "TRAN_CD"
            assert validation_issues[0]["reason"] == "InvalidValue"

        elif state_log.payment_id == pay_ref_2.payment.payment_id:
            validation_issues = state_log.outcome["validation_container"]["validation_issues"]
            assert len(validation_issues) == 2
            assert state_log.end_state_id == State.ADD_TO_GAX_ERROR_REPORT.state_id
            assert validation_issues[0]["details"] == "ERRORS"
            assert validation_issues[0]["reason"] == "OutboundStatusError"
            assert validation_issues[1]["details"] == "DOC_PHASE_CD"
            assert validation_issues[1]["reason"] == "InvalidValue"

        elif state_log.employee_id == emp_ref_1.employee.employee_id:
            validation_issues = state_log.outcome["validation_container"]["validation_issues"]
            assert len(validation_issues) == 1
            assert state_log.end_state_id == State.ADD_TO_VCC_ERROR_REPORT.state_id
            assert validation_issues[0]["details"] == "ERRORS"
            assert validation_issues[0]["reason"] == "OutboundStatusError"
        else:
            pytest.fail("Test data returned something unexpected")

    # for container in result:
    #     any(
    #         container.record_key == "'INTFDFMLGYLDEZWTZYCP"
    #         and issue.reason == ValidationReason.INVALID_VALUE
    #         and issue.details == "TRAN_CD and DOC_CD"
    #         for issue in container.validation_issues
    #     )
    #     any(
    #         container.record_key == "INTFDFMLLNILNPSWAVAB"
    #         and issue.reason == ValidationReason.INVALID_VALUE
    #         and issue.details == "UNIT_CD"
    #         for issue in container.validation_issues
    #     )
    #     any(
    #         container.record_key == "INTFDFMLLNILNPSWAVCD"
    #         and issue.reason == ValidationReason.MISSING_FIELD
    #         and issue.details == "UNIT_CD"
    #         for issue in container.validation_issues
    #     )
    #     any(
    #         container.record_key == "INTFDFMLLNILNPSWAVEF"
    #         and issue.reason == ValidationReason.INVALID_VALUE
    #         and issue.details == "DEPT_CD"
    #         for issue in container.validation_issues
    #     )
    #     any(
    #         container.record_key == "INTFDFMLLNILNPSWAVGH"
    #         and issue.reason == ValidationReason.INVALID_VALUE
    #         and issue.details == "TRAN_CD"
    #         for issue in container.validation_issues
    #     )
    #     any(
    #         container.record_key == "INTFDFMLLNILNPSWAVIJ"
    #         and issue.reason == ValidationReason.MISSING_FIELD
    #         and issue.details == "TRAN_CD"
    #         for issue in container.validation_issues
    #     )
    #     any(
    #         container.record_key == "None"
    #         and issue.reason == ValidationReason.MISSING_FIELD
    #         and issue.details == "DOC_ID"
    #         for issue in container.validation_issues
    #     )


def test_process_outbound_status_return_no_pay_ref(
    test_db_session, mock_s3_bucket, initialize_factories_session, caplog
):
    # Do setup
    full_path, test_file_path = get_paths(mock_s3_bucket, file_with_no_errors)
    ref_file = ReferenceFileFactory.create(
        file_location=full_path,
        reference_file_type_id=ReferenceFileType.OUTBOUND_STATUS_RETURN.reference_file_type_id,
    )
    caplog.set_level(logging.ERROR)  # noqa: B1

    # Run the process
    outbound_status_return.process_outbound_status_return(test_db_session, ref_file)

    # Toss anything that wasn't committed in the db transaction
    test_db_session.expire_all()

    # Verify that the file processed, even if the contents failed
    assert ref_file.file_location == "s3://test_bucket/ctr/inbound/processed/mock_status_return.dat"

    # Verify the exceptions are logged
    doc_ids = ["INTFDFMLGYLDEZWTZYCP", "INTFDFMLLNILNPSWAVCB", "INTFDFML161220200012"]
    for i, log_record in enumerate(caplog.records):
        assert (
            f"Failed to find a payment or employee for the specified CTR Document Identifier {doc_ids[i]}"
            in log_record.msg % log_record.args
        )


def test_process_outbound_status_return_invalid_path(
    test_db_session, mock_s3_bucket, initialize_factories_session
):
    ref_file = ReferenceFileFactory.create(
        file_location="s3://nowhere/nothing",
        reference_file_type_id=ReferenceFileType.OUTBOUND_PAYMENT_RETURN.reference_file_type_id,
    )

    with pytest.raises(Exception):
        outbound_status_return.process_outbound_status_return(test_db_session, ref_file)


def test_process_outbound_status_return_invalid_xml(
    test_db_session, mock_s3_bucket, initialize_factories_session
):
    full_path, _ = get_paths(
        mock_s3_bucket, "test_unparseable.xml", parent_dir=os.path.join("outbound_returns"),
    )

    ref_file = ReferenceFileFactory.create(
        file_location=full_path,
        reference_file_type_id=ReferenceFileType.OUTBOUND_STATUS_RETURN.reference_file_type_id,
    )

    with pytest.raises(Exception):
        outbound_status_return.process_outbound_status_return(test_db_session, ref_file)

    test_db_session.expire_all()
    assert ref_file.file_location == "s3://test_bucket/ctr/inbound/error/test_unparseable.xml"
