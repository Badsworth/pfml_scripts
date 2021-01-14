import csv
import os
import pathlib
import tempfile
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.config as payments_config
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    Claim,
    Employee,
    LatestStateLog,
    LkState,
    Payment,
    State,
    StateLog,
)
from massgov.pfml.util.aws.ses import EmailRecipient, send_email

logger = logging.get_logger(__name__)

####
# Most of the logic here is internal (any function starting with _)
# Entry-point functions are just:
#
# send_ctr_error_reports(db_session)
# send_fineos_error_reports(db_session)
#
# These should each be used in their respective ECS tasks (CTR-Payments and FINEOS-Payments)
# See the following docs for details:
# - https://lwd.atlassian.net/wiki/spaces/API/pages/1020067908/Payments+Reports+Errors
# - https://lwd.atlassian.net/wiki/spaces/API/pages/970326505/Payments+State+Machines
####

# The column headers in the CSV
DESCRIPTION_COLUMN = "Description of Issue"
FINEOS_CUSTOMER_NUM_COLUMN = "FINEOS Customer Number"
FINEOS_ABSENCE_ID_COLUMN = "FINEOS Absence Case ID"
MMARS_VENDOR_CUST_NUM_COLUMN = "MMARS Vendor Customer Number"
MMARS_DOCUMENT_ID_COLUMN = "MMARS Document ID"
PAYMENT_DATE_COLUMN = "Payment Date"

CSV_HEADER: List[str] = [
    DESCRIPTION_COLUMN,
    FINEOS_CUSTOMER_NUM_COLUMN,
    FINEOS_ABSENCE_ID_COLUMN,
    MMARS_VENDOR_CUST_NUM_COLUMN,
    MMARS_DOCUMENT_ID_COLUMN,
    PAYMENT_DATE_COLUMN,
]

FINEOS_PAYMENTS_EMAIL_SUBJECT = "DFML CPS Reports for {0}"
FINEOS_PAYMENTS_EMAIL_BODY = "This is the daily error report for {0}. Attached are errors resulting from the {1}. Note that the error report might be an empty file. If this happens it means there are no outstanding errors in that category for the day."
CTR_PAYMENTS_EMAIL_SUBJECT = "DFML CTR Reports for {0}"
CTR_PAYMENTS_EMAIL_BODY = "This is the daily error report for {0}. Attached are errors resulting from the {1}. Note that the error report might be an empty file. If this happens it means there are no outstanding errors in that category for the day."

GENERIC_OUTCOME_MSG = "No details provided for cause of issue"


@dataclass
class ErrorReport:
    description: str
    fineos_customer_number: Optional[str] = None
    fineos_absence_id: Optional[str] = None
    ctr_vendor_customer_code: Optional[str] = None
    mmars_document_id: Optional[str] = None
    payment_date: Optional[str] = None

    def get_dict(self) -> Dict[str, Optional[str]]:
        # The CSVWriter expects the dictionary of values
        # to have keys that match the headers, so map them here
        return {
            DESCRIPTION_COLUMN: self.description,
            FINEOS_CUSTOMER_NUM_COLUMN: self.fineos_customer_number,
            FINEOS_ABSENCE_ID_COLUMN: self.fineos_absence_id,
            MMARS_VENDOR_CUST_NUM_COLUMN: self.ctr_vendor_customer_code,
            MMARS_DOCUMENT_ID_COLUMN: self.mmars_document_id,
            PAYMENT_DATE_COLUMN: self.payment_date,
        }


@dataclass
class Outcome:
    key: Optional[str]
    description: str


@dataclass
class FileInfo:
    filepath: pathlib.Path  # The path on disk of the created file
    state_logs: List[StateLog]  # State logs, each row in the file has one


@dataclass
class ErrorLogs:
    errors: List[ErrorReport]
    state_logs: List[StateLog]


def _build_file_path(working_directory: pathlib.Path, file_name: str) -> pathlib.Path:
    # eg. "my_file" -> my_file-2020-01-01.csv
    return working_directory / f"{payments_util.get_now().strftime('%Y-%m-%d')}-{file_name}.csv"


