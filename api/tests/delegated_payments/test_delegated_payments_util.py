import logging  # noqa: B1
import os
import uuid
from datetime import date, datetime

import boto3
import faker
import pytest
from freezegun import freeze_time
from sqlalchemy.exc import SQLAlchemyError

import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    BankAccountType,
    ClaimType,
    ImportLog,
    PaymentCheck,
    PrenoteState,
    PubEft,
    ReferenceFile,
    ReferenceFileType,
)
from massgov.pfml.db.models.factories import (
    AbsencePeriodFactory,
    AddressFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployeePubEftPairFactory,
    EmployerFactory,
    ExperianAddressPairFactory,
    PaymentFactory,
    PubEftFactory,
    ReferenceFileFactory,
)
from massgov.pfml.db.models.geo import Country, GeoState
from massgov.pfml.db.models.payments import (
    FineosExtractVbiTaskReportSom,
    FineosExtractVpei,
    PaymentLog,
)
from massgov.pfml.delegated_payments.delegated_payments_util import (
    find_existing_address_pair,
    find_existing_eft,
    get_earliest_absence_period_for_payment_leave_request,
    get_earliest_matching_payment,
    is_employer_exempt_for_payment,
    is_same_address,
    is_same_eft,
    move_reference_file,
)
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory
from massgov.pfml.util.datetime import get_now_us_eastern
from tests.delegated_payments.conftest import upload_file_to_s3

fake = faker.Faker()

TEST_FILENAME = "test.txt"
TEST_SRC_DIR = "received"
TEST_DEST_DIR = "error"

# TODO: These should really be in payments_util or payments_config
PAYMENT_EXTRACT_FILENAMES = [
    "vpei.csv",
    "vpeiclaimdetails.csv",
    "vpeipaymentdetails.csv",
    "VBI_REQUESTEDABSENCE.csv",
]

CLAIMANT_EXTRACT_FILENAMES = ["Employee_feed.csv", "VBI_REQUESTEDABSENCE_SOM.csv"]
REQUEST_1099_DATA_EXTRACT_FILENAMES = ["VBI_1099DATA_SOM.csv"]


@pytest.fixture
def set_source_path(tmp_path, mock_fineos_s3_bucket):
    file_name = "2020-12-21-11-30-00-expected_file_one.csv"
    test_file = tmp_path / file_name
    test_file.write_text("test, data, rowOne\ntest, data, rowTwo")

    upload_file_to_s3(test_file, mock_fineos_s3_bucket, f"DT2/dataexports/{file_name}")

    file_name = "2020-12-21-11-30-00-expected_file_two.csv"
    test_file = tmp_path / file_name
    test_file.write_text("test, data, rowOne\ntest, data, rowTwo")

    upload_file_to_s3(test_file, mock_fineos_s3_bucket, f"DT2/dataexports/{file_name}")


def create_test_reference_file(test_db_session, mock_s3_bucket):
    src_path = os.path.join("s3://", mock_s3_bucket, TEST_SRC_DIR)
    dest_path = os.path.join("s3://", mock_s3_bucket, TEST_DEST_DIR)
    key = os.path.join(TEST_SRC_DIR, TEST_FILENAME)
    file_location = os.path.join(src_path, TEST_FILENAME)

    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key=key, Body="test\n")
    ref_file = ReferenceFileFactory.create(file_location=file_location)

    return (ref_file, src_path, dest_path)


def make_s3_file(s3_bucket, key, test_file_name):
    # Utility method to upload a test file to the mocked S3.
    # test_file_name corresponds to the name of the file in the test_files directory
    test_file_path = os.path.join(os.path.dirname(__file__), f"test_files/{test_file_name}")

    s3 = boto3.client("s3")
    s3.upload_file(test_file_path, s3_bucket, key)


def get_timestamped_filename(timestamp, filename):
    """Tiny utility to prepend timestamps to filenames"""
    return "-".join([timestamp, filename])


def upload_timestamped_s3_files(s3_bucket, s3_prefix, timestamp, filename_list):
    """Utility to create sets of files in a mock s3 bucket

    Files in filename_list must exist in the test_files directory

    Args:
        s3_bucket: Should be just the bucket name without s3://. Ex: "test_bucket"
        s3_prefix: The "folder" path. Ex: "DT2/dataexports/2020-01-01-11-30-00/"
        timestamp: A timestamp string with NO trailing hyphen. Ex: "2020-12-01-11-30-00"
        filename_list: A list of filenames to create.
            Ex: ["vpei.csv", "vpeiclaimdetails.csv", "vpeipaymentdetails.csv"]
    """
    for filename in filename_list:
        timestamped_filename = get_timestamped_filename(timestamp, filename)
        make_s3_file(s3_bucket, os.path.join(s3_prefix, timestamped_filename), filename)


def assert_copied_file_mapping_by_date_matches(
    copied_file_mapping_by_date, timestamp, s3_prefix, filename_list
):
    """Run asserts for all files in filename_list"""
    for filename in filename_list:
        timestamped_filename = get_timestamped_filename(timestamp, filename)
        assert copied_file_mapping_by_date[timestamp][filename] == os.path.join(
            s3_prefix, timestamped_filename
        )


## == Tests Begin ==


@pytest.mark.parametrize(
    "path, date_group",
    (
        ("2020-12-01-11-30-00-vpei.csv", "2020-12-01-11-30-00"),
        ("/2020-12-01-11-30-00-vpei.csv", "2020-12-01-11-30-00"),
        ("DT2/2020-12-01-11-30-00-vpei.csv", "2020-12-01-11-30-00"),
        ("2020-12-01-11-30-00/2020-12-01-vpei.csv", "2020-12-01-11-30-00"),
        ("2020-12-01-11-30-00/2020-12-01-11-30-00-vpei.csv", "2020-12-01-11-30-00"),
        ("2020-12-01-11-30-00/2020-12-01-11-45-00-vpei.csv", "2020-12-01-11-30-00"),
        ("2020-12-01-11-30-00/2020-12-02-11-30-00-vpei.csv", "2020-12-01-11-30-00"),
        ("2020-12-01-vpei.csv", None),
        ("vpei.csv", None),
    ),
)
def test_get_date_group_str_from_path(path, date_group):
    assert payments_util.get_date_group_str_from_path(path) == date_group


def test_get_date_group_folder_name():
    assert (
        payments_util.get_date_group_folder_name(
            "2020-12-01-11-30-00", ReferenceFileType.FINEOS_PAYMENT_EXTRACT
        )
        == "2020-12-01-11-30-00-payment-extract"
    )
    assert (
        payments_util.get_date_group_folder_name(
            "2020-12-01-11-30-00", ReferenceFileType.FINEOS_CLAIMANT_EXTRACT
        )
        == "2020-12-01-11-30-00-claimant-extract"
    )
    assert (
        payments_util.get_date_group_folder_name(
            "2022-01-01-11-30-00", ReferenceFileType.FINEOS_1099_DATA_EXTRACT
        )
        == "2022-01-01-11-30-00-1099-extract"
    )


