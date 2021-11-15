import csv
import io
import os
import pathlib
import re
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.util.batch.log as batch_log
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    Claim,
    DuaReductionPayment,
    DuaReductionPaymentReferenceFile,
    Employee,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.delegated_payments.delegated_payments_util import (
    get_now,
    move_file_and_update_ref_file,
)
from massgov.pfml.reductions.common import AgencyLoadResult, get_claimants_for_outbound
from massgov.pfml.reductions.config import get_moveit_config, get_s3_config
from massgov.pfml.util.datetime import utcnow
from massgov.pfml.util.files import create_csv_from_list, upload_to_s3
from massgov.pfml.util.sftp_s3_transfer import (
    SftpS3TransferConfig,
    copy_from_sftp_to_s3_and_archive_files,
    copy_to_sftp_and_archive_s3_files,
)

logger = logging.get_logger(__name__)

DuaReductionPaymentAndClaim = Tuple[DuaReductionPayment, Optional[Claim]]


class Metrics:
    PENDING_DUA_PAYMENT_REFERENCE_FILES_COUNT = "pending_dua_payment_reference_files_count"
    SUCCESSFUL_DUA_PAYMENT_REFERENCE_FILES_COUNT = "successful_dua_payment_reference_files_count"
    UNSUCCESSFUL_DUA_PAYMENT_REFERENCE_FILES_COUNT = (
        "unsuccessful_dua_payment_reference_files_count"
    )
    NEW_DUA_PAYMENT_ROW_COUNT = "new_dua_payment_row_count"
    TOTAL_DUA_PAYMENT_ROW_COUNT = "total_dua_payment_row_count"
    CLAIMANTS_SENT_TO_DUA_COUNT = "claimants_sent_to_dua_count"
    DUA_PAYMENT_LISTS_DOWNLOADED_COUNT = "dua_payment_lists_downloaded_count"
    REPORT_DUA_PAYMENTS_TO_DFML_ROW_COUNT = "report_dua_payments_to_dfml_row_count"