def _parse_outcome(state_log: StateLog) -> Outcome:
    if not state_log.outcome:
        logger.warning(
            f"No outcome specified for state_log {state_log.state_log_id}",
            extra={"state_log_id": state_log.state_log_id},
        )
        return Outcome(None, GENERIC_OUTCOME_MSG)

    outcome = cast(Dict[str, Any], state_log.outcome)
    message = outcome.get("message")

    if not message:
        logger.warning("No outcome present for record")
        message = GENERIC_OUTCOME_MSG

    description_values: List[str] = []
    description_values.append(str(message))
    key = None

    validation_container_dict = outcome.get("validation_container")
    if validation_container_dict:
        key = validation_container_dict.get("record_key")
        validation_issues = validation_container_dict.get("validation_issues")

        if validation_issues:
            for issue in validation_issues:
                # TODO - make these more user friendly
                reason = issue.get("reason")
                details = issue.get("details")
                description_values.append(f"{reason}:{details}")

    return Outcome(key, "\n".join(description_values))


def _create_file(errors: List[ErrorReport], outfile: pathlib.Path) -> pathlib.Path:
    # Note, from the docs:
    # "the value None is written as the empty string" - which is fine for us
    # https://docs.python.org/3/library/csv.html#csv.DictWriter
    with open(outfile, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADER, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for error in errors:
            writer.writerow(error.get_dict())

    return outfile


def _get_employee_claim_payment_from_state_log(
    associated_class: state_log_util.AssociatedClass, state_log: StateLog, db_session: db.Session
) -> Tuple[Optional[Employee], Optional[Claim], Optional[Payment]]:
    # An employee can have multiple claims which each can have multiple payments
    # So, starting from a PAYMENT is easy, but starting from an EMPLOYEE is more complicated
    if associated_class == state_log_util.AssociatedClass.PAYMENT:
        payment = state_log.payment
        claim = payment.claim  # Claim ID is not nullable on payment, will always be set
        employee = claim.employee  # This is possible to be null in some specific edge cases

        if not employee:
            # This scenario shouldn't happen unless we somehow have a payment
            # not associated with an employee (but is technically possible with our DB model setup)
            logger.error(
                f"No employee found for payment {payment.payment_id} associated with state_log {state_log.state_log_id}",
                extra={"payment_id": payment.payment_id, "state_log_id": state_log.state_log_id},
            )
            return None, None, None

        return employee, claim, payment
    if associated_class == state_log_util.AssociatedClass.EMPLOYEE:
        employee = state_log.employee

        # If an employee has no claims, it certainly has no payments either
        if not employee.claims:
            return employee, None, None

        claim_ids = [claim.claim_id for claim in employee.claims]

        # Get all payment IDs associated with the employees claims
        # as a subquery
        subquery = db_session.query(Payment.payment_id).filter(Payment.claim_id.in_(claim_ids))

        # This query in raw SQL is:
        #
        # SELECT * FROM state_log
        #   JOIN latest_state_log ON state_log.state_log_id = latest_state_log.state_log_id
        #  WHERE state_log.end_state_id={State.CONFIRM_VENDOR_STATUS_IN_MMARS.state_id} AND
        #        latest_state_log.payment_id IN (
        #           SELECT payment.payment_id FROM payment
        #            WHERE payment.claim_id in {claim_ids}
        #        )
        latest_payment_state_logs_in_state = (
            db_session.query(StateLog)
            .join(LatestStateLog)
            .filter(
                StateLog.end_state_id == State.CONFIRM_VENDOR_STATUS_IN_MMARS.state_id,
                LatestStateLog.payment_id.in_(subquery),
            )
            .all()
        )

        # We have a list of state logs at this point, each connected to one payment
        # IF AND ONLY IF this list is length 1, we can return a payment/claim, otherwise
        # we still return None for them
        if len(latest_payment_state_logs_in_state) != 1:
            return employee, None, None

        latest_state_log = latest_payment_state_logs_in_state[0]
        payment = latest_state_log.payment
        claim = payment.claim

        return employee, claim, payment

    # Shouldn't happen, this should only be possible
    # if associated_class==REFERENCE_FILE -> We don't use that in this file, shouldn't happen
    # if the state_log was created without using our utility which requires a Payment/Employee/ReferenceFile
    # In any case, log an error
    logger.warning(
        f"Error report generation encountered an unexpected scenario regarding State Log {state_log.state_log_id}",
        extra={"state_log_id": state_log.state_log_id},
    )
    return None, None, None


def _build_error_report(
    state_log: StateLog,
    associated_class: state_log_util.AssociatedClass,
    description: str,
    mmars_doc_id: Optional[str],
    add_vendor_customer_code: bool,
    db_session: db.Session,
) -> Optional[ErrorReport]:
    # If associated_class is PAYMENT, all of these should be set
    # If associated_class is EMPLOYEE, employee will always be set
    #    but claim/payment are only set if exactly one payment associated
    #    with that employee in the Confirm vendor status in MMARS state
    employee, claim, payment = _get_employee_claim_payment_from_state_log(
        associated_class, state_log, db_session
    )
    if not employee:
        # This is a bad case, but the above method already logged the problem
        # Just return None
        return None

    # Always set for PAYMENTs, sometimes set for EMPLOYEE (see details above)
    fineos_absence_id = None
    if claim:
        fineos_absence_id = claim.fineos_absence_id

    # Set if a PAYMENT could be found
    payment_date = None
    if payment and payment.payment_date:
        payment_date = payment.payment_date.strftime("%m/%d/%Y")

    # Set only for certain reports
    ctr_vendor_customer_code = None
    if add_vendor_customer_code:
        ctr_vendor_customer_code = employee.ctr_vendor_customer_code

    return ErrorReport(
        description=description,
        fineos_customer_number=employee.fineos_customer_number,
        fineos_absence_id=fineos_absence_id,
        ctr_vendor_customer_code=ctr_vendor_customer_code,
        mmars_document_id=mmars_doc_id,
        payment_date=payment_date,
    )


def _build_state_log(
    current_state_log: StateLog,
    associated_class: state_log_util.AssociatedClass,
    current_state: LkState,
    next_state: LkState,
    db_session: db.Session,
) -> None:
    associated_model: Union[Payment, Employee]
    # Create a new state log entry
    if associated_class == state_log_util.AssociatedClass.PAYMENT:
        associated_model = current_state_log.payment
    elif associated_class == state_log_util.AssociatedClass.EMPLOYEE:
        associated_model = current_state_log.employee
    else:
        logger.warning(
            "An unexpected scenario has occurred and a new state log has not been created."
        )
        return

    new_state_log = state_log_util.create_state_log(
        start_state=current_state,
        associated_model=associated_model,
        db_session=db_session,
        commit=False,
    )
    # Immediately end the state log entry
    # but don't add/commit it, we're only going to do
    # that if the email sends successfully.
    state_log_util.finish_state_log(
        state_log=new_state_log,
        end_state=next_state,
        db_session=db_session,
        outcome=state_log_util.build_outcome("Successfully sent email"),
        commit=False,
    )


def _make_simple_report(
    outfile: pathlib.Path,
    current_state: LkState,
    next_state: LkState,
    associated_class: state_log_util.AssociatedClass,
    add_vendor_customer_code: bool,
    add_mmars_doc_id: bool,
    db_session: db.Session,
) -> pathlib.Path:
    state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=associated_class, end_state=current_state, db_session=db_session
    )

    errors: List[ErrorReport] = []

    for state_log in state_logs:
        outcome = _parse_outcome(state_log)

        # Set only if explicitly declared - this requires
        # special logic/assumptions about the code elsewhere to work
        mmars_document_id = None
        if add_mmars_doc_id:
            # Use the validation containers record key
            # Yes, this is incredibly flimsy and hacky, but
            # this will only be used for VCC/GAX error cases
            if not outcome.key:
                logger.warning(
                    f"No MMARS doc ID present for state_log {state_log.state_log_id}",
                    extra={"state_log_id": state_log.state_log_id},
                )
            mmars_document_id = outcome.key

        error_report = _build_error_report(
            state_log=state_log,
            associated_class=associated_class,
            description=outcome.description,
            mmars_doc_id=mmars_document_id,
            add_vendor_customer_code=add_vendor_customer_code,
            db_session=db_session,
        )
        if not error_report:
            # Something went wrong with building
            # the error report, we've logged a warning
            # deeper down, we don't want to add a row
            # or mess with the state log, just continue
            continue
        errors.append(error_report)

        _build_state_log(
            current_state_log=state_log,
            associated_class=associated_class,
            current_state=current_state,
            next_state=next_state,
            db_session=db_session,
        )

    _create_file(errors, outfile)
    return outfile


