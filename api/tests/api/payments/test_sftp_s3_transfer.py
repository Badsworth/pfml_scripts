import os

import boto3
import pytest

import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import ReferenceFile, ReferenceFileType
from massgov.pfml.db.models.factories import ReferenceFileFactory
from massgov.pfml.payments.sftp_s3_transfer import (
    SftpS3TransferConfig,
    copy_from_sftp_to_s3_and_archive_files,
    copy_to_sftp_and_archive_s3_files,
)


def test_copy_to_sftp_and_archive_s3_files_success(
    mock_s3_bucket,
    setup_mock_sftp_client,
    mock_sftp_client,
    test_db_session,
    initialize_factories_session,
):
    archive_dir = "archive/testing"
    source_dir = "api/outbox"

    test_filenames = [
        "first_file.txt",
        "second_file.txt",
        "third_file.txt",
        "fourth_file.txt",
    ]

    s3 = boto3.client("s3")
    for filename in test_filenames:
        # Stock our mocked S3 bucket with the files.
        key = os.path.join(source_dir, filename)
        s3.put_object(Bucket=mock_s3_bucket, Key=key, Body="test\n")

        # Add ReferenceFile objects to the database for these files.
        file_location = "s3://" + os.path.join(mock_s3_bucket, key)
        reference_file = ReferenceFileFactory(
            file_location=file_location,
            reference_file_type_id=ReferenceFileType.OUTBOUND_STATUS_RETURN.reference_file_type_id,
        )
        test_db_session.add(reference_file)

        # Expect to find no ReferenceFiles with the archived file_location
        archived_file_location = "s3://" + os.path.join(mock_s3_bucket, archive_dir, filename)
        assert _first_ref_file(archived_file_location, test_db_session) is None

    test_db_session.commit()

    config = SftpS3TransferConfig(
        s3_bucket_uri="s3://" + mock_s3_bucket,
        source_dir=source_dir,
        archive_dir=archive_dir,
        # Following fields do not matter when mocking SFTP server. Included for completeness.
        dest_dir="inbound/from_api",
        sftp_uri="sftp://api_user@mass.gov",
        ssh_key_password="No ssh_key_password used during mocked tests",
        ssh_key="No ssh_key used during mocked tests",
    )
    copy_to_sftp_and_archive_s3_files(config=config, db_session=test_db_session)

    # Collect the files in the source and dest directories after the function ran.
    files_in_source_dir = file_util.list_files(
        path="s3://" + os.path.join(mock_s3_bucket, source_dir)
    )
    files_in_archive_dir = file_util.list_files(
        path="s3://" + os.path.join(mock_s3_bucket, archive_dir)
    )

    # Expect that the ReferenceFiles associated with the files in S3 updated their file_locations.
    for filename in test_filenames:
        # Expect to find no ReferenceFiles with the source file_location
        source_file_location = "s3://" + os.path.join(mock_s3_bucket, source_dir, filename)
        assert _first_ref_file(source_file_location, test_db_session) is None

        # Expect to find a single ReferenceFile with the archived file_location
        archived_file_location = "s3://" + os.path.join(mock_s3_bucket, archive_dir, filename)
        assert _first_ref_file(archived_file_location, test_db_session) is not None

        # Expect to find file in S3 archive dir
        assert filename in files_in_archive_dir

        # Expect to find no file with this filename in the source dir.
        assert filename not in files_in_source_dir

    # List contents of destination directory, then copy each of the 4 files in S3 to SFTP server.
    expected_sftp_calls = ["listdir"] + ["put"] * len(test_filenames)
    assert len(mock_sftp_client.calls) == len(expected_sftp_calls)
    for i, call in enumerate(mock_sftp_client.calls):
        assert call[0] == expected_sftp_calls[i]


