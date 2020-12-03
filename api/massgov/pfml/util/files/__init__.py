#
# Utilities for handling files.
#

import os
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


def list_files(path):
    if is_s3_path(path):
        parts = urlparse(path)
        bucket_name = parts.netloc
        prefix = parts.path.lstrip("/")

        files = []

        # TODO Use boto3 for now to address multithreading issue in lambda, revisit after pilot 2
        # https://github.com/RaRe-Technologies/smart_open/issues/340
        # for key, _content in smart_open.s3_iter_bucket(bucket_name, prefix=prefix, workers=1):
        #     files.append(get_file_name(key))

        s3 = boto3.client("s3")
        for object in s3.list_objects(Bucket=bucket_name, Prefix=prefix)["Contents"]:
            key = object["Key"]
            files.append(get_file_name(key))

        return files

    return os.listdir(path)


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
