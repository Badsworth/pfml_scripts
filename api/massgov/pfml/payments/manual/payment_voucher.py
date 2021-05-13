#
# Manual payment voucher tool - main entrypoint.
#
# Reads vpei.csv, vpeipaymentdetails.csv, vpeiclaimdetails.csv, and VBI_REQUESTEDABSENCE_SOM.
#
# Writes payment_voucher.csv.
#
# Makes no database changes. Does not move or remove any processed files.
#
# Test like this (requires database records to exist):
#   poetry run payments-manual-payment-voucher tests/payments/manual/test_files/ manual_payments/ |& python3 massgov/pfml/util/logging/decodelog.py
#
# Run locally like this from within poetry run python REPL (see test_payment_voucher.py for details about test scenarios):
#   import massgov.pfml.payments.mock.fineos_extract_generator as fineos_extract_generator
#   import massgov.pfml.payments.mock.payments_test_scenario_generator as scenario_generator
#   from massgov.pfml.payments.manual import payment_voucher
#   scenario_list = [scenario_generator.ScenarioNameWithCount(scenario_generator.ScenarioName.SCENARIO_VOUCHER_E, 1)]
#   scenario_config = scenario_generator.ScenarioDataConfig(scenario_list, ssn_id_base=526000028, fein_id_base=626000028)
#   scenario_data_list = fineos_extract_generator.generate(scenario_config, "mock_fineos_payments_input_files")
#   config = payment_voucher.Configuration(["mock_fineos_payments_input_files", "mock_voucher_output_files"])
#   payment_voucher.run_voucher_process(config)
#

import argparse
import csv
import datetime
import io
import os.path
import pathlib
import random
import string
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

import smart_open
from sqlalchemy.exc import SQLAlchemyError

import massgov.pfml.db
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.batch.log as batch_log
import massgov.pfml.util.datetime
import massgov.pfml.util.files
import massgov.pfml.util.logging
import massgov.pfml.util.logging.audit
from massgov.pfml.api.util import state_log_util
from massgov.pfml.db.models.employees import Employee, Flow, State, TaxIdentifier
from massgov.pfml.payments import fineos_payment_export, fineos_vendor_export, gax
from massgov.pfml.payments.manual.payment_voucher_csv import (
    PaymentVoucherCSV,
    WritebackCSV,
    payment_voucher_csv_writer,
    writeback_csv_writer,
)
from massgov.pfml.payments.step import Step
from massgov.pfml.util.sentry import initialize_sentry

logger = massgov.pfml.util.logging.get_logger("massgov.pfml.payments.manual.manual_payment")

# File names
VBI_REQUESTED_ASBSENCE = "VBI_REQUESTEDABSENCE.csv"


@dataclass
class Extract:
    file_location: str
    indexed_data: Dict[str, Dict[str, str]] = field(default_factory=dict)


class VoucherExtractData:
    vbi_requested_absence: Extract

    def __init__(self, s3_locations: List[str]):
        for s3_location in s3_locations:
            if s3_location.endswith(VBI_REQUESTED_ASBSENCE):
                self.vbi_requested_absence = Extract(s3_location)


class Configuration:
    input_path: str
    output_path: str
    payment_date: Optional[datetime.date]
    writeback: Optional[str]

    def __init__(self, input_args: List[str]):
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(description="Manual payment voucher tool")
        parser.add_argument("input_path", type=str, help="Input directory path (local or s3)")
        parser.add_argument("output_path", type=str, help="Output directory path (local or s3)")
        parser.add_argument(
            "--payment_date", type=datetime.date.fromisoformat, help="Override payment date"
        )
        parser.add_argument(
            "--writeback", type=str, help="Destination path for FINEOS writeback CSV"
        )

        args = parser.parse_args(input_args)
        self.input_path = args.input_path
        self.output_path = args.output_path
        self.payment_date = args.payment_date
        self.writeback = args.writeback


