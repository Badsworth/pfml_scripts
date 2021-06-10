import os
from datetime import date
from decimal import Decimal
from typing import IO, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Extra, Field

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.reductions.dia as dia
import massgov.pfml.util.csv as csv_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
import massgov.pfml.util.pydantic.csv as pydantic_csv_util
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    Claim,
    DiaReductionPayment,
    DiaReductionPaymentReferenceFile,
    Employee,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.payments.payments_util import get_now
from massgov.pfml.reductions.config import get_s3_config
from massgov.pfml.reductions.dia import Metrics
from massgov.pfml.util.batch.log import LogEntry

logger = logging.get_logger(__name__)

DFML_REPORT_FILENAME_PREFIX = "DIA_DFML_"
DFML_REPORT_FILENAME_TIME_FORMAT = "%Y%m%d%H%M"
DFML_REPORT_TIME_FORMAT = "%m/%d/%Y"

DFML_REPORT_CSV_ENCODERS: csv_util.Encoders = {
    date: lambda d: d.strftime("%m/%d/%Y"),
}


class DFMLReportRow(BaseModel):
    # all the raw data from DIA
    customer_number: str = Field(..., alias=dia.Constants.CUSTOMER_NUMBER_FIELD)
    board_no: Optional[str] = Field(None, alias=dia.Constants.BOARD_NO_FIELD)
    event_id: Optional[str] = Field(None, alias=dia.Constants.EVENT_ID)
    event_description: Optional[str] = Field(None, alias=dia.Constants.INS_FORM_OR_MEET_FIELD)
    eve_created_date: Optional[date] = Field(None, alias=dia.Constants.EVE_CREATED_DATE_FIELD)
    event_occurrence_date: Optional[date] = Field(
        None, alias=dia.Constants.FORM_RECEIVED_OR_DISPOSITION_FIELD
    )
    award_id: Optional[str] = Field(None, alias=dia.Constants.AWARD_ID_FIELD)
    award_code: Optional[str] = Field(None, alias=dia.Constants.AWARD_CODE_FIELD)
    award_amount: Optional[Decimal] = Field(None, alias=dia.Constants.AWARD_AMOUNT_FIELD)
    award_date: Optional[date] = Field(None, alias=dia.Constants.AWARD_DATE_FIELD)
    start_date: Optional[date] = Field(None, alias=dia.Constants.START_DATE_FIELD)
    end_date: Optional[date] = Field(None, alias=dia.Constants.END_DATE_FIELD)
    weekly_amount: Optional[Decimal] = Field(None, alias=dia.Constants.WEEKLY_AMOUNT_FIELD)
    award_created_date: Optional[date] = Field(None, alias=dia.Constants.AWARD_CREATED_DATE_FIELD)
    termination_date: Optional[date] = Field(None, alias=dia.Constants.TERMINATION_DATE_FIELD)

    # with additional data about existing claims
    absence_case_id: Optional[str] = Field(None, alias="ABSENCE_CASE_ID")
    absence_period_start_date: Optional[date] = Field(None, alias="ABSENCE_PERIOD_START_DATE")
    absence_period_end_date: Optional[date] = Field(None, alias="ABSENCE_PERIOD_END_DATE")
    absence_case_status: Optional[str] = Field(None, alias="ABSENCE_CASE_STATUS")

    class Config:
        allow_population_by_field_name = True
        extra = Extra.forbid


DFMLReportRowData = Tuple[DiaReductionPayment, Optional[Claim]]


def _make_report_row_from_payment(row_data: DFMLReportRowData) -> DFMLReportRow:
    payment, claim = row_data

    row = DFMLReportRow(
        customer_number=payment.fineos_customer_number,
        board_no=payment.board_no,
        event_id=payment.event_id,
        event_description=payment.event_description,
        eve_created_date=payment.eve_created_date,
        event_occurrence_date=payment.event_occurrence_date,
        award_id=payment.award_id,
        award_code=payment.award_code,
        award_amount=payment.award_amount,
        award_date=payment.award_date,
        start_date=payment.start_date,
        end_date=payment.end_date,
        weekly_amount=payment.weekly_amount,
        award_created_date=payment.award_created_date,
        termination_date=payment.termination_date,
    )

    if claim:
        row.absence_case_id = claim.fineos_absence_id
        row.absence_period_start_date = claim.absence_period_start_date
        row.absence_period_end_date = claim.absence_period_end_date
        row.absence_case_status = (
            AbsenceStatus.get_description(claim.fineos_absence_status_id)
            if claim.fineos_absence_status_id
            else None
        )

    return row