def test_multi_file_set_copy_to_sftp_and_archive_s3_files_success(
    mock_s3_bucket,
    setup_mock_sftp_client,
    mock_sftp_client,
    test_db_session,
    initialize_factories_session,
):
    archive_dir = "archive/testing"
    source_dir = "api/outbox"

    test_vcc_files_by_level = {
        "DFML_CLAIMANTS_FOR_DUA_20201122.csv": ["DFML_CLAIMANTS_FOR_DUA_20201122.csv"],
        "EOL20201123VCC13": [
            "EOL20201123VCC13/EOL20201123VCC13.DAT",
            "EOL20201123VCC13/EOL20201123VCC13.INF",
        ],
        "EOL20201124VCC11": [
            "EOL20201124VCC11/EOL20201124VCC11.DAT",
            "EOL20201124VCC11/EOL20201124VCC11.INF",
        ],
        "EOL20201125VCC11": [
            "EOL20201125VCC11/EOL20201125VCC11.DAT",
            "EOL20201125VCC11/EOL20201125VCC11.INF",
        ],
    }

    s3 = boto3.client("s3")
    total_file_count = 0
    for file_location, files_in_set in test_vcc_files_by_level.items():
        total_file_count = total_file_count + len(files_in_set)
        for setfile in files_in_set:
            # Stock our mocked S3 bucket with the files.
            key = os.path.join(source_dir, setfile)
            s3.put_object(Bucket=mock_s3_bucket, Key=key, Body="test\n")

        # For this test we're using 2 files as the signal that the type is VCC.
        reference_file_type_id = ReferenceFileType.DUA_CLAIMANT_LIST.reference_file_type_id
        if len(files_in_set) == 2:
            reference_file_type_id = ReferenceFileType.VCC.reference_file_type_id

        # Add ReferenceFile objects to the database for these files.
        reference_file = ReferenceFileFactory(
            file_location="s3://" + os.path.join(mock_s3_bucket, source_dir, file_location),
            reference_file_type_id=reference_file_type_id,
        )
        test_db_session.add(reference_file)

        # Expect to find no ReferenceFiles with the archived file_location
        archived_file_location = "s3://" + os.path.join(mock_s3_bucket, archive_dir, file_location)
        assert _first_ref_file(archived_file_location, test_db_session) is None

    test_db_session.commit()

    config = SftpS3TransferConfig(
        s3_bucket_uri="s3://" + mock_s3_bucket,
        source_dir=source_dir,
        archive_dir=archive_dir,
        # Following fields do not matter when mocking SFTP server. Included for completeness.
        dest_dir="inbound/from_api",
        sftp_uri="sftp://api_user@mass.gov",
        ssh_key_password="No ssh_key_password used during mocked tests",
        ssh_key="No ssh_key used during mocked tests",
    )
    copy_to_sftp_and_archive_s3_files(config=config, db_session=test_db_session)

    # Collect the files in the source and dest directories after the function ran.
    files_in_source_dir = file_util.list_s3_files_and_directories_by_level(
        path="s3://" + os.path.join(mock_s3_bucket, source_dir)
    ).keys()
    files_in_archive_dir = file_util.list_s3_files_and_directories_by_level(
        path="s3://" + os.path.join(mock_s3_bucket, archive_dir)
    ).keys()

    # Expect that the ReferenceFiles associated with the files in S3 updated their file_locations.
    for filename in test_vcc_files_by_level.keys():
        # Expect to find no ReferenceFiles with the source file_location
        source_file_location = "s3://" + os.path.join(mock_s3_bucket, source_dir, filename)
        assert _first_ref_file(source_file_location, test_db_session) is None

        # Expect to find a single ReferenceFile with the archived file_location
        archived_file_location = "s3://" + os.path.join(mock_s3_bucket, archive_dir, filename)
        assert _first_ref_file(archived_file_location, test_db_session) is not None

        # Expect to find file in S3 archive dir
        assert filename in files_in_archive_dir

        # Expect to find no file with this filename in the source dir.
        assert filename not in files_in_source_dir

    # List contents of destination directory, then copy each file in S3 to SFTP server.
    expected_sftp_calls = ["listdir"] + ["put"] * total_file_count
    assert len(mock_sftp_client.calls) == len(expected_sftp_calls)
    for i, call in enumerate(mock_sftp_client.calls):
        assert call[0] == expected_sftp_calls[i]


