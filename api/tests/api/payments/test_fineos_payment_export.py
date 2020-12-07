import os
import tempfile
import zipfile

import boto3
import pytest

import massgov.pfml.payments.fineos_payment_export as exporter
import massgov.pfml.util.files as file_util


@pytest.fixture
def mock_fineos_s3_bucket(mock_s3_bucket):
    # This relies on the context manager setup in the mock_s3_bucket fixture
    # which remains open because it uses yield rather than return
    s3 = boto3.resource("s3")
    bucket_name = "fineos_bucket"
    s3.create_bucket(Bucket=bucket_name)
    yield bucket_name


@pytest.fixture
def set_exporter_env_vars(mock_s3_bucket, mock_fineos_s3_bucket, monkeypatch):
    monkeypatch.setenv("FINEOS_DATA_EXPORT_PATH", f"s3://{mock_fineos_s3_bucket}/DT2/dataexports/")
    monkeypatch.setenv("PFML_FINEOS_INBOUND_PATH", f"s3://{mock_s3_bucket}/cps/inbound/received/")
    monkeypatch.setenv("FINEOS_DATA_IMPORT_PATH", "n/a")
    monkeypatch.setenv("PFML_FINEOS_OUTBOUND_PATH", "n/a")


def make_s3_zip_file(s3_bucket, key, test_file_name):
    # Utility method to convert one of our test files to a zipped
    # file in a temporary test directory and upload it to the mocked S3.
    # The name of the zip is based on the key passed in:
    # key: s3://test_bucket/path/to/file.csv.zip creates a zip named
    # file.csv.zip with the test file inside named file.csv
    # test_file_name corresponds to the name of the file in the test_files directory
    test_file_path = os.path.join(os.path.dirname(__file__), f"test_files/{test_file_name}")

    filename = key.split("/")[-1]
    if filename.endswith(".zip"):
        filename = filename[:-4]

    with tempfile.TemporaryDirectory() as directory:
        zip_path = f"{directory}/{filename}.zip"

        with zipfile.ZipFile(zip_path, "w") as zip_obj:
            zip_obj.write(test_file_path, arcname=filename)

        s3 = boto3.client("s3")
        s3.upload_file(zip_path, s3_bucket, key)


def test_copy_fineos_data_to_archival_bucket(
    mock_fineos_s3_bucket, mock_s3_bucket, set_exporter_env_vars
):
    s3_prefix = "DT2/dataexports/"
    # Add the 5 expected files
    make_s3_zip_file(mock_fineos_s3_bucket, f"{s3_prefix}vpei.csv.zip", "vpei.csv")
    make_s3_zip_file(
        mock_fineos_s3_bucket, f"{s3_prefix}vpeipaymentdetails.csv.zip", "vpei_payment_details.csv",
    )
    make_s3_zip_file(
        mock_fineos_s3_bucket, f"{s3_prefix}vpeiclaimdetails.csv.zip", "vpei_claim_details.csv"
    )
    make_s3_zip_file(mock_fineos_s3_bucket, f"{s3_prefix}LeavePlan_info.csv.zip", "leave_plan.csv")
    make_s3_zip_file(
        mock_fineos_s3_bucket, f"{s3_prefix}VBI_PERSON_SOM_ALL.csv.zip", "vbi_person_som.csv"
    )

    # Add a few other files in the same path with other names
    make_s3_zip_file(mock_fineos_s3_bucket, f"{s3_prefix}vpeiclaimants.csv.zip", "small.csv")
    make_s3_zip_file(mock_fineos_s3_bucket, f"{s3_prefix}vpeiother.csv.zip", "small.csv")
    make_s3_zip_file(mock_fineos_s3_bucket, f"{s3_prefix}VBI_OTHER.csv.zip", "small.csv")

    # Add a few more files with the same suffix in other S3 "folders"
    make_s3_zip_file(mock_fineos_s3_bucket, f"{s3_prefix}yesterday/vpei.csv.zip", "vpei.csv")
    make_s3_zip_file(
        mock_fineos_s3_bucket,
        f"{s3_prefix}2020-11-21/vpeipaymentdetails.csv.zip",
        "vpei_payment_details.csv",
    )
    make_s3_zip_file(
        mock_fineos_s3_bucket, "DT2/vpeiclaimdetails.csv.zip", "vpei_claim_details.csv"
    )
    make_s3_zip_file(mock_fineos_s3_bucket, "LeavePlan_info.csv.zip", "leave_plan.csv")
    make_s3_zip_file(
        mock_fineos_s3_bucket, "IDT/dataexports/VBI_PERSON_SOM_ALL.csv.zip", "vbi_person_som.csv"
    )

    pei_data = exporter.copy_fineos_data_to_archival_bucket()
    expected_prefix = f"s3://{mock_s3_bucket}/cps/inbound/received/"
    assert pei_data["vpei.csv.zip"] == f"{expected_prefix}vpei.csv.zip"
    assert pei_data["vpeipaymentdetails.csv.zip"] == f"{expected_prefix}vpeipaymentdetails.csv.zip"
    assert pei_data["vpeiclaimdetails.csv.zip"] == f"{expected_prefix}vpeiclaimdetails.csv.zip"
    assert pei_data["LeavePlan_info.csv.zip"] == f"{expected_prefix}LeavePlan_info.csv.zip"
    assert pei_data["VBI_PERSON_SOM_ALL.csv.zip"] == f"{expected_prefix}VBI_PERSON_SOM_ALL.csv.zip"


