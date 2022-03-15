from pydantic import Field

import massgov.pfml.util.logging
from massgov.pfml.util.pydantic import PydanticBaseSettings

logger = massgov.pfml.util.logging.get_logger(__name__)

NOT_SET = "ENV_VAR_NOT_SET"


class PaymentsS3Config(PydanticBaseSettings):
    """Config for Delegated Payments S3 Buckets

    This config is a wrapper around S3 paths (eg. s3://bucket/path/to/folder/).

    Vars prefixed with "fineos" are buckets owned by FINEOS. These env vars
    point to the S3 "folder" that contains the timestamped files & folders.

    Vars prefixed by "pfml" are owned by PFML. Payments uses the PFML agency
    transfer S3 bucket. The payments-related folders within that bucket follow
    this convention:

    Vars prefixed by "pub" are owned by us, but other processes move the files within
    to/from PUB via MoveIt

    Vars prefixed by "dfml" are owned by us, but other processes move the files within
    to/from DFML via sharepoint. These files are shared with either Program Integrity or
    Finance

    /<vendor_or_agency>
      /archive
        /<dataset>
          /received     - Input directory for processing
          /processed    - Successfully processed input file
          /error        - An error occurred with processing
          /skipped      - We received the file, but decided to skip it (extracts skip previous days)
          /sent         - We have sent the file
             <date>
                <filename>
      /inbound          - Files we are receiving, we will move these to a received directory for processing
        <files>
      /outbound         - Files we are sending out, we expect these to be moved/deleted
        <files>

    These env vars are of the format:
    s3://<agency transfer>/<vendor>/archive/<dataset>/
    They do not contain the final state folder (e.g. "received", "processed")
    """

    ## ---- FINEOS-related S3 Bucket envs
    # FINEOS generates data export files for PFML API to pick up
    # This is where FINEOS makes those files available to us
    # Ex: s3://fin-somprod-data-export/PRD/dataexports/
    fineos_data_export_path: str = Field(
        NOT_SET, description="This is where FINEOS makes extract files available to us"
    )
    # FINEOS allows us to generate adhoc query data export files for PFML API to pick up
    # This is where FINEOS makes those adhoc extract files available to us
    # Ex: s3://fin-somprod-data-export/PRD/dataExtracts/AdHocExtract/
    fineos_adhoc_data_export_path: str = Field(
        NOT_SET, description="This is where FINEOS makes adhoc extract files available to us"
    )
    # PFML API generates files for FINEOS to process
    # This is where FINEOS picks up files from us
    # Ex: s3://fin-somprod-data-import/PRD/peiupdate/
    fineos_data_import_path: str = Field(
        NOT_SET, description="This is where FINEOS picks up PEI writeback files from us"
    )
    # PFML API stores a copy of all files that FINEOS generates for us
    # Ex: s3://massgov-pfml-prod-agency-transfer/cps/archive/extracts/
    pfml_fineos_extract_archive_path: str = Field(
        NOT_SET, description="This is where we store the copy of the FINEOS extracts"
    )
    # PFML API stores a copy of all files that we generate for FINEOS
    # Ex: s3://massgov-pfml-prod-agency-transfer/cps/archive/pei-writeback/
    pfml_fineos_writeback_archive_path: str = Field(
        NOT_SET, description="This is where we store the copy of the FINEOS PEI writeback"
    )

    # All outgoing files destined for Sharepoint go in this directory.
    # Ex: s3://massgov-pfml-{env}-reports/dfml-reports/
    dfml_report_outbound_path: str = Field(
        NOT_SET, description="This is where we put files we want picked up and moved to Sharepoint"
    )
    # All incoming files copied from Sharepoint go in this directory.
    # Ex: s3://massgov-pfml-{env}-reports/dfml-responses/
    dfml_response_inbound_path: str = Field(
        NOT_SET, description="This is where files sent to us from Sharepoint are put"
    )

    # All files returned from PUB via MoveIt end up in this directory for our processing.
    # We will copy files from this directory to the below specific inbound paths.
    # Ex: massgov-pfml-{env}-agency-transfer/pub/inbound/
    pub_moveit_inbound_path: str = Field(
        NOT_SET, description="This is where we put files we want picked up and moved to MoveIt"
    )
    # All files destined for PUB that will get there via MoveIt end up in this directory for our processing.
    # Ex: massgov-pfml-{env}-agency-transfer/pub/outbound/
    pub_moveit_outbound_path: str = Field(
        NOT_SET, description="This is where files sent to us from MoveIt are put"
    )

    # ACH outgoing files are archived to this directory when we send them to PUB.
    # ACH return files we receive from PUB will be processed in this directory.
    # Ex: s3://massgov-pfml-prod-agency-transfer/pub/archive/ach/
    pfml_pub_ach_archive_path: str = Field(
        NOT_SET, description="This is where we store the copy of the ACH files"
    )
    # Check outgoing files are archive to this directory when we send them to PUB.
    # Check payment return files we receive from PUB will be processed in this directory.
    # Ex: s3://massgov-pfml-prod-agency-transfer/pub/archive/check/
    pfml_pub_check_archive_path: str = Field(
        NOT_SET, description="This is where we store the copy of the Check files"
    )

    # Where we store the manual PUB reject used to manually fail payments from PUB
    # that are otherwise not returned by the bank due to the particular type of error.
    # s3://massgov-pfml-prod-agency-transfer/pub/archive/manual-reject/
    pfml_manual_pub_reject_archive_path: str = Field(
        NOT_SET, description="This is where we store the copy of the manual PUB reject files"
    )

    # PFML API stores a copy of all files that we generate for reporting
    # Ex: s3://massgov-pfml-prod-agency-transfer/error-reports/archive/
    pfml_error_reports_archive_path: str = Field(
        ..., description="This is where we store a copy of all report files"
    )

    # PFML API stores a copy of the payment reject file we received
    # Ex s3://massgov-pfml-${environment_name}-agency-transfer/audit/archive
    pfml_payment_rejects_archive_path: str = Field(
        NOT_SET, description="This is where we store a copy of the payment reject response file"
    )

    # TODO: Add some description
    pfml_1099_document_archive_path: str = Field(
        NOT_SET, description="This is where we store all 1099 pdf documents"
    )


