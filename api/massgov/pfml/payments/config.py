import os
from dataclasses import dataclass

import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)


@dataclass
class PaymentsS3Config:
    """Config for Payments S3 Buckets

    This config is a wrapper around S3 paths (eg. s3://bucket/path/to/folder/).

    Vars prefixed with "fineos" are buckets owned by FINEOS. These env vars
    point to the S3 "folder" that contains the timestamped files & folders.

    Vars prefixed by "pfml" are owned by PFML. Payments uses the PFML agency
    transfer S3 bucket. The payments-related folders within that bucket follow
    this convention:

    /<vendor_or_agency>
      /inbound
        /received
        /processed
        /error
      /outbound
        /ready
        /sent
        /error

    These env vars are of the format:
    s3://<agency transfer>/<vendor>/<inbound or outbound>
    They do not contain the final state folder (e.g. "received", "processed")
    """

    ## ---- FINEOS-related S3 Bucket envs
    # FINEOS generates data export files for PFML API to pick up
    # This is where FINEOS makes those files available to us
    # Ex: s3://fin-somprod-data-export/PRD/dataexports/
    fineos_data_export_path: str
    # PFML API generates files for FINEOS to process
    # This is where FINEOS picks up files from us
    # Ex: s3://fin-somprod-data-import/PRD/peiupdate/
    fineos_data_import_path: str
    # PFML API stores a copy of all files that FINEOS generates for us
    # This is where we store that copy
    # Ex: s3://massgov-pfml-prod-agency-transfer/cps/inbound/
    pfml_fineos_inbound_path: str
    # PFML API stores a copy of all files that we generate for FINEOS
    # This is where we store that copy
    # Ex: s3://massgov-pfml-prod-agency-transfer/cps/outbound/
    pfml_fineos_outbound_path: str

    ## ---- CTR-related S3 bucket envs
    # PFML API stores a copy of all files that CTR/MMARS generates for us
    # This is where we store that copy
    # Ex: s3://massgov-pfml-prod-agency-transfer/ctr/inbound/
    pfml_ctr_inbound_path: str
    # PFML API stores a copy of all files that we generate for CTR/MMARS
    # This is where we store that copy
    # Ex: s3://massgov-pfml-prod-agency-transfer/ctr/outbound/
    pfml_ctr_outbound_path: str


def get_s3_config() -> PaymentsS3Config:
    return PaymentsS3Config(
        fineos_data_export_path=str(os.environ.get("FINEOS_DATA_EXPORT_PATH")),
        fineos_data_import_path=str(os.environ.get("FINEOS_DATA_IMPORT_PATH")),
        pfml_ctr_inbound_path=str(os.environ.get("PFML_CTR_INBOUND_PATH")),
        pfml_ctr_outbound_path=str(os.environ.get("PFML_CTR_OUTBOUND_PATH")),
        pfml_fineos_inbound_path=str(os.environ.get("PFML_FINEOS_INBOUND_PATH")),
        pfml_fineos_outbound_path=str(os.environ.get("PFML_FINEOS_OUTBOUND_PATH")),
    )


@dataclass
class PaymentsMoveItConfig:
    """Config for Payments MOVEit

    In order to send and receive files from Comptroller (CTR), the PFML API
    conects to the EOLWD MOVEit instance (an SFTP tool). The EOTSS MOVEit
    instance checks the LWD MOVEit and CTR's (MOVEit?) server every 15 minutes
    and moves files to and fro.

    This config is a wrapper around MOVEit env vars.

    Note: Unlike the S3 bucket paths, MOVEit paths are expected to be the
    relative path from the root of the MOVEit server.
    """

    ## ---- MOVEit paths
    # CTR/MMARS generates Outbound Return files for PFML API to pick up
    # This is the MOVEit location where those files are available to us
    # Ex: DFML/Comptroller_Office/Incoming/nmmarsload/
    ctr_moveit_incoming_path: str
    # Once PFML API picks up files from MOVEit, we need to put them into the
    # Archive folder
    # This is the MOVEit location where we archive folders
    # Ex: DFML/Comptroller_Office/Archive
    ctr_moveit_archive_path: str
    # PFML API generates files for CTR/MMARS to process
    # This is where CTR/MMARS picks up files from us
    # Ex: DFML/Comptroller_Office/Outgoing/nmmarsload/
    ctr_moveit_outgoing_path: str

    ## --- MOVEit connection details
    # Include protocol, user, and host in the URI.
    # Ex: sftp://DFML@transfertest.eol.mass.gov
    ctr_moveit_sftp_uri: str
    # SSH Key and password
    # Stored in a secure store (AWS Secrets Manager).
    ctr_moveit_ssh_key: str
    ctr_moveit_ssh_key_password: str


