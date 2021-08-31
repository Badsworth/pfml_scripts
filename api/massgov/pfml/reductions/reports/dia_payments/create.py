import os
from datetime import date
from typing import IO, Dict, List, Union

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.util.csv as csv_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
import massgov.pfml.util.pydantic.csv as pydantic_csv_util
from massgov.pfml.db.models.employees import (
    Claim,
    DiaReductionPayment,
    DiaReductionPaymentReferenceFile,
    Employee,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.delegated_payments.delegated_payments_util import get_now
from massgov.pfml.reductions.config import get_s3_config
from massgov.pfml.reductions.dia import Metrics
from massgov.pfml.reductions.reports.models.dia import (
    DFMLReportRow,
    DFMLReportRowData,
    make_report_row_from_payment,
)
from massgov.pfml.util.batch.log import LogEntry

logger = logging.get_logger(__name__)

DFML_REPORT_FILENAME_PREFIX = "DIA_DFML_"
DFML_REPORT_FILENAME_TIME_FORMAT = "%Y%m%d%H%M"
DFML_REPORT_TIME_FORMAT = "%m/%d/%Y"

DFML_REPORT_CSV_ENCODERS: csv_util.Encoders = {
    date: lambda d: d.strftime("%m/%d/%Y"),
}


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

    return list(map(make_report_row_from_payment, reduction_payments))


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
