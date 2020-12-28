import os

import boto3
import pytest

import massgov.pfml.util.files as file_util


def test_is_s3_path():
    assert file_util.is_s3_path("s3://bucket/folder/test.txt") is True
    assert file_util.is_s3_path("./relative/folder/test.txt") is False
    assert file_util.is_s3_path("http://example.com/test.txt") is False


@pytest.mark.parametrize(
    "path,result",
    (
        ("sftp://host/path/file", True),
        ("sftp://username@host/path/file", True),
        ("ssh://username@host/path/file", False),
        ("http://example.com/test.txt", False),
        ("s3://my_bucket/path/to/file.txt", False),
    ),
)
def test_is_sftp_path(path, result):
    assert file_util.is_sftp_path(path) is result


def test_get_file_name(test_fs_path):
    file_name = "test.txt"
    full_path = "{}/{}".format(test_fs_path, file_name)
    file_name = file_util.get_file_name(full_path)
    assert file_name == "test.txt"


@pytest.mark.parametrize(
    "path,bucket,prefix",
    (
        ("s3://my_bucket/my_key", "my_bucket", "my_key"),
        ("s3://my_bucket/path/to/directory/", "my_bucket", "path/to/directory/"),
        ("s3://my_bucket/path/to/file.txt", "my_bucket", "path/to/file.txt"),
    ),
)
def test_split_s3_url(path, bucket, prefix):
    assert file_util.split_s3_url(path) == (bucket, prefix)


@pytest.mark.parametrize(
    "path,user,host,port",
    (
        ("sftp://host/path/file", "", "host", 22),
        ("sftp://username@host:2345/path/file", "username", "host", 2345),
        ("sftp://username@host/path/file", "username", "host", 22),
        ("sftp://example.com/test.txt", "", "example.com", 22),
    ),
)
def test_split_sftp_url(path, user, host, port):
    assert file_util.split_sftp_url(path) == (user, host, port)


def test_get_directory():
    assert file_util.get_directory("s3://bucket/path/to/file.txt") == "s3://bucket/path/to/"
    assert file_util.get_directory("./relative/path/to/file.txt") == "./relative/path/to/"
    assert (
        file_util.get_directory("http://example.com/path/to/file.txt")
        == "http://example.com/path/to/"
    )


def test_read_fs_file(test_fs_path):
    file_name = "test.txt"
    full_path = "{}/{}".format(str(test_fs_path), file_name)
    # because function returns a map object instead of a list, must cast to list
    lines = list(file_util.read_file_lines(full_path))
    assert lines[0] == "line 1 text"
    assert lines[1] == "line 2 text"
    assert lines[2] == "line 3 text"


def test_copy_file_from_s3_to_sftp(mock_s3_bucket, mock_sftp_client):
    folder = "path/to/my_directory"
    file_name = "my_file.txt"
    key = "{}/{}".format(folder, file_name)

    # Put file in our mocked S3.
    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key=key, Body="line 1 text\nline 2 text\nline 3 text")

    source = "s3://{}/{}".format(mock_s3_bucket, key)
    dest = "sftp://example.com/incoming/{}".format(key)

    file_util.copy_file_from_s3_to_sftp(source, dest, mock_sftp_client)

    # Expect to make one call to the SFTP client to upload a tempfile to our dest.
    assert len(mock_sftp_client.calls) == 1
    assert mock_sftp_client.calls[0][0] == "put"
    assert mock_sftp_client.calls[0][2] == dest


def test_copy_file_from_sftp_to_s3(mock_s3_bucket, mock_sftp_client):
    source_dir = "agency/outbox"
    dest_dir = "pfml/inbox"
    filename = "my_test_file.csv"

    dest_filepath = os.path.join(dest_dir, filename)
    dest = os.path.join("s3://" + mock_s3_bucket, dest_filepath)

    source = os.path.join(source_dir, filename)
    file_util.copy_file_from_sftp_to_s3(source, dest, mock_sftp_client)

    # Expect to make one call to the SFTP client to download the source file.
    assert len(mock_sftp_client.calls) == 1
    assert mock_sftp_client.calls[0][0] == "get"
    assert mock_sftp_client.calls[0][1] == source

    # Expect that the file to appear in the mock_s3_bucket.
    s3 = boto3.client("s3")
    object_list = s3.list_objects(Bucket=mock_s3_bucket, Prefix=dest_dir)["Contents"]
    assert object_list
    if object_list:
        assert len(object_list) == 1
        assert object_list[0]["Key"] == dest_filepath


