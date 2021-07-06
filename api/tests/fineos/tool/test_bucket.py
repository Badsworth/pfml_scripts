import boto3
import pytest

from massgov.pfml.fineos.tool.bucket import bucket_tool, parse_args, run_tool


@pytest.fixture
def mock_fineos_s3_bucket(mock_s3_bucket):
    """
    Creates an additional mock bucket, so we can copy between two different S3 buckets.

    This relies on the mock S3 context started in the mock_s3_bucket fixture,
    which remains open because it uses yield rather than return.
    """
    s3 = boto3.resource("s3")
    bucket_name = "fineos_bucket"
    s3.create_bucket(Bucket=bucket_name)
    yield bucket_name


def test_validation_exclusivity(mock_s3_bucket):
    with pytest.raises(RuntimeError, match=r"Only one of the following can be specified.*"):
        run_tool(["--list", "s3://some-bucket", "--copy", "s3://some-bucket"])


def test_validation_copy_to(mock_s3_bucket):
    with pytest.raises(RuntimeError, match="Must specify --to with --copy"):
        run_tool(["--copy", "s3://some-bucket"])

    with pytest.raises(RuntimeError, match="Must specify --to with --copy"):
        run_tool(["--to", "s3://some-bucket"])


def test_validation_delete_delsize(mock_s3_bucket):
    with pytest.raises(RuntimeError, match="Must specify --delsize with --delete"):
        run_tool(["--delete", "s3://some-bucket/blah.json"])

    with pytest.raises(RuntimeError, match="Must specify --delsize with --delete"):
        run_tool(["--delsize", "100"])


def test_validation_copy_dir_to_dir(mock_s3_bucket):
    with pytest.raises(RuntimeError, match="Must specify --to_dir with --copy_dir"):
        run_tool(["--copy_dir", "s3://some-bucket/"])

    with pytest.raises(RuntimeError, match="Must specify --to_dir with --copy_dir"):
        run_tool(["--to_dir", "s3://some-bucket/"])


def test_validation_archive_without_source_and_dest(mock_s3_bucket):
    with pytest.raises(
        RuntimeError, match="Must specify --archive_dir with both --copy_dir and --to_dir"
    ):
        run_tool(["--archive_dir", "s3://some-archive"])

    with pytest.raises(
        RuntimeError, match="Must specify --archive_dir with both --copy_dir and --to_dir"
    ):
        run_tool(["--archive_dir", "s3://some-archive", "--copy_dir", "s3://some-source-bucket"])

    with pytest.raises(
        RuntimeError, match="Must specify --archive_dir with both --copy_dir and --to_dir"
    ):
        run_tool(["--archive_dir", "s3://some-archive", "--to_dir", "s3://some-dest-bucket"])


def test_validation_copy_dir_opts(mock_s3_bucket):
    with pytest.raises(
        RuntimeError, match=r"The following options are only valid when using copy_dir.*"
    ):
        run_tool(["--list", "s3://something", "--recursive"])

    with pytest.raises(
        RuntimeError, match=r"The following options are only valid when using copy_dir.*"
    ):
        run_tool(["--list", "s3://something", "--dated-folders"])

    with pytest.raises(
        RuntimeError, match=r"The following options are only valid when using copy_dir.*"
    ):
        run_tool(["--list", "s3://something", "--file_prefixes", "foo"])


def create_mock_s3_files(bucket, *files):
    for key in files:
        boto3.client("s3").put_object(
            Bucket=bucket, Key=key, Body="line 1 text\nline 2 text\nline 3 text"
        )


def test_copy_default_args(mock_s3_bucket, mock_fineos_s3_bucket):
    s3 = boto3.resource("s3")

    create_mock_s3_files(
        mock_s3_bucket, "filename.txt", "filename2.txt",
    )

    run_tool(
        [
            "--copy",
            f"s3://{mock_s3_bucket}/filename.txt",
            "--to",
            f"s3://{mock_fineos_s3_bucket}/filename.txt",
        ]
    )

    # list all the objects in the mock_fineos_s3_bucket and grab the keys
    copied_items = set(map(lambda x: x.key, s3.Bucket(name=mock_fineos_s3_bucket).objects.all()))

    assert copied_items == {"filename.txt"}


