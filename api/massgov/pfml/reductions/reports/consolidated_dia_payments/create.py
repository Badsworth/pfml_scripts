import collections
import os
from datetime import date, timedelta
from typing import IO, List, Tuple

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.util.csv as csv_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
import massgov.pfml.util.pydantic.csv as pydantic_csv_util
from massgov.pfml.db.models.employees import (
    Claim,
    DiaReductionPayment,
    Employee,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.delegated_payments.delegated_payments_util import get_now
from massgov.pfml.reductions.config import get_s3_config
from massgov.pfml.reductions.reports.models.dia import DFMLReportRow, make_report_row_from_payment

logger = logging.get_logger(__name__)

DFML_REPORT_FILENAME_PREFIX = "DIA_DFML_CONSOLIDATED_"
DFML_REPORT_FILENAME_TIME_FORMAT = "%Y%m%d%H%M"
DFML_REPORT_TIME_FORMAT = "%m/%d/%Y"

DFML_REPORT_CSV_ENCODERS: csv_util.Encoders = {
    date: lambda d: d.strftime("%m/%d/%Y"),
}

TERMINATION_CODES = ["NT", "GT"]


PaymentGroupKey = collections.namedtuple("PaymentGroupKey", ("fineos_customer_number", "board_no"))


def _get_dfml_report_file_name() -> str:
    return f"{DFML_REPORT_FILENAME_PREFIX}{get_now().strftime(DFML_REPORT_FILENAME_TIME_FORMAT)}"


def _get_dfml_error_report_file_name() -> str:
    return f"{DFML_REPORT_FILENAME_PREFIX}ERRORS_{get_now().strftime(DFML_REPORT_FILENAME_TIME_FORMAT)}"


def create_report_consolidated_dia_payments_to_dfml(db_session: db.Session) -> None:
    logger.info("Building consolidated DIA report")

    report_rows, failures = _get_consolidated_records(db_session)

    report_file_name = _get_dfml_report_file_name()
    file_type_id = ReferenceFileType.DIA_CONSOLIDATED_REDUCTION_REPORT.reference_file_type_id
    ref_file = _save_report_as_csv_in_s3(db_session, report_rows, report_file_name, file_type_id)

    # Update StateLog Tables
    logger.info("Creating state log record for report")
    state_log_util.create_finished_state_log(
        associated_model=ref_file,
        end_state=State.DIA_CONSOLIDATED_REPORT_CREATED,
        outcome=state_log_util.build_outcome("Created consolidated payments report for DIA"),
        db_session=db_session,
    )
    db_session.commit()

    if len(failures) > 0:
        error_report_file_name = _get_dfml_error_report_file_name()
        file_type_id = (
            ReferenceFileType.DIA_CONSOLIDATED_REDUCTION_REPORT_ERRORS.reference_file_type_id
        )
        _save_report_as_csv_in_s3(db_session, failures, error_report_file_name, file_type_id)


# Report Generation
def _get_consolidated_records(
    db_session: db.Session,
) -> Tuple[List[DFMLReportRow], List[DFMLReportRow]]:
    consolidated_report_records: List[DFMLReportRow] = []
    failures: List[DFMLReportRow] = []
    group_keys = _get_distinct_grouping_keys(db_session)

    for fineos_customer_id, board_no in group_keys:
        consolidated_record_group, failed_record_group = _consolidate_record_group(
            db_session, PaymentGroupKey(fineos_customer_id, board_no)
        )
        consolidated_report_records = consolidated_report_records + consolidated_record_group
        failures = failures + failed_record_group

    return (consolidated_report_records, failures)


def _get_distinct_grouping_keys(db_session: db.Session) -> List[Tuple[str, str]]:
    """
    Get a list of tuples with distinct pairs of fineos_customer_number and board_no
    Used to retrieve groups to build report
    """
    return (
        db_session.query(DiaReductionPayment.fineos_customer_number, DiaReductionPayment.board_no)
        .order_by(DiaReductionPayment.fineos_customer_number, DiaReductionPayment.board_no)
        .distinct()
        .all()
    )


def _consolidate_record_group(
    db_session: db.Session, group_key: PaymentGroupKey
) -> Tuple[List[DFMLReportRow], List[DFMLReportRow]]:
    """
    Implementation requirements provided by DIA:
    End Date Logic and use cases:
    Each pay record that is received must reference the subsequent record received (organized by award created date) to determine what the end date is for that record:
        1) If there is no subsequent record than the end date will be 156 weeks from the original start date
        2) If the subsequent record is a continuation of the benefit (no termination code – NT/GT) but the benefit amount changes, then the end date should be one day prior to the start date for the new benefit record with the updated benefit amount.
            a.Important note: when going chronologically, if the benefit amount changes and is not followed by a subsequent termination record, the end date 156-week logic should reference the original start date.
        3) The subsequent record is a termination (NT/GT): The end date will be the date of the termination.
        4) If the subsequent record is not a termination and there is no change in benefit amount, it should be ignored.

    Implementation logic:
    Read the DIA Benefits file and group it by FINEOS Customer Number (DFML_ID) and WC Board Number (BOARD_NO). For each group apply the following logic:
        1. If the TERMINATION_DATE is empty for the group, set TERMINATION_DATE to START_DATE + 156 weeks.
        2. Check if the group’s benefit amount changes, if yes, use START_DATE of the next row and use that as the TERMINATION_DATE for above rows.
        3. Check if the INS_FORM_OR_MEET column value is NT or GT, if yes use its TERMINATION_DATE for the row above it.
        4.Ignore the rest

    If there are records that do not match the above logic, they will be captured in an error report.
    """
    consolidated_records: List[DFMLReportRow] = []

    records = _get_record_group(db_session, group_key)

    curr, nxt = 0, 1

    original_start_date = records[curr].start_date

    # Records are sorted by start_date when retrieved from the db.
    # By default, Postgres moves nulls to the end of the group.
    # If the first record in the group has a null start_date we know that none of the records will have start_date populated,
    # so we cannot operate on this group.
    if original_start_date is None:
        logger.info(
            "First record in group missing start_date, unable to process",
            fineos_customer_number=group_key.fineos_customer_number,
            board_no=group_key.board_no,
        )
        return ([], records)

    #  If there is no subsequent record the end date will be 156 weeks from the earliest start date
    end_date_156_weeks_from_original_start = original_start_date + timedelta(weeks=156)

    try:
        while nxt <= len(records):
            current_record = records[curr]

            if nxt == len(records):
                last_record = records[-1]
                current_record.termination_date = (
                    last_record.termination_date or end_date_156_weeks_from_original_start
                )
                consolidated_records.append(current_record)
                break

            nxt_record = records[nxt]

            if nxt_record.event_description in TERMINATION_CODES:
                # If we encounter a termination record, we want to record it's end_date and append a consolidated record to the report
                current_record.termination_date = (
                    nxt_record.termination_date or end_date_156_weeks_from_original_start
                )
                consolidated_records.append(current_record)
                # Then we want to skip over the termination record and set the 'current' record to the one following the termination.
                curr = nxt + 1
                nxt += 1

            elif (
                nxt_record.weekly_amount is not None
                and nxt_record.weekly_amount != current_record.weekly_amount
            ):
                if nxt_record.start_date is not None:
                    current_record.termination_date = nxt_record.start_date - timedelta(days=1)
                    consolidated_records.append(current_record)
                    curr = nxt
                else:
                    # Next record needs a start date
                    logger.info(
                        "Issue processing record group: Change in amount without new start date",
                        fineos_customer_number=group_key.fineos_customer_number,
                        board_no=group_key.board_no,
                    )
                    return ([], records)

            nxt += 1
    except Exception as err:
        logger.info(
            "Error processing record group",
            message=str(err),
            fineos_customer_number=group_key.fineos_customer_number,
            board_no=group_key.board_no,
        )
        return ([], records)

    return (consolidated_records, [])


def _get_record_group(db_session: db.Session, group_key: PaymentGroupKey) -> List[DFMLReportRow]:
    data = (
        db_session.query(DiaReductionPayment, Claim)
        .outerjoin(
            Employee, DiaReductionPayment.fineos_customer_number == Employee.fineos_customer_number
        )
        .outerjoin(Claim, Claim.employee_id == Employee.employee_id)
        .filter(DiaReductionPayment.fineos_customer_number == group_key.fineos_customer_number)
        .filter(DiaReductionPayment.board_no == group_key.board_no)
        .order_by(
            DiaReductionPayment.start_date,
            DiaReductionPayment.award_created_date,
            DiaReductionPayment.created_at,
            Claim.created_at,
        )
        .all()
    )

    return [make_report_row_from_payment(payment) for payment in data]


# S3 Operations
def _write_dfml_report_rows(
    output_file: IO[str], reduction_payments_info: List[DFMLReportRow],
) -> None:
    writer = pydantic_csv_util.DataWriter(
        output_file, row_type=DFMLReportRow, encoders=DFML_REPORT_CSV_ENCODERS,
    )
    writer.writeheader()
    writer.writerows(reduction_payments_info)


def _save_report_as_csv_in_s3(
    db_session: db.Session, report: List[DFMLReportRow], file_name: str, reference_file_type_id: int
) -> ReferenceFile:
    config = get_s3_config()

    s3_file_path = os.path.join(config.s3_dfml_outbound_directory_path, file_name + ".csv",)

    s3_dest = os.path.join(config.s3_bucket_uri, s3_file_path)

    logger.info(
        "Starting to write report",
        extra={"output_file": s3_dest, "report_data_count": len(report)},
    )

    with file_util.open_stream(s3_dest, mode="w") as output_file:
        _write_dfml_report_rows(output_file, report)

    logger.info(
        "Finished writing report",
        extra={"output_file": s3_dest, "report_data_count": len(report),},
    )

    # Create ReferenceFile for new export
    ref_file = ReferenceFile(file_location=s3_dest, reference_file_type_id=reference_file_type_id,)

    db_session.add(ref_file)
    db_session.commit()

    return ref_file