class PaymentVoucherStep(Step):
    """Step to run Payment Voucher process."""

    config: Configuration

    def __init__(
        self,
        db_session: massgov.pfml.db.Session,
        log_entry_db_session: massgov.pfml.db.Session,
        config: Configuration,
    ) -> None:
        super().__init__(db_session=db_session, log_entry_db_session=log_entry_db_session)
        self.config = config

    def run_step(self) -> None:
        process_extracts_to_payment_voucher(
            input_path=self.config.input_path,
            output_path=self.config.output_path,
            payment_date=self.config.payment_date,
            writeback=self.config.writeback,
            db_session=self.db_session,
            log_entry=self.log_entry,
        )


def main():
    """Main entry point for manual payment voucher tool."""
    initialize_sentry()
    massgov.pfml.util.logging.audit.init_security_logging()
    massgov.pfml.util.logging.init("manual_payment")

    config = Configuration(sys.argv[1:])

    logger.info(
        "input_path %s, output_path %s, payment_date %s, writeback %s",
        config.input_path,
        config.output_path,
        config.payment_date,
        config.writeback,
    )
    run_voucher_process(config)


def run_voucher_process(config: Configuration) -> None:
    db_session_raw = massgov.pfml.db.init(sync_lookups=True)
    try:
        with batch_log.LogEntry(
            db_session_raw, "Payment voucher"
        ) as log_entry, massgov.pfml.db.session_scope(db_session_raw) as db_session:
            log_entry.set_metrics(vars(config))
            process_extracts_to_payment_voucher(
                config.input_path,
                config.output_path,
                config.payment_date,
                config.writeback,
                db_session,
                log_entry,
            )
    except Exception as ex:
        logger.exception("%s", ex)
        sys.exit(1)


def process_extracts_to_payment_voucher(
    input_path: str,
    output_path: str,
    payment_date: Optional[datetime.date],
    writeback: Optional[str],
    db_session: massgov.pfml.db.Session,
    log_entry: Optional[batch_log.LogEntry],
) -> None:
    """Get FINEOS extract files from input path and write to payment voucher CSV."""
    if payment_date is None:
        payment_date = datetime.date.today()

    input_files = copy_input_files_to_output_path(input_path, output_path)

    # Read vpei.csv, vpeipaymentdetails.csv, vpeiclaimdetails.csv
    payment_extract_data = fineos_payment_export.ExtractData(input_files, "manual")
    with tempfile.TemporaryDirectory() as temp_dir:
        fineos_payment_export.download_and_process_data(
            payment_extract_data, pathlib.Path(temp_dir)
        )

    # Read VBI_REQUESTEDABSENCE_SOM.csv, Employee_feed.csv, LeavePlan_info.csv
    vendor_extract_data = fineos_vendor_export.ExtractData(input_files, "manual")
    with tempfile.TemporaryDirectory() as vendor_temp_dir:
        fineos_vendor_export.download_and_index_data(vendor_extract_data, vendor_temp_dir)

    # Read the VBI_REQUESTEDABSENCE.csv
    # Not to be confused with the similarly named VBI_REQUESTEDABSENCE_SOM.csv
    voucher_extract_data = VoucherExtractData(input_files)
    with tempfile.TemporaryDirectory() as voucher_temp_dir:
        download_and_index_voucher_data(voucher_extract_data, voucher_temp_dir)

    csv_path = os.path.join(
        output_path, datetime.datetime.now().strftime("%Y%m%d_%H%M%S_payment_voucher.csv")
    )
    writeback_path = os.path.join(
        output_path, datetime.datetime.now().strftime("%Y%m%d_%H%M%S_writeback.csv")
    )
    with smart_open.open(csv_path, "w", newline="") as output_file, smart_open.open(
        writeback_path, "w", newline=""
    ) as writeback_file:
        process_payment_records(
            payment_extract_data,
            vendor_extract_data,
            voucher_extract_data,
            output_file,
            writeback_file,
            payment_date,
            db_session,
            log_entry,
        )

    # Optionally copy the writeback CSV to a destination location.
    if writeback:
        logger.info("copy writeback %s to %s", writeback_path, writeback)
        massgov.pfml.util.files.copy_file(writeback_path, writeback)


