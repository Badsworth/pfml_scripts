#
# Utilities for handling files.
#

import io
import os
import shutil
import tempfile
from typing import List, Optional
from urllib.parse import urlparse

import boto3
import ebcdic  # noqa: F401
import paramiko
import smart_open
from botocore.config import Config

EBCDIC_ENCODING = "cp1140"  # See https://pypi.org/project/ebcdic/ for further details


def is_s3_path(path):
    return path.startswith("s3://")


def is_sftp_path(path):
    return path.startswith("sftp://")


def get_s3_bucket(path):
    return urlparse(path).hostname


def get_s3_file_key(path):
    return urlparse(path).path[1:]


def get_file_name(path: str) -> str:
    # TODO when the DOR importer is updated to use the file system in upcoming tickets,
    # this function should replace get_file_name() that exists there
    return os.path.basename(path)


def get_directory(path: str) -> str:
    # This handles getting the "directory" of any path (local or S3)
    # Grab everything in the path except the last X characters
    # where X is the length of the file name
    # This preserves the trailing /
    return path[: -len(get_file_name(path))]


def split_s3_url(path):
    parts = urlparse(path)
    bucket_name = parts.netloc
    prefix = parts.path.lstrip("/")
    return (bucket_name, prefix)


# "sftp://test_user@example.com:2222/" -> ("test_user", "example.com", 2222)
def split_sftp_url(path):
    parts = urlparse(path)
    return (parts.username or "", parts.hostname, parts.port or 22)


def list_files(
    path: str, delimiter: str = "/", boto_session: Optional[boto3.Session] = None
) -> List[str]:
    """List the immediate files under path.

    There is minor inconsistency between local path handling and S3 paths.
    Directory names will be included for local paths, whereas they will not for
    S3 paths.

    Also, for S3 paths, only the first 1000 files will be returned.

    Args:
        path: Supports s3:// and local paths.
        delimiter: Only applicable for S3 paths.

            If set to "" will list all keys under path, but note only the
            basename of the key will be included, so any directory structure to
            the key will be lost. You probably do not want to use this for
            getting all keys in a bucket.
        boto_session: Boto session object to use for S3 access. Only necessary
            if needing to access an S3 bucket with assumed credentials (e.g.,
            cross-account bucket access).
    """
    if is_s3_path(path):
        bucket_name, prefix = split_s3_url(path)

        # TODO Use boto3 for now to address multithreading issue in lambda, revisit after pilot 2
        # https://github.com/RaRe-Technologies/smart_open/issues/340
        # for key, _content in smart_open.s3_iter_bucket(bucket_name, prefix=prefix, workers=1):
        #     files.append(get_file_name(key))

        # in order for s3.list_objects to only list the immediate "files" under
        # the given path, the prefix should end in the path delimiter
        if prefix and not prefix.endswith(delimiter):
            prefix = prefix + delimiter

        s3 = boto_session.client("s3") if boto_session else boto3.client("s3")

        object_contents = s3.list_objects_v2(
            Bucket=bucket_name, Prefix=prefix, Delimiter=delimiter
        ).get("Contents")

        if object_contents:
            return [get_file_name(object["Key"]) for object in object_contents]

        return []

    return os.listdir(path)


def copy_file(source, destination):
    is_source_s3 = is_s3_path(source)
    is_dest_s3 = is_s3_path(destination)

    # This isn't a download or upload method
    # Don't allow "copying" between mismatched locations
    if is_source_s3 != is_dest_s3:
        raise Exception("Cannot download/upload between disk and S3 using this method")

    if is_source_s3:
        source_bucket, source_path = split_s3_url(source)
        dest_bucket, dest_path = split_s3_url(destination)

        # TODO - might need to do something with credentials here
        s3 = boto3.client("s3")
        copy_source = {"Bucket": source_bucket, "Key": source_path}
        s3.copy(copy_source, dest_bucket, dest_path)
    else:
        shutil.copy2(source, destination)