def get_moveit_config() -> PaymentsMoveItConfig:
    return PaymentsMoveItConfig(
        ctr_moveit_incoming_path=str(os.environ.get("CTR_MOVEIT_INCOMING_PATH")),
        ctr_moveit_outgoing_path=str(os.environ.get("CTR_MOVEIT_OUTGOING_PATH")),
        ctr_moveit_archive_path=str(os.environ.get("CTR_MOVEIT_ARCHIVE_PATH")),
        ctr_moveit_sftp_uri=str(os.environ.get("EOLWD_MOVEIT_SFTP_URI")),
        ctr_moveit_ssh_key=str(os.environ.get("CTR_MOVEIT_SSH_KEY")),
        ctr_moveit_ssh_key_password=str(os.environ.get("CTR_MOVEIT_SSH_KEY_PASSWORD")),
    )


@dataclass
class PaymentsEmailConfig:
    """Config for Payments email

    PFML API needs to send the following types of emails:
    - GAX BIEVNT info
    - VCC BIEVNT info
    - Error reports

    This config is a wrapper around email env vars.
    """

    # Sender email address
    # Ex: noreplypfml@mass.gov
    pfml_email_address: str
    # Bounce forwarding email address
    # Ex: noreplypfml@mass.gov
    bounce_forwarding_email_address: str
    # Recipient email address for GAX BIEVNT info
    # Ex: Accounts.Payable@detma.org
    ctr_gax_bievnt_email_address: str
    # Recipient email address for VCC BIEVNT info
    # Ex: EOL-DL-DFML-GAXVCC_Confirmation@mass.gov
    ctr_vcc_bievnt_email_address: str
    # Recipient email address for Error reports
    # Ex: EOL-DL-DFML-GAXVCC_Confirmation@mass.gov
    dfml_business_operations_email_address: str


def get_email_config() -> PaymentsEmailConfig:
    payments_email_config = PaymentsEmailConfig(
        pfml_email_address=os.getenv("PFML_EMAIL_ADDRESS", "noreplypfml@mass.gov"),
        bounce_forwarding_email_address=os.getenv(
            "BOUNCE_FORWARDING_EMAIL_ADDRESS", "noreplypfml@mass.gov"
        ),
        ctr_gax_bievnt_email_address=os.getenv("CTR_GAX_BIEVNT_EMAIL_ADDRESS", ""),
        ctr_vcc_bievnt_email_address=os.getenv("CTR_VCC_BIEVNT_EMAIL_ADDRESS", ""),
        dfml_business_operations_email_address=os.getenv(
            "DFML_BUSINESS_OPERATIONS_EMAIL_ADDRESS", ""
        ),
    )

    logger.info(
        "Constructed payments configuration",
        extra={
            "pfml_email_address": payments_email_config.pfml_email_address,
            "bounce_forwarding_email_address": payments_email_config.bounce_forwarding_email_address,
            "ctr_gax_bievnt_email_address": payments_email_config.ctr_gax_bievnt_email_address,
            "ctr_vcc_bievnt_email_address": payments_email_config.ctr_vcc_bievnt_email_address,
            "dfml_business_operations_email_address": payments_email_config.dfml_business_operations_email_address,
        },
    )

    return payments_email_config
