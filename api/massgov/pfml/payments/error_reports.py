import os
import pathlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, cast

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
    PaymentMethod,
    State,
    StateLog,
)
from massgov.pfml.payments.reporting.abstract_reporting import Report
from massgov.pfml.payments.reporting.error_reporting import (
    ErrorRecord,
    initialize_ctr_payments_error_report_group,
    initialize_error_report,
    initialize_fineos_payments_error_report_group,
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
#
# See also massgov.pfml.payments.reporting.error_reporting which contains
# many of the data class style objects used for reporting
####


GENERIC_OUTCOME_MSG = "No details provided for cause of issue"


@dataclass
class DbModels:
    is_valid: bool
    employee: Optional[Employee] = None
    claim: Optional[Claim] = None
    payment: Optional[Payment] = None


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
    errors: List[ErrorRecord]
    state_logs: List[StateLog]


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

        # If a key is present - add it to the description at the start
        if key:
            description_values.insert(0, key)

    return Outcome(key, "\n".join(description_values))


def _get_employee_claim_payment_from_state_log(
    associated_class: state_log_util.AssociatedClass, state_log: StateLog, db_session: db.Session
) -> DbModels:
    # An employee can have multiple claims which each can have multiple payments
    # So, starting from a PAYMENT is easy, but starting from an EMPLOYEE is more complicated
    if associated_class == state_log_util.AssociatedClass.PAYMENT:
        payment = state_log.payment
        if not payment:
            # If payment is not set on a payment state log, we've hit the case where
            # payment validation failed and we couldn't create the payment.
            return DbModels(True)
        claim = payment.claim  # Claim ID is not nullable on payment, will always be set
        employee = claim.employee  # This is possible to be null in some specific edge cases

        if not employee:
            # This scenario shouldn't happen unless we somehow have a payment
            # not associated with an employee (but is technically possible with our DB model setup)
            logger.error(
                f"No employee found for payment {payment.payment_id} associated with state_log {state_log.state_log_id}",
                extra={"payment_id": payment.payment_id, "state_log_id": state_log.state_log_id},
            )
            return DbModels(False)

        return DbModels(True, payment=payment, claim=claim, employee=employee)

    if associated_class == state_log_util.AssociatedClass.EMPLOYEE:
        employee = state_log.employee

        # If an employee has no claims, it certainly has no payments either
        if not employee.claims:
            return DbModels(True, employee=employee)

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
            return DbModels(True, employee=employee)

        latest_state_log = latest_payment_state_logs_in_state[0]
        payment = latest_state_log.payment
        claim = payment.claim

        return DbModels(True, employee=employee, payment=payment, claim=claim)

    # Shouldn't happen, this should only be possible
    # if associated_class==REFERENCE_FILE -> We don't use that in this file, shouldn't happen
    # if the state_log was created without using our utility which requires a Payment/Employee/ReferenceFile
    # In any case, log an error
    logger.warning(
        f"Error report generation encountered an unexpected scenario regarding State Log {state_log.state_log_id}",
        extra={"state_log_id": state_log.state_log_id},
    )
    return DbModels(False)


def _build_error_report(
    state_log: StateLog,
    associated_class: state_log_util.AssociatedClass,
    description: str,
    mmars_doc_id: Optional[str],
    add_vendor_customer_code: bool,
    db_session: db.Session,
) -> Optional[ErrorRecord]:
    # If associated_class is PAYMENT, all of these should be set
    #    unless the payment errored before we were able to create the
    #    payment in fineos_payment_export. In that case, we will have no
    # unless the payment errored before we were able to create the
    # payment in fineos_payment_export. In that case, we will have no
    # payment even when associated_class is PAYMENT.
    # If associated_class is EMPLOYEE, employee will always be set
    #    but claim/payment are only set if exactly one payment associated
    #    with that employee in the Confirm vendor status in MMARS state
    db_models = _get_employee_claim_payment_from_state_log(associated_class, state_log, db_session)

    if not db_models.is_valid:
        # This is a bad case, but the above method already logged the problem
        return None

    # Always set for PAYMENTs, sometimes set for EMPLOYEE (see details above)
    fineos_absence_id = None
    if db_models.claim:
        fineos_absence_id = db_models.claim.fineos_absence_id

    # Set if a PAYMENT could be found
    payment_date = None
    if db_models.payment and db_models.payment.payment_date:
        payment_date = db_models.payment.payment_date.strftime("%m/%d/%Y")

    # Set only for certain reports
    fineos_customer_number = None
    ctr_vendor_customer_code = None
    if db_models.employee:
        fineos_customer_number = db_models.employee.fineos_customer_number
        if add_vendor_customer_code:
            ctr_vendor_customer_code = db_models.employee.ctr_vendor_customer_code

    return ErrorRecord(
        description=description,
        fineos_customer_number=fineos_customer_number,
        fineos_absence_id=fineos_absence_id,
        ctr_vendor_customer_code=ctr_vendor_customer_code,
        mmars_document_id=mmars_doc_id,
        payment_date=payment_date,
    )


def _build_state_log(
    current_state_log: StateLog,
    associated_class: state_log_util.AssociatedClass,
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

    if associated_model:
        state_log_util.create_finished_state_log(
            end_state=next_state,
            associated_model=associated_model,
            outcome=state_log_util.build_outcome("Successfully sent email"),
            db_session=db_session,
        )
    else:  # For the payment edge case where it has no associated model
        state_log_util.create_state_log_without_associated_model(
            end_state=next_state,
            associated_class=associated_class,
            prev_state_log=current_state_log,
            outcome=state_log_util.build_outcome("Successfully sent email"),
            db_session=db_session,
        )

    # If a vendor's payment method is EFT:
    # - If they do not yet exist in MMARS, then we add them to the next VCC
    #   and move the employee forward in the VENDOR_EFT flow to the
    #   EFT_PENDING step. The VCC will add the EFT information for the
    #   Employee into MMARS.
    # - If they do already exist in MMARS, then we add them to the VCM report
    #   for a manual person to update the EFT information in MMARS. Once we
    #   send the VCM report, we need to move the Employee forward in the
    #   VENDOR_EFT flow to the EFT_PENDING step.
    if (
        next_state == State.VCM_REPORT_SENT
        and associated_class == state_log_util.AssociatedClass.EMPLOYEE
    ):
        employee = cast(Employee, associated_model)
        if employee.eft and employee.payment_method_id == PaymentMethod.ACH.payment_method_id:
            state_log_util.create_finished_state_log(
                associated_model=associated_model,
                end_state=State.EFT_PENDING,
                outcome=state_log_util.build_outcome(
                    "Added vendor to VCM Report, EFT data is included"
                ),
                db_session=db_session,
            )


def _make_simple_report(
    report_name: str,
    current_states: List[LkState],
    next_state: LkState,
    associated_class: state_log_util.AssociatedClass,
    add_vendor_customer_code: bool,
    add_mmars_doc_id: bool,
    db_session: db.Session,
) -> Report:
    """Create a simple report from StateLog outcomes"""

    # Create a combined list of all state logs whose latest state is in the
    # `current_states` list.
    state_logs: List[StateLog] = []
    for current_state in current_states:
        results = state_log_util.get_all_latest_state_logs_in_end_state(
            associated_class=associated_class, end_state=current_state, db_session=db_session
        )
        state_logs.extend(results)

        logger.info(
            "Building error reports for %s with end state: %s - found %s",
            associated_class.value,
            current_state.state_description,
            len(state_logs),
        )

    # Build the error reports.
    errors: List[ErrorRecord] = []

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
            next_state=next_state,
            db_session=db_session,
        )
    report = initialize_error_report(report_name)
    report.add_records(errors)

    return report


def _get_time_based_errors(
    current_state: LkState,
    next_state: LkState,
    associated_class: state_log_util.AssociatedClass,
    days_stuck: int,
    now: datetime,
    db_session: db.Session,
) -> List[ErrorRecord]:
    state_logs = state_log_util.get_state_logs_stuck_in_state(
        associated_class=associated_class,
        end_state=current_state,
        days_stuck=60,  # TODO - after launch, set this back to days_stuck, we don't want to send stuck messages while we've half-processed data before launch
        db_session=db_session,
        now=now,
    )

    logger.info(
        "Building time based error reports for %s with end state: %s, days stuck: %i, - found %s",
        associated_class.value,
        current_state.state_description,
        days_stuck,
        len(state_logs),
    )

    errors: List[ErrorRecord] = []

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
            next_state=next_state,
            db_session=db_session,
        )

    return errors


