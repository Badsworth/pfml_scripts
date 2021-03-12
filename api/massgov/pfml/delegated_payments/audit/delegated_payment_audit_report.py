import pathlib
from dataclasses import dataclass
from typing import Iterable, List, Optional

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    Address,
    Claim,
    ClaimType,
    Employee,
    EmployeeAddress,
    Employer,
    LkClaimType,
    LkPaymentMethod,
    Payment,
    PaymentMethod,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_csv import (
    PAYMENT_AUDIT_CSV_HEADERS,
    PaymentAuditCSV,
)
from massgov.pfml.delegated_payments.reporting.delegated_abstract_reporting import (
    FileConfig,
    Report,
    ReportGroup,
)
from massgov.pfml.delegated_payments.step import Step

logger = logging.get_logger(__name__)

#################################
## Common Audit File Utilities ##
## TODO move to util file      ##
#################################


class PaymentAuditRowError(Exception):
    """An error in a row that prevents processing of the payment."""


@dataclass
class PaymentAuditData:
    """Wrapper class to create payment audit report"""

    payment: Payment
    is_first_time_payment: bool
    is_updated_payment: bool
    is_rejected_or_error: bool
    days_in_rejected_state: int
    rejected_by_program_integrity: Optional[bool] = None
    rejected_notes: str = ""


def write_audit_report(
    payment_audit_data_set: Iterable[PaymentAuditData],
    output_path: str,
    db_session: db.Session,
    report_name: str = "Payment-Audit-Report",
) -> Optional[pathlib.Path]:
    payment_audit_report_rows: List[PaymentAuditCSV] = []
    for payment_audit_data in payment_audit_data_set:
        payment_audit_report_rows.append(build_audit_report_row(payment_audit_data))

    return write_audit_report_rows(payment_audit_report_rows, output_path, db_session, report_name)


def write_audit_report_rows(
    payment_audit_report_rows: Iterable[PaymentAuditCSV],
    output_path: str,
    db_session: db.Session,
    report_name: str,
) -> Optional[pathlib.Path]:
    # Setup the output file
    file_config = FileConfig(file_prefix=output_path)
    report_group = ReportGroup(file_config=file_config)

    report = Report(report_name=report_name, header_record=PAYMENT_AUDIT_CSV_HEADERS)
    report_group.add_report(report)

    for payment_audit_report_row in payment_audit_report_rows:
        report.add_record(payment_audit_report_row)

    return report_group.create_and_send_reports()


def build_audit_report_row(payment_audit_data: PaymentAuditData) -> PaymentAuditCSV:
    """Build a single row of the payment audit report file"""

    payment: Payment = payment_audit_data.payment
    claim: Claim = payment.claim
    employee: Employee = claim.employee
    employee_address: EmployeeAddress = employee.addresses.first()  # TODO adjust after address validation work to get the most recent valid address
    address: Address = employee_address.address
    employer: Employer = claim.employer

    payment_audit_row = PaymentAuditCSV(
        pfml_payment_id=payment.payment_id,
        leave_type=get_leave_type(claim),
        first_name=payment.claim.employee.first_name,
        last_name=payment.claim.employee.last_name,
        address_line_1=address.address_line_one,
        address_line_2=address.address_line_two,
        city=address.city,
        state=address.geo_state.geo_state_description,
        zip=address.zip_code,
        payment_preference=get_payment_preference(employee),
        scheduled_payment_date=payment.payment_date.isoformat(),
        payment_period_start_date=payment.period_start_date.isoformat(),
        payment_period_end_date=payment.period_end_date.isoformat(),
        payment_amount=payment.amount,
        absence_case_number=claim.fineos_absence_id,
        c_value=payment.fineos_pei_c_value,
        i_value=payment.fineos_pei_i_value,
        employer_id=employer.fineos_employer_id if employer else None,
        case_status=claim.fineos_absence_status.absence_status_description
        if claim.fineos_absence_status
        else None,
        leave_request_id="",  # TODO these are not currently persisted - persist somewhere and fetch or take out of audit
        leave_request_decision="",  # TODO these are not currently persisted - persist somewhere and fetch or take out of audit
        is_first_time_payment=bool_to_str(payment_audit_data.is_first_time_payment),
        is_updated_payment=bool_to_str(payment_audit_data.is_updated_payment),
        is_rejected_or_error=bool_to_str(payment_audit_data.is_rejected_or_error),
        days_in_rejected_state=payment_audit_data.days_in_rejected_state,
        rejected_by_program_integrity=bool_to_str(payment_audit_data.rejected_by_program_integrity),
        rejected_notes=payment_audit_data.rejected_notes,
    )

    return payment_audit_row


def bool_to_str(flag: Optional[bool]) -> str:
    if flag is None:
        return ""

    if flag:
        return "Y"
    else:
        return "N"


def get_leave_type(claim: Claim) -> Optional[str]:
    claim_type: LkClaimType = claim.claim_type
    if not claim_type:
        return None

    if claim_type.claim_type_id == ClaimType.FAMILY_LEAVE.claim_type_id:
        return "Family"
    elif claim_type.claim_type_id == ClaimType.MEDICAL_LEAVE.claim_type_id:
        return "Medical"

    raise PaymentAuditRowError("Unexpected leave type %s" % claim_type.claim_type_description)


