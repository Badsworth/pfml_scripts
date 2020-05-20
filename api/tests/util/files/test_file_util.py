import boto3

import massgov.pfml.util.files as file_util


def test_is_s3_path():
    assert file_util.is_s3_path("s3://bucket/folder/test.txt") is True
    assert file_util.is_s3_path("./relative/folder/test.txt") is False
    assert file_util.is_s3_path("http://example.com/test.txt") is False


def test_get_file_name(test_fs_path):
    file_name = "test.txt"
    full_path = "{}/{}".format(test_fs_path, file_name)
    file_name = file_util.get_file_name(full_path)
    assert file_name == "test.txt"


def test_read_fs_file(test_fs_path):
    file_name = "test.txt"
    full_path = "{}/{}".format(str(test_fs_path), file_name)
    # because function returns a map object instead of a list, must cast to list
    lines = list(file_util.read_file_lines(full_path))
    assert lines[0] == "line 1 text"
    assert lines[1] == "line 2 text"
    assert lines[2] == "line 3 text"


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
