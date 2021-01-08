import logging  # noqa: B1
import os
import pathlib

import pytest

from massgov.pfml.db.models.employees import ReferenceFileType
from massgov.pfml.db.models.factories import ReferenceFileFactory
from massgov.pfml.payments.ctr_outbound_return import (
    process_ctr_outbound_returns,
    read_and_inspect_file,
)

TEST_FOLDER = pathlib.Path(__file__).parent

TEST_FILES_FOLDER = os.path.join(TEST_FOLDER, "test_files", "outbound_returns")


@pytest.fixture
def ctr_folder_mock(monkeypatch):
    env_test_dir = monkeypatch.setenv("PFML_CTR_INBOUND_PATH", TEST_FILES_FOLDER)
    return env_test_dir


def create_mock_stubs(monkeypatch):
    function_call_order = []

    def mock_stub_outbound_status_return(db_session, reference_file):
        mock_stub_outbound_status_return.times_called = (
            mock_stub_outbound_status_return.times_called + 1
        )
        assert (
            reference_file.reference_file_type.reference_file_type_description
            == ReferenceFileType.OUTBOUND_STATUS_RETURN.reference_file_type_description
        )
        function_call_order.append("mock_stub_outbound_status_return")

    mock_stub_outbound_status_return.times_called = 0
    monkeypatch.setattr(
        "massgov.pfml.payments.ctr_outbound_return.process_outbound_status_return",
        mock_stub_outbound_status_return,
    )

    def mock_stub_process_outbound_vendor_customer_return(reference_file, db_session):
        mock_stub_process_outbound_vendor_customer_return.times_called = (
            mock_stub_process_outbound_vendor_customer_return.times_called + 1
        )
        assert (
            reference_file.reference_file_type.reference_file_type_description
            == ReferenceFileType.OUTBOUND_VENDOR_CUSTOMER_RETURN.reference_file_type_description
        )
        function_call_order.append("mock_stub_process_outbound_vendor_customer_return")

    mock_stub_process_outbound_vendor_customer_return.times_called = 0
    monkeypatch.setattr(
        "massgov.pfml.payments.ctr_outbound_return.process_outbound_vendor_customer_return",
        mock_stub_process_outbound_vendor_customer_return,
    )

    def mock_stub_process_outbound_payment_return(db_session, reference_file):
        mock_stub_process_outbound_payment_return.times_called = (
            mock_stub_process_outbound_payment_return.times_called + 1
        )
        assert (
            reference_file.reference_file_type.reference_file_type_description
            == ReferenceFileType.OUTBOUND_PAYMENT_RETURN.reference_file_type_description
        )
        function_call_order.append("mock_stub_process_outbound_payment_return")

    mock_stub_process_outbound_payment_return.times_called = 0
    monkeypatch.setattr(
        "massgov.pfml.payments.ctr_outbound_return.process_outbound_payment_return",
        mock_stub_process_outbound_payment_return,
    )

    def mock_handle_unknown_type(source_filepath, reference_file):
        # the real version of this function moves files, but we don't actually want to move the test files
        mock_handle_unknown_type.times_called = mock_handle_unknown_type.times_called + 1
        assert source_filepath in [
            os.path.join(TEST_FILES_FOLDER, "received", "test_unparseable.xml"),
            os.path.join(TEST_FILES_FOLDER, "received", "test_wrong_file_type.xml"),
        ]

    mock_handle_unknown_type.times_called = 0

    monkeypatch.setattr(
        "massgov.pfml.payments.ctr_outbound_return.handle_unknown_type", mock_handle_unknown_type,
    )

    return (
        mock_stub_outbound_status_return,
        mock_stub_process_outbound_vendor_customer_return,
        mock_stub_process_outbound_payment_return,
        function_call_order,
        mock_handle_unknown_type,
    )


def test_read_and_inspect_file(caplog):
    test_files = os.listdir(os.path.join(TEST_FILES_FOLDER, "received"))
    caplog.set_level(logging.ERROR)  # noqa: B1

    assert len(test_files) == 5
    for test_file_name in test_files:
        file_type = read_and_inspect_file(
            os.path.join(TEST_FILES_FOLDER, "received", test_file_name)
        )
        if "_opr" in test_file_name:
            assert file_type is ReferenceFileType.OUTBOUND_PAYMENT_RETURN
        elif "_ovr" in test_file_name:
            assert file_type is ReferenceFileType.OUTBOUND_VENDOR_CUSTOMER_RETURN
        elif "_osr" in test_file_name:
            assert file_type is ReferenceFileType.OUTBOUND_STATUS_RETURN
        elif "_wrong_filetype" in test_file_name:
            assert file_type is None
        elif "_unparseable" in test_file_name:
            assert (
                "Unable to parse file as xml: /app/tests/api/payments/test_files/outbound_returns/received/test_unparseable.xml"
                in caplog.text
            )


def test_process_ctr_outbound_returns(
    test_db_session, initialize_factories_session, monkeypatch, ctr_folder_mock, caplog
):
    test_files = os.listdir(os.path.join(TEST_FILES_FOLDER, "received"))
    # set up mocks
    (
        mock_stub_outbound_status_return,
        mock_stub_process_outbound_vendor_customer_return,
        mock_stub_process_outbound_payment_return,
        function_call_order,
        mock_handle_unknown_type,
    ) = create_mock_stubs(monkeypatch)

    # Create ReferenceFiles
    for test_file_name in test_files:
        reference_file = ReferenceFileFactory.create()
        reference_file.file_location = os.path.join(
            os.path.join(TEST_FILES_FOLDER, "received", test_file_name)
        )
        test_db_session.add(reference_file)
    test_db_session.commit()

    caplog.set_level(logging.ERROR)  # noqa: B1
    process_ctr_outbound_returns(test_db_session)

    # check function calls
    assert mock_stub_outbound_status_return.times_called == 1
    assert mock_stub_process_outbound_vendor_customer_return.times_called == 1
    assert mock_stub_process_outbound_payment_return.times_called == 1

    # check function call order
    assert function_call_order[0] == "mock_stub_outbound_status_return"
    assert function_call_order[1] == "mock_stub_process_outbound_vendor_customer_return"
    assert function_call_order[2] == "mock_stub_process_outbound_payment_return"

    # check that files with parsing issue or invalid file type is handled
    assert mock_handle_unknown_type.times_called == 2

    # parsing error was raised:
    assert (
        "Unable to parse file as xml: /app/tests/api/payments/test_files/outbound_returns/received/test_unparseable.xml"
        in caplog.text
    )