def test_payment_extract_reference_file_exists_by_date_group_for_processed_payment(
    test_db_session, initialize_factories_session, set_exporter_env_vars
):
    date_group = "2020-12-01-11-30-00"

    assert not payments_util.payment_extract_reference_file_exists_by_date_group(
        test_db_session, date_group, ReferenceFileType.FINEOS_PAYMENT_EXTRACT
    )

    file_location = os.path.join(
        payments_config.get_s3_config().pfml_fineos_extract_archive_path,
        payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
        payments_util.get_date_group_folder_name(
            date_group, ReferenceFileType.FINEOS_PAYMENT_EXTRACT
        ),
    )
    ReferenceFileFactory.create(
        file_location=file_location,
        reference_file_type_id=ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id,
    )

    assert payments_util.payment_extract_reference_file_exists_by_date_group(
        test_db_session, date_group, ReferenceFileType.FINEOS_PAYMENT_EXTRACT
    )


def test_payment_extract_reference_file_exists_by_date_group_for_skipped_payment(
    test_db_session, initialize_factories_session, set_exporter_env_vars
):
    date_group = "2020-12-01-11-30-00"

    assert not payments_util.payment_extract_reference_file_exists_by_date_group(
        test_db_session, date_group, ReferenceFileType.FINEOS_PAYMENT_EXTRACT
    )

    file_location = os.path.join(
        payments_config.get_s3_config().pfml_fineos_extract_archive_path,
        payments_util.Constants.S3_INBOUND_SKIPPED_DIR,
        payments_util.get_date_group_folder_name(
            date_group, ReferenceFileType.FINEOS_PAYMENT_EXTRACT
        ),
    )
    ReferenceFileFactory.create(
        file_location=file_location,
        reference_file_type_id=ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id,
    )

    assert payments_util.payment_extract_reference_file_exists_by_date_group(
        test_db_session, date_group, ReferenceFileType.FINEOS_PAYMENT_EXTRACT
    )


def test_copy_fineos_data_to_archival_bucket(
    test_db_session, mock_fineos_s3_bucket, mock_s3_bucket, set_exporter_env_vars, monkeypatch
):
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2020-01-01")

    expected_timestamp_1 = "2020-01-02-11-30-00"
    s3_prefix = "DT2/dataexports/"
    # Add 3 top level expected files
    upload_timestamped_s3_files(
        mock_fineos_s3_bucket, s3_prefix, expected_timestamp_1, PAYMENT_EXTRACT_FILENAMES
    )

    # Add a few other files in the same path with other names
    make_s3_file(
        mock_fineos_s3_bucket, f"{s3_prefix}{expected_timestamp_1}-vpeiclaimants.csv", "small.csv"
    )
    make_s3_file(
        mock_fineos_s3_bucket, f"{s3_prefix}{expected_timestamp_1}-vpeiother.csv", "small.csv"
    )
    make_s3_file(
        mock_fineos_s3_bucket, f"{s3_prefix}{expected_timestamp_1}-VBI_OTHER.csv", "small.csv"
    )

    # Add 3 files in a date folder
    expected_timestamp_2 = "2020-01-01-11-30-00"
    s3_prefix = "DT2/dataexports/2020-01-01-11-30-00/"
    # Add 3 subfolder expected files
    upload_timestamped_s3_files(
        mock_fineos_s3_bucket, s3_prefix, expected_timestamp_2, PAYMENT_EXTRACT_FILENAMES
    )

    # Add a few more invalid files with the same suffix in other S3 "folders"
    make_s3_file(mock_fineos_s3_bucket, f"{s3_prefix}-yesterday/vpei.csv", "vpei.csv")
    make_s3_file(
        mock_fineos_s3_bucket,
        f"{s3_prefix}-2020-11-21-11-30-00/vpeipaymentdetails.csv",
        "vpeipaymentdetails.csv",
    )
    make_s3_file(mock_fineos_s3_bucket, "DT2/vpeiclaimdetails.csv", "vpeiclaimdetails.csv")
    make_s3_file(mock_fineos_s3_bucket, "IDT/dataexports/vpeiclaimdetails.csv", "small.csv")
    copied_file_mapping_by_date = payments_util.copy_fineos_data_to_archival_bucket(
        test_db_session, PAYMENT_EXTRACT_FILENAMES, ReferenceFileType.FINEOS_PAYMENT_EXTRACT
    )

    received_s3_prefix = f"s3://{mock_s3_bucket}/cps/inbound/received/"

    # These should be there
    assert_copied_file_mapping_by_date_matches(
        copied_file_mapping_by_date,
        expected_timestamp_1,
        received_s3_prefix,
        PAYMENT_EXTRACT_FILENAMES,
    )

    # These should also be there
    assert_copied_file_mapping_by_date_matches(
        copied_file_mapping_by_date,
        expected_timestamp_1,
        received_s3_prefix,
        PAYMENT_EXTRACT_FILENAMES,
    )


def test_copy_fineos_data_to_archival_bucket_skip_old_payment(
    test_db_session,
    initialize_factories_session,
    mock_fineos_s3_bucket,
    mock_s3_bucket,
    set_exporter_env_vars,
    monkeypatch,
    caplog,
):
    # Monkey path the max history date
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2020-01-02")
    caplog.set_level(logging.INFO)  # noqa: B1

    # Add 3 top level files: should be processed
    expected_timestamp_1 = "2020-01-03-11-30-00"
    s3_prefix = "DT2/dataexports/"
    upload_timestamped_s3_files(
        mock_fineos_s3_bucket, s3_prefix, expected_timestamp_1, PAYMENT_EXTRACT_FILENAMES
    )

    # Add 3 files in a date folder: should be processed
    expected_timestamp_2 = "2020-01-02-11-30-00"
    s3_prefix = f"DT2/dataexports/{expected_timestamp_2}/"
    upload_timestamped_s3_files(
        mock_fineos_s3_bucket, s3_prefix, expected_timestamp_2, PAYMENT_EXTRACT_FILENAMES
    )

    # Add 3 files in a date folder: should NOT be processed
    not_expected_timestamp_1 = "2020-01-01-11-30-00"
    s3_prefix = f"DT2/dataexports/{not_expected_timestamp_1}/"
    upload_timestamped_s3_files(
        mock_fineos_s3_bucket, s3_prefix, not_expected_timestamp_1, PAYMENT_EXTRACT_FILENAMES
    )

    # Check there are no processed or skipped files
    date_group = "2020-12-01-11-30-00"
    assert not payments_util.payment_extract_reference_file_exists_by_date_group(
        test_db_session, date_group, ReferenceFileType.FINEOS_PAYMENT_EXTRACT
    )

    # Actually run the command
    copied_file_mapping_by_date = payments_util.copy_fineos_data_to_archival_bucket(
        test_db_session, PAYMENT_EXTRACT_FILENAMES, ReferenceFileType.FINEOS_PAYMENT_EXTRACT
    )

    # Verify there is a skipped file
    file_location = os.path.join(
        payments_config.get_s3_config().pfml_fineos_extract_archive_path,
        payments_util.Constants.S3_INBOUND_SKIPPED_DIR,
        payments_util.get_date_group_folder_name(
            date_group, ReferenceFileType.FINEOS_PAYMENT_EXTRACT
        ),
    )
    ReferenceFileFactory.create(
        file_location=file_location,
        reference_file_type_id=ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id,
    )

    assert payments_util.payment_extract_reference_file_exists_by_date_group(
        test_db_session, date_group, ReferenceFileType.FINEOS_PAYMENT_EXTRACT
    )

    received_s3_prefix = f"s3://{mock_s3_bucket}/cps/inbound/received/"

    # 2020-01-03 files should be there
    assert_copied_file_mapping_by_date_matches(
        copied_file_mapping_by_date,
        expected_timestamp_1,
        received_s3_prefix,
        PAYMENT_EXTRACT_FILENAMES,
    )

    # 2020-01-02 files should be there
    assert_copied_file_mapping_by_date_matches(
        copied_file_mapping_by_date,
        expected_timestamp_2,
        received_s3_prefix,
        PAYMENT_EXTRACT_FILENAMES,
    )

    # 2020-01-01 files should NOT be there
    assert copied_file_mapping_by_date.get(not_expected_timestamp_1) is None
    assert (
        "Skipping FINEOS extract folder dated 2020-01-01-11-30-00 as it is prior to 2020-01-02"
        in [record.message for record in caplog.records]
    )