def get_payment_preference(employee: Employee) -> str:
    payment_preference: LkPaymentMethod = employee.payment_method
    if payment_preference.payment_method_id == PaymentMethod.ACH.payment_method_id:
        return "ACH"
    elif payment_preference.payment_method_id == PaymentMethod.CHECK.payment_method_id:
        return "Check"

    raise PaymentAuditRowError(
        "Unexpected payment preference %s" % payment_preference.payment_method_description
    )


##########################################
## Payment Audit Report file processing ##
##########################################


class PaymentAuditError(Exception):
    """An error in a row that prevents processing of the payment."""


class PaymentAuditReportStep(Step):
    def run_step(self) -> None:
        self.generate_audit_report()

    def sample_payments_for_audit_report(self) -> Iterable[Payment]:
        logger.info("Start sampling payments for audit report")

        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            state_log_util.AssociatedClass.PAYMENT,
            State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
            self.db_session,
        )

        payments: List[Payment] = []
        for state_log in state_logs:
            payment = state_log.payment

            # Shouldn't happen as they should always have a payment attached
            # but due to our unassociated state log logic, it technically can happen
            # elsewhere in the code and we want to be certain it isn't happening here
            if not payment:
                raise PaymentAuditError(
                    f"A state log was found without a payment in while trying to sample payments for audit report: {state_log.state_log_id}"
                )

            # transition the state sampling state
            # NOTE: we currently sample 100% of all available payments for audit.
            # In the future this will be based on a number of criteria
            # https://lwd.atlassian.net/wiki/spaces/API/pages/1309737679/Payment+Audit+and+Rejection#Sampling-Rules
            state_log_util.create_finished_state_log(
                payment,
                State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_AUDIT_REPORT,
                state_log_util.build_outcome("Add to Payment Audit Report"),
                self.db_session,
            )

            payments.append(payment)

        logger.info("Done sampling payments for audit report: %i", len(payments))

        return payments

    def set_sampled_payments_to_sent_state(self):
        logger.info("Start setting sampled payments to sent state")

        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            state_log_util.AssociatedClass.PAYMENT,
            State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_AUDIT_REPORT,
            self.db_session,
        )

        for state_log in state_logs:
            payment = state_log.payment

            # Shouldn't happen as they should always have a payment attached
            # but due to our unassociated state log logic, it technically can happen
            # elsewhere in the code and we want to be certain it isn't happening here
            if not payment:
                raise PaymentAuditError(
                    f"A state log was found without a payment while processing audit report: {state_log.state_log_id}"
                )

            state_log_util.create_finished_state_log(
                payment,
                State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
                state_log_util.build_outcome("Payment Audit Report sent"),
                self.db_session,
            )

        logger.info("Done setting sampled payments to sent state: %i", len(state_logs))

    def build_payment_audit_data_set(
        self, payments: Iterable[Payment]
    ) -> Iterable[PaymentAuditData]:
        logger.info("Start building payment audit data for sampled payments")

        payment_audit_data_set: List[Payment] = []

        for payment in payments:
            # TODO query state logs to populate the following
            is_first_time_payment = True
            is_updated_payment = False
            is_rejected_or_error = False
            days_in_rejected_state = 0

            payment_audit_data = PaymentAuditData(
                payment=payment,
                is_first_time_payment=is_first_time_payment,
                is_updated_payment=is_updated_payment,
                is_rejected_or_error=is_rejected_or_error,
                days_in_rejected_state=days_in_rejected_state,
            )
            payment_audit_data_set.append(payment_audit_data)

        logger.info(
            "Start building payment audit data for sampled payments: %i",
            len(payment_audit_data_set),
        )

        return payment_audit_data_set

    def generate_audit_report(self):
        """Top level function to generate and send payment audit report"""

        try:
            logger.info("Start generating payment audit report")

            s3_config = payments_config.get_s3_config()

            # sample files
            payments: Iterable[Payment] = self.sample_payments_for_audit_report()

            # generate payment audit data
            payment_audit_data_set: Iterable[PaymentAuditData] = self.build_payment_audit_data_set(
                payments
            )

            # write the report
            outbound_file_path = write_audit_report(
                payment_audit_data_set,
                s3_config.payment_audit_report_outbound_folder_path,
                self.db_session,
                report_name="Payment-Audit-Report",
            )

            if outbound_file_path is None:
                raise Exception("Payment Audit Report file not written to outbound folder")

            logger.info(
                "Done writing Payment Audit Report file to outbound folder: %s", outbound_file_path
            )

            # also write the report to the sent folder
            send_file_path = write_audit_report(
                payment_audit_data_set,
                s3_config.payment_audit_report_sent_folder_path,
                self.db_session,
                report_name="Payment-Audit-Report",
            )

            if send_file_path is None:
                raise Exception("Payment Audit Report file not written to send folder")

            logger.info(
                "Done writing Payment Audit Report file to outbound folder: %s", send_file_path
            )

            # create a reference file
            reference_file = ReferenceFile(
                file_location=str(send_file_path),
                reference_file_type_id=ReferenceFileType.DELEGATED_PAYMENT_AUDIT_REPORT.reference_file_type_id,
            )
            self.db_session.add(reference_file)

            # set sampled payments as sent
            self.set_sampled_payments_to_sent_state()

            # persist changes
            self.db_session.commit()

            logger.info("Done generating payment audit report")

        except Exception:
            self.db_session.rollback()
            logger.exception("Error creating Payment Audit file")

            # We do not want to run any subsequent steps if this fails
            raise