def copy_input_files_to_output_path(input_path, output_path):
    """Copy the input files to the output directory for use and as an archive."""
    input_files = []
    for input_file in massgov.pfml.util.files.list_files(input_path):
        copy = False
        for pattern in (
            "Employee_feed.csv",
            "LeavePlan_info.csv",
            "VBI_REQUESTEDABSENCE_SOM.csv",
            VBI_REQUESTED_ASBSENCE,
            "vpei.csv",
            "vpeiclaimdetails.csv",
            "vpeipaymentdetails.csv",
        ):
            if input_file.endswith(pattern):
                copy = True
        if not copy:
            continue
        source = os.path.join(input_path, input_file)
        destination = os.path.join(output_path, input_file)
        logger.info("copy %s to %s", source, destination)
        massgov.pfml.util.files.copy_file(source, destination)
        input_files.append(destination)
    return input_files


def process_payment_records(
    payment_extract_data: fineos_payment_export.ExtractData,
    vendor_extract_data: fineos_vendor_export.ExtractData,
    voucher_extract_data: VoucherExtractData,
    output_file: io.TextIOWrapper,
    writeback_file: io.TextIOWrapper,
    payment_date: datetime.date,
    db_session: massgov.pfml.db.Session,
    log_entry: Optional[batch_log.LogEntry],
) -> None:
    """Process the extracted records and write to output CSV."""
    output_csv = payment_voucher_csv_writer(output_file)
    writeback_csv = writeback_csv_writer(writeback_file)

    if log_entry is not None:
        log_entry.set_metrics({"total": len(payment_extract_data.pei.indexed_data)})

    for ci_index, pei_record in massgov.pfml.util.logging.log_every(
        logger,
        payment_extract_data.pei.indexed_data.items(),
        count=10,
        total_count=len(payment_extract_data.pei.indexed_data),
        start_time=massgov.pfml.util.datetime.utcnow(),
        item_name="pei record",
    ):
        process_payment_record(
            payment_extract_data,
            vendor_extract_data,
            voucher_extract_data,
            ci_index,
            pei_record,
            output_csv,
            writeback_csv,
            payment_date,
            db_session,
            log_entry,
        )


class PaymentRowError(Exception):
    """An error in a row that prevents processing of the payment."""

    pass


def process_payment_record(
    payment_extract_data: fineos_payment_export.ExtractData,
    vendor_extract_data: fineos_vendor_export.ExtractData,
    voucher_extract_data: VoucherExtractData,
    ci_index: fineos_payment_export.CiIndex,
    pei_record: Dict[str, str],
    output_csv: csv.DictWriter,
    writeback_csv: csv.DictWriter,
    payment_date: datetime.date,
    db_session: massgov.pfml.db.Session,
    log_entry: Optional[batch_log.LogEntry],
) -> None:
    """Process a single payment record with the given index."""
    extra: Dict[str, Optional[str]] = {}

    try:
        payment_data = fineos_payment_export.PaymentData(payment_extract_data, ci_index, pei_record)
        extra.update(absence_case=payment_data.absence_case_number, i_value=ci_index.i)

        if payment_data.validation_container.has_validation_issues():
            logger.warning(
                "validation issues: %r",
                payment_data.validation_container.validation_issues,
                extra=extra,
            )

        voucher_has_errors = write_row_to_output(
            ci_index,
            payment_data,
            vendor_extract_data,
            voucher_extract_data,
            payment_date,
            output_csv,
            extra,
            db_session,
        )
        write_writeback_row(ci_index, voucher_has_errors, writeback_csv)

        logger.info("wrote payment row", extra=extra)

        if log_entry is not None:
            if voucher_has_errors:
                log_entry.increment("error_count")
            else:
                log_entry.increment("success_count")

    except PaymentRowError as err:
        logger.warning("Unexpected: %s", err, extra=extra)
        if log_entry is not None:
            log_entry.increment("error_count")

    except Exception:
        logger.exception("Unexpected: exception for payment row", extra=extra)
        if log_entry is not None:
            log_entry.increment("exception_count")