def test_copy_fineos_data_to_archival_bucket_skip_old_claimant_Extract(
    test_db_session, mock_fineos_s3_bucket, mock_s3_bucket, set_exporter_env_vars, monkeypatch
):
    # Monkey path the max history date
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2020-01-02")

    # Add 2 top level files: should be processed
    expected_timestamp_1 = "2020-01-03-11-30-00"
    s3_prefix = "DT2/dataexports/"
    upload_timestamped_s3_files(
        mock_fineos_s3_bucket, s3_prefix, expected_timestamp_1, CLAIMANT_EXTRACT_FILENAMES
    )

    # Add 2 files in a date folder: should be processed
    expected_timestamp_2 = "2020-01-02-11-30-00"
    s3_prefix = f"DT2/dataexports/{expected_timestamp_2}/"
    upload_timestamped_s3_files(
        mock_fineos_s3_bucket, s3_prefix, expected_timestamp_2, CLAIMANT_EXTRACT_FILENAMES
    )

    # Add 2 files in a date folder: should NOT be processed
    not_expected_timestamp_1 = "2020-01-01-11-30-00"
    s3_prefix = f"DT2/dataexports/{not_expected_timestamp_1}/"
    upload_timestamped_s3_files(
        mock_fineos_s3_bucket, s3_prefix, not_expected_timestamp_1, CLAIMANT_EXTRACT_FILENAMES
    )

    # Actually run the command
    copied_file_mapping_by_date = payments_util.copy_fineos_data_to_archival_bucket(
        test_db_session, CLAIMANT_EXTRACT_FILENAMES, ReferenceFileType.FINEOS_CLAIMANT_EXTRACT
    )

    received_s3_prefix = f"s3://{mock_s3_bucket}/cps/inbound/received/"

    # 2020-01-03 files should be there
    assert_copied_file_mapping_by_date_matches(
        copied_file_mapping_by_date,
        expected_timestamp_1,
        received_s3_prefix,
        CLAIMANT_EXTRACT_FILENAMES,
    )

    # 2020-01-02 files should be there
    assert_copied_file_mapping_by_date_matches(
        copied_file_mapping_by_date,
        expected_timestamp_2,
        received_s3_prefix,
        CLAIMANT_EXTRACT_FILENAMES,
    )

    # 2020-01-01 files should NOT be there
    assert copied_file_mapping_by_date.get(not_expected_timestamp_1) is None


def test_copy_fineos_data_to_archival_bucket_skip_top_level(
    test_db_session, mock_fineos_s3_bucket, mock_s3_bucket, set_exporter_env_vars, monkeypatch
):
    # Monkey path the max history date
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2020-04-01")

    # Add 3 top level files: should not be processed
    expected_timestamp_1 = "2020-01-03-11-30-00"
    s3_prefix = "DT2/dataexports/"
    upload_timestamped_s3_files(
        mock_fineos_s3_bucket, s3_prefix, expected_timestamp_1, CLAIMANT_EXTRACT_FILENAMES
    )

    # Actually run the command
    copied_file_mapping_by_date = payments_util.copy_fineos_data_to_archival_bucket(
        test_db_session, CLAIMANT_EXTRACT_FILENAMES, ReferenceFileType.FINEOS_CLAIMANT_EXTRACT
    )

    # Files should be empty
    assert copied_file_mapping_by_date == {}


def test_copy_fineos_data_to_archival_bucket_duplicate_suffix_error(
    test_db_session, mock_fineos_s3_bucket, mock_s3_bucket, set_exporter_env_vars, monkeypatch
):
    # Monkey path the max history date
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2020-12-01")

    date_prefix = "2020-12-01-11-30-00"
    s3_prefix = "DT2/dataexports/"
    upload_timestamped_s3_files(
        mock_fineos_s3_bucket, s3_prefix, date_prefix, PAYMENT_EXTRACT_FILENAMES
    )

    # Add an extra vpei.csv file in the same folder
    make_s3_file(mock_fineos_s3_bucket, f"{s3_prefix}{date_prefix}-ANOTHER-vpei.csv", "vpei.csv")

    with pytest.raises(
        Exception,
        match=f"Error while copying fineos extracts - duplicate files found for vpei.csv: s3://test_bucket/cps/inbound/received/{date_prefix}-ANOTHER-vpei.csv and s3://fineos_bucket/DT2/dataexports/{date_prefix}-vpei.csv",
    ):
        payments_util.copy_fineos_data_to_archival_bucket(
            test_db_session, PAYMENT_EXTRACT_FILENAMES, ReferenceFileType.FINEOS_PAYMENT_EXTRACT
        )


def test_copy_fineos_data_to_archival_bucket_missing_file_error(
    test_db_session, mock_fineos_s3_bucket, mock_s3_bucket, set_exporter_env_vars, monkeypatch
):
    # Monkey path the max history date
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2020-12-01")

    date_prefix = "2020-12-01-11-30-00"
    s3_prefix = f"DT2/dataexports/{date_prefix}"
    # Add only one file
    make_s3_file(mock_fineos_s3_bucket, f"{s3_prefix}-vpei.csv", "vpei.csv")

    with pytest.raises(
        Exception,
        match=f"Error while copying fineos extracts - The following expected files were not found {date_prefix}-vpeiclaimdetails.csv,{date_prefix}-vpeipaymentdetails.csv",
    ):
        payments_util.copy_fineos_data_to_archival_bucket(
            test_db_session, PAYMENT_EXTRACT_FILENAMES, ReferenceFileType.FINEOS_PAYMENT_EXTRACT
        )