def _get_time_based_errors(
    current_state: LkState,
    next_state: LkState,
    associated_class: state_log_util.AssociatedClass,
    days_stuck: int,
    now: datetime,
    db_session: db.Session,
) -> List[ErrorReport]:
    state_logs = state_log_util.get_state_logs_stuck_in_state(
        associated_class=associated_class,
        end_state=current_state,
        days_stuck=30,  # TODO - after launch, set this back to days_stuck, we don't want to send stuck messages while we've half-processed data before launch
        db_session=db_session,
        now=now,
    )

    errors: List[ErrorReport] = []

    for state_log in state_logs:
        description = f"Process has been stuck for {days_stuck} days in [{current_state.state_description}] without a resolution."

        error_report = _build_error_report(
            state_log=state_log,
            associated_class=associated_class,
            description=description,
            mmars_doc_id=None,
            add_vendor_customer_code=True,
            db_session=db_session,
        )
        if not error_report:
            # Something went wrong with building
            # the error report, we've logged a warning
            # deeper down, we don't want to add a row
            # or mess with the state log, just continue
            continue
        errors.append(error_report)

        _build_state_log(
            current_state_log=state_log,
            associated_class=associated_class,
            current_state=current_state,
            next_state=next_state,
            db_session=db_session,
        )

    return errors