def copy_s3_files(source, destination, expected_file_names, delimeter="/"):
    s3_objects = list_files(source, delimeter)

    # A dictionary of mapping from expected file names to the new S3 location
    file_mapping = dict.fromkeys(expected_file_names, "")

    for s3_object in s3_objects:
        for expected_file_name in expected_file_names:
            # The objects will be just the file name
            # eg. a file at s3://bucket/path/to/2020-01-01-file.csv.zip
            # would be named 2020-01-01-file.csv.zip here
            if s3_object.endswith(expected_file_name):
                source_file = os.path.join(source, s3_object)
                dest_file = os.path.join(destination, s3_object)

                # We found two files which end the same, error
                if file_mapping.get(expected_file_name):
                    raise RuntimeError(
                        f"Duplicate files found for {expected_file_name}: {file_mapping.get(expected_file_name)} and {source_file}"
                    )

                copy_file(source_file, dest_file)
                file_mapping[expected_file_name] = dest_file

    missing_files = []
    for expected_file_name, destination in file_mapping.items():
        if not destination:
            missing_files.append(expected_file_name)

    if missing_files:
        raise Exception(f"The following files were not found in S3 {','.join(missing_files)}")

    return file_mapping


def delete_file(path):
    if is_s3_path(path):
        bucket, s3_path = split_s3_url(path)

        s3 = boto3.client("s3")
        s3.delete_object(Bucket=bucket, Key=s3_path)
    else:
        os.remove(path)


def rename_file(source, destination):
    is_source_s3 = is_s3_path(source)
    is_dest_s3 = is_s3_path(destination)

    # This isn't a download or upload method
    # Don't allow "copying" between mismatched locations
    if is_source_s3 != is_dest_s3:
        raise Exception("Cannot download/upload between disk and S3 using this method")

    if is_source_s3:
        # S3 doesn't have any actual rename process, need to copy and delete the old
        copy_file(source, destination)
        delete_file(source)
    else:
        os.rename(source, destination)


def download_from_s3(source, destination):
    is_source_s3 = is_s3_path(source)
    is_dest_s3 = is_s3_path(destination)

    if not is_source_s3 or is_dest_s3:
        raise Exception("Source must be an S3 URI and destination must not be")

    bucket, path = split_s3_url(source)

    s3 = boto3.client("s3")
    s3.download_file(bucket, path, destination)


def open_stream(path, mode="r"):
    if is_s3_path(path):
        so_config = Config(
            max_pool_connections=10,
            connect_timeout=14400,
            read_timeout=14400,
            retries={"max_attempts": 10},
        )
        so_transport_params = {"resource_kwargs": {"config": so_config}}

        return smart_open.open(path, mode, transport_params=so_transport_params)
    else:
        return smart_open.open(path, mode)


def read_file(path, mode="r", encoding=None):
    return smart_open.open(path, mode, encoding=encoding).read()


def write_file(path, mode="w", encoding=None):
    return smart_open.open(path, mode, encoding=encoding)


def read_file_lines(path, mode="r", encoding=None):
    stream = smart_open.open(path, mode, encoding=encoding)
    return map(lambda line: line.rstrip(), stream)


def get_sftp_client(uri: str, ssh_key_password: str, ssh_key: str) -> paramiko.SFTPClient:
    if not is_sftp_path(uri):
        raise ValueError("uri must be an SFTP URI")

    # Paramiko expects to receive the private key as a file-like object so we write the string
    # to a StringIO object.
    # https://docs.paramiko.org/en/stable/api/keys.html#paramiko.pkey.PKey.from_private_key
    ssh_key_fileobj = io.StringIO(ssh_key)
    pkey = paramiko.rsakey.RSAKey.from_private_key(ssh_key_fileobj, password=ssh_key_password)

    user, host, port = split_sftp_url(uri)
    t = paramiko.Transport((host, port))
    t.connect(username=user, pkey=pkey)

    return paramiko.SFTPClient.from_transport(t)


def copy_file_from_s3_to_sftp(source: str, dest: str, sftp: paramiko.SFTPClient) -> None:
    if not is_s3_path(source):
        raise ValueError("source must be an S3 URI")

    # Download file from S3 to a tempfile.
    _handle, tempfile_path = tempfile.mkstemp()
    download_from_s3(source, tempfile_path)

    # Copy the file from local tempfile to destination.
    sftp.put(tempfile_path, dest)


def remove_if_exists(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
