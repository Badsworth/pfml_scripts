#
# Utilities for handling files.
#

import csv
import io
import os
import pathlib
import shutil
import tempfile
from typing import Dict, Iterable, List, Optional
from urllib.parse import urlparse

import boto3
import botocore
import ebcdic  # noqa: F401
import paramiko
import smart_open
from botocore.config import Config

import massgov.pfml.util.aws.sts as aws_sts
import massgov.pfml.util.logging as logging

logger = logging.get_logger(__name__)

EBCDIC_ENCODING = "cp1140"  # See https://pypi.org/project/ebcdic/ for further details
FINEOS_BUCKET_PREFIX = "fin-som"


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


def get_s3_client(
    bucket_name: str, boto_session: Optional[boto3.Session] = None
) -> botocore.client.BaseClient:
    """Returns the appropriate S3 client for a given bucket
    """
    if boto_session:
        return boto_session.client("s3")
    elif bucket_name.startswith(FINEOS_BUCKET_PREFIX):
        # This should get passed in from the method but getting it
        # directly from the environment due to time constraints.
        fineos_boto_session = aws_sts.assume_session(
            role_arn=os.environ["FINEOS_AWS_IAM_ROLE_ARN"],
            external_id=os.environ["FINEOS_AWS_IAM_ROLE_EXTERNAL_ID"],
            role_session_name="payments_copy_file",
            region_name="us-east-1",
        )
        return fineos_boto_session.client("s3")
    else:
        return boto3.client("s3")


def list_folders(folder_path: str, boto_session: Optional[boto3.Session] = None) -> List[str]:
    """List immediate subfolders under folder path.
    Returns a list of subfolders names (maximum of 1000).
    Args:
        folder_path: path to a folder.
            If S3 this may be a folder under the bucket or just a path to the bucket.
        boto_session: Boto session object to use for S3 access. Only necessary
            if needing to access an S3 bucket with assumed credentials (e.g.,
            cross-account bucket access).
    """
    if is_s3_path(folder_path):
        bucket_name, prefix = split_s3_url(folder_path)

        if prefix and not prefix.endswith("/"):
            prefix = prefix + "/"

        s3 = get_s3_client(bucket_name, boto_session)
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix, Delimiter="/")

        subfolders = []
        folder_details = response.get("CommonPrefixes")
        if folder_details:
            for folder_detail in folder_details:
                subfolder = folder_detail["Prefix"]
                start_index = subfolder.index(prefix) + len(prefix)
                subfolders.append(subfolder[start_index:].strip("/"))

        return subfolders

    # Handle file system
    return [f.name for f in os.scandir(folder_path) if f.is_dir()]