def _send_errors_email(subject: str, body: str, error_files: List[pathlib.Path]) -> None:
    email_config = payments_config.get_email_config()
    sender = email_config.pfml_email_address
    recipient = EmailRecipient(to_addresses=[email_config.dfml_business_operations_email_address])
    send_email(
        recipient=recipient,
        subject=subject,
        body_text=body,
        sender=sender,
        bounce_forwarding_email_address_arn=email_config.bounce_forwarding_email_address_arn,
        attachments=error_files,
    )

    s3_prefix = payments_config.get_s3_config().pfml_error_reports_path

    for error_file in error_files:
        # upload the error reports to a path like: s3://bucket/path/2020-01-01/2020-01-01-CPS-payment-export-error-report.csv
        output_path = os.path.join(
            s3_prefix, payments_util.get_now().strftime("%Y-%m-%d"), error_file.name
        )
        file_util.upload_to_s3(str(error_file), output_path)


def _send_fineos_payments_errors(working_directory: pathlib.Path, db_session: db.Session) -> None:
    ### Simple Reports
    # ADD_TO_PAYMENT_EXPORT_ERROR_REPORT -> PAYMENT_EXPORT_ERROR_REPORT_SENT
    cps_payment_export_report = _make_simple_report(
        outfile=_build_file_path(working_directory, "CPS-payment-export-error-report"),
        current_state=State.ADD_TO_PAYMENT_EXPORT_ERROR_REPORT,
        next_state=State.PAYMENT_EXPORT_ERROR_REPORT_SENT,
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        add_vendor_customer_code=False,
        add_mmars_doc_id=False,
        db_session=db_session,
    )

    # ADD_TO_VENDOR_EXPORT_ERROR_REPORT -> VENDOR_EXPORT_ERROR_REPORT_SENT
    cps_vendor_export_report = _make_simple_report(
        outfile=_build_file_path(working_directory, "CPS-vendor-export-error-report"),
        current_state=State.ADD_TO_VENDOR_EXPORT_ERROR_REPORT,
        next_state=State.VENDOR_EXPORT_ERROR_REPORT_SENT,
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        add_vendor_customer_code=False,
        add_mmars_doc_id=False,
        db_session=db_session,
    )
    ### No time based reports exist for this task

    today = payments_util.get_now()

    files = [cps_payment_export_report, cps_vendor_export_report]
    _send_errors_email(
        subject=FINEOS_PAYMENTS_EMAIL_SUBJECT.format(today.strftime("%m/%d/%Y")),
        body=FINEOS_PAYMENTS_EMAIL_BODY.format(today.strftime("%m/%d/%Y"), "FINEOS processing"),
        error_files=files,
    )


