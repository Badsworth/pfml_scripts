from typing import Optional

from pydantic import Field

from massgov.pfml.util.pydantic import PydanticBaseSettings


class DUAS3Config(PydanticBaseSettings):
    s3_bucket_uri: str = Field(..., env="S3_BUCKET")  # Ex: s3://massgov-pfml-prod-agency-transfer/
    # S3 directory paths are relative to the root of the bucket but should not have leading slashes.
    s3_archive_directory_path: str = "dua/archive"
    s3_error_directory_path: str = "dua/error"
    s3_pending_directory_path: str = "dua/pending"


def get_s3_config() -> DUAS3Config:
    return DUAS3Config()


class DUAMoveItConfig(PydanticBaseSettings):
    # Ex: sftp://DFML@transfertest.eol.mass.gov
    moveit_sftp_uri: str
    # SSH Key and password stored in AWS Secrets Manager.
    moveit_ssh_key: str
    moveit_ssh_key_password: Optional[str] = None
    moveit_archive_path: str = Field("/DFML/DUA/Archive", env="MOVEIT_DUA_ARCHIVE_PATH")
    moveit_outbound_path: str = Field("/DFML/DUA/Outbound", env="MOVEIT_DUA_OUTBOUND_PATH")


def get_moveit_config() -> DUAMoveItConfig:
    return DUAMoveItConfig()
