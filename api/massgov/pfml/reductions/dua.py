import csv
import io
import os
import pathlib
from typing import Any, Dict, List, Optional

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    Claim,
    DuaReductionPayment,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.payments.payments_util import get_now
from massgov.pfml.payments.sftp_s3_transfer import (
    SftpS3TransferConfig,
    copy_to_sftp_and_archive_s3_files,
)
from massgov.pfml.reductions.config import get_moveit_config, get_s3_config

logger = logging.get_logger(__name__)


class Constants:
    DUA_PAYMENT_CSV_COLUMN_TO_TABLE_DATA_FIELD_MAP = {
        "CASE_ID": "absence_case_id",
        "EMPR_FEIN": "employer_fein",
        "WARRANT_DT": "payment_date",
        "RQST_WK_DT": "request_week_begin_date",
        "WBA_ADDITIONS": "gross_payment_amount_cents",
        "PAID_AM": "payment_amount_cents",
        "FRAUD_IND": "fraud_indicator",
        "BYB_DT": "benefit_year_begin_date",
        "BYE_DT": "benefit_year_end_date",
    }

    CASE_ID_FIELD = "CASE_ID"
    BENEFIT_START_DATE_FIELD = "START_DATE"
    SSN_FIELD = "SSN"

    CLAIMAINT_LIST_FIELDS = [
        CASE_ID_FIELD,
        SSN_FIELD,
        BENEFIT_START_DATE_FIELD,
    ]

    TEMPORARY_BENEFIT_START_DATE = "20210101"

    CLAIMAINT_LIST_FILENAME_PREFIX = "DFML_CLAIMANTS_FOR_DUA_"
    CLAIMAINT_LIST_FILENAME_TIME_FORMAT = "%Y%m%d%H%M"


def copy_claimant_list_to_moveit(db_session: db.Session) -> None:
    s3_config = get_s3_config()
    moveit_config = get_moveit_config()

    transfer_config = SftpS3TransferConfig(
        s3_bucket_uri=s3_config.s3_bucket,
        source_dir=s3_config.s3_dua_outbound_directory_path,
        archive_dir=s3_config.s3_dua_archive_directory_path,
        dest_dir=moveit_config.moveit_dua_inbound_path,
        sftp_uri=moveit_config.moveit_sftp_uri,
        ssh_key_password=moveit_config.moveit_ssh_key_password,
        ssh_key=moveit_config.moveit_ssh_key,
    )

    copied_reference_files = copy_to_sftp_and_archive_s3_files(transfer_config, db_session)
    for ref_file in copied_reference_files:
        state_log_util.create_finished_state_log(
            associated_model=ref_file,
            end_state=State.DUA_CLAIMANT_LIST_SUBMITTED,
            outcome=state_log_util.build_outcome("Sent list of claimants to DUA via MoveIt"),
            db_session=db_session,
        )

    # Commit the StateLogs we created to the database.
    db_session.commit()


def get_approved_claims(db_session: db.Session) -> List[Claim]:
    return (
        db_session.query(Claim)
        .filter_by(fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id)
        .all()
    )


def format_claims_for_dua_claimant_list(approved_claims: List[Claim]) -> List[Dict]:
    approved_claims_info = []

    for claim in approved_claims:
        employee = claim.employee
        if employee is not None:
            _info = {
                Constants.CASE_ID_FIELD: claim.fineos_absence_id,
                Constants.SSN_FIELD: employee.tax_identifier.tax_identifier.replace("-", ""),
                Constants.BENEFIT_START_DATE_FIELD: Constants.TEMPORARY_BENEFIT_START_DATE,
            }

            approved_claims_info.append(_info)

    return approved_claims_info


def get_approved_claims_info_csv_path(approved_claims: List[Dict]) -> pathlib.Path:
    file_name = Constants.CLAIMAINT_LIST_FILENAME_PREFIX + get_now().strftime(
        Constants.CLAIMAINT_LIST_FILENAME_TIME_FORMAT
    )
    return file_util.create_csv_from_list(
        approved_claims, Constants.CLAIMAINT_LIST_FIELDS, file_name
    )