def send_fineos_error_reports(db_session: db.Session) -> None:
    try:
        working_directory = pathlib.Path(tempfile.mkdtemp())
        _send_fineos_payments_errors(working_directory, db_session)

        # Finally if the email was sent successfully, we commit the state log
        # entries to the DB. The objects are already in a finished state
        # so they don't need to be modified/directly accessed here
        db_session.commit()
    except Exception:
        logger.exception("Error creating FINEOS payment reports")
        db_session.rollback()


def _send_ctr_payments_errors(working_directory: pathlib.Path, db_session: db.Session) -> None:
    now = datetime_util.utcnow()  # This has the same TZ as the StateLogs

    ### Simple Reports
    # ADD_TO_GAX_ERROR_REPORT -> GAX_ERROR_REPORT_SENT
    gax_error_report = _make_simple_report(
        outfile=_build_file_path(working_directory, "GAX-error-report"),
        current_state=State.ADD_TO_GAX_ERROR_REPORT,
        next_state=State.GAX_ERROR_REPORT_SENT,
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        add_vendor_customer_code=True,
        add_mmars_doc_id=True,
        db_session=db_session,
    )
    # ADD_TO_VCC_ERROR_REPORT -> VCC_ERROR_REPORT_SENT
    vcc_error_report = _make_simple_report(
        outfile=_build_file_path(working_directory, "VCC-error-report"),
        current_state=State.ADD_TO_VCC_ERROR_REPORT,
        next_state=State.VCC_ERROR_REPORT_SENT,
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        add_vendor_customer_code=True,
        add_mmars_doc_id=True,
        db_session=db_session,
    )
    # ADD_TO_VCM_REPORT -> VCM_REPORT_SENT
    vcm_report = _make_simple_report(
        outfile=_build_file_path(working_directory, "VCM-report"),
        current_state=State.ADD_TO_VCM_REPORT,
        next_state=State.VCM_REPORT_SENT,
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        add_vendor_customer_code=True,
        add_mmars_doc_id=False,
        db_session=db_session,
    )
    # ADD_TO_EFT_ERROR_REPORT -> EFT_ERROR_REPORT_SENT
    eft_error_report = _make_simple_report(
        outfile=_build_file_path(working_directory, "EFT-error-report"),
        current_state=State.ADD_TO_EFT_ERROR_REPORT,
        next_state=State.EFT_ERROR_REPORT_SENT,
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        add_vendor_customer_code=True,
        add_mmars_doc_id=False,
        db_session=db_session,
    )

    ### Time Based Reports
    ## Payment Audit Error Report - Contains 3 separate queries worth of data
    # GAX_ERROR_REPORT_SENT >> 5 days >> PAYMENT_ALLOWABLE_TIME_IN_STATE_EXCEEDED
    gax_error_report_stuck_errors = _get_time_based_errors(
        current_state=State.GAX_ERROR_REPORT_SENT,
        next_state=State.PAYMENT_ALLOWABLE_TIME_IN_STATE_EXCEEDED,
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        days_stuck=5,
        now=now,
        db_session=db_session,
    )
    # GAX_SENT >> 5 days >> PAYMENT_ALLOWABLE_TIME_IN_STATE_EXCEEDED
    gax_sent_stuck_errors = _get_time_based_errors(
        current_state=State.GAX_SENT,
        next_state=State.PAYMENT_ALLOWABLE_TIME_IN_STATE_EXCEEDED,
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        days_stuck=5,
        now=now,
        db_session=db_session,
    )
    # CONFIRM_VENDOR_STATUS_IN_MMARS >> 15 days >> PAYMENT_ALLOWABLE_TIME_IN_STATE_EXCEEDED
    confirm_vend_status_in_mmars_stuck_errors = _get_time_based_errors(
        current_state=State.CONFIRM_VENDOR_STATUS_IN_MMARS,
        next_state=State.PAYMENT_ALLOWABLE_TIME_IN_STATE_EXCEEDED,
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        days_stuck=15,
        now=now,
        db_session=db_session,
    )

    # Build the CSV from all three sets of payment errors
    payment_audit_errors = (
        gax_error_report_stuck_errors
        + gax_sent_stuck_errors
        + confirm_vend_status_in_mmars_stuck_errors
    )
    payment_audit_error_report = _create_file(
        payment_audit_errors, _build_file_path(working_directory, "payment-audit-error-report"),
    )

    ## Vendor Audit Error Report - Contains 3 separate queries worth of data
    # VCM_REPORT_SENT >> 15 days >> VENDOR_ALLOWABLE_TIME_IN_STATE_EXCEEDED
    vcm_sent_stuck_errors = _get_time_based_errors(
        current_state=State.VCM_REPORT_SENT,
        next_state=State.VENDOR_ALLOWABLE_TIME_IN_STATE_EXCEEDED,
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        days_stuck=15,
        now=now,
        db_session=db_session,
    )
    # VCC_SENT >> 5 days >> VENDOR_ALLOWABLE_TIME_IN_STATE_EXCEEDED
    vcc_sent_stuck_errors = _get_time_based_errors(
        current_state=State.VCC_SENT,
        next_state=State.VENDOR_ALLOWABLE_TIME_IN_STATE_EXCEEDED,
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        days_stuck=5,
        now=now,
        db_session=db_session,
    )
    # VCC_ERROR_REPORT_SENT >> 5 days >> VENDOR_ALLOWABLE_TIME_IN_STATE_EXCEEDED
    vcc_error_report_stuck_errors = _get_time_based_errors(
        current_state=State.VCC_ERROR_REPORT_SENT,
        next_state=State.VENDOR_ALLOWABLE_TIME_IN_STATE_EXCEEDED,
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        days_stuck=5,
        now=now,
        db_session=db_session,
    )

    # Build the CSV from all three sets of vendor errors
    vendor_audit_errors = (
        vcm_sent_stuck_errors + vcc_sent_stuck_errors + vcc_error_report_stuck_errors
    )
    vendor_audit_error_report = _create_file(
        vendor_audit_errors, _build_file_path(working_directory, "vendor-audit-error-report"),
    )

    # EFT audit error report - Contains just one queries worth of data
    # EFT_PENDING >> 15 days >> EFT_ALLOWABLE_TIME_IN_STATE_EXCEEDED
    eft_stuck_errors = _get_time_based_errors(
        current_state=State.EFT_PENDING,
        next_state=State.EFT_ALLOWABLE_TIME_IN_STATE_EXCEEDED,
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        days_stuck=15,
        now=now,
        db_session=db_session,
    )
    # Build the CSV for EFT errors
    eft_audit_error_report = _create_file(
        eft_stuck_errors, _build_file_path(working_directory, "EFT-audit-error-report"),
    )

    files = [
        gax_error_report,
        vcc_error_report,
        vcm_report,
        eft_error_report,
        payment_audit_error_report,
        vendor_audit_error_report,
        eft_audit_error_report,
    ]

    today = payments_util.get_now()

    _send_errors_email(
        subject=CTR_PAYMENTS_EMAIL_SUBJECT.format(today.strftime("%m/%d/%Y")),
        body=CTR_PAYMENTS_EMAIL_BODY.format(today.strftime("%m/%d/%Y"), "CTR processing"),
        error_files=files,
    )


def send_ctr_error_reports(db_session: db.Session) -> None:
    try:
        working_directory = pathlib.Path(tempfile.mkdtemp())
        _send_ctr_payments_errors(working_directory, db_session)

        # Finally if the email was sent successfully, we commit the state log
        # entries to the DB. The objects are already in a finished state
        # so they don't need to be modified/directly accessed here
        db_session.commit()
    except Exception:
        logger.exception("Error creating CTR payment reports")
        db_session.rollback()