def test_read_s3_stream(mock_s3_bucket):
    # path variables
    folder_name = "test_folder"
    file_name = "test.txt"
    key = "{}/{}".format(folder_name, file_name)
    full_path = "s3://{}/{}".format(mock_s3_bucket, key)

    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key=key, Body="line 1 text\nline 2 text\nline 3 text")
    # because function returns a map object instead of a list, must cast to list
    file_stream = file_util.open_stream(full_path)

    line_count = 0

    for line in file_stream:
        line_count += 1
        if line_count == 1:
            assert line == "line 1 text\n"
        if line_count == 2:
            assert line == "line 2 text\n"
        if line_count == 3:
            assert line == "line 3 text"


def test_read_s3_file(mock_s3_bucket):
    # path variables
    folder_name = "test_folder"
    file_name = "test.txt"
    key = "{}/{}".format(folder_name, file_name)
    full_path = "s3://{}/{}".format(mock_s3_bucket, key)

    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key=key, Body="line 1 text\nline 2 text\nline 3 text")
    # because function returns a map object instead of a list, must cast to list
    lines = list(file_util.read_file_lines(full_path))
    assert lines[0] == "line 1 text"
    assert lines[1] == "line 2 text"
    assert lines[2] == "line 3 text"


def test_list_files_in_folder_fs(test_fs_path):
    files = file_util.list_files(str(test_fs_path))
    assert files == ["test.txt"]


def test_list_files_in_folder_s3(mock_s3_bucket):
    # path variables
    folder_name = "test_folder"
    file_name = "test.txt"
    key = "{}/{}".format(folder_name, file_name)

    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key=key, Body="test")
    folder_path = "s3://{}/{}".format(mock_s3_bucket, folder_name)
    files = file_util.list_files(folder_path)
    assert files == [file_name]


def test_list_files_in_folder_s3_does_not_recurse_by_default(mock_s3_bucket):
    # path variables
    folder_name = "test_folder"
    file_name = "test.txt"
    key = "{}/{}".format(folder_name, file_name)

    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key=key, Body="test")

    # add "empty" "sub directory"
    s3.put_object(Bucket=mock_s3_bucket, Key=f"{folder_name}/foo/", Body="test")

    # add "sub directory" with a file
    s3.put_object(Bucket=mock_s3_bucket, Key=f"{folder_name}/bar/baz.txt", Body="test")

    # we should only see the test.txt file immediately inside test_folder
    folder_path = "s3://{}/{}".format(mock_s3_bucket, folder_name)
    files = file_util.list_files(folder_path)
    assert files == [file_name]

    # but if passed "" as delimiter for S3, returns list of all file basenames
    # under path recursively, note that folder names come through as ""
    files = file_util.list_files(folder_path, delimiter="")
    assert files == ["baz.txt", "", file_name]


def test_list_files_in_folder_s3_empty(mock_s3_bucket):
    files = file_util.list_files(f"s3://{mock_s3_bucket}")
    assert files == []


def test_list_files_without_folder_s3(mock_s3_bucket):
    # path variables
    folder_name = "test_folder"
    file_name = "test.txt"
    key = "{}/{}".format(folder_name, file_name)

    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key=key, Body="test")

    # add "empty" "sub directory"
    s3.put_object(Bucket=mock_s3_bucket, Key=f"{folder_name}/foo/", Body="test")

    # add "sub directory" with a file
    s3.put_object(Bucket=mock_s3_bucket, Key=f"{folder_name}/bar/baz.txt", Body="test")

    # we should only see the test.txt file immediately inside test_folder
    folder_path = "s3://{}/{}".format(mock_s3_bucket, folder_name)

    # but if passed "" as delimiter for S3, returns list of all file basenames
    # under path recursively, note that folder names come through as ""
    files = file_util.list_files_without_folder(folder_path, delimiter="")
    assert files == ["baz.txt", file_name]


