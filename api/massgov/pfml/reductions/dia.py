import csv
import os
import tempfile
from typing import Dict, List

from sqlalchemy import func

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import Claim, ReferenceFile, ReferenceFileType, State
from massgov.pfml.payments.payments_util import get_now
from massgov.pfml.payments.sftp_s3_transfer import (
    SftpS3TransferConfig,
    copy_from_sftp_to_s3_and_archive_files,
    copy_to_sftp_and_archive_s3_files,
)
from massgov.pfml.reductions.common import get_claims_for_outbound
from massgov.pfml.reductions.config import get_moveit_config, get_s3_config
from massgov.pfml.util.files import upload_to_s3

logger = logging.get_logger(__name__)


class Constants:
    TEMPORARY_BENEFIT_START_DATE = "20210101"
    DATE_OF_BIRTH_FORMAT = "%Y%m%d"

    CLAIMAINT_LIST_FILENAME_PREFIX = "DFML_DIA_CLAIMANTS_"
    CLAIMAINT_LIST_FILENAME_TIME_FORMAT = "%Y%m%d%H%M"

    CASE_ID_FIELD = "CASE_ID"
    SSN_FIELD = "SSN"
    FIRST_NAME_FIELD = "FIRST_NAME"
    LAST_NAME_FIELD = "LAST_NAME"
    BIRTH_DATE_FIELD = "BIRTH_DATE"
    BENEFIT_START_DATE_FIELD = "START_DATE"
    CLAIMAINT_LIST_FIELDS = [
        CASE_ID_FIELD,
        SSN_FIELD,
        FIRST_NAME_FIELD,
        LAST_NAME_FIELD,
        BIRTH_DATE_FIELD,
        BENEFIT_START_DATE_FIELD,
    ]


def _format_claims_for_dia_claimant_list(claims: List[Claim]) -> List[Dict]:
    claims_info = []

    # DIA cannot accept CSVs that contain commas
    value_errors = []

    for claim in claims:
        employee = claim.employee
        if employee is not None:
            formatted_dob = (
                employee.date_of_birth.strftime(Constants.DATE_OF_BIRTH_FORMAT)
                if employee.date_of_birth
                else ""
            )
            info = {
                Constants.CASE_ID_FIELD: claim.fineos_absence_id,
                Constants.BENEFIT_START_DATE_FIELD: Constants.TEMPORARY_BENEFIT_START_DATE,
                Constants.FIRST_NAME_FIELD: employee.first_name,
                Constants.LAST_NAME_FIELD: employee.last_name,
                Constants.BIRTH_DATE_FIELD: formatted_dob,
                Constants.SSN_FIELD: employee.tax_identifier.tax_identifier.replace("-", ""),
            }

            for key in info:
                value = info[key]
                if "," in value:
                    value_errors.append(f"({claim.claim_id}, {key})")

            claims_info.append(info)

    # API-1335: DIA cannot accept values that contain commas, and we don't expect to see values
    # commas. If/when we encounter this situation, discuss a solution with DIA (Different file
    # format? Update DIA process to accept commas? Exclude claims in code in the meantime?).
    if len(value_errors) > 0:
        errors = ", ".join(value_errors)
        raise ValueError(f"Value for claims contains comma: {errors}")

    return claims_info


def _write_claims_to_tempfile(claims: List[Dict]) -> str:
    # Not using file_util.create_csv_from_list() because DIA does not want a header row.
    _handle, csv_filepath = tempfile.mkstemp()
    with open(csv_filepath, mode="w") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=Constants.CLAIMAINT_LIST_FIELDS)
        for data in claims:
            writer.writerow(data)

    return csv_filepath


def upload_claimant_list_to_moveit(db_session: db.Session) -> None:
    moveit_config = get_moveit_config()
    s3_config = get_s3_config()

    transfer_config = SftpS3TransferConfig(
        s3_bucket_uri=s3_config.s3_bucket_uri,
        source_dir=s3_config.s3_dia_outbound_directory_path,
        archive_dir=s3_config.s3_dia_archive_directory_path,
        dest_dir=moveit_config.moveit_dia_inbound_path,
        sftp_uri=moveit_config.moveit_sftp_uri,
        ssh_key_password=moveit_config.moveit_ssh_key_password,
        ssh_key=moveit_config.moveit_ssh_key,
    )

    copied_reference_files = copy_to_sftp_and_archive_s3_files(transfer_config, db_session)
    for ref_file in copied_reference_files:
        state_log_util.create_finished_state_log(
            associated_model=ref_file,
            end_state=State.DIA_CLAIMANT_LIST_SUBMITTED,
            outcome=state_log_util.build_outcome("Sent list of claimants to DIA via MoveIt"),
            db_session=db_session,
        )

    # Commit the StateLogs we created to the database.
    db_session.commit()