def test_copy_dir(mock_s3_bucket, mock_fineos_s3_bucket):
    s3 = boto3.resource("s3")
    s3_fineos = boto3.resource("s3")

    create_mock_s3_files(
        mock_fineos_s3_bucket,
        "nested/key/in/filename.txt",
        "nested/key/in/filename2.txt",
        "filename.txt",
        "filename2.txt",
    )

    args = parse_args(
        ["--copy_dir", f"s3://{mock_fineos_s3_bucket}", "--to_dir", f"s3://{mock_s3_bucket}",]
    )

    bucket_tool(args, s3, s3_fineos, boto3, None)

    # list all the objects in the mock_s3_bucket and grab the keys
    copied_items = set(map(lambda x: x.key, s3.Bucket(name=mock_s3_bucket).objects.all()))

    assert copied_items == {"filename.txt", "filename2.txt"}


def test_copy_dir_recursive(mock_s3_bucket, mock_fineos_s3_bucket):
    s3 = boto3.resource("s3")
    s3_fineos = boto3.resource("s3")

    create_mock_s3_files(
        mock_fineos_s3_bucket,
        "nested/key/in/filename.txt",
        "nested/key/in/filename2.txt",
        "filename.txt",
        "filename2.txt",
    )

    args = parse_args(
        [
            "--copy_dir",
            f"s3://{mock_fineos_s3_bucket}",
            "--to_dir",
            f"s3://{mock_s3_bucket}",
            "--recursive",
        ]
    )

    bucket_tool(args, s3, s3_fineos, boto3, None)

    copied_items = set(map(lambda x: x.key, s3.Bucket(name=mock_s3_bucket).objects.all()))

    assert copied_items == {
        "nested/key/in/filename.txt",
        "nested/key/in/filename2.txt",
        "filename.txt",
        "filename2.txt",
    }


def test_copy_dir_dated_folders(mock_s3_bucket, mock_fineos_s3_bucket):
    s3 = boto3.resource("s3")
    s3_fineos = boto3.resource("s3")

    create_mock_s3_files(
        mock_fineos_s3_bucket,
        "2021-01-02-01-02-03/2021-01-02-01-02-03-filename.txt",
        "2021-01-02-01-02-03/2021-01-02-01-02-03-filename2.txt",
        "2021-01-03-01-02-03-filename.txt",
        "2021-01-03-01-02-03-filename2.txt",
    )

    args = parse_args(
        [
            "--copy_dir",
            f"s3://{mock_fineos_s3_bucket}",
            "--to_dir",
            f"s3://{mock_s3_bucket}",
            "--recursive",
            "--dated-folders",
        ]
    )

    bucket_tool(args, s3, s3_fineos, boto3, None)

    copied_items = set(map(lambda x: x.key, s3.Bucket(name=mock_s3_bucket).objects.all()))

    assert copied_items == {
        "2021-01-02-01-02-03/2021-01-02-01-02-03-filename.txt",
        "2021-01-02-01-02-03/2021-01-02-01-02-03-filename2.txt",
        "2021-01-03-01-02-03/2021-01-03-01-02-03-filename.txt",
        "2021-01-03-01-02-03/2021-01-03-01-02-03-filename2.txt",
    }


def test_copy_dir_dated_folders_no_date(mock_s3_bucket, mock_fineos_s3_bucket):
    s3 = boto3.resource("s3")
    s3_fineos = boto3.resource("s3")

    create_mock_s3_files(
        mock_fineos_s3_bucket, "2021-01-02-XX-XX-XX-filename.txt",
    )

    args = parse_args(
        [
            "--copy_dir",
            f"s3://{mock_fineos_s3_bucket}",
            "--to_dir",
            f"s3://{mock_s3_bucket}",
            "--recursive",
            "--dated-folders",
        ]
    )

    bucket_tool(args, s3, s3_fineos, boto3, None)

    copied_items = set(map(lambda x: x.key, s3.Bucket(name=mock_s3_bucket).objects.all()))

    assert copied_items == {
        "2021-01-02-XX-XX-XX-filename.txt",
    }


