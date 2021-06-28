from typing import Optional

from pydantic import Field

import massgov.pfml.util.logging
from massgov.pfml.util.pydantic import PydanticBaseSettings

logger = massgov.pfml.util.logging.get_logger(__name__)


class ReductionsS3Config(PydanticBaseSettings):
    s3_bucket_uri: str = Field(..., env="S3_BUCKET")  # Ex: s3://massgov-pfml-prod-agency-transfer/
    # S3 directory paths are relative to the root of the bucket but should not have leading slashes.
    s3_dfml_archive_directory_path: str = "reductions/dfml/archive"
    s3_dfml_outbound_directory_path: str = "reductions/dfml/outbound"
    s3_dfml_error_directory_path: str = "reductions/dfml/error"
    s3_dia_archive_directory_path: str = "reductions/dia/archive"
    s3_dia_outbound_directory_path: str = "reductions/dia/outbound"
    s3_dia_pending_directory_path: str = "reductions/dia/pending"
    s3_dua_archive_directory_path: str = "reductions/dua/archive"
    s3_dua_outbound_directory_path: str = "reductions/dua/outbound"
    s3_dua_pending_directory_path: str = "reductions/dua/pending"


def get_s3_config() -> ReductionsS3Config:
    return ReductionsS3Config()


class ReductionsMoveItConfig(PydanticBaseSettings):
    # Ex: sftp://DFML@transfertest.eol.mass.gov
    moveit_sftp_uri: str
    # SSH Key and password stored in AWS Secrets Manager.
    moveit_ssh_key: str
    moveit_ssh_key_password: Optional[str] = None
    # These config names are from the perspective of the API system, namely:
    # "inbound" = "where does API look for files coming from DIA/DUA"
    # "outbound" = "where does API put files to send to DIA/DUA"
    #
    # The actual paths in MOVEit may not always correspond to the API
    # perspective (the defaults here do to avoid confusion).
    moveit_dia_archive_path: str = "/DFML/DIA/Archive"
    moveit_dia_inbound_path: str = "/DFML/DIA/Inbound"
    moveit_dia_outbound_path: str = "/DFML/DIA/Outbound"
    moveit_dua_archive_path: str = "/DFML/DUA/Archive"
    moveit_dua_inbound_path: str = "/DFML/DUA/Inbound"
    moveit_dua_outbound_path: str = "/DFML/DUA/Outbound"


def get_moveit_config() -> ReductionsMoveItConfig:
    return ReductionsMoveItConfig()


class ReductionsEmailConfig(PydanticBaseSettings):
    """Config for Reductions email

    This config is a wrapper around email env vars.
    """

    # Bounce forwarding email address
    # Ex: noreplypfml@mass.gov
    bounce_forwarding_email_address_arn: str
    bounce_forwarding_email_address: str = "PFML_DoNotReply@eol.mass.gov"
    # Sender email address
    # Ex: noreplypfml@mass.gov
    pfml_email_address: str = "PFML_DoNotReply@eol.mass.gov"
    agency_reductions_email_address: str = "EOL-DL-DFML-Agency-Reductions@mass.gov"


def get_email_config() -> ReductionsEmailConfig:
    reductions_email_config = ReductionsEmailConfig()

    logger.info(
        "Constructed reductions email configuration",
        extra={
            "pfml_email_address": reductions_email_config.pfml_email_address,
            "bounce_forwarding_email_address": reductions_email_config.bounce_forwarding_email_address,
            "bounce_forwarding_email_address_arn": reductions_email_config.bounce_forwarding_email_address_arn,
            "agency_reductions_email_address": reductions_email_config.agency_reductions_email_address,
        },
    )

    return reductions_email_config
