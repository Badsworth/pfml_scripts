from typing import Optional

from pydantic import Field

from massgov.pfml.util.pydantic import PydanticBaseSettings


class DUATransferConfig(PydanticBaseSettings):
    base_path: str = Field(
        ..., env="DUA_TRANSFER_BASE_PATH"
    )  # Ex: s3://massgov-pfml-prod-agency-transfer/
    # S3 directory paths are relative to the root of the bucket but should not have leading slashes.
    archive_directory_path: str = "dua/archive"
    error_directory_path: str = "dua/error"
    pending_directory_path: str = "dua/pending"
    outbound_directory_path: str = "dua/outbound"


def get_transfer_config() -> DUATransferConfig:
    return DUATransferConfig()


class DUAMoveItConfig(PydanticBaseSettings):
    # Ex: sftp://DFML@transfertest.eol.mass.gov
    moveit_sftp_uri: str
    # SSH Key and password stored in AWS Secrets Manager.
    moveit_ssh_key: str
    moveit_ssh_key_password: Optional[str] = None
    moveit_archive_path: str = Field("/DFML/DUA/Archive", env="MOVEIT_DUA_ARCHIVE_PATH")
    # Warning:
    # If the environment variable is set appropriately, the inbound path will actually point at /DUA/Outbound
    # and the outbound path will point at /DUA/Inbound.  The default values here will only be correct after
    # this is fixed in https://lwd.atlassian.net/browse/API-1626
    moveit_inbound_path: str = Field("/DFML/DUA/Inbound", env="MOVEIT_DUA_INBOUND_PATH")
    moveit_outbound_path: str = Field("/DFML/DUA/Outbound", env="MOVEIT_DUA_OUTBOUND_PATH")


def get_moveit_config() -> DUAMoveItConfig:
    return DUAMoveItConfig()