def test_list_s3_files_and_directories_by_level(mock_s3_bucket):
    source_folder = "agency/outbound/ready"

    expected_response = {
        "a-stellar-testfile.txt": ["a-stellar-testfile.txt"],
        "a-subfolder": ["a-subfolder/my-file.txt", "a-subfolder/second-file.txt"],
    }

    s3 = boto3.client("s3")
    for files in expected_response.values():
        for key in files:
            s3.put_object(Bucket=mock_s3_bucket, Key=f"{source_folder}/{key}", Body="test")

    path = f"s3://{mock_s3_bucket}/{source_folder}"
    files_by_level = file_util.list_s3_files_and_directories_by_level(path)
    assert expected_response == files_by_level


def test_copy_file_s3(mock_s3_bucket):
    # source variables
    source_folder_name = "test_folder"
    source_file_name = "test.txt"
    source_key = "{}/{}".format(source_folder_name, source_file_name)

    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key=source_key, Body="line1\nline2")
    source_path = f"s3://{mock_s3_bucket}/{source_key}"

    # Dest variables
    dest_folder_name = "another_folder"
    dest_file_name = "other.txt"
    dest_key = "{}/{}".format(dest_folder_name, dest_file_name)
    dest_path = f"s3://{mock_s3_bucket}/{dest_key}"

    file_util.copy_file(source_path, dest_path)

    # Verify we can then fetch the file
    lines = list(file_util.read_file_lines(dest_path))
    assert lines[0] == "line1"
    assert lines[1] == "line2"


def test_rename_file_s3(mock_s3_bucket):
    # source variables
    source_folder_name = "test_folder"
    source_file_name = "test.txt"
    source_key = "{}/{}".format(source_folder_name, source_file_name)

    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key=source_key, Body="line1\nline2")
    source_path = f"s3://{mock_s3_bucket}/{source_key}"

    # Dest variables
    dest_folder_name = "another_folder"
    dest_file_name = "other.txt"
    dest_key = "{}/{}".format(dest_folder_name, dest_file_name)
    dest_path = f"s3://{mock_s3_bucket}/{dest_key}"

    file_util.rename_file(source_path, dest_path)

    # Verify we can then fetch the file
    lines = list(file_util.read_file_lines(dest_path))
    assert lines[0] == "line1"
    assert lines[1] == "line2"

    # Verify the original isn't present:
    with pytest.raises(OSError, match=r"NoSuchKey"):
        file_util.read_file_lines(source_path)


def test_ebcdic_encoding(test_fs_path):
    # This test is here as an example for future usage of ebcdic encoding
    # + verification that this works with our existing file utilities.
    file_name = "test.txt"
    full_path = "{}/{}".format(str(test_fs_path), file_name)
    test_file = file_util.write_file(full_path, encoding=file_util.EBCDIC_ENCODING)

    line1 = "hello,world\n"
    line2 = "hello world"

    test_file.writelines([line1, line2])
    test_file.close()

    # Read the file as bytes to validate it is encoded properly.
    lines = list(file_util.read_file_lines(full_path, mode="rb"))
    assert (
        lines[0]
        == b"\x88\x85\x93\x93\x96k\xa6\x96\x99\x93\x84%\x88\x85\x93\x93\x96@\xa6\x96\x99\x93\x84"
    )

    # Read the file using the encoding to validate text is the same.
    lines = list(file_util.read_file_lines(full_path, encoding=file_util.EBCDIC_ENCODING))
    assert lines[0] == line1.rstrip()  # read_file_lines does an rstrip itself which removes the \n.
    assert lines[1] == line2


def test_remove_if_exists_when_exists(tmp_path):
    test_file_that_exists = tmp_path / "test.txt"
    test_file_that_exists.write_text("foo")

    assert os.path.exists(test_file_that_exists) is True

    file_util.remove_if_exists(test_file_that_exists)

    assert os.path.exists(test_file_that_exists) is False


def test_remove_if_exists_when_not_exists():
    test_file_that_does_not_exist = "./foobar/test.txt"

    assert os.path.exists(test_file_that_does_not_exist) is False

    file_util.remove_if_exists(test_file_that_does_not_exist)

    assert os.path.exists(test_file_that_does_not_exist) is False