def create_list_of_claimants(db_session: db.Session) -> None:
    config = get_s3_config()

    approved_claims = get_approved_claims(db_session)

    dua_claimant_info = format_claims_for_dua_claimant_list(approved_claims)

    claimant_info_path = get_approved_claims_info_csv_path(dua_claimant_info)

    s3_dest = os.path.join(
        config.s3_bucket, config.s3_dua_outbound_directory_path, claimant_info_path.name
    )
    file_util.upload_to_s3(str(claimant_info_path), s3_dest)

    # Update ReferenceFile and StateLog Tables
    ref_file = ReferenceFile(
        file_location=s3_dest,
        reference_file_type_id=ReferenceFileType.DUA_CLAIMANT_LIST.reference_file_type_id,
    )
    db_session.add(ref_file)
    # commit ref_file to db
    db_session.commit()

    # Update StateLog Tables
    state_log_util.create_finished_state_log(
        associated_model=ref_file,
        end_state=State.DUA_CLAIMANT_LIST_CREATED,
        outcome=state_log_util.build_outcome("Created claimant list for DUA"),
        db_session=db_session,
    )

    # commit StateLog to db
    db_session.commit()


def load_new_dua_payments(db_session: db.Session) -> None:
    s3_config = get_s3_config()
    pending_directory = os.path.join(s3_config.s3_bucket, s3_config.s3_dua_pending_directory_path)
    archive_directory = os.path.join(s3_config.s3_bucket, s3_config.s3_dua_archive_directory_path)

    for ref_file in _get_pending_dua_payment_reference_files(pending_directory, db_session):
        try:
            load_dua_payment_from_reference_file(ref_file, archive_directory, db_session)
        except Exception:
            # Log exceptions but continue attempting to load other payment files into the database.
            logger.exception(
                "Failed to load new DUA payments to database from file",
                extra={
                    "file_location": ref_file.file_location,
                    "reference_file_id": ref_file.reference_file_id,
                },
            )


def load_dua_payment_from_reference_file(
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


def _get_pending_dua_payment_reference_files(
    pending_directory: str, db_session: db.Session
) -> List[ReferenceFile]:
    # Add a trailing % so that we match anything within the directory.
    return (
        db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.DUA_PAYMENT_LIST.reference_file_type_id,
            ReferenceFile.file_location.like(pending_directory + "%"),
        )
        .all()
    )


def _convert_dict_with_csv_keys_to_db_keys(csv_data: Dict[str, Any]) -> Dict[str, Any]:
    # Load empty strings as null values.
    return {
        Constants.DUA_PAYMENT_CSV_COLUMN_TO_TABLE_DATA_FIELD_MAP[k]: None if v == "" else v
        for k, v in csv_data.items()
    }


def _get_matching_dua_reduction_payments(
    db_data: Dict[str, Any], db_session: db.Session
) -> Optional[DuaReductionPayment]:
    # https://stackoverflow.com/questions/7604967/sqlalchemy-build-query-filter-dynamically-from-dict
    query = db_session.query(DuaReductionPayment)
    for attr, value in db_data.items():
        # Empty fields are read as empty strings. Convert those values to nulls for the datbase.
        if value == "":
            value = None

        query = query.filter(getattr(DuaReductionPayment, attr) == value)

    return query.all()


def _load_new_rows_from_file(file: io.StringIO, db_session: db.Session) -> None:
    for row in csv.DictReader(file):
        db_data = _convert_dict_with_csv_keys_to_db_keys(row)
        if len(_get_matching_dua_reduction_payments(db_data, db_session)) == 0:
            dua_reduction_payment = DuaReductionPayment(**db_data)
            db_session.add(dua_reduction_payment)

    # Commit these changes to the database after we've updated the ReferenceFile's file_location
    # in the calling code.