class Constants:
    TEMPORARY_BENEFIT_START_DATE = "20210101"

    CLAIMANT_LIST_FILENAME_PREFIX = "DFML_CLAIMANTS_FOR_DUA_"
    CLAIMANT_LIST_FILENAME_TIME_FORMAT = "%Y%m%d%H%M"
    # The "DFML Report" is the "payment list" file. Some things will refer to
    # "payment list" others will use "payment report" or just "report", they are
    # the all the same thing, means these files.
    PAYMENT_LIST_FILENAME_PREFIX = "DUA_DFML_"
    PAYMENT_LIST_FILENAME_TIME_FORMAT = "%Y%m%d%H%M"
    PAYMENT_REPORT_TIME_FORMAT = "%m/%d/%Y"

    # Originally we sent DUA one row per absence case and this CASE_ID field
    # held the absence case id.
    #
    # But we switched to sending one row per claimant (as they may have multiple
    # cases over time), so the field has been repurposed to hold the customer
    # number to avoid DUA needing to change anything on their end.
    CASE_ID_FIELD = "CASE_ID"

    # We changed the primary key from being by absence case to being by customer
    # number. This is the first column in the DUA report.
    CUSTOMER_ID_FIELD = "CUSTOMER_ID"
    EMPR_FEIN_FIELD = "EMPR_FEIN"
    WARRANT_DT_OUTBOUND_DFML_REPORT_FIELD = "PAYMENT_DATE"
    RQST_WK_DT_OUTBOUND_DFML_REPORT_FIELD = "BENEFIT_WEEK_START_DATE"
    WBA_ADDITIONS_OUTBOUND_DFML_REPORT_FIELD = "GROSS_PAYMENT_AMOUNT"
    PAID_AM_OUTBOUND_DFML_REPORT_FIELD = "NET_PAYMENT_AMOUNT"
    FRAUD_IND_FIELD = "FRAUD_IND"
    BYB_DT_FIELD = "BYB_DT"
    BYE_DT_FIELD = "BYE_DT"
    DATE_PAYMENT_ADDED_TO_REPORT_FIELD = "DATE_PAYMENT_ADDED_TO_REPORT"
    BENEFIT_START_DATE_FIELD = "START_DATE"
    SSN_FIELD = "SSN"
    WARRANT_DT_FIELD = "WARRANT_DT"
    RQST_WK_DT_FIELD = "RQST_WK_DT"
    WBA_ADDITIONS_FIELD = "WBA_ADDITIONS"
    PAID_AM_FIELD = "PAID_AM"
    ABSENCE_CASE_ID_FIELD = "ABSENCE_CASE_ID"
    ABSENCE_CASE_STATUS_FIELD = "ABSENCE_CASE_STATUS"
    ABSENCE_CASE_PERIOD_START_FIELD = "ABSENCE_PERIOD_START_DATE"
    ABSENCE_CASE_PERIOD_END_FIELD = "ABSENCE_PERIOD_END_DATE"

    CLAIMANT_LIST_FIELDS = [
        CASE_ID_FIELD,
        SSN_FIELD,
        BENEFIT_START_DATE_FIELD,
    ]

    DFML_REPORT_CSV_COLUMN_TO_TABLE_DATA_FIELD_MAP = {
        CUSTOMER_ID_FIELD: "fineos_customer_number",
        WARRANT_DT_OUTBOUND_DFML_REPORT_FIELD: "payment_date",
        RQST_WK_DT_OUTBOUND_DFML_REPORT_FIELD: "request_week_begin_date",
        WBA_ADDITIONS_OUTBOUND_DFML_REPORT_FIELD: "gross_payment_amount_cents",
        PAID_AM_OUTBOUND_DFML_REPORT_FIELD: "payment_amount_cents",
        FRAUD_IND_FIELD: "fraud_indicator",
        BYB_DT_FIELD: "benefit_year_begin_date",
        BYE_DT_FIELD: "benefit_year_end_date",
        DATE_PAYMENT_ADDED_TO_REPORT_FIELD: "created_at",
        ABSENCE_CASE_ID_FIELD: "claim.fineos_absence_id",
        ABSENCE_CASE_PERIOD_START_FIELD: "claim.absence_period_start_date",
        ABSENCE_CASE_PERIOD_END_FIELD: "claim.absence_period_end_date",
        ABSENCE_CASE_STATUS_FIELD: "claim.fineos_absence_status.absence_status_description",
    }

    DUA_PAYMENT_CSV_COLUMN_TO_TABLE_DATA_FIELD_MAP = {
        CASE_ID_FIELD: "fineos_customer_number",
        EMPR_FEIN_FIELD: "employer_fein",
        WARRANT_DT_FIELD: "payment_date",
        RQST_WK_DT_FIELD: "request_week_begin_date",
        WBA_ADDITIONS_FIELD: "gross_payment_amount_cents",
        PAID_AM_FIELD: "payment_amount_cents",
        FRAUD_IND_FIELD: "fraud_indicator",
        BYB_DT_FIELD: "benefit_year_begin_date",
        BYE_DT_FIELD: "benefit_year_end_date",
    }


