from dataclasses import dataclass
from os import environ


@dataclass
class ReductionsConfig:
    s3_bucket: str
    s3_dua_pending_directory_path: str
    s3_dua_archive_directory_path: str


def get_config() -> ReductionsConfig:
    return ReductionsConfig(
        s3_bucket=str(environ.get("S3_BUCKET")),
        s3_dua_pending_directory_path=str(environ.get("S3_DUA_PENDING_DIRECTORY_PATH")),
        s3_dua_archive_directory_path=str(environ.get("S3_DUA_ARCHIVE_DIRECTORY_PATH")),
    )
