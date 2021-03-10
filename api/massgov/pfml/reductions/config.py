import os
from dataclasses import dataclass
from os import environ

import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)


@dataclass
class ReductionsS3Config:
    s3_bucket_uri: str  # Ex: s3://massgov-pfml-prod-agency-transfer/
    # S3 directory paths are relative to the root of the bucket but should not have leading slashes.
    s3_dfml_outbound_directory_path: str  # Ex. reductions/dfml/outbound
    s3_dfml_archive_directory_path: str  # Ex. reductions/dfml/archive
    s3_dua_outbound_directory_path: str  # Ex. reductions/dua/outbound
    s3_dua_pending_directory_path: str  # Ex. reductions/dua/pending
    s3_dua_archive_directory_path: str  # Ex. reductions/dua/archive
    s3_dia_archive_directory_path: str  # Ex. reductions/dia/archive
    s3_dia_outbound_directory_path: str  # Ex. reductions/dia/outbound
    s3_dia_pending_directory_path: str  # Ex. reductions/dia/pending


def get_s3_config() -> ReductionsS3Config:
    return ReductionsS3Config(
        s3_bucket_uri=str(environ.get("S3_BUCKET")),
        s3_dfml_outbound_directory_path=str(environ.get("S3_DFML_OUTBOUND_DIRECTORY_PATH")),
        s3_dfml_archive_directory_path=str(environ.get("S3_DFML_ARCHIVE_DIRECTORY_PATH")),
        s3_dua_outbound_directory_path=str(environ.get("S3_DUA_OUTBOUND_DIRECTORY_PATH")),
        s3_dua_pending_directory_path=str(environ.get("S3_DUA_PENDING_DIRECTORY_PATH")),
        s3_dua_archive_directory_path=str(environ.get("S3_DUA_ARCHIVE_DIRECTORY_PATH")),
        s3_dia_archive_directory_path=str(environ.get("S3_DIA_ARCHIVE_DIRECTORY_PATH")),
        s3_dia_outbound_directory_path=str(environ.get("S3_DIA_OUTBOUND_DIRECTORY_PATH")),
        s3_dia_pending_directory_path=str(environ.get("S3_DIA_PENDING_DIRECTORY_PATH")),
    )


@dataclass
class ReductionsMoveItConfig:
    moveit_dua_inbound_path: str  # Ex: /DFML/DUA/Inbound
    moveit_dua_archive_path: str  # Ex: /DFML/DUA/Archive
    moveit_dua_outbound_path: str  # Ex: /DFML/DUA/Outbound
    moveit_dia_inbound_path: str  # Ex: /DFML/DIA/Inbound
    moveit_dia_outbound_path: str  # Ex: /DFML/DIA/Outbound
    moveit_dia_archive_path: str  # Ex: /DFML/DIA/Archive
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
        moveit_dia_inbound_path=str(environ.get("MOVEIT_DIA_INBOUND_PATH")),
        moveit_dia_archive_path=str(environ.get("MOVEIT_DIA_ARCHIVE_PATH")),
        moveit_dia_outbound_path=str(environ.get("MOVEIT_DIA_OUTBOUND_PATH")),
        moveit_sftp_uri=str(environ.get("MOVEIT_SFTP_URI")),
        moveit_ssh_key=str(environ.get("MOVEIT_SSH_KEY")),
        moveit_ssh_key_password=str(environ.get("MOVEIT_SSH_KEY_PASSWORD")),
    )


@dataclass
class ReductionsEmailConfig:
    """Config for Reductions email

    This config is a wrapper around email env vars.
    """

    # DFML project manager email address. Should be CC'd on the BIEVNT emails
    # Ex: kevin.bailey@mass.gov
    dfml_project_manager_email_address: str
    # Sender email address
    # Ex: noreplypfml@mass.gov
    pfml_email_address: str
    # Bounce forwarding email address
    # Ex: noreplypfml@mass.gov
    bounce_forwarding_email_address: str
    bounce_forwarding_email_address_arn: str
    dfml_business_operations_email_address: str
    agency_reductions_email_address: str


def get_email_config() -> ReductionsEmailConfig:
    reductions_email_config = ReductionsEmailConfig(
        dfml_project_manager_email_address=os.getenv("DFML_PROJECT_MANAGER_EMAIL_ADDRESS", ""),
        pfml_email_address=os.getenv("PFML_EMAIL_ADDRESS", "noreplypfml@mass.gov"),
        bounce_forwarding_email_address=os.getenv(
            "BOUNCE_FORWARDING_EMAIL_ADDRESS", "noreplypfml@mass.gov"
        ),
        bounce_forwarding_email_address_arn=os.getenv("BOUNCE_FORWARDING_EMAIL_ADDRESS_ARN", ""),
        dfml_business_operations_email_address=os.getenv(
            "DFML_BUSINESS_OPERATIONS_EMAIL_ADDRESS", ""
        ),
        agency_reductions_email_address=os.getenv(
            "AGENCY_REDUCTIONS_EMAIL_ADDRESS", "EOL-DL-DFML-Agency-Reductions@mass.gov"
        ),
    )

    logger.info(
        "Constructed payments configuration",
        extra={
            "dfml_project_manager_email_address": reductions_email_config.dfml_project_manager_email_address,
            "pfml_email_address": reductions_email_config.pfml_email_address,
            "bounce_forwarding_email_address": reductions_email_config.bounce_forwarding_email_address,
            "bounce_forwarding_email_address_arn": reductions_email_config.bounce_forwarding_email_address_arn,
            "dfml_business_operations_email_address": reductions_email_config.dfml_business_operations_email_address,
        },
    )

    return reductions_email_config