def test_copy_to_sftp_and_archive_s3_files_no_files_in_s3(
    mock_s3_bucket, setup_mock_sftp_client, mock_sftp_client, test_db_session
):
    config = SftpS3TransferConfig(
        s3_bucket_uri="s3://" + mock_s3_bucket,
        source_dir="api/outbox",
        archive_dir="archive/testing",
        dest_dir="inbound/from_api",
        sftp_uri="sftp://api_user@mass.gov",
        ssh_key_password="No ssh_key_password used during mocked tests",
        ssh_key="No ssh_key used during mocked tests",
    )
    copy_to_sftp_and_archive_s3_files(config=config, db_session=test_db_session)

    assert len(mock_sftp_client.calls) == 0, "Expect no SFTP commands when there are no files in S3"


def test_copy_to_sftp_and_archive_s3_files_file_exists_in_sftp_dest(
    mock_s3_bucket,
    setup_mock_sftp_client,
    mock_sftp_client,
    test_db_session,
    mock_sftp_dir_with_conflicts,
    mock_sftp_filename_conflicts,
    initialize_factories_session,
):
    archive_dir = "archive/testing"
    source_dir = "api/outbox"

    s3 = boto3.client("s3")
    for filename in mock_sftp_filename_conflicts:
        # Stock our mocked S3 bucket with the files.
        key = os.path.join(source_dir, filename)
        s3.put_object(Bucket=mock_s3_bucket, Key=key, Body="test\n")

        # Add ReferenceFile objects to the database for these files.
        file_location = "s3://" + os.path.join(mock_s3_bucket, key)
        reference_file = ReferenceFileFactory(
            file_location=file_location,
            reference_file_type_id=ReferenceFileType.OUTBOUND_STATUS_RETURN.reference_file_type_id,
        )
        test_db_session.add(reference_file)

        # Expect to find no ReferenceFiles with the archived file_location
        archived_file_location = "s3://" + os.path.join(mock_s3_bucket, archive_dir, filename)
        assert _first_ref_file(archived_file_location, test_db_session) is None

    test_db_session.commit()

    config = SftpS3TransferConfig(
        s3_bucket_uri="s3://" + mock_s3_bucket,
        source_dir=source_dir,
        archive_dir=archive_dir,
        dest_dir=mock_sftp_dir_with_conflicts,
        sftp_uri="sftp://api_user@mass.gov",
        ssh_key_password="No ssh_key_password used during mocked tests",
        ssh_key="No ssh_key used during mocked tests",
    )
    copy_to_sftp_and_archive_s3_files(config=config, db_session=test_db_session)

    # Expect that the ReferenceFiles associated with the files in S3 were not updated because the
    # conflict in the destination SFTP server prevented the transfer.
    for filename in mock_sftp_filename_conflicts:
        source_file_location = "s3://" + os.path.join(mock_s3_bucket, source_dir, filename)
        assert _first_ref_file(source_file_location, test_db_session) is not None

        archived_file_location = "s3://" + os.path.join(mock_s3_bucket, archive_dir, filename)
        assert _first_ref_file(archived_file_location, test_db_session) is None

    # Listed contents of destination directory, but did not copy any files to the SFTP server
    # because files with the same name already exist.
    expected_sftp_calls = ["listdir"]
    assert len(mock_sftp_client.calls) == len(expected_sftp_calls)
    for i, call in enumerate(mock_sftp_client.calls):
        assert call[0] == expected_sftp_calls[i]


def test_copy_to_sftp_and_archive_s3_files_no_reference_file_row_in_database(
    mock_s3_bucket, setup_mock_sftp_client, mock_sftp_client, test_db_session
):
    source_dir = "api/outbox"
    test_filenames = ["file_1.txt", "file_2.txt"]

    s3 = boto3.client("s3")
    for filename in test_filenames:
        # Stock our mocked S3 bucket with the files, but do not add any ReferenceFile objects to
        # the database for these files.
        key = os.path.join(source_dir, filename)
        s3.put_object(Bucket=mock_s3_bucket, Key=key, Body="test\n")

    config = SftpS3TransferConfig(
        s3_bucket_uri="s3://" + mock_s3_bucket,
        source_dir=source_dir,
        archive_dir="archive/testing",
        dest_dir="inbound/from_api",
        sftp_uri="sftp://api_user@mass.gov",
        ssh_key_password="No ssh_key_password used during mocked tests",
        ssh_key="No ssh_key used during mocked tests",
    )
    copy_to_sftp_and_archive_s3_files(config=config, db_session=test_db_session)

    assert (
        len(mock_sftp_client.calls) == 1
    ), "Expected to make a send a single command to SFTP client because loop continues if there are no ReferenceFile objects for a given file_location"
    assert mock_sftp_client.calls[0][0] == "listdir"


