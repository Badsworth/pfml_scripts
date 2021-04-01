import os
from dataclasses import dataclass

import massgov.pfml.util.logging
from massgov.pfml.util.pydantic import PydanticBaseSettings

logger = massgov.pfml.util.logging.get_logger(__name__)


class PaymentsS3Config(PydanticBaseSettings):
    """Config for Delegated Payments S3 Buckets

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

    ## ---- PUB-related S3 bucket envs
    # All files we receive from PUB will be saved up in this directory.
    # Ex: s3://massgov-pfml-prod-agency-transfer/pub/inbound/
    pfml_pub_inbound_path: str
    # All files we send to PUB will be saved in this directory
    # Ex: s3://massgov-pfml-prod-agency-transfer/pub/outbound/
    pfml_pub_outbound_path: str

    # PFML API stores a copy of all files that we generate for error reporting
    # This is where the store that copy
    # Ex: s3://massgov-pfml-prod-agency-transfer/error-reports/outbound/
    pfml_error_reports_path: str
    pfml_error_reports_archive_path: str

    # Delegated configs start here
    payment_audit_report_outbound_folder_path: str
    payment_audit_report_sent_folder_path: str

    payment_rejects_received_folder_path: str
    payment_rejects_processed_folder_path: str
    payment_rejects_report_outbound_folder: str
    payment_rejects_report_sent_folder_path: str


def get_s3_config() -> PaymentsS3Config:
    return PaymentsS3Config()


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
    # Ex: /DFML/Comptroller_Office/Incoming/nmmarsload/
    ctr_moveit_incoming_path: str
    # Once PFML API picks up files from MOVEit, we need to put them into the
    # Archive folder
    # This is the MOVEit location where we archive folders
    # Ex: /DFML/Comptroller_Office/Archive
    ctr_moveit_archive_path: str
    # PFML API generates files for CTR/MMARS to process
    # This is where CTR/MMARS picks up files from us
    # Ex: /DFML/Comptroller_Office/Outgoing/nmmarsload/
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
        dfml_project_manager_email_address=os.getenv("DFML_PROJECT_MANAGER_EMAIL_ADDRESS", ""),
        pfml_email_address=os.getenv("PFML_EMAIL_ADDRESS", "PFML_DoNotReply@eol.mass.gov"),
        bounce_forwarding_email_address=os.getenv(
            "BOUNCE_FORWARDING_EMAIL_ADDRESS", "PFML_DoNotReply@eol.mass.gov"
        ),
        bounce_forwarding_email_address_arn=os.getenv("BOUNCE_FORWARDING_EMAIL_ADDRESS_ARN", ""),
        ctr_gax_bievnt_email_address=os.getenv("CTR_GAX_BIEVNT_EMAIL_ADDRESS", ""),
        ctr_vcc_bievnt_email_address=os.getenv("CTR_VCC_BIEVNT_EMAIL_ADDRESS", ""),
        dfml_business_operations_email_address=os.getenv(
            "DFML_BUSINESS_OPERATIONS_EMAIL_ADDRESS", ""
        ),
    )

    logger.info(
        "Constructed payments configuration",
        extra={
            "dfml_project_manager_email_address": payments_email_config.dfml_project_manager_email_address,
            "pfml_email_address": payments_email_config.pfml_email_address,
            "bounce_forwarding_email_address": payments_email_config.bounce_forwarding_email_address,
            "bounce_forwarding_email_address_arn": payments_email_config.bounce_forwarding_email_address_arn,
            "ctr_gax_bievnt_email_address": payments_email_config.ctr_gax_bievnt_email_address,
            "ctr_vcc_bievnt_email_address": payments_email_config.ctr_vcc_bievnt_email_address,
            "dfml_business_operations_email_address": payments_email_config.dfml_business_operations_email_address,
        },
    )

    return payments_email_config


class PaymentsDateConfig(PydanticBaseSettings):
    """Config for Payments dates

    PFML API processes the following timestamped files from FINEOS:
    - vendor extracts
    - payment extracts

    Due to some challenges around launch, we need to be able to configure
    how far back in time we look when checking each folder.

    This config is a wrapper around date env vars.
    """

    # PFML API will not process FINEOS vendor data older than this date
    fineos_vendor_max_history_date: str
    # PFML API will not process FINEOS payment data older than this date
    fineos_payment_max_history_date: str


def get_date_config() -> PaymentsDateConfig:
    payments_date_config = PaymentsDateConfig()

    logger.info(
        "Constructed payments date config",
        extra={
            "fineos_vendor_max_history_date": payments_date_config.fineos_vendor_max_history_date,
            "fineos_payment_max_history_date": payments_date_config.fineos_payment_max_history_date,
        },
    )
    return payments_date_config