def test_copy_dir_file_prefixes(mock_s3_bucket, mock_fineos_s3_bucket):
    s3 = boto3.resource("s3")
    s3_fineos = boto3.resource("s3")

    create_mock_s3_files(
        mock_fineos_s3_bucket,
        "2021-01-02-01-02-03/2021-01-02-01-02-03-filename.txt",
        "2021-01-02-01-02-03/2021-01-02-01-02-03-filename2.txt",
        "2021-01-03-01-02-03-filename1.txt",
        "2021-01-03-01-02-03-filename2.txt",
    )

    args = parse_args(
        [
            "--copy_dir",
            f"s3://{mock_fineos_s3_bucket}",
            "--to_dir",
            f"s3://{mock_s3_bucket}",
            "--recursive",
            "--file_prefixes",
            "filename2",
        ]
    )

    bucket_tool(args, s3, s3_fineos, boto3, None)

    copied_items = set(map(lambda x: x.key, s3.Bucket(name=mock_s3_bucket).objects.all()))

    assert copied_items == {
        "2021-01-02-01-02-03/2021-01-02-01-02-03-filename2.txt",
        "2021-01-03-01-02-03-filename2.txt",
    }


def test_copy_dir_with_archival_filter(mock_s3_bucket, mock_fineos_s3_bucket):
    s3 = boto3.resource("s3")
    s3_fineos = boto3.resource("s3")

    # Create files in the source bucket that should be copied over
    create_mock_s3_files(
        mock_fineos_s3_bucket,
        "nested/key/in/filename.txt",
        "nested/key/in/filename2.txt",
        "filename.txt",
        "filename2.txt",
        "antique.txt",
        "archaic.txt",
    )

    # Create archived files in the dest bucket that should NOT be copied over
    create_mock_s3_files(mock_s3_bucket, "processed/antique.txt", "processed/archaic.txt")

    args = parse_args(
        [
            "--copy_dir",
            f"s3://{mock_fineos_s3_bucket}",
            "--to_dir",
            f"s3://{mock_s3_bucket}/received",
            "--archive_dir",
            f"s3://{mock_s3_bucket}/processed",
            "--recursive",
        ]
    )

    # Run the tool
    bucket_tool(args, s3, s3_fineos, boto3, None)

    copied_items = set(map(lambda x: x.key, s3.Bucket(name=mock_s3_bucket).objects.all()))

    assert "received/antique.txt" not in copied_items and "received/archaic.txt" not in copied_items
    assert copied_items == {
        "received/nested/key/in/filename.txt",
        "received/nested/key/in/filename2.txt",
        "received/filename.txt",
        "received/filename2.txt",
        "processed/antique.txt",
        "processed/archaic.txt",
    }


def test_copy_dir_with_empty_archival_dir(mock_s3_bucket, mock_fineos_s3_bucket):
    s3 = boto3.resource("s3")
    s3_fineos = boto3.resource("s3")

    # Create files in the source bucket that should be copied over
    create_mock_s3_files(
        mock_fineos_s3_bucket,
        "nested/key/in/filename.txt",
        "nested/key/in/filename2.txt",
        "filename.txt",
        "filename2.txt",
        "antique.txt",
        "archaic.txt",
    )

    # There are NO files in the dest bucket's archive_dir, so ALL files in the source bucket should be copied over
    args = parse_args(
        [
            "--copy_dir",
            f"s3://{mock_fineos_s3_bucket}",
            "--to_dir",
            f"s3://{mock_s3_bucket}/received",
            "--archive_dir",
            f"s3://{mock_s3_bucket}/processed",
            "--recursive",
        ]
    )

    # Run the tool
    bucket_tool(args, s3, s3_fineos, boto3, None)

    copied_items = set(map(lambda x: x.key, s3.Bucket(name=mock_s3_bucket).objects.all()))
    assert copied_items == {
        "received/nested/key/in/filename.txt",
        "received/nested/key/in/filename2.txt",
        "received/filename.txt",
        "received/filename2.txt",
        "received/antique.txt",
        "received/archaic.txt",
    }