def _send_errors_email(subject: str, body: str, error_files: List[pathlib.Path]) -> None:
    try:
        email_config = payments_config.get_email_config()
        sender = email_config.pfml_email_address
        recipient = EmailRecipient(
            to_addresses=[email_config.dfml_business_operations_email_address]
        )
        send_email(
            recipient=recipient,
            subject=subject,
            body_text=body,
            sender=sender,
            bounce_forwarding_email_address_arn=email_config.bounce_forwarding_email_address_arn,
            attachments=error_files,
        )
    except Exception:
        logger.error("Failed to send emails - uploading to S3 - will need to be sent manually")

    s3_prefix = payments_config.get_s3_config().pfml_error_reports_path

    for error_file in error_files:
        # upload the error reports to a path like: s3://bucket/path/2020-01-01/2020-01-01-12-00-00-CPS-payment-export-error-report.csv
        output_path = os.path.join(
            s3_prefix, payments_util.get_now().strftime("%Y-%m-%d"), error_file.name
        )
        file_util.upload_to_s3(str(error_file), output_path)
        logger.info(
            f"Error report file written to S3: {output_path}", extra={"s3_path": output_path}
        )


def _send_fineos_payments_errors(db_session: db.Session) -> None:
    # Create the report group which will contain the reports
    report_group = initialize_fineos_payments_error_report_group()

    ### Simple Reports
    # ADD_TO_PAYMENT_EXPORT_ERROR_REPORT -> PAYMENT_EXPORT_ERROR_REPORT_SENT
    cps_payment_export_report = _make_simple_report(
        report_name="CPS-payment-export-error-report",
        current_states=[State.ADD_TO_PAYMENT_EXPORT_ERROR_REPORT],
        next_state=State.PAYMENT_EXPORT_ERROR_REPORT_SENT,
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        add_vendor_customer_code=False,
        add_mmars_doc_id=False,
        db_session=db_session,
    )
    report_group.add_report(cps_payment_export_report)

    # ADD_TO_VENDOR_EXPORT_ERROR_REPORT -> VENDOR_EXPORT_ERROR_REPORT_SENT
    cps_vendor_export_report = _make_simple_report(
        report_name="CPS-vendor-export-error-report",
        current_states=[State.ADD_TO_VENDOR_EXPORT_ERROR_REPORT],
        next_state=State.VENDOR_EXPORT_ERROR_REPORT_SENT,
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        add_vendor_customer_code=False,
        add_mmars_doc_id=False,
        db_session=db_session,
    )
    report_group.add_report(cps_vendor_export_report)
    ### No time based reports exist for this task

    # Finally create the reports and send them
    report_group.create_and_send_reports()