def list_files(
    path: str, recursive: bool = False, boto_session: Optional[boto3.Session] = None
) -> List[str]:
    """List the immediate files under path.

    There is minor inconsistency between local path handling and S3 paths.
    Directory names will be included for local paths, whereas they will not for
    S3 paths.

    Args:
        path: Supports s3:// and local paths.
        recursive: Only applicable for S3 paths.
            If set to True will recursively list all relative key paths under the prefix.
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
        if prefix and not prefix.endswith("/"):
            prefix = prefix + "/"

        s3 = get_s3_client(bucket_name, boto_session)

        # When the delimiter is provided, s3 knows to stop listing keys that contain it (starting after the prefix).
        # https://docs.aws.amazon.com/AmazonS3/latest/dev/ListingKeysHierarchy.html
        delimiter = "" if recursive else "/"

        paginator = s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix, Delimiter=delimiter)

        file_paths = []
        for page in pages:
            object_contents = page.get("Contents")

            if object_contents:
                for object in object_contents:
                    if recursive:
                        key = object["Key"]
                        start_index = key.index(prefix) + len(prefix)
                        file_paths.append(key[start_index:])
                    else:
                        file_paths.append(get_file_name(object["Key"]))

        return file_paths

    # os.listdir throws an exception if the path doesn't exist
    # Make it behave like S3 list and return an empty list
    if os.path.exists(path):
        return os.listdir(path)
    return []


def list_files_without_folder(
    path: str, recursive: bool = False, boto_session: Optional[boto3.Session] = None
) -> List[str]:
    files = list_files(path, recursive=recursive, boto_session=boto_session)
    return list(filter(lambda file: file != "", [get_file_name(path) for path in files]))


# Lists all files and directories in the path. Keys in the returned dict are equivalent to a
# simple bash `ls`. Values of the returned dict are the relative path from the current path to the
# contents of that directory.
# Example response: {
#     "a-stellar-testfile.txt": ["a-stellar-testfile.txt"],
#     "a-subfolder": [
#         "a-subfolder/my-file.txt",
#         "a-subfolder/second-file.txt"
#     ]
# }
def list_s3_files_and_directories_by_level(
    path: str, boto_session: Optional[boto3.Session] = None
) -> Dict[str, List[str]]:
    if not is_s3_path(path):
        return {}

    # Add an empty string at the end of the prefix so it always ends in "/".
    bucket_name, prefix = split_s3_url(path)
    prefix = os.path.join(prefix, "")
    s3 = get_s3_client(bucket_name, boto_session)

    contents_by_level: Dict[str, List[str]] = {}
    logger.info(f"retrieving object list from s3, bucket: {bucket_name}, prefix: {prefix}")
    contents = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix).get("Contents")
    if contents is None:
        return contents_by_level

    for object in contents:
        full_key = object["Key"]

        # Exclude the directory itself from the list of files and directories within the directory.
        if full_key == prefix:
            continue

        relative_path = full_key[len(prefix) :]
        local_component = relative_path.split("/")[0]

        if contents_by_level.get(local_component) is None:
            contents_by_level[local_component] = []

        # Exclude the subdirectories from the list of files and directories returned.
        if not relative_path[-1:] == "/":
            contents_by_level[local_component].append(relative_path)

    return contents_by_level


def copy_file(source, destination):
    logger.info(f"Copying file from {source} to {destination}")
    is_source_s3 = is_s3_path(source)
    is_dest_s3 = is_s3_path(destination)

    # This isn't a download or upload method
    # Don't allow "copying" between mismatched locations
    if is_source_s3 != is_dest_s3:
        raise Exception("Cannot download/upload between disk and S3 using this method")

    if is_source_s3:
        source_bucket, source_path = split_s3_url(source)
        dest_bucket, dest_path = split_s3_url(destination)

        # TODO - switch back to this after FINEOS roles have the updated permissions.
        # s3 = boto3.client("s3")
        # copy_source = {"Bucket": source_bucket, "Key": source_path}
        # s3.copy(copy_source, dest_bucket, dest_path)

        # Simulate copy for now using independent download and upload.

        # TODO - temporarily commenting this out to use get_s3_client() helper function.
        # source_boto3_session = boto3
        # dest_boto3_session = boto3

        # is_fineos_source = source_bucket.startswith("fin-som")
        # is_fineos_dest = dest_bucket.startswith("fin-som")

        # if is_fineos_source or is_fineos_dest:
        #     # This should get passed in from the method but getting it
        #     # directly from the environment due to time constraints.
        #     fineos_boto_session = aws_sts.assume_session(
        #         role_arn=os.environ["FINEOS_AWS_IAM_ROLE_ARN"],
        #         external_id=os.environ["FINEOS_AWS_IAM_ROLE_EXTERNAL_ID"],
        #         role_session_name="payments_copy_file",
        #         region_name="us-east-1",
        #     )

        #     if is_fineos_source:
        #         source_boto3_session = fineos_boto_session

        #     if is_fineos_dest:
        #         dest_boto3_session = fineos_boto_session

        file_descriptor, tempfile_path = tempfile.mkstemp()

        try:
            # dest_s3 = source_boto3_session.client("s3")
            source_s3 = get_s3_client(source_bucket)
            source_s3.download_file(source_bucket, source_path, tempfile_path)

            # dest_s3 = dest_boto3_session.client("s3")
            dest_s3 = get_s3_client(dest_bucket)
            dest_s3.upload_file(tempfile_path, dest_bucket, dest_path)
        finally:
            os.close(file_descriptor)
            os.remove(tempfile_path)

    else:
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copy2(source, destination)


def copy_s3_files(source, destination, expected_file_names, recursive=False):
    s3_objects = list_files(source, recursive=recursive)

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
        # This will create any missing intermediary directories
        os.renames(source, destination)


def download_from_s3(source, destination):
    is_source_s3 = is_s3_path(source)
    is_dest_s3 = is_s3_path(destination)

    if not is_source_s3 or is_dest_s3:
        raise Exception("Source must be an S3 URI and destination must not be")

    bucket, path = split_s3_url(source)

    s3 = boto3.client("s3")
    s3.download_file(bucket, path, destination)


def upload_to_s3(source, destination):
    is_source_s3 = is_s3_path(source)
    is_dest_s3 = is_s3_path(destination)

    if is_source_s3 or not is_dest_s3:
        raise Exception("Destination must be an S3 URI and source must not be")

    bucket, path = split_s3_url(destination)

    s3 = boto3.client("s3")
    s3.upload_file(source, bucket, path)


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
    if not is_s3_path(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    config = botocore.client.Config(retries={"max_attempts": 10, "mode": "standard"})
    params = {"resource_kwargs": {"config": config}}
    return smart_open.open(path, mode, encoding=encoding, transport_params=params)


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
    logger.info(f"Connecting to SFTP endpoint {uri}")

    user, host, port = split_sftp_url(uri)
    t = paramiko.Transport((host, port))
    t.connect(username=user, pkey=pkey)

    return paramiko.SFTPClient.from_transport(t)


def copy_file_from_s3_to_sftp(source: str, dest: str, sftp: paramiko.SFTPClient) -> None:
    if not is_s3_path(source):
        raise ValueError("source must be an S3 URI")

    # Download file from S3 to a tempfile.
    _handle, tempfile_path = tempfile.mkstemp()
    logger.info(f"Downloading files from {source} to a temporary local directory.")
    download_from_s3(source, tempfile_path)

    # Copy the file from local tempfile to destination.
    logger.info(f"Uploading files to SFTP at {dest}")
    # confirm=False is added as otherwise SFTP will attempt to read
    # the file it just wrote and fail, and the file might not be available yet.
    sftp.put(tempfile_path, dest, confirm=False)


# Copy the file through a local tempfile instead of streaming from SFTP directly to S3 to reduce the
# number of network connections open at any given time (1 at a time instead of 2).
def copy_file_from_sftp_to_s3(source: str, dest: str, sftp: paramiko.SFTPClient) -> None:
    if not is_s3_path(dest):
        raise ValueError("dest must be an S3 URI")

    # Download file from SFTP to a tempfile.
    _handle, tempfile_path = tempfile.mkstemp()
    sftp.get(source, tempfile_path)

    # Copy the file from the local tempfile to S3 destination.
    upload_to_s3(tempfile_path, dest)


def remove_if_exists(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def create_csv_from_list(
    data: Iterable[Dict],
    fieldnames: Iterable[str],
    file_name: str,
    folder_path: Optional[str] = None,
) -> pathlib.Path:
    if not folder_path:
        directory = tempfile.mkdtemp()
        csv_filepath = os.path.join(directory, f"{file_name}.csv")
    else:
        csv_filepath = os.path.join(folder_path, f"{file_name}.csv")

    with write_file(csv_filepath) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction="ignore")

        writer.writeheader()
        for d in data:
            writer.writerow(d)

    return pathlib.Path(csv_filepath)