def get_employee(tax_identifier: Optional[str], db_session: massgov.pfml.db.Session) -> Employee:
    """Return employee by tax identifier"""
    try:
        employee = (
            db_session.query(Employee)
            .join(TaxIdentifier)
            .filter(TaxIdentifier.tax_identifier == tax_identifier)
            .one_or_none()
        )
    except SQLAlchemyError as e:
        logger.exception(
            "Experienced error %s with one_or_none query when fetching employee for mmars_vendor_code",
            type(e),
        )
        raise
    if employee:
        return employee
    else:
        raise PaymentRowError("not found in employee table")


def get_mmars_vendor_code(employee: Employee) -> str:
    """Get Comptroller vendor code for the given SSN from the database."""
    if employee.ctr_vendor_customer_code:
        return employee.ctr_vendor_customer_code
    else:
        raise PaymentRowError("ctr_vendor_customer_code is NULL")


def get_vcm_flag(employee: Employee, db_session: massgov.pfml.db.Session) -> str:
    """Returns indicator for whether an employee has an outstanding VCM

        Returns:
            - 'Yes' if the employee has an outstanding VCM
            - 'Missing State' if employee has no current state (aka has not gone through the VCC/VCM process yet)
            - 'No' otherwise
    """
    current_state_log = state_log_util.get_latest_state_log_in_flow(
        employee, Flow.VENDOR_CHECK, db_session
    )

    if current_state_log is None:
        return "Missing State"
    elif current_state_log.end_state_id == State.VCM_REPORT_SENT.state_id:
        return "Yes"
    else:
        return "No"