def test_group_s3_files_by_date(mock_s3_bucket, set_exporter_env_vars):
    shared_prefix = "cps/inbound/received/"

    for prefix in [
        f"{shared_prefix}2020-01-01-11-30-00-",
        f"{shared_prefix}2020-01-02-11-30-00-",
        f"{shared_prefix}2020-01-03-11-30-00-",
    ]:
        # Add the 3 expected files
        make_s3_file(mock_s3_bucket, f"{prefix}vpei.csv", "vpei.csv")
        make_s3_file(mock_s3_bucket, f"{prefix}vpeipaymentdetails.csv", "vpeipaymentdetails.csv")
        make_s3_file(mock_s3_bucket, f"{prefix}vpeiclaimdetails.csv", "vpeiclaimdetails.csv")
        # Add some other random files to the same folder
        make_s3_file(mock_s3_bucket, f"{prefix}somethingelse.csv", "small.csv")
        make_s3_file(mock_s3_bucket, f"{prefix}vpeiandsuch.csv", "small.csv")
        make_s3_file(mock_s3_bucket, f"{prefix}secretrecipe.csv", "small.csv")

    data_by_date = payments_util.group_s3_files_by_date(PAYMENT_EXTRACT_FILENAMES)
    assert set(data_by_date.keys()) == set(
        ["2020-01-01-11-30-00", "2020-01-02-11-30-00", "2020-01-03-11-30-00"]
    )
    for date_item, paths in data_by_date.items():
        expected_path_to_file = f"s3://{mock_s3_bucket}/{shared_prefix}{date_item}-"
        assert set(paths) == set(
            [
                f"{expected_path_to_file}vpei.csv",
                f"{expected_path_to_file}vpeiclaimdetails.csv",
                f"{expected_path_to_file}vpeipaymentdetails.csv",
            ]
        )


def test_same_address(initialize_factories_session):
    first = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110",
        country_id=Country.USA.country_id,
    )
    second = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110",
        country_id=Country.USA.country_id,
    )
    assert is_same_address(first, second) is True

    # Test that None == ""
    third = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="",
        city="boston",
        zip_code="02110",
        country_id=Country.USA.country_id,
    )
    fourth = AddressFactory(
        address_line_one="1234 main st",
        address_line_two=None,
        city="boston",
        zip_code="02110",
        country_id=Country.USA.country_id,
    )
    assert is_same_address(third, fourth) is True


def test_same_address_comparable(initialize_factories_session):
    first = AddressFactory(
        address_line_one=" 1234 MaIn sT ",
        address_line_two="   #827 uNIT",
        city="BOSTON",
        zip_code=" 02110  ",
    )
    second = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110",
    )
    assert is_same_address(first, second) is True


def test_different_address(initialize_factories_session):
    first = AddressFactory()
    second = AddressFactory()
    assert is_same_address(first, second) is False

    # Different address line one
    third = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110",
    )
    fourth = AddressFactory(
        address_line_one="1234 main street",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110",
    )
    assert is_same_address(third, fourth) is False

    # Different city
    fifth = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="watertown",
        zip_code="02110",
    )
    assert is_same_address(third, fifth) is False

    # Different state
    sixth = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        geo_state_id=GeoState.CA.geo_state_id,
        zip_code="02110",
    )
    assert is_same_address(third, sixth) is False

    # Different zip code
    seventh = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110-1234",
    )
    assert is_same_address(third, seventh) is False

    # Different country
    eighth = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110",
        country_id=Country.USA.country_id,
    )
    ninth = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110",
        country_id=Country.TWN.country_id,
    )
    assert is_same_address(eighth, ninth) is False


def test_address_line_two(initialize_factories_session):
    first = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110",
    )
    second = AddressFactory(address_line_one="1234 main st", city="boston", zip_code="02110")
    assert is_same_address(first, second) is False

    third = AddressFactory(address_line_one="1234 main st", city="boston", zip_code="02110")
    fourth = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110",
    )
    assert is_same_address(third, fourth) is False


@pytest.mark.parametrize(
    "routing_nbr, account_nbr, bank_account_type_id",
    (
        (
            fake.random_number(digits=9, fix_len=True),
            fake.random_number(digits=40, fix_len=False),
            BankAccountType.SAVINGS.bank_account_type_id,
        ),
        (
            fake.random_number(digits=9, fix_len=True),
            fake.random_number(digits=40, fix_len=False),
            BankAccountType.CHECKING.bank_account_type_id,
        ),
    ),
    # pytest-xdist marks each parameterized test as a unique instance. Example: xdist will recieve test_is_same_eft[123-1], test_is_same_eft[456-2] on one instance and test_is_same_eft[789-1], test_is_same_eft[000-2] on a different instance. this causes errors because the "name" isn't the same
    ids=["savings", "checking"],
)
def test_is_same_eft(routing_nbr, account_nbr, bank_account_type_id, initialize_factories_session):
    first = PubEft(
        routing_nbr=routing_nbr,
        account_nbr=account_nbr,
        bank_account_type_id=bank_account_type_id,
        prenote_state=PrenoteState.PENDING_PRE_PUB,
    )
    second = PubEft(
        routing_nbr=routing_nbr,
        account_nbr=account_nbr,
        bank_account_type_id=bank_account_type_id,
        prenote_state=PrenoteState.REJECTED,  # Does not need to match
    )

    assert first != second
    assert is_same_eft(first, second) is True


def test_is_same_eft_different_routing_number():
    account_nbr = fake.random_number(digits=40, fix_len=False)
    first = PubEft(
        routing_nbr=fake.random_number(digits=9, fix_len=True),
        account_nbr=account_nbr,
        bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
        prenote_state=PrenoteState.PENDING_PRE_PUB,
    )
    second = PubEft(
        routing_nbr=fake.random_number(digits=9, fix_len=True),
        account_nbr=account_nbr,
        bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
        prenote_state=PrenoteState.PENDING_PRE_PUB,
    )

    assert is_same_eft(first, second) is False


def test_is_same_eft_different_account_number():
    routing_nbr = fake.random_number(digits=9, fix_len=True)
    first = PubEft(
        routing_nbr=routing_nbr,
        account_nbr=fake.random_number(digits=40, fix_len=False),
        bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
        prenote_state=PrenoteState.PENDING_PRE_PUB,
    )
    second = PubEft(
        routing_nbr=routing_nbr,
        account_nbr=fake.random_number(digits=40, fix_len=False),
        bank_account_type_id=BankAccountType.SAVINGS.bank_account_type_id,
        prenote_state=PrenoteState.PENDING_PRE_PUB,
    )

    assert is_same_eft(first, second) is False


def test_is_same_eft_different_bank_account_type():
    routing_nbr = fake.random_number(digits=9, fix_len=True)
    account_nbr = fake.random_number(digits=40, fix_len=False)
    first = PubEft(
        routing_nbr=routing_nbr,
        account_nbr=account_nbr,
        bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
        prenote_state=PrenoteState.PENDING_PRE_PUB,
    )
    second = PubEft(
        routing_nbr=routing_nbr,
        account_nbr=account_nbr,
        bank_account_type_id=BankAccountType.SAVINGS.bank_account_type_id,
        prenote_state=PrenoteState.PENDING_PRE_PUB,
    )

    assert is_same_eft(first, second) is False