def create_list_of_claimants(db_session: db.Session) -> None:
    s3_config = get_s3_config()

    claims = get_claims_for_outbound(db_session)

    # get dia info for claims
    dia_claimant_info = _format_claims_for_dia_claimant_list(claims)

    tempfile_path = _write_claims_to_tempfile(dia_claimant_info)

    # Upload info to s3
    file_name = (
        Constants.CLAIMAINT_LIST_FILENAME_PREFIX
        + get_now().strftime(Constants.CLAIMAINT_LIST_FILENAME_TIME_FORMAT)
        + ".csv"
    )
    s3_dest = os.path.join(
        s3_config.s3_bucket_uri, s3_config.s3_dia_outbound_directory_path, file_name
    )
    upload_to_s3(tempfile_path, s3_dest)

    # Update ReferenceFile and StateLog Tables
    ref_file = ReferenceFile(
        file_location=s3_dest,
        reference_file_type_id=ReferenceFileType.DIA_CLAIMANT_LIST.reference_file_type_id,
    )
    db_session.add(ref_file)

    # commit ref_file to db
    db_session.commit()

    # Update StateLog Tables
    state_log_util.create_finished_state_log(
        associated_model=ref_file,
        end_state=State.DIA_CLAIMANT_LIST_CREATED,
        outcome=state_log_util.build_outcome("Created claimant list for DIA"),
        db_session=db_session,
    )

    # commit StateLog to db
    db_session.commit()


def _payment_list_has_been_downloaded_today(db_session: db.Session) -> bool:
    midnight_today = get_now().replace(hour=0, minute=0)
    num_files = (
        db_session.query(func.count(ReferenceFile.reference_file_id))
        .filter(
            ReferenceFile.created_at >= midnight_today,
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.DIA_PAYMENT_LIST.reference_file_type_id,
        )
        .scalar()
    )
    return num_files > 0


def download_payment_list_from_moveit(db_session: db.Session) -> None:
    s3_config = get_s3_config()
    moveit_config = get_moveit_config()

    transfer_config = SftpS3TransferConfig(
        s3_bucket_uri=s3_config.s3_bucket_uri,
        source_dir=moveit_config.moveit_dia_outbound_path,
        archive_dir=moveit_config.moveit_dia_archive_path,
        dest_dir=s3_config.s3_dia_pending_directory_path,
        sftp_uri=moveit_config.moveit_sftp_uri,
        ssh_key_password=moveit_config.moveit_ssh_key_password,
        ssh_key=moveit_config.moveit_ssh_key,
    )

    copied_reference_files = copy_from_sftp_to_s3_and_archive_files(transfer_config, db_session)
    for ref_file in copied_reference_files:
        ref_file.reference_file_type_id = ReferenceFileType.DIA_PAYMENT_LIST.reference_file_type_id
        state_log_util.create_finished_state_log(
            associated_model=ref_file,
            end_state=State.DIA_PAYMENT_LIST_SAVED_TO_S3,
            outcome=state_log_util.build_outcome("Saved DIA payment list to S3"),
            db_session=db_session,
        )

    # Commit the ReferenceFile changes and StateLogs we created to the database.
    db_session.commit()

    if len(copied_reference_files) == 0:
        logger.info("No new payment files were detected in the SFTP server.")
    else:
        logger.info(
            "New payment files were detected in the SFTP server.",
            extra={"reference_file_count": len(copied_reference_files)},
        )


# Meant to be called from ECS directly as a task.
def download_payment_list_if_none_today(db_session: db.Session) -> None:
    # Downloading payment lists from requires connecting to MoveIt. Wrap that call in this condition
    # so we only incur the overhead of that connection if we haven't retrieved a payment list today.
    if _payment_list_has_been_downloaded_today(db_session) is False:
        download_payment_list_from_moveit(db_session)


def _get_pending_dia_payment_reference_files(
    pending_directory: str, db_session: db.Session
) -> List[ReferenceFile]:
    # Add a trailing % so that we match anything within the directory.
    return (
        db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.DIA_PAYMENT_LIST.reference_file_type_id,
            ReferenceFile.file_location.like(pending_directory + "%"),
        )
        .all()
    )


def _load_dia_payment_from_reference_file(
    ref_file: ReferenceFile, archive_directory: str, db_session: db.Session
) -> None:
    # Load to database.
    with file_util.open_stream(ref_file.file_location) as f:
        _load_new_rows_from_file(f, db_session)

    # Move to archive directory and update ReferenceFile.
    filename = os.path.basename(ref_file.file_location)
    dest_path = os.path.join(archive_directory, filename)
    file_util.rename_file(ref_file.file_location, dest_path)
    ref_file.file_location = dest_path
    db_session.commit()

    # Create StateLog entry.
    state_log_util.create_finished_state_log(
        associated_model=ref_file,
        end_state=State.DUA_PAYMENT_LIST_SAVED_TO_DB,
        outcome=state_log_util.build_outcome("Loaded DUA payment file into database"),
        db_session=db_session,
    )
    db_session.commit()


def load_new_dia_payments(db_session: db.Session) -> None:
    s3_config = get_s3_config()
    pending_dir = os.path.join(s3_config.s3_bucket_uri, s3_config.s3_dia_pending_directory_path)
    archive_dir = os.path.join(s3_config.s3_bucket_uri, s3_config.s3_dia_archive_directory_path)

    for ref_file in _get_pending_dia_payment_reference_files(pending_dir, db_session):
        try:
            _load_dia_payment_from_reference_file(ref_file, archive_dir, db_session)
        except Exception:
            # Log exceptions but continue attempting to load other payment files into the database.
            logger.exception(
                "Failed to load new DIA payments to database from file",
                extra={
                    "file_location": ref_file.file_location,
                    "reference_file_id": ref_file.reference_file_id,
                },
            )