def write_row_to_output(
    ci_index: fineos_payment_export.CiIndex,
    payment_data: fineos_payment_export.PaymentData,
    vendor_extract_data: fineos_vendor_export.ExtractData,
    voucher_extract_data: VoucherExtractData,
    payment_date: datetime.date,
    output_csv: csv.DictWriter,
    extra: Dict[str, Optional[str]],
    db_session: massgov.pfml.db.Session,
) -> bool:
    """Write a single row to the output CSV.

    Payment Voucher should have one row for each row in the vpei.csv.

    All fields should be filled if possible; otherwise they should be left blank.

    Returns:
        - bool: True if one or more errors were encountered; False otherwise.
    """
    has_errors = False

    # Process fields requiring database lookups.
    mmars_vendor_code = ""
    vcm_flag = ""
    try:
        employee = get_employee(payment_data.tin, db_session)
        vcm_flag = get_vcm_flag(employee, db_session)
        mmars_vendor_code = get_mmars_vendor_code(employee)
    except Exception as err:
        logger.warning("%s; cannot set mmars_vendor_code, vcm_flag", err, extra=extra)
        has_errors = True

    # Process fields from vpeiclaimdetails.csv.
    absence_case_number = ""
    vendor_invoice_number = ""
    if payment_data.absence_case_number is not None:
        absence_case_number = payment_data.absence_case_number
        vendor_invoice_number = gax.get_vendor_invoice_number(
            payment_data.absence_case_number, ci_index.i
        )
    else:
        logger.warning(
            "Absence case missing from vpei.csv; cannot set absence_case_number, vendor_invoice_number",
            extra=extra,
        )
        has_errors = True

    # Process fields from VBI_REQUESTEDABSENCE.csv.
    # Note: Using VBI_REQUESTEDABSENCE.csv is the most accurate source when attempting to
    # get data at the leave request level of granularity because we are indexing this
    # extract by leave_request_id.
    leave_request_id: Optional[str] = ""
    leave_request_decision: Optional[str] = ""
    absence_case_creation_date: Optional[str] = ""
    absence_reason_name: Optional[str] = ""
    leave_type: Optional[str] = ""
    activity_code: Optional[str] = ""
    case_status: Optional[str] = ""
    employer_id: Optional[str] = ""
    if (
        payment_data.leave_request_id is not None
        and payment_data.leave_request_id in voucher_extract_data.vbi_requested_absence.indexed_data
    ):
        vbi_requested_absence = voucher_extract_data.vbi_requested_absence.indexed_data[
            payment_data.leave_request_id
        ]
        leave_request_id = payment_data.leave_request_id
        leave_request_decision = vbi_requested_absence.get("LEAVEREQUEST_DECISION")
        absence_case_creation_date = vbi_requested_absence.get("ABSENCE_CASECREATIONDATE")
        absence_reason_name = vbi_requested_absence.get("ABSENCEREASON_NAME")
        case_status = vbi_requested_absence.get("ABSENCE_CASESTATUS")
        employer_id = vbi_requested_absence.get("EMPLOYER_CUSTOMERNO")

        try:
            leave_type = get_leave_type(vbi_requested_absence)
            activity_code = get_activity_code(vbi_requested_absence)
        except PaymentRowError as err:
            logger.warning("%s", err, extra=extra)
            has_errors = True

    else:
        logger.warning(
            "Leave request id missing from vpeiclaimdetails.csv and/or leave request id not found in VBI_REQUESTEDABSENCE.csv; cannot set leave_request_id, leave_request_decision, absence_case_creation_date, absence_reason_name, leave_type, activity_code, case_status, employer_id",
            extra=extra,
        )
        has_errors = True

    # Process fields from vpeipaymentdetails.csv.
    payment_period_start_date = None
    payment_period_start_date_str = ""
    if hasattr(payment_data, "payment_start_period") and payment_data.payment_start_period:
        payment_period_start_date = datetime.datetime.fromisoformat(
            payment_data.payment_start_period
        ).date()
        payment_period_start_date_str = payment_period_start_date.isoformat()
    else:
        logger.warning("Pay period start date missing", extra=extra)
        has_errors = True

    payment_period_end_date = None
    payment_period_end_date_str = ""
    vendor_invoice_date = ""
    if hasattr(payment_data, "payment_end_period") and payment_data.payment_end_period:
        payment_period_end_date = datetime.datetime.fromisoformat(
            payment_data.payment_end_period
        ).date()
        payment_period_end_date_str = payment_period_end_date.isoformat()
        vendor_invoice_date = gax.get_vendor_invoice_date_str(payment_period_end_date)
    else:
        logger.warning("Pay period end date missing; cannot set vendor_invoice_date", extra=extra)
        has_errors = True

    # Composite field: check description.
    check_description = ""
    if (
        payment_data.absence_case_number is not None
        and payment_period_start_date
        and payment_period_end_date
    ):
        check_description = gax.get_check_description(
            absence_case_id=payment_data.absence_case_number,
            payment_start_period=payment_period_start_date,
            payment_end_period=payment_period_end_date,
        )
    else:
        logger.warning(
            "Absence case missing and/or pay period start date missing and/or pay period end date missing; cannot set check_description",
            extra=extra,
        )
        has_errors = True

    # Calculate whether the payment amount is zero or negative.
    claimants_that_have_zero_or_credit_value = ""
    if payment_data.payment_amount is not None and float(payment_data.payment_amount) <= 0:
        claimants_that_have_zero_or_credit_value = "1"

    # Any values directly from vpei.csv are looked up here using:
    # - payment_data.<field>
    # - ci_index.<field>
    payment_row = PaymentVoucherCSV(
        leave_type=leave_type,
        activity_code=activity_code,
        payment_doc_id_code="GAX",
        payment_doc_id_dept="EOL",
        doc_id=get_doc_id(),
        mmars_vendor_code=mmars_vendor_code,
        first_last_name=payment_data.full_name,
        payment_preference=payment_data.raw_payment_method,
        address_code="AD010",
        address_line_1=payment_data.address_line_one,
        address_line_2=payment_data.address_line_two,
        city=payment_data.city,
        state=payment_data.state,
        zip=payment_data.zip_code,
        scheduled_payment_date=payment_date.isoformat(),
        vendor_single_payment="Yes",
        event_type="AP01",
        payment_amount=payment_data.payment_amount,
        description=check_description,
        vendor_invoice_number=vendor_invoice_number,
        vendor_invoice_line="1",
        vendor_invoice_date=vendor_invoice_date,
        payment_period_start_date=payment_period_start_date_str,
        payment_period_end_date=payment_period_end_date_str,
        absence_case_number=absence_case_number,
        c_value=ci_index.c,
        i_value=ci_index.i,
        fineos_customer_number_employee=payment_data.fineos_customer_number_employee,
        case_status=case_status,
        employer_id=employer_id,
        leave_request_id=leave_request_id,
        leave_request_decision=leave_request_decision,
        payment_event_type=payment_data.payment_event_type,
        vcm_flag=vcm_flag,
        absence_case_creation_date=absence_case_creation_date,
        absence_reason_name=absence_reason_name,
        good_to_pay_from_prior_batch="",
        had_a_payment_in_a_prior_batch_by_vc_code="",
        inv="",
        payments_offset_to_zero="",
        claimants_that_have_zero_or_credit_value=claimants_that_have_zero_or_credit_value,
        is_exempt="",
        leave_decision_not_approved="",
        has_a_check_preference_with_an_adl2_issue="",
        adl2_corrected="",
        removed_or_added_after_audit_of_info="",
        to_be_removed_from_file="",
        notes="",
    )
    output_csv.writerow(asdict(payment_row))

    return has_errors


