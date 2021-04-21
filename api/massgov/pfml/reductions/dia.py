import csv
import io
import os
import tempfile
from typing import Any, Dict, List

from sqlalchemy import func

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    DiaReductionPayment,
    Employee,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.payments.payments_util import get_now
from massgov.pfml.payments.sftp_s3_transfer import (
    SftpS3TransferConfig,
    copy_from_sftp_to_s3_and_archive_files,
    copy_to_sftp_and_archive_s3_files,
)
from massgov.pfml.reductions.common import get_claimants_for_outbound
from massgov.pfml.reductions.config import get_moveit_config, get_s3_config
from massgov.pfml.util.files import upload_to_s3

logger = logging.get_logger(__name__)


class Constants:
    # DIA claims can last up to 3 years, so hard-coding to the start of 2018 for
    # the 2021 launch.
    TEMPORARY_BENEFIT_START_DATE = "20180101"
    DATE_OF_BIRTH_FORMAT = "%Y%m%d"

    CLAIMAINT_LIST_FILENAME_PREFIX = "DFML_DIA_CLAIMANTS_"
    CLAIMAINT_LIST_FILENAME_TIME_FORMAT = "%Y%m%d%H%M"

    CUSTOMER_NUMBER_FIELD = "DFML_ID"
    SSN_FIELD = "SSN"
    FIRST_NAME_FIELD = "FIRST_NAME"
    LAST_NAME_FIELD = "LAST_NAME"
    BIRTH_DATE_FIELD = "BIRTH_DATE"
    BENEFIT_START_DATE_FIELD = "START_DATE"
    BOARD_NO_FIELD = "BOARD_NO"
    EVENT_ID = "EVENT_ID"
    INS_FORM_OR_MEET_FIELD = "INS_FORM_OR_MEET"
    EVE_CREATED_DATE_FIELD = "EVE_CREATED_DATE"
    FORM_RECEIVED_OR_DISPOSITION_FIELD = "FORM_RECEIVED_OR_DISPOSITION"
    AWARD_ID_FIELD = "AWARD_ID"
    AWARD_CODE_FIELD = "AWARD_CODE"
    AWARD_AMOUNT_FIELD = "AWARD_AMOUNT"
    AWARD_DATE_FIELD = "AWARD_DATE"
    START_DATE_FIELD = "START_DATE"
    END_DATE_FIELD = "END_DATE"
    WEEKLY_AMOUNT_FIELD = "WEEKLY_AMOUNT"
    AWARD_CREATED_DATE_FIELD = "AWARD_CREATED_DATE"

    CLAIMAINT_LIST_FIELDS = [
        CUSTOMER_NUMBER_FIELD,
        SSN_FIELD,
        FIRST_NAME_FIELD,
        LAST_NAME_FIELD,
        BIRTH_DATE_FIELD,
        BENEFIT_START_DATE_FIELD,
    ]

    PAYMENT_LIST_FIELDS = [
        CUSTOMER_NUMBER_FIELD,
        BOARD_NO_FIELD,
        EVENT_ID,
        INS_FORM_OR_MEET_FIELD,
        EVE_CREATED_DATE_FIELD,
        FORM_RECEIVED_OR_DISPOSITION_FIELD,
        AWARD_ID_FIELD,
        AWARD_CODE_FIELD,
        AWARD_AMOUNT_FIELD,
        AWARD_DATE_FIELD,
        START_DATE_FIELD,
        END_DATE_FIELD,
        WEEKLY_AMOUNT_FIELD,
        AWARD_CREATED_DATE_FIELD,
    ]

    PAYMENT_CSV_FIELD_MAPPINGS = {
        CUSTOMER_NUMBER_FIELD: "fineos_customer_number",
        BOARD_NO_FIELD: "board_no",
        EVENT_ID: "event_id",
        INS_FORM_OR_MEET_FIELD: "event_description",
        FORM_RECEIVED_OR_DISPOSITION_FIELD: "event_occurrence_date",
        EVE_CREATED_DATE_FIELD: "eve_created_date",
        AWARD_ID_FIELD: "award_id",
        AWARD_CODE_FIELD: "award_code",
        AWARD_AMOUNT_FIELD: "award_amount",
        AWARD_DATE_FIELD: "award_date",
        START_DATE_FIELD: "start_date",
        END_DATE_FIELD: "end_date",
        WEEKLY_AMOUNT_FIELD: "weekly_amount",
        AWARD_CREATED_DATE_FIELD: "award_created_date",
    }