def test_find_existing_address_pair(test_db_session, initialize_factories_session):
    lookup_address = AddressFactory.create()
    employee = EmployeeFactory.create()
    claim = ClaimFactory.create(employee=employee)

    # Doesn't break if employee isn't set
    assert not find_existing_address_pair(None, lookup_address, test_db_session)

    # Verify it can match the fineos address of another payment
    fineos_lookup_address = AddressFactory.create()
    fineos_address_pair = ExperianAddressPairFactory.create(fineos_address=fineos_lookup_address)
    PaymentFactory.create(claim=claim, experian_address_pair=fineos_address_pair)

    result = find_existing_address_pair(employee, fineos_lookup_address, test_db_session)
    assert result and result.fineos_address_id == fineos_address_pair.fineos_address_id

    # Verify it can match the experian address of another payment
    experian_lookup_address = AddressFactory.create()
    experian_address_pair = ExperianAddressPairFactory.create(
        fineos_address=AddressFactory.create(), experian_address=experian_lookup_address
    )
    PaymentFactory.create(claim=claim, experian_address_pair=experian_address_pair)

    result = find_existing_address_pair(employee, experian_lookup_address, test_db_session)
    assert (
        result and result.fineos_address_id == experian_address_pair.fineos_address_id
    )  # Primary key is the fineos address

    # Verify that an address won't be found if it's not associated with that employee
    # Even if it exists elsewhere with another employee
    employee2 = EmployeeFactory.create()
    claim2 = ClaimFactory.create(employee=employee2)
    address_pair2 = ExperianAddressPairFactory.create()
    PaymentFactory.create(claim=claim2, experian_address_pair=address_pair2)

    assert not find_existing_address_pair(employee2, fineos_lookup_address, test_db_session)
    assert not find_existing_address_pair(employee2, experian_lookup_address, test_db_session)


def test_find_existing_eft():
    eft1 = PubEftFactory.build(prenote_state_id=PrenoteState.PENDING_PRE_PUB.prenote_state_id)

    employee = EmployeeFactory.build()

    # Employee has no EFT info
    assert len(employee.pub_efts.all()) == 0
    assert not find_existing_eft(employee, eft1)

    # Add a few associated EFT objects
    EmployeePubEftPairFactory.build(employee=employee)
    EmployeePubEftPairFactory.build(employee=employee)
    assert len(employee.pub_efts.all()) == 2
    assert not find_existing_eft(employee, eft1)

    # Add another EFT info with the same account info
    # but currently in a different state
    EmployeePubEftPairFactory.build(
        employee=employee,
        pub_eft=PubEftFactory.build(
            routing_nbr=eft1.routing_nbr,
            account_nbr=eft1.account_nbr,
            bank_account_type_id=eft1.bank_account_type_id,
            prenote_state_id=PrenoteState.REJECTED,
        ),
    )
    assert len(employee.pub_efts.all()) == 3
    assert find_existing_eft(employee, eft1)


def test_move_reference_file(test_db_session, initialize_factories_session, mock_s3_bucket):
    (ref_file, src_path, dest_path) = create_test_reference_file(test_db_session, mock_s3_bucket)

    move_reference_file(test_db_session, ref_file, TEST_SRC_DIR, TEST_DEST_DIR)

    # File should no longer exist in the src_dir
    src_files = file_util.list_files(src_path)
    assert src_files == []

    # File should now be in the dest dir
    dest_files = file_util.list_files(dest_path)
    assert dest_files == [TEST_FILENAME]

    # reference_file.file_location should be updated in the db
    test_db_session.refresh(ref_file)
    test_db_session.flush()
    assert ref_file.file_location == os.path.join(dest_path, TEST_FILENAME)


def test_move_reference_file_invalid_file_location(test_db_session, initialize_factories_session):
    ref_file = ReferenceFileFactory.create()
    with pytest.raises(ValueError):
        move_reference_file(test_db_session, ref_file, TEST_SRC_DIR, TEST_DEST_DIR)


def test_move_reference_file_missing_src_dir(test_db_session, initialize_factories_session):
    ref_file = ReferenceFileFactory.create(
        file_location=os.path.join("s3://", "foo", TEST_FILENAME)
    )
    with pytest.raises(ValueError):
        move_reference_file(test_db_session, ref_file, TEST_SRC_DIR, TEST_DEST_DIR)


def test_move_reference_file_s3_failure(
    test_db_session, initialize_factories_session, caplog, mock_s3_bucket, tmp_path
):
    (ref_file, src_path, dest_path) = create_test_reference_file(test_db_session, mock_s3_bucket)

    # Test S3 failure
    ref_file.file_location = os.path.join(tmp_path, ref_file.file_location.replace("s3://", ""))
    with pytest.raises(FileNotFoundError):
        move_reference_file(test_db_session, ref_file, TEST_SRC_DIR, TEST_DEST_DIR)

    # File should still be in the src_dir
    src_files = file_util.list_files(src_path)
    assert src_files == [TEST_FILENAME]

    # File should not be in the dest dir
    dest_files = file_util.list_files(dest_path)
    assert dest_files == []

    # reference_file.file_location should not be changed in the db
    test_db_session.refresh(ref_file)
    test_db_session.flush()
    assert ref_file.file_location == os.path.join(src_path, TEST_FILENAME)


def test_move_reference_file_db_failure(
    test_db_session, initialize_factories_session, caplog, mock_s3_bucket
):
    (ref_file, src_path, dest_path) = create_test_reference_file(test_db_session, mock_s3_bucket)

    # Test DB failure
    # insert a ReferenceFile already containing the error path, forcing a unique key error
    ReferenceFileFactory(file_location=ref_file.file_location.replace(TEST_SRC_DIR, TEST_DEST_DIR))
    test_db_session.commit()
    test_db_session.begin_nested()
    with pytest.raises(SQLAlchemyError):
        move_reference_file(test_db_session, ref_file, TEST_SRC_DIR, TEST_DEST_DIR)

    # File should still be in the src_dir
    src_files = file_util.list_files(src_path)
    assert src_files == [TEST_FILENAME]

    # File should not be in the dest dir
    dest_files = file_util.list_files(dest_path)
    assert dest_files == []

    # reference_file.file_location should not be changed in the db
    # test_db_session.refresh(ref_file)
    # test_db_session.flush()
    assert ref_file.file_location == os.path.join(src_path, TEST_FILENAME)


def test_get_fineos_max_history_date(monkeypatch):
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2021-01-01")
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2021-01-15")

    claimant_datetime = payments_util.get_fineos_max_history_date(
        ReferenceFileType.FINEOS_CLAIMANT_EXTRACT
    )
    assert claimant_datetime == datetime(2021, 1, 1, 0, 0)

    payment_datetime = payments_util.get_fineos_max_history_date(
        ReferenceFileType.FINEOS_PAYMENT_EXTRACT
    )
    assert payment_datetime == datetime(2021, 1, 15, 0, 0)


def test_get_fineos_max_history_date_bad_type(monkeypatch):
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2021-01-01")

    with pytest.raises(ValueError):
        payments_util.get_fineos_max_history_date(ReferenceFileType.GAX)


def test_get_fineos_max_history_date_bad_string(monkeypatch):
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "foo")
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "bar")

    with pytest.raises(ValueError):
        payments_util.get_fineos_max_history_date(ReferenceFileType.FINEOS_CLAIMANT_EXTRACT)

    with pytest.raises(ValueError):
        payments_util.get_fineos_max_history_date(ReferenceFileType.FINEOS_PAYMENT_EXTRACT)


