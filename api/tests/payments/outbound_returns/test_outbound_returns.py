import logging  # noqa: B1
import os
import pathlib

import pytest

import massgov.pfml.payments.outbound_returns as outbound_returns
from massgov.pfml.db.models.employees import ReferenceFileType
from massgov.pfml.db.models.factories import ReferenceFileFactory
from massgov.pfml.payments.outbound_returns import (
    outbound_payment_return,
    outbound_status_return,
    outbound_vendor_customer_return,
)
from massgov.pfml.payments.payments_util import Constants
from tests.api.payments.conftest import upload_file_to_s3

# TEST_FILES_FOLDER = os.path.join(pathlib.Path(__file__).parent, "test_files")
TEST_FILES_FOLDER = os.path.join(pathlib.Path(__file__).parent, "test_files", "outbound_returns")


def setup_test_files(mock_s3_bucket, initialize_factories_session, with_ref_file=True):
    test_files = os.listdir(TEST_FILES_FOLDER)
    assert len(test_files) == 5

    file_pairs = []
    for test_file_name in test_files:

        local_file_path = os.path.join(TEST_FILES_FOLDER, test_file_name)
        key = os.path.join(Constants.S3_INBOUND_RECEIVED_DIR, test_file_name)
        upload_file_to_s3(local_file_path, mock_s3_bucket, key)

        if with_ref_file:
            s3_file_location = os.path.join("s3://", mock_s3_bucket, key)
            ref_file = ReferenceFileFactory.create(file_location=s3_file_location)
            file_pairs.append({"test_file_name": s3_file_location, "ref_file": ref_file})

    return file_pairs


def populate_outbound_return_data(test_db_session, mock_s3_bucket, initialize_factories_session):
    file_pairs = setup_test_files(mock_s3_bucket, initialize_factories_session)
    outbound_return_data = outbound_returns.OutboundReturnData(test_db_session)
    for item in file_pairs:
        ref_file = item["ref_file"]

        # Call the function
        outbound_returns._set_outbound_reference_file_type(
            test_db_session, ref_file, outbound_return_data
        )

    return outbound_return_data


def setup_mocks(mocker):
    mocked_process_outbound_status_return = mocker.patch.object(
        outbound_status_return, "process_outbound_status_return", return_value=None
    )
    mocked_process_outbound_vendor_customer_return = mocker.patch.object(
        outbound_vendor_customer_return,
        "process_outbound_vendor_customer_return",
        return_value=None,
    )
    mocked_process_outbound_payment_return = mocker.patch.object(
        outbound_payment_return, "process_outbound_payment_return", return_value=None
    )
    return (
        mocked_process_outbound_status_return,
        mocked_process_outbound_vendor_customer_return,
        mocked_process_outbound_payment_return,
    )


# === TESTS BEGIN ===


def test_identify_outbound_return(initialize_factories_session, mock_s3_bucket):
    file_pairs = setup_test_files(mock_s3_bucket, initialize_factories_session)

    for item in file_pairs:
        test_file_name = item["test_file_name"]
        ref_file = item["ref_file"]

        # Verify errors
        if "_unparseable" in test_file_name:
            with pytest.raises(Exception):
                outbound_returns._identify_outbound_return(ref_file)
        elif "_wrong_file_type" in test_file_name:
            with pytest.raises(ValueError):
                outbound_returns._identify_outbound_return(ref_file)
        else:
            file_type = outbound_returns._identify_outbound_return(ref_file)

        # Verify success
        if "_opr" in test_file_name:
            assert file_type is ReferenceFileType.OUTBOUND_PAYMENT_RETURN
        elif "_ovr" in test_file_name:
            assert file_type is ReferenceFileType.OUTBOUND_VENDOR_CUSTOMER_RETURN
        elif "_osr" in test_file_name:
            assert file_type is ReferenceFileType.OUTBOUND_STATUS_RETURN


def test_set_outbound_reference_file_type(
    test_db_session, initialize_factories_session, caplog, mock_s3_bucket
):
    caplog.set_level(logging.WARNING)  # noqa: B1
    outbound_return_data = populate_outbound_return_data(
        test_db_session, mock_s3_bucket, initialize_factories_session
    )

    # Verify successfully identified 3 outbound returns
    assert len(outbound_return_data.outbound_status_return_files) == 1
    assert len(outbound_return_data.outbound_vendor_customer_return_files) == 1
    assert len(outbound_return_data.outbound_payment_return_files) == 1

    # Verify ReferenceFileType
    assert (
        outbound_return_data.outbound_status_return_files[
            0
        ].reference_file_type.reference_file_type_id
        == ReferenceFileType.OUTBOUND_STATUS_RETURN.reference_file_type_id
    )
    assert (
        outbound_return_data.outbound_vendor_customer_return_files[
            0
        ].reference_file_type.reference_file_type_id
        == ReferenceFileType.OUTBOUND_VENDOR_CUSTOMER_RETURN.reference_file_type_id
    )
    assert (
        outbound_return_data.outbound_payment_return_files[
            0
        ].reference_file_type.reference_file_type_id
        == ReferenceFileType.OUTBOUND_PAYMENT_RETURN.reference_file_type_id
    )

    # Verify 2 errors were captured in logs
    assert len(caplog.records) == 2
    for record in caplog.records:
        assert "Unexpected file type" in record.msg