def test_copy_to_sftp_and_archive_s3_files_s3_archive_failure(
    mock_s3_bucket,
    monkeypatch,
    setup_mock_sftp_client,
    mock_sftp_client,
    test_db_session,
    initialize_factories_session,
):
    # Raise an Exception when we attempt to move the file in S3.
    monkeypatch.setattr(
        file_util,
        "rename_file",
        lambda source, destination: _raise_exception(Exception("Failed to rename file in S3")),
    )

    archive_dir = "archive/testing"
    source_dir = "api/outbox"

    test_filenames = ["2000.txt", "2002.txt", "2008.txt"]

    s3 = boto3.client("s3")
    for filename in test_filenames:
        # Stock our mocked S3 bucket with the files.
        key = os.path.join(source_dir, filename)
        s3.put_object(Bucket=mock_s3_bucket, Key=key, Body="test\n")

        # Add ReferenceFile objects to the database for these files.
        file_location = "s3://" + os.path.join(mock_s3_bucket, key)
        reference_file = ReferenceFileFactory(
            file_location=file_location,
            reference_file_type_id=ReferenceFileType.OUTBOUND_STATUS_RETURN.reference_file_type_id,
        )
        test_db_session.add(reference_file)

        # Expect to find no ReferenceFiles with the archived file_location
        archived_file_location = "s3://" + os.path.join(mock_s3_bucket, archive_dir, filename)
        assert _first_ref_file(archived_file_location, test_db_session) is None

    test_db_session.commit()

    config = SftpS3TransferConfig(
        s3_bucket_uri="s3://" + mock_s3_bucket,
        source_dir=source_dir,
        archive_dir=archive_dir,
        # Following fields do not matter when mocking SFTP server. Included for completeness.
        dest_dir="inbound/from_api",
        sftp_uri="sftp://api_user@mass.gov",
        ssh_key_password="No ssh_key_password used during mocked tests",
        ssh_key="No ssh_key used during mocked tests",
    )

    with pytest.raises(Exception):
        copy_to_sftp_and_archive_s3_files(config=config, db_session=test_db_session)

    # Expect that the ReferenceFiles associated with the files in S3 did not update their
    # file locations.
    for filename in test_filenames:
        source_file_location = "s3://" + os.path.join(mock_s3_bucket, source_dir, filename)
        assert _first_ref_file(source_file_location, test_db_session) is not None

        archived_file_location = "s3://" + os.path.join(mock_s3_bucket, archive_dir, filename)
        assert _first_ref_file(archived_file_location, test_db_session) is None

    # List contents of destination directory, then copies first file but S3 archive fails so we
    # attempt to "roll back" the SFTP upload with a remove before exiting with the Exception.
    expected_sftp_calls = ["listdir", "put", "remove"]
    assert len(mock_sftp_client.calls) == len(expected_sftp_calls)
    for i, call in enumerate(mock_sftp_client.calls):
        assert call[0] == expected_sftp_calls[i]


def test_copy_from_sftp_to_s3_and_archive_files_success(
    mock_s3_bucket,
    setup_mock_sftp_client,
    mock_sftp_client,
    mock_sftp_default_listdir_filenames,
    test_db_session,
):
    config = SftpS3TransferConfig(
        s3_bucket_uri="s3://" + mock_s3_bucket,
        source_dir="source/outbox",
        archive_dir="archive",
        dest_dir="pfml/inbox",
        sftp_uri="sftp://api_user@mass.gov",
        ssh_key_password="No ssh_key_password used during mocked tests",
        ssh_key="No ssh_key used during mocked tests",
    )

    # Expect there to be no ReferenceFiles for the files prior to copying them from SFTP to S3.
    for filename in mock_sftp_default_listdir_filenames:
        filepath = os.path.join(config.s3_bucket_uri, config.dest_dir, filename)
        assert _first_ref_file(filepath, test_db_session) is None

    copy_from_sftp_to_s3_and_archive_files(config=config, db_session=test_db_session)

    # Expect to find ReferenceFiles for each file after copying them from SFTP to S3.
    for filename in mock_sftp_default_listdir_filenames:
        filepath = os.path.join(config.s3_bucket_uri, config.dest_dir, filename)
        assert _first_ref_file(filepath, test_db_session)

    # List contents of destination directory, then download (get) and archive (rename) each file in
    # the destination directory.
    expected_sftp_calls = ["listdir"] + ["get", "rename"] * len(mock_sftp_default_listdir_filenames)
    assert len(mock_sftp_client.calls) == len(expected_sftp_calls)
    for i, call in enumerate(mock_sftp_client.calls):
        assert call[0] == expected_sftp_calls[i]


