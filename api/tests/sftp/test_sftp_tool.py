import os.path

import pytest

import massgov.pfml.util.files as file_util
from massgov.pfml.sftp.utility import run_tool

SFTP_DEST_PATH = "sftp://dest/from"


@pytest.fixture
def create_mock_sftp_files(monkeypatch, mock_sftp_client, setup_mock_sftp_client):
    monkeypatch.setenv("SFTP_URI", "sftp://sftp_uri")
    monkeypatch.setenv("SFTP_SSH_KEY", "abcd1234")
    test_file_path = os.path.join(os.path.dirname(__file__), "test_files")
    mock_sftp_client.put(test_file_path, f"{SFTP_DEST_PATH}", confirm=False)


@pytest.fixture
def create_mock_s3_files(mock_s3_bucket):
    test_file_path = os.path.join(os.path.dirname(__file__), "test_files", "test_file.csv")
    file_util.upload_to_s3(test_file_path, f"s3://{mock_s3_bucket}/test_file.csv")


def test_validation_exclusivity(mock_sftp_client):
    with pytest.raises(RuntimeError, match=r"Only one of the following can be specified.*"):
        run_tool(mock_sftp_client, ["--list", "s3://some-bucket", "--copy", "s3://some-bucket"])


def test_validation_copy_to(mock_sftp_client):
    with pytest.raises(RuntimeError, match="Must specify --to with --copy"):
        run_tool(mock_sftp_client, ["--copy", "s3://some-bucket"])

    with pytest.raises(RuntimeError, match="Must specify --to with --copy"):
        run_tool(mock_sftp_client, ["--to", "s3://some-bucket"])


def test_validation_copy_dir_to_dir(mock_sftp_client):
    with pytest.raises(RuntimeError, match="Must specify --to_dir with --copy_dir"):
        run_tool(mock_sftp_client, ["--copy_dir", "s3://some-bucket/"])

    with pytest.raises(RuntimeError, match="Must specify --to_dir with --copy_dir"):
        run_tool(mock_sftp_client, ["--to_dir", "s3://some-bucket/"])


def test_list_contents(mock_sftp_client, create_mock_sftp_files):
    _, files = run_tool(mock_sftp_client, ["--list", SFTP_DEST_PATH])
    assert len(files) == 1

    with pytest.raises(RuntimeError, match="Unsupported feature: Listing S3 bucket contents"):
        run_tool(mock_sftp_client, ["--list", "s3://something"])


def test_copy_one_s3_to_s3_unsupported(mock_sftp_client):
    with pytest.raises(RuntimeError, match="Unsupported feature: Copying/moving from s3 to s3"):
        run_tool(mock_sftp_client, ["--copy", "s3://from", "--to", "s3://to"])


def test_copy_dir_s3_to_s3_unsupported(mock_sftp_client):
    with pytest.raises(RuntimeError, match="Unsupported feature: Copying/moving from s3 to s3"):
        run_tool(mock_sftp_client, ["--copy_dir", "s3://from", "--to_dir", "s3://to"])


def test_rename_one_sftp(mock_sftp_client, create_mock_sftp_files):
    from_path = f"{SFTP_DEST_PATH}/test_file.csv"
    renamed_file = "renamed_file.csv"
    to_path = f"{SFTP_DEST_PATH}/{renamed_file}"

    run_tool(mock_sftp_client, ["--rename", from_path, "--to", to_path])

    _, files2 = run_tool(mock_sftp_client, ["--list", SFTP_DEST_PATH])
    assert len(files2) == 1
    assert renamed_file in files2


def test_rename_dir_sftp(mock_sftp_client, create_mock_sftp_files):
    to_path = "sftp://dest/renamed"

    run_tool(mock_sftp_client, ["--rename", SFTP_DEST_PATH, "--to", to_path])

    _, files = run_tool(mock_sftp_client, ["--list", to_path])
    assert len(files) == 1
    assert "test_file.csv" in files


def test_copy_one_sftp_to_sftp(mock_sftp_client, create_mock_sftp_files):
    from_path = f"{SFTP_DEST_PATH}/test_file.csv"
    renamed_file = "renamed_file.csv"
    to_path = f"{SFTP_DEST_PATH}/{renamed_file}"

    run_tool(mock_sftp_client, ["--copy", from_path, "--to", to_path])

    _, files2 = run_tool(mock_sftp_client, ["--list", SFTP_DEST_PATH])
    assert len(files2) == 2
    assert renamed_file in files2
    assert "test_file.csv" in files2


def test_copy_one_s3_to_sftp(mock_sftp_client, mock_s3_bucket, create_mock_s3_files):
    s3_path = f"s3://{mock_s3_bucket}"
    from_path = f"{s3_path}/test_file.csv"
    to_path = f"{SFTP_DEST_PATH}/target.csv"

    run_tool(mock_sftp_client, ["--copy", from_path, "--to", to_path])

    _, files2 = run_tool(mock_sftp_client, ["--list", SFTP_DEST_PATH])
    assert len(files2) == 1
    assert "target.csv" in files2


def test_copy_one_sftp_to_s3(mock_sftp_client, mock_s3_bucket, create_mock_sftp_files):
    s3_path = f"s3://{mock_s3_bucket}"
    from_path = f"{SFTP_DEST_PATH}/test_file.csv"
    to_path = f"{s3_path}/target.csv"

    run_tool(mock_sftp_client, ["--copy", from_path, "--to", to_path])

    files2 = file_util.list_files(s3_path)
    assert len(files2) == 1
    assert "target.csv" in files2


def test_copy_dir_sftp_to_s3(mock_sftp_client, mock_s3_bucket, create_mock_sftp_files):
    s3_path = f"s3://{mock_s3_bucket}"
    to_path = f"{s3_path}/target"

    run_tool(mock_sftp_client, ["--copy_dir", SFTP_DEST_PATH, "--to_dir", to_path])

    s3_files = file_util.list_files(to_path)
    assert len(s3_files) == 1
    assert "test_file.csv" in s3_files


def test_copy_dir_s3_to_sftp(mock_sftp_client, mock_s3_bucket, create_mock_s3_files):
    s3_path = f"s3://{mock_s3_bucket}"
    to_path = "sftp://target"

    run_tool(mock_sftp_client, ["--copy_dir", s3_path, "--to_dir", to_path])

    _, files2 = run_tool(mock_sftp_client, ["--list", to_path])
    assert len(files2) == 1
    assert "test_file.csv" in files2