def test_internal_process_outbound_returns(
    test_db_session, mock_s3_bucket, initialize_factories_session, mocker
):
    outbound_return_data = populate_outbound_return_data(
        test_db_session, mock_s3_bucket, initialize_factories_session
    )
    (
        mocked_process_outbound_status_return,
        mocked_process_outbound_vendor_customer_return,
        mocked_process_outbound_payment_return,
    ) = setup_mocks(mocker)

    outbound_returns._process_outbound_returns(outbound_return_data)

    # Assert functions were called once each
    assert mocked_process_outbound_payment_return.call_count == 1
    assert mocked_process_outbound_vendor_customer_return.call_count == 1
    assert mocked_process_outbound_payment_return.call_count == 1


def test_internal_process_outbound_returns_status_error(
    test_db_session, mock_s3_bucket, initialize_factories_session, mocker
):
    outbound_return_data = populate_outbound_return_data(
        test_db_session, mock_s3_bucket, initialize_factories_session
    )
    (
        mocked_process_outbound_status_return,
        mocked_process_outbound_vendor_customer_return,
        mocked_process_outbound_payment_return,
    ) = setup_mocks(mocker)

    # Mock an error
    mocked_process_outbound_status_return = mocker.patch.object(
        outbound_status_return, "process_outbound_status_return", side_effect=Exception()
    )

    # An error should be raised
    with pytest.raises(Exception):
        outbound_returns._process_outbound_returns(outbound_return_data)

    # All functions should have been called
    assert mocked_process_outbound_status_return.call_count == 1
    assert mocked_process_outbound_vendor_customer_return.call_count == 0
    assert mocked_process_outbound_payment_return.call_count == 0


def test_internal_process_outbound_returns_vendor_error(
    test_db_session, mock_s3_bucket, initialize_factories_session, mocker
):
    outbound_return_data = populate_outbound_return_data(
        test_db_session, mock_s3_bucket, initialize_factories_session
    )
    (
        mocked_process_outbound_status_return,
        mocked_process_outbound_vendor_customer_return,
        mocked_process_outbound_payment_return,
    ) = setup_mocks(mocker)

    # Now, mock the outbound vendor process having an error
    mocked_process_outbound_vendor_customer_return = mocker.patch.object(
        outbound_vendor_customer_return,
        "process_outbound_vendor_customer_return",
        side_effect=Exception(),
    )

    # An error should be raised
    with pytest.raises(Exception):
        outbound_returns._process_outbound_returns(outbound_return_data)

    # First two functions should have been called
    assert mocked_process_outbound_status_return.call_count == 1
    assert mocked_process_outbound_vendor_customer_return.call_count == 1
    assert mocked_process_outbound_payment_return.call_count == 0

    mocked_process_outbound_status_return = mocker.patch.object(
        outbound_status_return, "process_outbound_status_return", side_effect=Exception()
    )


def test_internal_process_outbound_returns_payment_error(
    test_db_session, mock_s3_bucket, initialize_factories_session, mocker
):
    outbound_return_data = populate_outbound_return_data(
        test_db_session, mock_s3_bucket, initialize_factories_session
    )
    (
        mocked_process_outbound_status_return,
        mocked_process_outbound_vendor_customer_return,
        mocked_process_outbound_payment_return,
    ) = setup_mocks(mocker)

    # Mock the outbound payment process having an error
    mocked_process_outbound_payment_return = mocker.patch.object(
        outbound_payment_return, "process_outbound_payment_return", side_effect=Exception()
    )

    # An error should be raised
    with pytest.raises(Exception):
        outbound_returns._process_outbound_returns(outbound_return_data)

    # All functions should have been called
    assert mocked_process_outbound_status_return.call_count == 1
    assert mocked_process_outbound_vendor_customer_return.call_count == 1
    assert mocked_process_outbound_payment_return.call_count == 1


def test_process_outbound_returns(
    test_db_session,
    mock_s3_bucket,
    initialize_factories_session,
    mocker,
    set_exporter_env_vars,
    caplog,
):
    setup_test_files(mock_s3_bucket, initialize_factories_session)
    (
        mocked_process_outbound_status_return,
        mocked_process_outbound_vendor_customer_return,
        mocked_process_outbound_payment_return,
    ) = setup_mocks(mocker)
    caplog.set_level(logging.WARNING)  # noqa: B1

    outbound_returns.process_outbound_returns(test_db_session)

    # All functions should have been called
    assert mocked_process_outbound_status_return.call_count == 1
    assert mocked_process_outbound_vendor_customer_return.call_count == 1
    assert mocked_process_outbound_payment_return.call_count == 1

    assert len(caplog.records) == 2


def test_process_outbound_returns_no_ref_file(
    test_db_session,
    mock_s3_bucket,
    initialize_factories_session,
    mocker,
    set_exporter_env_vars,
    caplog,
):
    setup_test_files(mock_s3_bucket, initialize_factories_session, with_ref_file=False)
    (
        mocked_process_outbound_status_return,
        mocked_process_outbound_vendor_customer_return,
        mocked_process_outbound_payment_return,
    ) = setup_mocks(mocker)
    caplog.set_level(logging.WARNING)  # noqa: B1

    outbound_returns.process_outbound_returns(test_db_session)

    # All functions should have been called
    assert mocked_process_outbound_status_return.call_count == 0
    assert mocked_process_outbound_vendor_customer_return.call_count == 0
    assert mocked_process_outbound_payment_return.call_count == 0

    assert len(caplog.records) == 5