def send_fineos_error_reports(db_session: db.Session) -> None:
    logger.info("Creating FINEOS payment reports")

    try:
        _send_fineos_payments_errors(db_session)

        # Finally if the email was sent successfully, we commit the state log
        # entries to the DB. The objects are already in a finished state
        # so they don't need to be modified/directly accessed here
        db_session.commit()
        logger.info("Successfully created FINEOS payment reports")
    except Exception:
        logger.exception("Error creating FINEOS payment reports")
        db_session.rollback()


def _send_ctr_payments_errors(db_session: db.Session) -> None:
    now = datetime_util.utcnow()  # This has the same TZ as the StateLogs

    report_group = initialize_ctr_payments_error_report_group()

    ### Simple Reports
    # ADD_TO_GAX_ERROR_REPORT -> GAX_ERROR_REPORT_SENT
    gax_error_report = _make_simple_report(
        report_name="GAX-error-report",
        current_states=[State.ADD_TO_GAX_ERROR_REPORT],
        next_state=State.GAX_ERROR_REPORT_SENT,
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        add_vendor_customer_code=True,
        add_mmars_doc_id=True,
        db_session=db_session,
    )
    report_group.add_report(gax_error_report)
    # ADD_TO_VCC_ERROR_REPORT -> VCC_ERROR_REPORT_SENT
    vcc_error_report = _make_simple_report(
        report_name="VCC-error-report",
        current_states=[State.ADD_TO_VCC_ERROR_REPORT],
        next_state=State.VCC_ERROR_REPORT_SENT,
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        add_vendor_customer_code=True,
        add_mmars_doc_id=True,
        db_session=db_session,
    )
    report_group.add_report(vcc_error_report)
    # ADD_TO_VCM_REPORT -> VCM_REPORT_SENT
    # VCM_REPORT_SENT -> VCM_REPORT_SENT
    #
    # The VCM report was originally a delta of just the current run's entries that
    # needed to be added to the VCM report. API-1386 changed it to no longer be
    # a delta, so this report actually combines records that are in
    # ADD_TO_VCM_REPORT plus VCM_REPORT_SENT together.
    vcm_report = _make_simple_report(
        report_name="VCM-report",
        current_states=[State.ADD_TO_VCM_REPORT, State.VCM_REPORT_SENT],
        next_state=State.VCM_REPORT_SENT,
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        add_vendor_customer_code=True,
        add_mmars_doc_id=False,
        db_session=db_session,
    )
    report_group.add_report(vcm_report)
    # ADD_TO_EFT_ERROR_REPORT -> EFT_ERROR_REPORT_SENT
    eft_error_report = _make_simple_report(
        report_name="EFT-error-report",
        current_states=[State.ADD_TO_EFT_ERROR_REPORT],
        next_state=State.EFT_ERROR_REPORT_SENT,
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        add_vendor_customer_code=True,
        add_mmars_doc_id=False,
        db_session=db_session,
    )
    report_group.add_report(eft_error_report)

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

    # Build the report from all three sets of payment errors
    payment_audit_errors = (
        gax_error_report_stuck_errors
        + gax_sent_stuck_errors
        + confirm_vend_status_in_mmars_stuck_errors
    )
    payment_audit_error_report = initialize_error_report("payment-audit-error-report")
    payment_audit_error_report.add_records(payment_audit_errors)
    report_group.add_report(payment_audit_error_report)

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

    # Build the report from all three sets of vendor errors
    vendor_audit_errors = (
        vcm_sent_stuck_errors + vcc_sent_stuck_errors + vcc_error_report_stuck_errors
    )
    vendor_audit_error_report = initialize_error_report("vendor-audit-error-report")
    vendor_audit_error_report.add_records(vendor_audit_errors)
    report_group.add_report(vendor_audit_error_report)

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
    # Build the report for EFT errors
    eft_audit_error_report = initialize_error_report("EFT-audit-error-report")
    eft_audit_error_report.add_records(eft_stuck_errors)
    report_group.add_report(eft_audit_error_report)

    # Finally create the reports and send them
    report_group.create_and_send_reports()


def send_ctr_error_reports(db_session: db.Session) -> None:
    logger.info("Creating CTR payment error reports")

    try:
        _send_ctr_payments_errors(db_session)

        # Finally if the email was sent successfully, we commit the state log
        # entries to the DB. The objects are already in a finished state
        # so they don't need to be modified/directly accessed here
        db_session.commit()

        logger.info("Successfully created CTR payment error reports")
    except Exception:
        logger.exception("Error creating CTR payment error reports")
        db_session.rollback()
