import logging  # noqa: B1
import os

import boto3
import defusedxml.ElementTree as ET
import pytest

import massgov.pfml.payments.outbound_returns.outbound_payment_return as outbound_payment_return
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    PaymentReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import (
    CtrDocumentIdentifierFactory,
    PaymentReferenceFileFactory,
    ReferenceFileFactory,
)
from massgov.pfml.payments.payments_util import Constants, ValidationReason

# every test in here requires real resources
pytestmark = pytest.mark.integration

file_with_no_errors = "mock_payment_return.dat"
file_with_errors = "mock_payment_return_2.dat"


def get_paths(mock_s3_bucket, file_name, parent_dir="outbound_payment_returns"):
    s3 = boto3.resource("s3")
    folder_name = "ctr/inbound/received"
    key = "{}/{}".format(folder_name, file_name)

    test_file_path = os.path.join(os.path.dirname(__file__), "test_files", parent_dir, file_name)
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


# === TESTS BEGIN ===


def test_get_validation_issues_no_issues():
    file_location = os.path.join(
        os.path.dirname(__file__), "test_files", "outbound_payment_returns", file_with_no_errors
    )
    file = file_util.read_file(file_location)
    mock_xml_data = ET.fromstring(file)
    single_payment_return_doc = mock_xml_data[0]

    payment_return_doc_data = outbound_payment_return.PaymentReturnDocData(
        single_payment_return_doc
    )
    validation_container = payment_return_doc_data.validation_container

    assert validation_container.record_key == "INTFDFMLN50LINES0001"
    assert len(validation_container.validation_issues) == 0

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

    payment_return_doc_data = outbound_payment_return.PaymentReturnDocData(
        single_invalid_payment_return_doc
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


# TODO: parameterize
def test_process_outbound_payment_return_success(
    test_db_session, mock_s3_bucket, initialize_factories_session
):
    # Do setup
    full_path, test_file_path = get_paths(mock_s3_bucket, file_with_no_errors)
    pay_ref_1, pay_ref_2 = payment_reference_file_setup(
        test_db_session, initialize_factories_session
    )

    ref_file = ReferenceFileFactory.create(
        file_location=full_path,
        reference_file_type_id=ReferenceFileType.OUTBOUND_PAYMENT_RETURN.reference_file_type_id,
    )

    # Run the process
    outbound_payment_return.process_outbound_payment_return(test_db_session, ref_file)

    # Toss anything that wasn't committed in the db transaction
    test_db_session.expire_all()

    # Verify all the state logs
    all_state_logs = test_db_session.query(StateLog).all()
    assert len(all_state_logs) == 2

    # Verify first payment's state log
    payment_1 = pay_ref_1.payment
    state_logs = test_db_session.query(StateLog).filter(StateLog.payment == payment_1).all()

    assert len(state_logs) == 1
    state_log_1 = state_logs[0]
    assert state_log_1.end_state_id == State.SEND_PAYMENT_DETAILS_TO_FINEOS.state_id
    assert state_log_1.payment_id == payment_1.payment_id
    assert state_log_1.outcome == {
        "message": f"Successfully processed payment with PY_ID {pay_ref_1.ctr_document_identifier.ctr_document_identifier} from Outbound Payment Return"
    }

    # Verify second payment's state log
    payment_2 = pay_ref_2.payment
    state_logs = test_db_session.query(StateLog).filter(StateLog.payment == payment_2).all()

    assert len(state_logs) == 1
    state_log_2 = state_logs[0]
    assert state_log_2.end_state_id == State.SEND_PAYMENT_DETAILS_TO_FINEOS.state_id
    assert state_log_2.payment_id == payment_2.payment_id
    assert state_log_2.outcome == {
        "message": f"Successfully processed payment with PY_ID {pay_ref_2.ctr_document_identifier.ctr_document_identifier} from Outbound Payment Return"
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


def test_payment_obj_updates(test_db_session, mock_s3_bucket, initialize_factories_session):
    full_path, test_file_path = get_paths(mock_s3_bucket, file_with_no_errors)
    pay_ref_1, pay_ref_2 = payment_reference_file_setup(
        test_db_session, initialize_factories_session
    )

    payment_1 = pay_ref_1.payment
    payment_2 = pay_ref_2.payment

    ref_file = ReferenceFileFactory.create(
        file_location=full_path,
        reference_file_type_id=ReferenceFileType.OUTBOUND_PAYMENT_RETURN.reference_file_type_id,
    )
    outbound_payment_return.process_outbound_payment_return(test_db_session, ref_file)
    test_db_session.expire_all()

    # test that after outbound payment return has been processed, payment object is updated
    # with values from the xml file
    assert str(payment_1.disb_amount) == "50.00"
    assert str(payment_1.disb_check_eft_issue_date) == "2020-12-17"
    assert payment_1.disb_check_eft_number == "00002493873"
    assert payment_1.disb_method.payment_method_description == "Check"

    assert str(payment_2.disb_amount) == "75.00"
    assert str(payment_2.disb_check_eft_issue_date) == "2020-12-17"
    assert payment_2.disb_check_eft_number == "0000249123A"
    assert payment_2.disb_method.payment_method_description == "Elec Funds Transfer"


def test_process_outbound_payment_return_with_issues(
    test_db_session, mock_s3_bucket, initialize_factories_session, caplog
):
    # Do setup
    full_path, test_file_path = get_paths(mock_s3_bucket, file_with_errors)
    pay_ref_1, pay_ref_2 = payment_reference_file_setup(
        test_db_session, initialize_factories_session
    )

    ref_file = ReferenceFileFactory.create(
        file_location=full_path,
        reference_file_type_id=ReferenceFileType.OUTBOUND_PAYMENT_RETURN.reference_file_type_id,
    )
    caplog.set_level(logging.ERROR)  # noqa: B1

    # Run the process
    outbound_payment_return.process_outbound_payment_return(test_db_session, ref_file)

    # Toss anything that wasn't committed in the db transaction
    test_db_session.expire_all()

    # Verify that the file is processed, even though all the records had errors
    assert (
        ref_file.file_location == "s3://test_bucket/ctr/inbound/processed/mock_payment_return_2.dat"
    )

    # 4 entries are missing PaymentReferenceFile records and will be captured
    # by logger.exception()
    # 1 entry is missing a PY_ID and has a different exception message
    # TODO: The 4 cases should get PaymentReferenceFiles so we can
    # explicitly test these other cases
    assert len(caplog.records) == 5
    for i, record in enumerate(caplog.records):
        if i == 4:
            assert "PYMT_RETN_DOC is missing PY_ID value in file" in record.msg
        else:
            assert (
                "Failed to find a payment for the specified CTR Document Identifier" in record.msg
            )

    state_logs = test_db_session.query(StateLog).all()
    assert len(state_logs) == 2

    for state_log in state_logs:
        assert state_log.end_state_id == State.ADD_TO_GAX_ERROR_REPORT.state_id
        assert state_log.outcome["message"] == "Validation issues found"

        validation_issues = state_log.outcome["validation_container"]["validation_issues"]
        assert len(validation_issues) == 1
        assert validation_issues[0]["reason"] == "InvalidValue"

        if state_log.payment_id == pay_ref_1.payment.payment_id:
            assert validation_issues[0]["details"] == "PY_CD"
        elif state_log.payment_id == pay_ref_2.payment.payment_id:
            assert validation_issues[0]["details"] == "PY_DEPT"
        else:
            pytest.fail(f"Test data returned payment id {state_log.payment_id}")


def test_process_outbound_payment_return_no_pay_ref(
    test_db_session, mock_s3_bucket, initialize_factories_session, caplog
):
    # Do setup
    full_path, test_file_path = get_paths(mock_s3_bucket, file_with_no_errors)

    ref_file = ReferenceFileFactory.create(
        file_location=full_path,
        reference_file_type_id=ReferenceFileType.OUTBOUND_PAYMENT_RETURN.reference_file_type_id,
    )
    caplog.set_level(logging.ERROR)  # noqa: B1

    # Run the process
    outbound_payment_return.process_outbound_payment_return(test_db_session, ref_file)

    # Toss anything that wasn't committed in the db transaction
    test_db_session.expire_all()

    # Verify that the file processed, even if the contents failed
    assert (
        ref_file.file_location == "s3://test_bucket/ctr/inbound/processed/mock_payment_return.dat"
    )

    # Verify the exceptions are logged
    doc_ids = ["INTFDFMLN50LINES0001", "INTFDFMLGYLDEZWTZYCP"]
    for i, log_record in enumerate(caplog.records):
        assert (
            f"Failed to find a payment for the specified CTR Document Identifier {doc_ids[i]}"
            in log_record.msg % log_record.args
        )


def test_process_outbound_payment_return_invalid_path(
    test_db_session, mock_s3_bucket, initialize_factories_session
):
    ref_file = ReferenceFileFactory.create(
        file_location="s3://nowhere/nothing",
        reference_file_type_id=ReferenceFileType.OUTBOUND_PAYMENT_RETURN.reference_file_type_id,
    )

    with pytest.raises(Exception):
        outbound_payment_return.process_outbound_payment_return(test_db_session, ref_file)


def test_process_outbound_payment_return_invalid_xml(
    test_db_session, mock_s3_bucket, initialize_factories_session
):
    full_path, _ = get_paths(
        mock_s3_bucket, "test_unparseable.xml", parent_dir=os.path.join("outbound_returns"),
    )

    ref_file = ReferenceFileFactory.create(
        file_location=full_path,
        reference_file_type_id=ReferenceFileType.OUTBOUND_PAYMENT_RETURN.reference_file_type_id,
    )

    with pytest.raises(Exception):
        outbound_payment_return.process_outbound_payment_return(test_db_session, ref_file)

    test_db_session.expire_all()
    assert ref_file.file_location == "s3://test_bucket/ctr/inbound/error/test_unparseable.xml"
