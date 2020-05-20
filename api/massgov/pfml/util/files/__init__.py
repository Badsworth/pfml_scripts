#
# Utilities for handling files.
#

import os
from urllib.parse import urlparse

from smart_open import s3_iter_bucket, smart_open


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

        for key, _content in s3_iter_bucket(bucket_name, prefix=prefix):
            files.append(get_file_name(key))
        return files
    return os.listdir(path)


def read_file_lines(path):
    stream = smart_open(path, "r", encoding="utf-8")
    return map(lambda line: line.rstrip(), stream)