def test_create_staging_table_instance(test_db_session, initialize_factories_session, caplog):
    """We test if an extra column is provided to given staging data model, an instance of data
    model is created, excluding the extra columns. The extra columns that aren't in
    ignore_properties are logged as a warning.
    """

    caplog.set_level(logging.INFO)  # noqa: B1

    ref_file = ReferenceFileFactory.create()
    vpei_data = {
        "addressline6": "test",
        "addressline7": "test",
        "addressline8": "test",  # no matching column in FineosExtractVpei
        "addressline9": "test",  # no matching column in FineosExtractVpei
    }

    vpei_instance = payments_util.create_staging_table_instance(
        vpei_data, FineosExtractVpei, ref_file, None, ignore_properties=["addressline9"]
    )
    test_db_session.add(vpei_instance)
    test_db_session.commit()

    employee = (
        test_db_session.query(FineosExtractVpei)
        .filter_by(addressline6="test", addressline7="test")
        .all()
    )

    assert len(employee) == 1

    warnings = 0
    for record in caplog.records:
        if record.msg == "Unconfigured columns in FINEOS extract after first record.":
            assert "addressline8" in record.fields
            assert "addressline9" not in record.fields
            warnings += 1

    assert warnings == 1


def test_create_payment_log(test_db_session, initialize_factories_session):
    # Create a payment without a claim/employee/etc. So this only has the additional info
    import_log = ImportLog(import_log_id=1)
    test_db_session.add(import_log)
    payment = PaymentFactory.create(claim=None, claim_id=None)

    additional_details = {"info": {"nested": 1}}
    payments_util.create_payment_log(
        payment, import_log.import_log_id, test_db_session, additional_details
    )

    payment_log = test_db_session.query(PaymentLog).first()
    assert payment_log.payment_id == payment.payment_id
    assert payment_log.import_log_id == import_log.import_log_id

    excepted_details = {"snapshot": {}}
    excepted_details.update(additional_details)
    assert payment_log.details == excepted_details


def test_create_payment_log_full(test_db_session, initialize_factories_session):
    import_log = ImportLog(import_log_id=1)
    test_db_session.add(import_log)

    employer = EmployerFactory.create()
    claim = ClaimFactory.create(employer=employer, employer_id=employer.employer_id)
    payment = PaymentFactory.create(claim=claim)
    employee = claim.employee

    payment_check = PaymentCheck(payment_id=payment.payment_id, check_number=25)
    test_db_session.add(payment_check)
    test_db_session.commit()

    # Don't provide any additional details
    payments_util.create_payment_log(payment, import_log.import_log_id, test_db_session)

    payment_log = test_db_session.query(PaymentLog).first()
    assert payment_log.payment_id == payment.payment_id
    assert payment_log.import_log_id == import_log.import_log_id

    # Verify the only record in the details is the snapshot data
    assert len(payment_log.details) == 1
    assert "snapshot" in payment_log.details

    snapshot = payment_log.details["snapshot"]

    # Claim should be present and match exactly
    assert "claim" in snapshot
    assert snapshot["claim"].items() == claim.for_json().items()

    # Employee should be present, and a subset of the data
    assert "employee" in snapshot
    assert len(snapshot["employee"]) > 7  # Sanity check to verify not empty
    assert snapshot["employee"].items() <= employee.for_json().items()

    # Employer should be present, and a subset of the data
    assert "employer" in snapshot
    assert len(snapshot["employer"]) > 7  # Sanity check to verify not empty
    assert snapshot["employer"].items() <= employer.for_json().items()

    # Payment check should be present and match exactly
    assert "payment_check" in snapshot
    assert snapshot["payment_check"].items() == payment_check.for_json().items()


def test_create_success_file(mock_s3_bucket, monkeypatch):
    archive_folder_path = f"s3://{mock_s3_bucket}/reports"
    monkeypatch.setenv("PFML_ERROR_REPORTS_ARCHIVE_PATH", archive_folder_path)

    # Make this act like the FINEOS extract process often does
    # Starting at 11pm, but finishing a bit after.
    with freeze_time("2021-08-01 23:00:00", tz_offset=4):
        now = get_now_us_eastern()
    with freeze_time("2021-08-02 00:15:00", tz_offset=4):
        payments_util.create_success_file(now, "example-process")

    # Will be saved at a path with a folder showing the start date
    # and a timestamp showing when it actually finished
    files = file_util.list_files(archive_folder_path, recursive=True)
    assert len(files) == 1
    assert files[0] == "processed/2021-08-01/2021-08-02-00-15-00-example-process.SUCCESS"


def test_copy_fineos_data_to_archival_bucket_skip_old_1099_Extract(
    test_db_session, mock_fineos_s3_bucket, mock_s3_bucket, set_exporter_env_vars, monkeypatch
):
    # Monkey path the max history date
    monkeypatch.setenv("fineos_1099_data_extract_max_history_date", "2022-01-04")

    # Add 2 top level files: should be processed
    expected_timestamp_1 = "2022-01-05-11-30-00"
    s3_prefix = "DT2/dataexports/"
    upload_timestamped_s3_files(
        mock_fineos_s3_bucket, s3_prefix, expected_timestamp_1, REQUEST_1099_DATA_EXTRACT_FILENAMES
    )

    # Add 2 files in a date folder: should be processed
    expected_timestamp_2 = "2022-01-07-11-30-00"
    s3_prefix = f"DT2/dataexports/{expected_timestamp_2}/"
    upload_timestamped_s3_files(
        mock_fineos_s3_bucket, s3_prefix, expected_timestamp_2, REQUEST_1099_DATA_EXTRACT_FILENAMES
    )

    # Add 2 files in a date folder: should NOT be processed
    not_expected_timestamp_1 = "2022-01-01-11-30-00"
    s3_prefix = f"DT2/dataexports/{not_expected_timestamp_1}/"
    upload_timestamped_s3_files(
        mock_fineos_s3_bucket,
        s3_prefix,
        not_expected_timestamp_1,
        REQUEST_1099_DATA_EXTRACT_FILENAMES,
    )

    # Actually run the command
    copied_file_mapping_by_date = payments_util.copy_fineos_data_to_archival_bucket(
        test_db_session,
        REQUEST_1099_DATA_EXTRACT_FILENAMES,
        ReferenceFileType.FINEOS_1099_DATA_EXTRACT,
    )

    received_s3_prefix = f"s3://{mock_s3_bucket}/cps/inbound/received/"

    # 2022-01-05 files should be there
    assert_copied_file_mapping_by_date_matches(
        copied_file_mapping_by_date,
        expected_timestamp_1,
        received_s3_prefix,
        REQUEST_1099_DATA_EXTRACT_FILENAMES,
    )

    # 2022-01-07 files should be there
    assert_copied_file_mapping_by_date_matches(
        copied_file_mapping_by_date,
        expected_timestamp_2,
        received_s3_prefix,
        REQUEST_1099_DATA_EXTRACT_FILENAMES,
    )

    # 2022-01-01 files should NOT be there
    assert copied_file_mapping_by_date.get(not_expected_timestamp_1) is None


def test_copy_fineos_data_to_archival_bucket_no_files_copied(
    test_db_session, mock_fineos_s3_bucket, mock_s3_bucket, set_exporter_env_vars, monkeypatch
):
    # Monkey path the max history date
    monkeypatch.setenv("fineos_1099_data_extract_max_history_date", "2022-01-04")

    # Add 3 top level files: should not be processed
    expected_timestamp_1 = "2022-01-03-11-30-00"
    s3_prefix = "DT2/dataexports/"
    upload_timestamped_s3_files(
        mock_fineos_s3_bucket, s3_prefix, expected_timestamp_1, REQUEST_1099_DATA_EXTRACT_FILENAMES
    )

    # Actually run the command
    copied_file_mapping_by_date = payments_util.copy_fineos_data_to_archival_bucket(
        test_db_session,
        REQUEST_1099_DATA_EXTRACT_FILENAMES,
        ReferenceFileType.FINEOS_1099_DATA_EXTRACT,
    )

    # Files should be empty
    assert copied_file_mapping_by_date == {}