def _format_claimants_for_dia_claimant_list(claimants: List[Employee]) -> List[Dict[str, str]]:
    claimants_info = []

    # DIA cannot accept CSVs that contain commas, we strip them from the name
    # fields below, but track if any show up in other fields
    value_errors = []

    for employee in claimants:
        fineos_customer_number = employee.fineos_customer_number
        date_of_birth = employee.date_of_birth
        tax_id = employee.tax_identifier

        if not (fineos_customer_number and date_of_birth and tax_id):
            logger.warning(
                "Employee missing required information. Skipping.",
                extra={
                    "employee_id": employee.employee_id,
                    "has_fineos_customer_number": bool(fineos_customer_number),
                    "has_date_of_birth": bool(date_of_birth),
                    "has_tax_id": bool(tax_id),
                },
            )
            continue

        info: Dict[str, str] = {
            Constants.CUSTOMER_NUMBER_FIELD: fineos_customer_number,
            Constants.BENEFIT_START_DATE_FIELD: Constants.TEMPORARY_BENEFIT_START_DATE,
            Constants.FIRST_NAME_FIELD: employee.first_name.replace(",", ""),
            Constants.LAST_NAME_FIELD: employee.last_name.replace(",", ""),
            Constants.BIRTH_DATE_FIELD: date_of_birth.strftime(Constants.DATE_OF_BIRTH_FORMAT),
            Constants.SSN_FIELD: tax_id.tax_identifier.replace("-", ""),
        }

        for key, value in info.items():
            if "," in value:
                value_errors.append(f"({employee.employee_id}, {key})")

        claimants_info.append(info)

    # This should be impossible, but if commas slipped in somehow, bail out.
    # Could just skip the record above, but failing hard for how.
    if len(value_errors) > 0:
        errors = ", ".join(value_errors)
        raise ValueError(f"Value for claimants contains comma: {errors}")

    return claimants_info


def _write_claimants_to_tempfile(claimants: List[Dict]) -> str:
    # Not using file_util.create_csv_from_list() because DIA does not want a header row.
    _handle, csv_filepath = tempfile.mkstemp()
    with open(csv_filepath, mode="w") as csv_file:
        # No quoting because DIA does not ever want quotes around fields and no
        # escape character either (so any value containing quotes will cause an
        # error)
        writer = csv.DictWriter(
            csv_file,
            fieldnames=Constants.CLAIMAINT_LIST_FIELDS,
            quoting=csv.QUOTE_NONE,
            escapechar=None,
        )
        for data in claimants:
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

    claimants = get_claimants_for_outbound(db_session)
    dia_claimant_info = _format_claimants_for_dia_claimant_list(claimants)

    tempfile_path = _write_claimants_to_tempfile(dia_claimant_info)

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
    files = (
        db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.DIA_PAYMENT_LIST.reference_file_type_id,
            ReferenceFile.file_location.like(pending_directory + "%"),
        )
        .all()
    )
    return files


def _convert_dict_with_csv_keys_to_db_keys(csv_data: Dict[str, Any]) -> Dict[str, Any]:
    # Load empty strings as null values.
    return {
        Constants.PAYMENT_CSV_FIELD_MAPPINGS[k]: None if v == "" else v for k, v in csv_data.items()
    }


def _get_matching_dia_reduction_payments(
    db_data: Dict[str, Any], db_session: db.Session
) -> List[DiaReductionPayment]:
    # https://stackoverflow.com/questions/7604967/sqlalchemy-build-query-filter-dynamically-from-dict
    query = db_session.query(DiaReductionPayment)
    for attr, value in db_data.items():
        # Empty fields are read as empty strings. Convert those values to nulls for the database.
        if value == "":
            value = None

        query = query.filter(getattr(DiaReductionPayment, attr) == value)

    return query.all()


def _load_new_rows_from_file(file: io.StringIO, db_session: db.Session) -> None:
    rows = csv.DictReader(file, fieldnames=Constants.PAYMENT_LIST_FIELDS)
    for row in rows:
        db_data = _convert_dict_with_csv_keys_to_db_keys(row)
        if len(_get_matching_dia_reduction_payments(db_data, db_session)) == 0:
            dua_reduction_payment = DiaReductionPayment(**db_data)
            db_session.add(dua_reduction_payment)


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
        end_state=State.DIA_PAYMENT_LIST_SAVED_TO_DB,
        outcome=state_log_util.build_outcome("Loaded DIA payment file into database"),
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