def test_copy_from_sftp_to_s3_and_archive_files_no_files_in_sftp(
    mock_s3_bucket,
    setup_mock_sftp_client,
    mock_sftp_client,
    mock_sftp_default_listdir_filenames,
    mock_sftp_dir_with_no_files,
    test_db_session,
):
    config = SftpS3TransferConfig(
        s3_bucket_uri="s3://" + mock_s3_bucket,
        source_dir=mock_sftp_dir_with_no_files,
        archive_dir="archive",
        dest_dir="pfml/inbox",
        sftp_uri="sftp://api_user@mass.gov",
        ssh_key_password="No ssh_key_password used during mocked tests",
        ssh_key="No ssh_key used during mocked tests",
    )

    copy_from_sftp_to_s3_and_archive_files(config=config, db_session=test_db_session)

    # List contents of destination directory, then return early because we didn't find any files.
    expected_sftp_calls = ["listdir"]
    assert len(mock_sftp_client.calls) == len(expected_sftp_calls)
    for i, call in enumerate(mock_sftp_client.calls):
        assert call[0] == expected_sftp_calls[i]


def test_copy_from_sftp_to_s3_and_archive_files_some_files_already_exist(
    mock_s3_bucket,
    setup_mock_sftp_client,
    mock_sftp_client,
    mock_sftp_default_listdir_filenames,
    test_db_session,
    initialize_factories_session,
):
    config = SftpS3TransferConfig(
        s3_bucket_uri="s3://" + mock_s3_bucket,
        source_dir="source/outbox",
        archive_dir="archive",
        dest_dir="pfml/inbox",
        sftp_uri="sftp://api_user@mass.gov",
        ssh_key_password="No ssh_key_password used during mocked tests",
        ssh_key="No ssh_key used during mocked tests",
    )

    # Create ReferenceFiles for half of the files in SFTP server.
    files_to_be_downloaded = []
    for i, filename in enumerate(mock_sftp_default_listdir_filenames):
        if i % 2 == 0:
            filepath = os.path.join(config.s3_bucket_uri, config.dest_dir, filename)
            reference_file = ReferenceFileFactory(
                file_location=filepath,
                reference_file_type_id=ReferenceFileType.OUTBOUND_STATUS_RETURN.reference_file_type_id,
            )
            test_db_session.add(reference_file)
        else:
            files_to_be_downloaded.append(filename)
    test_db_session.commit()

    copy_from_sftp_to_s3_and_archive_files(config=config, db_session=test_db_session)

    # Expect to find ReferenceFiles for each file after copying them from SFTP to S3.
    for filename in mock_sftp_default_listdir_filenames:
        filepath = os.path.join(config.s3_bucket_uri, config.dest_dir, filename)
        assert _first_ref_file(filepath, test_db_session)

    # List contents of destination directory, then download (get) and archive (rename) each file
    # that does not already have a ReferenceFile record.
    expected_sftp_calls = ["listdir"] + ["get", "rename"] * len(files_to_be_downloaded)
    assert len(mock_sftp_client.calls) == len(expected_sftp_calls)
    for i, call in enumerate(mock_sftp_client.calls):
        assert call[0] == expected_sftp_calls[i]


def _raise_exception(ex):
    raise ex


def _first_ref_file(file_loc, db_session):
    return (
        db_session.query(ReferenceFile)
        .filter(ReferenceFile.file_location == file_loc)
        .one_or_none()
    )
