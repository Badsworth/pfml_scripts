#
# Utilities for handling files.
#

import os
import shutil
from typing import List, Optional
from urllib.parse import urlparse

import boto3
import ebcdic  # noqa: F401
import smart_open
from botocore.config import Config

EBCDIC_ENCODING = "cp1140"  # See https://pypi.org/project/ebcdic/ for further details


def is_s3_path(path):
    return path.startswith("s3://")


def get_s3_bucket(path):
    return urlparse(path).hostname


def get_s3_file_key(path):
    return urlparse(path).path[1:]


def get_file_name(path: str) -> str:
    # TODO when the DOR importer is updated to use the file system in upcoming tickets,
    # this function should replace get_file_name() that exists there
    return os.path.basename(path)


def split_s3_url(path):
    parts = urlparse(path)
    bucket_name = parts.netloc
    prefix = parts.path.lstrip("/")
    return (bucket_name, prefix)


def list_files(
    path: str, delimiter: str = "", boto_session: Optional[boto3.Session] = None
) -> List[str]:
    if is_s3_path(path):
        bucket_name, prefix = split_s3_url(path)
        files = []

        # TODO Use boto3 for now to address multithreading issue in lambda, revisit after pilot 2
        # https://github.com/RaRe-Technologies/smart_open/issues/340
        # for key, _content in smart_open.s3_iter_bucket(bucket_name, prefix=prefix, workers=1):
        #     files.append(get_file_name(key))

        s3 = boto_session.client("s3") if boto_session else boto3.client("s3")
        for object in s3.list_objects(Bucket=bucket_name, Prefix=prefix, Delimiter=delimiter)[
            "Contents"
        ]:
            key = object["Key"]
            files.append(get_file_name(key))

        return files

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


def remove_if_exists(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