def test_copy_fineos_data_to_archival_bucket_duplicate_1099_file_error(
    test_db_session, mock_fineos_s3_bucket, mock_s3_bucket, set_exporter_env_vars, monkeypatch
):
    # Monkey path the max history date
    monkeypatch.setenv("fineos_1099_data_extract_max_history_date", "2022-01-04")

    date_prefix = "2022-01-04-11-30-00"
    s3_prefix = "DT2/dataexports/"

    upload_timestamped_s3_files(
        mock_fineos_s3_bucket, s3_prefix, date_prefix, REQUEST_1099_DATA_EXTRACT_FILENAMES
    )
    make_s3_file(
        mock_fineos_s3_bucket,
        f"{s3_prefix}{date_prefix}-ANOTHER-VBI_1099DATA_SOM.csv",
        "VBI_1099DATA_SOM.csv",
    )

    with pytest.raises(
        Exception,
        match=f"Error while copying fineos extracts - duplicate files found for VBI_1099DATA_SOM.csv: s3://test_bucket/cps/inbound/received/{date_prefix}-ANOTHER-VBI_1099DATA_SOM.csv and s3://fineos_bucket/DT2/dataexports/{date_prefix}-VBI_1099DATA_SOM.csv",
    ):
        payments_util.copy_fineos_data_to_archival_bucket(
            test_db_session,
            REQUEST_1099_DATA_EXTRACT_FILENAMES,
            ReferenceFileType.FINEOS_1099_DATA_EXTRACT,
        )


@pytest.mark.parametrize(
    "employer_exempt_family, employer_exempt_medical, absence_period_start_date, claim_type, expected_result",
    (
        # No exemptions
        (False, False, date(2022, 1, 15), ClaimType.MEDICAL_LEAVE, False),
        # Exemption is for other leave type
        (True, False, date(2022, 1, 15), ClaimType.MEDICAL_LEAVE, False),
        # Exemption is for other leave type
        (False, True, date(2022, 1, 15), ClaimType.FAMILY_LEAVE, False),
        # Date is before exemption start
        (True, True, date(2021, 12, 15), ClaimType.FAMILY_LEAVE, False),
        # Date is after exemption end
        (True, True, date(2022, 2, 15), ClaimType.FAMILY_LEAVE, False),
        # Employer exempt for family leave
        (True, False, date(2022, 1, 15), ClaimType.FAMILY_LEAVE, True),
        # Employer exempt for medical leave
        (False, True, date(2022, 1, 15), ClaimType.MEDICAL_LEAVE, True),
        # Verifying dates are inclusive
        (True, True, date(2022, 1, 1), ClaimType.MEDICAL_LEAVE, True),
        (True, True, date(2022, 1, 31), ClaimType.MEDICAL_LEAVE, True),
    ),
)
def test_is_employer_exempt_for_payment(
    employer_exempt_family,
    employer_exempt_medical,
    absence_period_start_date,
    claim_type,
    expected_result,
    initialize_factories_session,
    test_db_session,
):
    payment = DelegatedPaymentFactory(
        test_db_session,
        # Payment
        is_adhoc_payment=False,
        # Claim
        claim_type=claim_type,
        absence_period_start_date=absence_period_start_date,
        # Employer
        employer_exempt_commence_date=date(2022, 1, 1),
        employer_exempt_cease_date=date(2022, 1, 31),
        employer_exempt_family=employer_exempt_family,
        employer_exempt_medical=employer_exempt_medical,
    ).get_or_create_payment()

    assert (
        is_employer_exempt_for_payment(payment, payment.claim, payment.claim.employer)
        is expected_result
    )

    # Show that adhoc payments always return false from check
    adhoc_payment = DelegatedPaymentFactory(
        test_db_session,
        # Payment
        is_adhoc_payment=True,
        # Claim
        claim_type=claim_type,
        absence_period_start_date=absence_period_start_date,
        # Employer
        employer_exempt_commence_date=date(2022, 1, 1),
        employer_exempt_cease_date=date(2022, 1, 31),
        employer_exempt_family=employer_exempt_family,
        employer_exempt_medical=employer_exempt_medical,
    ).get_or_create_payment()

    assert (
        is_employer_exempt_for_payment(
            adhoc_payment, adhoc_payment.claim, adhoc_payment.claim.employer
        )
        is False
    )


def test_get_earliest_absence_period_for_payment_leave_request(
    initialize_factories_session, test_db_session
):
    # This test simply implements the example given in the relevant method
    claim = ClaimFactory.create()

    # Paid Leave 0 (not connected to any payments - occurs before)
    AbsencePeriodFactory.create(
        claim=claim,
        absence_period_start_date=date(2021, 12, 1),
        absence_period_end_date=date(2021, 12, 28),
        fineos_leave_request_id=0,
    )
    # Paid Leave 1
    fineos_leave_request_id_1 = 1
    ## Absence Period A
    absence_period_a = AbsencePeriodFactory.create(
        claim=claim,
        absence_period_start_date=date(2022, 1, 1),
        absence_period_end_date=date(2022, 1, 28),
        fineos_leave_request_id=fineos_leave_request_id_1,
    )
    ### Payment I
    payment_1 = PaymentFactory.create(
        claim=claim,
        fineos_leave_request_id=fineos_leave_request_id_1,
        period_start_date=date(2022, 1, 1),
        period_end_date=date(2022, 1, 7),
    )
    ### Payment II
    payment_2 = PaymentFactory.create(
        claim=claim,
        fineos_leave_request_id=fineos_leave_request_id_1,
        period_start_date=date(2022, 1, 8),
        period_end_date=date(2022, 1, 14),
    )
    ## Absence Period B
    AbsencePeriodFactory.create(
        claim=claim,
        absence_period_start_date=date(2022, 2, 1),
        absence_period_end_date=date(2022, 2, 28),
        fineos_leave_request_id=fineos_leave_request_id_1,
    )
    ### Payment III
    payment_3 = PaymentFactory.create(
        claim=claim,
        fineos_leave_request_id=fineos_leave_request_id_1,
        period_start_date=date(2022, 2, 1),
        period_end_date=date(2022, 2, 7),
    )
    ### Payment IV
    payment_4 = PaymentFactory.create(
        claim=claim,
        fineos_leave_request_id=fineos_leave_request_id_1,
        period_start_date=date(2022, 2, 8),
        period_end_date=date(2022, 2, 14),
    )

    # Paid Leave 2
    fineos_leave_request_id_2 = 2
    ## Absence Period C
    absence_period_c = AbsencePeriodFactory.create(
        claim=claim,
        absence_period_start_date=date(2022, 3, 1),
        absence_period_end_date=date(2022, 3, 28),
        fineos_leave_request_id=fineos_leave_request_id_2,
    )
    ### Payment V
    payment_5 = PaymentFactory.create(
        claim=claim,
        fineos_leave_request_id=fineos_leave_request_id_2,
        period_start_date=date(2022, 3, 1),
        period_end_date=date(2022, 3, 7),
    )
    ### Payment VI
    payment_6 = PaymentFactory.create(
        claim=claim,
        fineos_leave_request_id=fineos_leave_request_id_2,
        period_start_date=date(2022, 3, 8),
        period_end_date=date(2022, 3, 14),
    )
    ## Absence Period D
    AbsencePeriodFactory.create(
        claim=claim,
        absence_period_start_date=date(2022, 4, 1),
        absence_period_end_date=date(2022, 4, 28),
        fineos_leave_request_id=fineos_leave_request_id_2,
    )
    ### Payment VII
    payment_7 = PaymentFactory.create(
        claim=claim,
        fineos_leave_request_id=fineos_leave_request_id_2,
        period_start_date=date(2022, 4, 1),
        period_end_date=date(2022, 4, 7),
    )
    ## Absence Period E
    AbsencePeriodFactory.create(
        claim=claim,
        absence_period_start_date=date(2022, 5, 1),
        absence_period_end_date=date(2022, 5, 28),
        fineos_leave_request_id=fineos_leave_request_id_2,
    )
    ### Payment VIII
    payment_8 = PaymentFactory.create(
        claim=claim,
        fineos_leave_request_id=fineos_leave_request_id_2,
        period_start_date=date(2022, 5, 1),
        period_end_date=date(2022, 5, 7),
    )

    # Paid Leave 3 (Occurs after, no payments associated)
    AbsencePeriodFactory.create(
        claim=claim,
        absence_period_start_date=date(2023, 1, 1),
        absence_period_end_date=date(2023, 1, 28),
        fineos_leave_request_id=3,
    )

    for payment in [payment_1, payment_2, payment_3, payment_4]:
        absence_period = get_earliest_absence_period_for_payment_leave_request(
            test_db_session, payment
        )
        assert absence_period.absence_period_id == absence_period_a.absence_period_id

    for payment in [payment_5, payment_6, payment_7, payment_8]:
        absence_period = get_earliest_absence_period_for_payment_leave_request(
            test_db_session, payment
        )
        assert absence_period.absence_period_id == absence_period_c.absence_period_id


