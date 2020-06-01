#
# Utilities for handling files.
#

import os
from urllib.parse import urlparse

import smart_open


def is_s3_path(path):
    return path.startswith("s3://")


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

        for key, _content in smart_open.s3_iter_bucket(bucket_name, prefix=prefix):
            files.append(get_file_name(key))
        return files
    return os.listdir(path)


def read_file(path, mode="r"):
    return smart_open.open(path, mode).read()


def read_file_lines(path, mode="r"):
    stream = smart_open.open(path, mode)
    return map(lambda line: line.rstrip(), stream)
