from dataclasses import dataclass
from os import environ


@dataclass
class ReductionsS3Config:
    s3_bucket: str  # Ex: s3://massgov-pfml-prod-agency-transfer/
    # S3 directory paths are relative to the root of the bucket but should not have leading slashes.
    s3_dua_outbound_directory_path: str  # Ex. reductions/dua/outbound
    s3_dua_pending_directory_path: str  # Ex. reductions/dua/pending
    s3_dua_archive_directory_path: str  # Ex. reductions/dua/archive
    s3_dia_outbound_directory_path: str


def get_s3_config() -> ReductionsS3Config:
    return ReductionsS3Config(
        s3_bucket=str(environ.get("S3_BUCKET")),
        s3_dua_outbound_directory_path=str(environ.get("S3_DUA_OUTBOUND_DIRECTORY_PATH")),
        s3_dua_pending_directory_path=str(environ.get("S3_DUA_PENDING_DIRECTORY_PATH")),
        s3_dua_archive_directory_path=str(environ.get("S3_DUA_ARCHIVE_DIRECTORY_PATH")),
        s3_dia_outbound_directory_path=str(environ.get("S3_DIA_OUTBOUND_DIRECTORY_PATH")),
    )


@dataclass
class ReductionsMoveItConfig:
    moveit_dua_inbound_path: str  # Ex: /DFML/DUA/Inbound
    moveit_dua_archive_path: str  # Ex: /DFML/DUA/Archive
    moveit_dua_outbound_path: str  # Ex: /DFML/DUA/Outbound
    # Ex: sftp://DFML@transfertest.eol.mass.gov
    moveit_sftp_uri: str
    # SSH Key and password stored in AWS Secrets Manager.
    moveit_ssh_key: str
    moveit_ssh_key_password: str


def get_moveit_config() -> ReductionsMoveItConfig:
    return ReductionsMoveItConfig(
        moveit_dua_inbound_path=str(environ.get("MOVEIT_DUA_INBOUND_PATH")),
        moveit_dua_archive_path=str(environ.get("MOVEIT_DUA_ARCHIVE_PATH")),
        moveit_dua_outbound_path=str(environ.get("MOVEIT_DUA_OUTBOUND_PATH")),
        moveit_sftp_uri=str(environ.get("MOVEIT_SFTP_URI")),
        moveit_ssh_key=str(environ.get("MOVEIT_SSH_KEY")),
        moveit_ssh_key_password=str(environ.get("MOVEIT_SSH_KEY_PASSWORD")),
    )