def test_get_earliest_matching_payment(initialize_factories_session, test_db_session):
    # Test ensures that we are retrieving the payment
    # with the oldest created_at matching C/I values
    fineos_pei_c_value = "1234"
    fineos_pei_i_value = "5678"
    payment_factory = DelegatedPaymentFactory(
        test_db_session,
        fineos_pei_c_value=fineos_pei_c_value,
        fineos_pei_i_value=fineos_pei_i_value,
    )
    earliest_payment = payment_factory.get_or_create_payment()

    # Create a series of related payments

    for i in range(10):
        new_payment = payment_factory.create_related_payment(weeks_later=i + 1)
        assert new_payment.fineos_pei_c_value == earliest_payment.fineos_pei_c_value
        assert new_payment.fineos_pei_i_value == earliest_payment.fineos_pei_i_value

    earliest_matching_payment = get_earliest_matching_payment(
        test_db_session, fineos_pei_c_value, fineos_pei_i_value
    )

    assert earliest_matching_payment.payment_id == earliest_payment.payment_id


def test_get_earliest_matching_payment__no_previous_payments(
    initialize_factories_session, test_db_session
):
    fineos_pei_c_value = "1234"
    fineos_pei_i_value = "5678"

    earliest_matching_payment = get_earliest_matching_payment(
        test_db_session, fineos_pei_c_value, fineos_pei_i_value
    )

    assert earliest_matching_payment is None


def test_get_unconfigured_fineos_columns():
    expected_columns = {"addressline6": "test", "addressline7": "test"}

    unconfigured_columns = payments_util.get_unconfigured_fineos_columns(
        expected_columns, FineosExtractVpei
    )

    assert len(unconfigured_columns) == 0

    extra_columns = {
        "addressline6": "test",
        "addressline7": "test",
        "addressline8": "test",  # no matching column in FineosExtractVpei
        "addressline9": "test",  # no matching column in FineosExtractVpei
    }

    unconfigured_columns = payments_util.get_unconfigured_fineos_columns(
        extra_columns, FineosExtractVpei
    )

    assert unconfigured_columns == ["addressline8", "addressline9"]


def test_get_open_tasks(test_db_session):
    reference_file_id = uuid.uuid4()
    reference_file = ReferenceFile(
        file_location="fake_file_location",
        reference_file_type_id=ReferenceFileType.FINEOS_VBI_TASKREPORT_SOM_EXTRACT.reference_file_type_id,
        reference_file_id=reference_file_id,
    )
    test_db_session.add(reference_file)

    mock_task_1 = FineosExtractVbiTaskReportSom(
        status="928000",
        casenumber="mock_casenum_1",
        tasktypename="Employee Reported Other Income",
        reference_file_id=reference_file_id,
    )
    mock_task_2 = FineosExtractVbiTaskReportSom(
        status="928001",
        casenumber="mock_casenum_1",
        tasktypename="Employee Reported Other Income",
        reference_file_id=reference_file_id,
    )
    mock_task_3 = FineosExtractVbiTaskReportSom(
        status="928000",
        casenumber="mock_casenum_1",
        tasktypename="Adjudicate Absence",
        reference_file_id=reference_file_id,
    )
    mock_task_4 = FineosExtractVbiTaskReportSom(
        status="928000",
        casenumber="mock_casenum_2",
        tasktypename="Employee Reported Other Income",
        reference_file_id=reference_file_id,
    )
    mock_task_5 = FineosExtractVbiTaskReportSom(
        status="928001",
        casenumber="mock_casenum_3",
        tasktypename="Employee Reported Other Income",
        reference_file_id=reference_file_id,
    )
    test_db_session.add(mock_task_1)
    test_db_session.add(mock_task_2)
    test_db_session.add(mock_task_3)
    test_db_session.add(mock_task_4)
    test_db_session.add(mock_task_5)

    # Check that we only return open tasks from the correct absence case
    tasks = payments_util.get_open_tasks(
        test_db_session, "mock_casenum_1", ["Employee Reported Other Income"]
    )
    assert len(tasks) == 1
    assert tasks[0].casenumber == "mock_casenum_1"
    assert tasks[0].tasktypename == "Employee Reported Other Income"

    # Check that we return all open tasks with matching task names
    tasks = payments_util.get_open_tasks(
        test_db_session, "mock_casenum_1", ["Employee Reported Other Income", "Adjudicate Absence"]
    )
    assert len(tasks) == 2
    assert tasks[0].casenumber == "mock_casenum_1"
    assert tasks[0].tasktypename in ("Employee Reported Other Income", "Adjudicate Absence")
    assert tasks[1].casenumber == "mock_casenum_1"
    assert tasks[1].tasktypename in ("Employee Reported Other Income", "Adjudicate Absence")

    # Check that if there are no open tasks, we return an empty list
    tasks = payments_util.get_open_tasks(
        test_db_session, "mock_casenum_3", ["Employee Reported Other Income"]
    )
    assert len(tasks) == 0