def download_and_index_voucher_data(
    extract_data: VoucherExtractData, download_directory: str
) -> None:
    vbi_requested_absence_rows = payments_util.download_and_parse_csv(
        extract_data.vbi_requested_absence.file_location, download_directory
    )

    vbi_requested_absence_indexed_data: Dict[str, Dict[str, str]] = {}
    for row in vbi_requested_absence_rows:
        leave_request_id = str(row.get("LEAVEREQUEST_ID"))
        vbi_requested_absence_indexed_data[leave_request_id] = row
        logger.debug(
            "indexed vbi_REQUESTEDABSENCE file row with leave request id: %s", leave_request_id
        )

    extract_data.vbi_requested_absence.indexed_data = vbi_requested_absence_indexed_data

    return


def write_writeback_row(
    ci_index: fineos_payment_export.CiIndex, set_inactive: bool, writeback_csv: csv.DictWriter
) -> None:
    """Write a single row to the FINEOS Writeback CSV."""

    # Set status: if there were errors in the corresponding payment voucher row, then
    # leave status blank. Otherwise, set to "Active".
    status = "" if set_inactive else "Active"

    # Note: the trans_status_date is hardcoded because it is just a hint to manual
    # process. Hardcoding to 12:00:00 to avoid any timezone issues.
    writeback_row = WritebackCSV(
        c_value=ci_index.c,
        i_value=ci_index.i,
        status=status,
        transaction_status="",
        trans_status_date=datetime.datetime.now().strftime("%Y-%m-%d 12:00:00"),
        stock_no="",
    )
    writeback_csv.writerow(asdict(writeback_row))


def get_leave_type(absence_info):
    reason_coverage = absence_info.get("ABSENCEREASON_COVERAGE")
    if reason_coverage == "Family":
        return "PFMLFAMLFY2170030632"
    elif reason_coverage == "Employee":
        return "PFMLMEDIFY2170030632"
    raise PaymentRowError("unknown absence reason %s" % reason_coverage)


def get_activity_code(absence_info):
    reason_coverage = absence_info.get("ABSENCEREASON_COVERAGE")
    if reason_coverage == "Family":
        return "7246"
    elif reason_coverage == "Employee":
        return "7247"
    raise PaymentRowError("unknown absence reason %s" % reason_coverage)


def get_doc_id() -> str:
    """Generate a payment doc id.

    Same pattern as gax.get_doc_id() except that it has AAAA as the first 4 after INTFDFML to help
    identify manual payments.
    """
    return (
        "GAXMDFMLAAAA" + "".join(random.choices(string.ascii_letters + string.digits, k=8)).upper()
    )


if __name__ == "__main__":
    main()