def _get_data_for_report(db_session: db.Session) -> List[DFMLReportRowData]:
    # TODO: currently we are grabbing all data, filtering strategy will be determined in the future
    return (
        db_session.query(DiaReductionPayment, Claim)
        .outerjoin(
            Employee, DiaReductionPayment.fineos_customer_number == Employee.fineos_customer_number
        )
        .outerjoin(Claim, Claim.employee_id == Employee.employee_id)
        .order_by(DiaReductionPayment.created_at, Claim.created_at)
        .all()
    )


def _format_data_for_report(
    reduction_payments: List[DFMLReportRowData],
) -> List[Union[DFMLReportRow, Dict[str, str]]]:
    if len(reduction_payments) == 0:
        return [{field.alias: "NO NEW PAYMENTS" for field in DFMLReportRow.__fields__.values()}]

    return list(map(_make_report_row_from_payment, reduction_payments))


def _get_dfml_report_file_name() -> str:
    return f"{DFML_REPORT_FILENAME_PREFIX}{get_now().strftime(DFML_REPORT_FILENAME_TIME_FORMAT)}"


def _write_dfml_report_rows(
    output_file: IO[str], reduction_payments_info: List[Union[DFMLReportRow, Dict[str, str]]],
) -> None:
    writer = pydantic_csv_util.DataWriter(
        output_file, row_type=DFMLReportRow, encoders=DFML_REPORT_CSV_ENCODERS,
    )
    writer.writeheader()
    writer.writerows(reduction_payments_info)


def create_report_new_dia_payments_to_dfml(db_session: db.Session, log_entry: LogEntry) -> None:
    config = get_s3_config()

    s3_file_path = os.path.join(
        config.s3_dfml_outbound_directory_path, _get_dfml_report_file_name() + ".csv",
    )
    s3_dest = os.path.join(config.s3_bucket_uri, s3_file_path)

    logger.info("Getting data for report")

    report_data = _get_data_for_report(db_session)
    report_rows = _format_data_for_report(report_data)

    unique_reduction_payments = {r.dia_reduction_payment_id: r for r, _ in report_data}.values()

    logger.info(
        "Starting to write report",
        extra={
            "output_file": s3_dest,
            "report_data_count": len(report_data),
            "unique_reduction_payments_count": len(unique_reduction_payments),
        },
    )

    log_entry.set_metrics(
        {
            Metrics.REPORT_DIA_PAYMENTS_TO_DFML_ROW_COUNT: len(report_data),
            Metrics.REPORT_DIA_UNIQUE_REDUCTION_PAYMENTS_COUNT: len(unique_reduction_payments),
        }
    )

    with file_util.open_stream(s3_dest, mode="w") as output_file:
        _write_dfml_report_rows(output_file, report_rows)

    logger.info(
        "Finished writing report",
        extra={
            "output_file": s3_dest,
            "report_data_count": len(report_data),
            "unique_reduction_payments_count": len(unique_reduction_payments),
        },
    )

    # Create ReferenceFile for new export
    ref_file = ReferenceFile(
        file_location=s3_dest,
        reference_file_type_id=ReferenceFileType.DIA_REDUCTION_REPORT_FOR_DFML.reference_file_type_id,
    )
    db_session.add(ref_file)
    db_session.commit()

    # Link the exported DiaReductionPayments to the ReferenceFile
    logger.info("Linking exported reduction payment records to reference file record")
    for reduction_payment in unique_reduction_payments:
        link_obj = DiaReductionPaymentReferenceFile(
            dia_reduction_payment=reduction_payment, reference_file=ref_file
        )
        db_session.add(link_obj)

    # Update StateLog Tables
    logger.info("Creating state log record for report")
    state_log_util.create_finished_state_log(
        associated_model=ref_file,
        end_state=State.DIA_REPORT_FOR_DFML_CREATED,
        outcome=state_log_util.build_outcome("Created payments DFML report for DIA"),
        db_session=db_session,
    )
    db_session.commit()