def test_copy_fineos_data_to_archival_bucket_duplicate_suffix_error(
    mock_fineos_s3_bucket, mock_s3_bucket, set_exporter_env_vars
):
    s3_prefix = "DT2/dataexports/"
    # Add the 5 expected files
    make_s3_zip_file(mock_fineos_s3_bucket, f"{s3_prefix}vpei.csv.zip", "vpei.csv")
    make_s3_zip_file(
        mock_fineos_s3_bucket, f"{s3_prefix}vpeipaymentdetails.csv.zip", "vpei_payment_details.csv",
    )
    make_s3_zip_file(
        mock_fineos_s3_bucket, f"{s3_prefix}vpeiclaimdetails.csv.zip", "vpei_claim_details.csv"
    )
    make_s3_zip_file(mock_fineos_s3_bucket, f"{s3_prefix}LeavePlan_info.csv.zip", "leave_plan.csv")
    make_s3_zip_file(
        mock_fineos_s3_bucket, f"{s3_prefix}VBI_PERSON_SOM_ALL.csv.zip", "vbi_person_som.csv"
    )

    # Add an extra vpei.csv file in the same folder
    make_s3_zip_file(mock_fineos_s3_bucket, f"{s3_prefix}ANOTHER-vpei.csv.zip", "vpei.csv")

    with pytest.raises(
        Exception,
        match="Duplicate files found for vpei.csv.zip: s3://test_bucket/cps/inbound/received/ANOTHER-vpei.csv.zip and s3://fineos_bucket/DT2/dataexports/vpei.csv.zip",
    ):
        exporter.copy_fineos_data_to_archival_bucket()


def test_copy_fineos_data_to_archival_bucket_missing_file_error(
    mock_fineos_s3_bucket, mock_s3_bucket, set_exporter_env_vars
):
    s3_prefix = "DT2/dataexports/"
    # Add only one file
    make_s3_zip_file(mock_fineos_s3_bucket, f"{s3_prefix}vpei.csv.zip", "vpei.csv")

    with pytest.raises(
        Exception,
        match="The following files were not found in S3 vpeipaymentdetails.csv.zip,vpeiclaimdetails.csv.zip,LeavePlan_info.csv.zip,VBI_PERSON_SOM_ALL.csv.zip",
    ):
        exporter.copy_fineos_data_to_archival_bucket()


def test_download_and_parse_data(mock_s3_bucket, tmp_path):
    make_s3_zip_file(mock_s3_bucket, "path/to/file/test.csv.zip", "small.csv")

    raw_data = exporter.download_and_parse_data(
        f"s3://{mock_s3_bucket}/path/to/file/test.csv.zip", tmp_path
    )

    # First verify the file was downloaded and named right
    downloaded_files = file_util.list_files(str(tmp_path))
    assert set(downloaded_files) == set(["test.csv.zip"])

    # Verify that it was parsed properly and handles new lines in a data column
    assert len(raw_data) == 2
    assert raw_data[0] == {
        "ColumnA": "Data1a",
        "ColumnB": "Data1b",
        "ColumnC": "Data\n1\nc",
        "ColumnD": "Data1d",
    }

    assert raw_data[1] == {
        "ColumnA": "",
        "ColumnB": "",
        "ColumnC": "",
        "ColumnD": "",
    }