def get_s3_config() -> PaymentsS3Config:
    return PaymentsS3Config()


class PaymentsDateConfig(PydanticBaseSettings):
    """Config for Payments dates

    PFML API processes the following timestamped files from FINEOS:
    - claimant extracts
    - payment extracts

    Due to some challenges around launch, we need to be able to configure
    how far back in time we look when checking each folder.

    This config is a wrapper around date env vars.
    """

    # PFML API will not process FINEOS claimant data older than this date
    fineos_claimant_extract_max_history_date: str = Field(
        NOT_SET, description="The earliest file we will copy from FINEOS for the claimant extract"
    )
    # PFML API will not process FINEOS payment data older than this date
    fineos_payment_extract_max_history_date: str = Field(
        NOT_SET, description="The earliest file we will copy from FINEOS for the payment extract"
    )
    # PFML API will not process FINEOS payment data older than this date
    fineos_payment_reconciliation_extract_max_history_date: str = Field(
        NOT_SET,
        description="The earliest file we will copy from FINEOS for the payment reconciliation extract",
    )
    # PFML API will not process FINEOS IAWW data older than this date
    fineos_iaww_extract_max_history_date: str = Field(
        NOT_SET, description="The earliest file we will copy from FINEOS for the IAWW extract"
    )

    fineos_1099_data_extract_max_history_date: str = Field(
        NOT_SET, description="The earliest file we will copy from FINEOS for the 1099 extract"
    )


def get_date_config() -> PaymentsDateConfig:
    payments_date_config = PaymentsDateConfig()

    logger.info(
        "Constructed payments date config",
        extra={
            "fineos_claimant_extract_max_history_date": payments_date_config.fineos_claimant_extract_max_history_date,
            "fineos_payment_extract_max_history_date": payments_date_config.fineos_payment_extract_max_history_date,
        },
    )
    return payments_date_config