def copy_claimant_list_to_moveit(db_session: db.Session) -> None:
    s3_config = get_s3_config()
    moveit_config = get_moveit_config()

    transfer_config = SftpS3TransferConfig(
        s3_bucket_uri=s3_config.s3_bucket_uri,
        source_dir=s3_config.s3_dua_outbound_directory_path,
        archive_dir=s3_config.s3_dua_archive_directory_path,
        dest_dir=moveit_config.moveit_dua_outbound_path,
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


def _format_claimants_for_dua_claimant_list(claimants: List[Employee]) -> List[Dict[str, str]]:
    claimants_info = []

    for employee in claimants:
        fineos_customer_number = employee.fineos_customer_number
        tax_id = employee.tax_identifier

        if not (fineos_customer_number and tax_id):
            logger.warning(
                "Employee missing required information. Skipping.",
                extra={
                    "employee_id": employee.employee_id,
                    "has_fineos_customer_number": bool(fineos_customer_number),
                    "has_tax_id": bool(tax_id),
                },
            )
            continue

        info = {
            Constants.CASE_ID_FIELD: fineos_customer_number,
            Constants.SSN_FIELD: tax_id.tax_identifier.replace("-", ""),
            Constants.BENEFIT_START_DATE_FIELD: Constants.TEMPORARY_BENEFIT_START_DATE,
        }

        claimants_info.append(info)

    return claimants_info


def _get_claimants_info_csv_path(claimants: List[Dict]) -> pathlib.Path:
    file_name = Constants.CLAIMANT_LIST_FILENAME_PREFIX + get_now().strftime(
        Constants.CLAIMANT_LIST_FILENAME_TIME_FORMAT
    )
    return file_util.create_csv_from_list(claimants, Constants.CLAIMANT_LIST_FIELDS, file_name)


def create_list_of_claimants(db_session: db.Session, log_entry: batch_log.LogEntry) -> None:
    config = get_s3_config()

    claimants = get_claimants_for_outbound(db_session)

    dua_claimant_info = _format_claimants_for_dua_claimant_list(claimants)

    claimant_info_path = _get_claimants_info_csv_path(dua_claimant_info)

    log_entry.set_metrics({Metrics.CLAIMANTS_SENT_TO_DUA_COUNT: len(dua_claimant_info)})

    s3_dest = os.path.join(
        config.s3_bucket_uri, config.s3_dua_outbound_directory_path, claimant_info_path.name
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


def load_new_dua_payments(
    db_session: db.Session, log_entry: batch_log.LogEntry
) -> AgencyLoadResult:
    s3_config = get_s3_config()
    pending_dir = os.path.join(s3_config.s3_bucket_uri, s3_config.s3_dua_pending_directory_path)
    archive_dir = os.path.join(s3_config.s3_bucket_uri, s3_config.s3_dua_archive_directory_path)
    error_dir = os.path.join(s3_config.s3_bucket_uri, s3_config.s3_dfml_error_directory_path)

    result = AgencyLoadResult()
    for ref_file in _get_pending_dua_payment_reference_files(pending_dir, db_session):
        log_entry.increment(Metrics.PENDING_DUA_PAYMENT_REFERENCE_FILES_COUNT)
        result.found_pending_files = True

        try:
            new_row_count, total_row_count = _load_dua_payment_from_reference_file(
                ref_file, archive_dir, db_session
            )
            log_entry.increment(Metrics.SUCCESSFUL_DUA_PAYMENT_REFERENCE_FILES_COUNT)
            log_entry.increment(Metrics.NEW_DUA_PAYMENT_ROW_COUNT, new_row_count)
            log_entry.increment(Metrics.TOTAL_DUA_PAYMENT_ROW_COUNT, total_row_count)

        except Exception:
            # Move to error directory and update ReferenceFile.
            filename = os.path.basename(ref_file.file_location)
            dest_path = os.path.join(error_dir, filename)
            move_file_and_update_ref_file(db_session, dest_path, ref_file)

            # transition to an error state
            state_log_util.create_finished_state_log(
                associated_model=ref_file,
                end_state=State.DUA_PAYMENT_LIST_ERROR_SAVE_TO_DB,
                outcome=state_log_util.build_outcome(
                    "Error loading DUA payment file into database"
                ),
                db_session=db_session,
            )
            db_session.commit()

            log_entry.increment(Metrics.UNSUCCESSFUL_DUA_PAYMENT_REFERENCE_FILES_COUNT)

            # Log exceptions but continue attempting to load other payment files into the database.
            logger.exception(
                "Failed to load new DUA payments to database from file",
                extra={
                    "file_location": ref_file.file_location,
                    "reference_file_id": ref_file.reference_file_id,
                },
            )
    return result


def _load_dua_payment_from_reference_file(
    ref_file: ReferenceFile, archive_directory: str, db_session: db.Session,
) -> Tuple[int, int]:
    new_row_count = 0
    total_row_count = 0

    # Load to database.
    with file_util.open_stream(ref_file.file_location) as f:
        new_row_count, total_row_count = _load_new_rows_from_file(f, db_session)

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

    return new_row_count, total_row_count


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
) -> List[DuaReductionPayment]:
    # https://stackoverflow.com/questions/7604967/sqlalchemy-build-query-filter-dynamically-from-dict
    query = db_session.query(DuaReductionPayment)
    for attr, value in db_data.items():
        # Empty fields are read as empty strings. Convert those values to nulls for the database.
        if value == "":
            value = None

        query = query.filter(getattr(DuaReductionPayment, attr) == value)

    return query.all()


def _load_new_rows_from_file(file: io.StringIO, db_session: db.Session) -> Tuple[int, int]:
    new_row_count = 0
    total_row_count = 0

    for row in csv.DictReader(file):
        total_row_count += 1
        db_data = _convert_dict_with_csv_keys_to_db_keys(row)
        if len(_get_matching_dua_reduction_payments(db_data, db_session)) == 0:
            dua_reduction_payment = DuaReductionPayment(**db_data)
            db_session.add(dua_reduction_payment)

            new_row_count += 1

    return new_row_count, total_row_count

    # Commit these changes to the database after we've updated the ReferenceFile's file_location
    # in the calling code.


def download_payment_list_from_moveit(db_session: db.Session, log_entry: batch_log.LogEntry) -> int:
    s3_config = get_s3_config()
    moveit_config = get_moveit_config()

    transfer_config = SftpS3TransferConfig(
        s3_bucket_uri=s3_config.s3_bucket_uri,
        source_dir=moveit_config.moveit_dua_inbound_path,
        archive_dir=moveit_config.moveit_dua_archive_path,
        dest_dir=s3_config.s3_dua_pending_directory_path,
        sftp_uri=moveit_config.moveit_sftp_uri,
        ssh_key_password=moveit_config.moveit_ssh_key_password,
        ssh_key=moveit_config.moveit_ssh_key,
        regex_filter=re.compile(r"DUA_DFML_\d+.csv"),
    )

    copied_reference_files = copy_from_sftp_to_s3_and_archive_files(transfer_config, db_session)
    for ref_file in copied_reference_files:
        ref_file.reference_file_type_id = ReferenceFileType.DUA_PAYMENT_LIST.reference_file_type_id
        state_log_util.create_finished_state_log(
            associated_model=ref_file,
            end_state=State.DUA_PAYMENT_LIST_SAVED_TO_S3,
            outcome=state_log_util.build_outcome("Saved DUA payment list to S3"),
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

    log_entry.set_metrics({Metrics.DUA_PAYMENT_LISTS_DOWNLOADED_COUNT: len(copied_reference_files)})
    return len(copied_reference_files)


def _convert_cent_to_dollars(cent: Optional[int] = 0) -> Decimal:
    cent_str = f"{cent or 0 :02}"
    dollar = cent_str[:-2] + "." + cent_str[-2:]
    return Decimal(dollar)


def _get_non_submitted_reduction_payments(
    db_session: db.Session,
) -> List[DuaReductionPaymentAndClaim]:
    """
    Include only payment records created within the last 90 days
    """
    ninety_days_ago = utcnow().date() - timedelta(days=90)
    return (
        db_session.query(DuaReductionPayment, Claim)
        .outerjoin(
            Employee, DuaReductionPayment.fineos_customer_number == Employee.fineos_customer_number,
        )
        .outerjoin(Claim, Claim.employee_id == Employee.employee_id)
        .filter(DuaReductionPayment.created_at >= ninety_days_ago)
        .order_by(DuaReductionPayment.created_at, Claim.created_at)
        .all()
    )


def _format_date_for_report(raw_date: Optional[date]) -> str:
    if raw_date is None:
        return ""

    return raw_date.strftime(Constants.PAYMENT_REPORT_TIME_FORMAT)


def _format_reduction_payments_for_report(
    reduction_payments: List[DuaReductionPaymentAndClaim],
) -> List[Dict]:
    if len(reduction_payments) == 0:
        return [
            {
                field: "NO NEW PAYMENTS"
                for field in Constants.DFML_REPORT_CSV_COLUMN_TO_TABLE_DATA_FIELD_MAP.keys()
            }
        ]
    payments = []

    for payment, claim in reduction_payments:
        info = {
            Constants.CUSTOMER_ID_FIELD: payment.fineos_customer_number,
            Constants.WARRANT_DT_OUTBOUND_DFML_REPORT_FIELD: _format_date_for_report(
                payment.payment_date
            ),
            Constants.RQST_WK_DT_OUTBOUND_DFML_REPORT_FIELD: _format_date_for_report(
                payment.request_week_begin_date
            ),
            Constants.WBA_ADDITIONS_OUTBOUND_DFML_REPORT_FIELD: _convert_cent_to_dollars(
                payment.gross_payment_amount_cents
            ),
            Constants.PAID_AM_OUTBOUND_DFML_REPORT_FIELD: _convert_cent_to_dollars(
                payment.payment_amount_cents
            ),
            Constants.FRAUD_IND_FIELD: payment.fraud_indicator,
            Constants.BYB_DT_FIELD: _format_date_for_report(payment.benefit_year_begin_date),
            Constants.BYE_DT_FIELD: _format_date_for_report(payment.benefit_year_end_date),
            Constants.DATE_PAYMENT_ADDED_TO_REPORT_FIELD: _format_date_for_report(
                payment.created_at
            ),
        }

        if claim is not None:
            info.update(
                {
                    Constants.ABSENCE_CASE_ID_FIELD: claim.fineos_absence_id,
                    Constants.ABSENCE_CASE_STATUS_FIELD: (
                        AbsenceStatus.get_description(claim.fineos_absence_status_id)
                        if claim.fineos_absence_status_id
                        else None
                    ),
                    Constants.ABSENCE_CASE_PERIOD_START_FIELD: _format_date_for_report(
                        claim.absence_period_start_date
                    ),
                    Constants.ABSENCE_CASE_PERIOD_END_FIELD: _format_date_for_report(
                        claim.absence_period_end_date
                    ),
                }
            )

        payments.append(info)
    return payments


def _get_new_dua_payments_to_dfml_report_csv_path(
    reduction_payments_info: List[Dict],
) -> pathlib.Path:
    file_name = Constants.PAYMENT_LIST_FILENAME_PREFIX + get_now().strftime(
        Constants.PAYMENT_LIST_FILENAME_TIME_FORMAT
    )
    return create_csv_from_list(
        reduction_payments_info,
        list(Constants.DFML_REPORT_CSV_COLUMN_TO_TABLE_DATA_FIELD_MAP.keys()),
        file_name,
    )


def create_report_new_dua_payments_to_dfml(
    db_session: db.Session, log_entry: batch_log.LogEntry
) -> None:
    config = get_s3_config()

    # get non-submitted payments
    non_submitted_payments = _get_non_submitted_reduction_payments(db_session)

    # get reduction payment report info
    reduction_payment_report_info = _format_reduction_payments_for_report(non_submitted_payments)

    # get csv path for reduction report
    reduction_report_csv_path = _get_new_dua_payments_to_dfml_report_csv_path(
        reduction_payment_report_info
    )

    log_entry.set_metrics(
        {Metrics.REPORT_DUA_PAYMENTS_TO_DFML_ROW_COUNT: len(non_submitted_payments)}
    )

    # Upload info to s3
    s3_dest = os.path.join(
        config.s3_bucket_uri, config.s3_dfml_outbound_directory_path, reduction_report_csv_path.name
    )
    upload_to_s3(str(reduction_report_csv_path), s3_dest)

    # Create ReferenceFile
    ref_file = ReferenceFile(
        file_location=s3_dest,
        reference_file_type_id=ReferenceFileType.DUA_REDUCTION_REPORT_FOR_DFML.reference_file_type_id,
    )
    db_session.add(ref_file)
    db_session.commit()

    unique_reduction_payments = {
        p.dua_reduction_payment_id: p for p, _ in non_submitted_payments
    }.values()

    # Create objects that link DuaReductionPayments to the ReferenceFile.
    for unique_reduction_payment in unique_reduction_payments:
        link_obj = DuaReductionPaymentReferenceFile(
            dua_reduction_payment=unique_reduction_payment, reference_file=ref_file
        )
        db_session.add(link_obj)

    # Update StateLog Tables
    state_log_util.create_finished_state_log(
        associated_model=ref_file,
        end_state=State.DUA_REPORT_FOR_DFML_CREATED,
        outcome=state_log_util.build_outcome("Created payments DFML report for DUA"),
        db_session=db_session,
    )

    # commit StateLog to db
    db_session.commit()
