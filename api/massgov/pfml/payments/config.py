import os
from dataclasses import dataclass

import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)


@dataclass
class PaymentsS3Config:
    # S3 paths (eg. s3://bucket/path/to/folder/)
    # Vars prefixed with fineos are buckets owned by fineos
    # Vars prefixed by pfml are owned by us

    # FINEOS generates data export files for PFML API to pick up
    # This is where FINEOS makes those files available to us
    fineos_data_export_path: str
    # PFML API stores a copy of all files that FINEOS generates for us
    # This is where we store that copy
    fineos_data_import_path: str
    # PFML API stores a copy of all files that we retrieve from CTR
    # This is where we store that copy
    pfml_ctr_inbound_path: str
    ## PFML API stores a copy of all files that we generate for the office of the Comptroller
    ## This is where we store that copy
    pfml_ctr_outbound_path: str
    ## PFML API stores a copy of all files that we generate for FINEOS
    ## This is where we store that copy
    pfml_fineos_inbound_path: str
    # PFML API generates files for FINEOS to process
    # This is where FINEOS picks up files from us
    pfml_fineos_outbound_path: str


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
class PaymentsEmailConfig:
    payments_gax_bievnt_email: str
    pfml_email_address: str
    bounce_forwarding_email_address: str


def get_email_config() -> PaymentsEmailConfig:
    payments_email_config = PaymentsEmailConfig(
        payments_gax_bievnt_email=os.getenv("PAYMENTS_GAX_BIEVNT_EMAIL", ""),
        pfml_email_address=os.getenv("PFML_EMAIL_ADDRESS", "noreplypfml@mass.gov"),
        bounce_forwarding_email_address=os.getenv(
            "BOUNCE_FORWARDING_EMAIL_ADDRESS", "noreplypfml@mass.gov"
        ),
    )

    logger.info(
        "Constructed payments configuration",
        extra={
            "payments_gax_bievnt_email": payments_email_config.payments_gax_bievnt_email,
            "pfml_email_address": payments_email_config.pfml_email_address,
            "bounce_forwarding_email_address": payments_email_config.bounce_forwarding_email_address,
        },
    )

    return payments_email_config
