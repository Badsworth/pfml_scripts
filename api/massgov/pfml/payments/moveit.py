import os
from urllib.parse import urlparse

import massgov.pfml.payments.config as payments_config
import massgov.pfml.util.files as file_util
from massgov.pfml import db
from massgov.pfml.payments.payments_util import Constants
from massgov.pfml.payments.sftp_s3_transfer import (
    SftpS3TransferConfig,
    copy_from_sftp_to_s3_and_archive_files,
    copy_to_sftp_and_archive_s3_files,
)


def pickup_files_from_moveit(db_session: db.Session) -> None:
    moveit_config = payments_config.get_moveit_config()
    s3_config = payments_config.get_s3_config()

    parsed_s3_path = urlparse(s3_config.pfml_ctr_inbound_path)
    s3_bucket_uri = "s3://" + (parsed_s3_path.hostname or "")
    dest_dir = os.path.join(parsed_s3_path.path, Constants.S3_INBOUND_RECEIVED_DIR)

    transfer_config = SftpS3TransferConfig(
        s3_bucket_uri=s3_bucket_uri,
        dest_dir=dest_dir,
        sftp_uri=moveit_config.ctr_moveit_sftp_uri,
        source_dir=moveit_config.ctr_moveit_incoming_path,
        archive_dir=moveit_config.ctr_moveit_archive_path,
        ssh_key=moveit_config.ctr_moveit_ssh_key,
        ssh_key_password=moveit_config.ctr_moveit_ssh_key_password,
    )

    copy_from_sftp_to_s3_and_archive_files(transfer_config, db_session)


def send_files_to_moveit(db_session: db.Session) -> None:
    moveit_config = payments_config.get_moveit_config()
    s3_config = payments_config.get_s3_config()

    # This logic should be rewritten a bit, we're splitting this to put it together to split it
    bucket, prefix = file_util.split_s3_url(s3_config.pfml_ctr_outbound_path)
    s3_bucket_uri = f"s3://{bucket}"

    source_dir = os.path.join(prefix, Constants.S3_OUTBOUND_READY_DIR)
    archive_dir = os.path.join(prefix, Constants.S3_OUTBOUND_SENT_DIR)

    transfer_config = SftpS3TransferConfig(
        s3_bucket_uri=s3_bucket_uri,
        source_dir=source_dir,
        archive_dir=archive_dir,
        sftp_uri=moveit_config.ctr_moveit_sftp_uri,
        dest_dir=moveit_config.ctr_moveit_outgoing_path,
        ssh_key=moveit_config.ctr_moveit_ssh_key,
        ssh_key_password=moveit_config.ctr_moveit_ssh_key_password,
    )

    copy_to_sftp_and_archive_s3_files(transfer_config, db_session)
