#
# Tests for massgov.pfml.dor.importer.paths.
#

import boto3

import massgov.pfml.dor.importer.paths
from massgov.pfml.dor.importer.paths import ImportBatch


def test_get_files_for_import_grouped_by_date(tmp_path, mock_s3_bucket):
    # test file system paths
    (tmp_path / "extra_file").touch()
    (tmp_path / "DORDFMLEMP_20200518155555").touch()
    (tmp_path / "DORDFML_20200518155555").touch()
    (tmp_path / "DORDFMLEMP_20200519133333").touch()
    (tmp_path / "DORDFML_20200519133333").touch()
    (tmp_path / "DORDFML_20201001133333").touch()
    files_by_date = massgov.pfml.dor.importer.paths.get_files_for_import_grouped_by_date(
        str(tmp_path)
    )
    assert files_by_date == {
        "20200518155555": {
            "DORDFMLEMP_": str(tmp_path / "DORDFMLEMP_20200518155555"),
            "DORDFML_": str(tmp_path / "DORDFML_20200518155555"),
        },
        "20200519133333": {
            "DORDFMLEMP_": str(tmp_path / "DORDFMLEMP_20200519133333"),
            "DORDFML_": str(tmp_path / "DORDFML_20200519133333"),
        },
        "20201001133333": {"DORDFML_": str(tmp_path / "DORDFML_20201001133333")},
    }


def test_get_files_for_import_grouped_by_date_s3(mock_s3_bucket):
    # test s3 paths
    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key="extra_file", Body="")
    s3.put_object(Bucket=mock_s3_bucket, Key="DORDFMLEMP_20200519133333", Body="")
    s3.put_object(Bucket=mock_s3_bucket, Key="DORDFML_20200519133333", Body="")
    s3.put_object(Bucket=mock_s3_bucket, Key="DORDFML_20201001133333", Body="")
    s3.put_object(Bucket=mock_s3_bucket, Key="DORDFMLEMP_20200518155555", Body="")
    s3.put_object(Bucket=mock_s3_bucket, Key="DORDFML_20200518155555", Body="")

    files_by_date = massgov.pfml.dor.importer.paths.get_files_for_import_grouped_by_date(
        f"s3://{mock_s3_bucket}"
    )
    s3_prefix = f"s3://{mock_s3_bucket}"

    assert files_by_date == {
        "20200518155555": {
            "DORDFMLEMP_": f"{s3_prefix}/DORDFMLEMP_20200518155555",
            "DORDFML_": f"{s3_prefix}/DORDFML_20200518155555",
        },
        "20200519133333": {
            "DORDFMLEMP_": f"{s3_prefix}/DORDFMLEMP_20200519133333",
            "DORDFML_": f"{s3_prefix}/DORDFML_20200519133333",
        },
        "20201001133333": {"DORDFML_": f"{s3_prefix}/DORDFML_20201001133333"},
    }


def test_get_files_for_import(mock_s3_bucket):
    # test s3 paths
    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key="extra_file", Body="")
    s3.put_object(Bucket=mock_s3_bucket, Key="DORDFMLEMP_20200519133333", Body="")
    s3.put_object(Bucket=mock_s3_bucket, Key="DORDFML_20200519133333", Body="")
    s3.put_object(Bucket=mock_s3_bucket, Key="DORDFML_20201001133333", Body="")
    s3.put_object(Bucket=mock_s3_bucket, Key="DORDFMLEMP_20200518155555", Body="")
    s3.put_object(Bucket=mock_s3_bucket, Key="DORDFML_20200518155555", Body="")

    files_by_date = massgov.pfml.dor.importer.paths.get_files_to_process(f"s3://{mock_s3_bucket}")

    batches = []
    batches.append(
        ImportBatch(
            upload_date="20200518155555",
            employer_file="{}/{}".format(f"s3://{mock_s3_bucket}", "DORDFMLEMP_20200518155555"),
            employee_file="",
        )
    )
    batches.append(
        ImportBatch(
            upload_date="20200519133333",
            employer_file="{}/{}".format(f"s3://{mock_s3_bucket}", "DORDFMLEMP_20200519133333"),
            employee_file="",
        )
    )
    batches.append(
        ImportBatch(
            upload_date="20200518155555",
            employer_file="",
            employee_file="{}/{}".format(f"s3://{mock_s3_bucket}", "DORDFML_20200518155555"),
        )
    )
    batches.append(
        ImportBatch(
            upload_date="20200519133333",
            employer_file="",
            employee_file="{}/{}".format(f"s3://{mock_s3_bucket}", "DORDFML_20200519133333"),
        )
    )
    batches.append(
        ImportBatch(
            upload_date="20201001133333",
            employer_file="",
            employee_file="{}/{}".format(f"s3://{mock_s3_bucket}", "DORDFML_20201001133333"),
        )
    )

    assert files_by_date == batches
