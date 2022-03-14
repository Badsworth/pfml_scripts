from enum import Enum, unique
from typing import List, Optional

from sqlalchemy import desc

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import Payment, PaymentTransactionType, SharedPaymentConstants
from massgov.pfml.db.models.payments import PaymentAuditReportDetails
from massgov.pfml.db.models.state import Flow
from massgov.pfml.delegated_payments.delegated_payments_util import get_traceable_payment_details

logger = massgov.pfml.util.logging.get_logger(__name__)


@unique
class PreapprovalIssue(str, Enum):
    ORPHANED_TAX_WITHOLDING = "Orphaned Tax Withholding"
    ORPHANED_EMPLOYER_REIMBURSEMENT = "Orphaned Employer Reimbursement"
    CLAIM_CONTAINS_EMPLOYER_REIMBURSEMENT = "Claim contains Employer Reimbursements"
    # The description for this is issue is generated from the audit report detail descriptions and this value is not used
    PAYMENT_HAS_AUDIT_REPORT_DETAIL_RECORDS = "Payment has audit report details"
    LESS_THAN_THREE_PREVIOUS_PAYMENTS = "There were less than three previous payments"
    LAST_THREE_PAYMENTS_NOT_SUCCESSFUL = "Last 3 Payments Not Successful"
    CHANGED_EFT = "Changed EFT"
    CHANGED_ADDRESS = "Changed Address"
    CHANGED_PAYMENT_PREFERENCE = "Changed Payment Preference"
    CHANGED_NAME = "Changed Name"
    UNKNOWN = "Error occurred determining preapproval status for payment"


class PreapprovalStatus:

    payment: Payment
    last_payment: Optional[Payment]
    issues: List[PreapprovalIssue]
    audit_report_detail_records: List[PaymentAuditReportDetails]

    def __init__(
        self, payment: Payment, audit_report_detail_records: List[PaymentAuditReportDetails]
    ) -> None:
        self.payment = payment
        self.last_payment = None
        self.audit_report_detail_records = audit_report_detail_records
        self.issues = []

    def add_issue(self, issue: PreapprovalIssue) -> None:
        if (
            issue
            in [
                PreapprovalIssue.CHANGED_ADDRESS,
                PreapprovalIssue.CHANGED_EFT,
                PreapprovalIssue.CHANGED_NAME,
                PreapprovalIssue.CHANGED_PAYMENT_PREFERENCE,
            ]
            and self.last_payment is None
        ):
            raise Exception(
                "Issue cannot be added if previous payments do not exist.  Please confirm issue is getting added correctly"
            )
        if issue not in self.issues:
            self.issues.append(issue)

    def is_preapproved(self):
        return len(self.issues) == 0

    def get_preapproval_issue_description(self) -> Optional[str]:
        if self.is_preapproved():
            return None
        extra = get_traceable_payment_details(self.payment)
        try:
            issue_descriptions = []
            for issue in self.issues:
                extra["preapproval_issue"] = issue.value
                logger.info("Payment encountered preapproval issue", extra=extra)

                if issue == PreapprovalIssue.CHANGED_ADDRESS and self.last_payment:
                    old_address = (
                        f"{self.last_payment.experian_address_pair.fineos_address.address_line_one} {self.last_payment.experian_address_pair.fineos_address.city} {self.last_payment.experian_address_pair.fineos_address.zip_code}"
                        if self.last_payment.experian_address_pair
                        else "No address associated with last payment"
                    )
                    new_address = (
                        f"{self.payment.experian_address_pair.fineos_address.address_line_one} {self.payment.experian_address_pair.fineos_address.city} {self.payment.experian_address_pair.fineos_address.zip_code}"
                        if self.payment.experian_address_pair
                        else "No address associated with payment"
                    )
                    issue_descriptions.append(f"{issue.value}: {old_address} -> {new_address}")

                elif issue == PreapprovalIssue.CHANGED_EFT and self.last_payment:
                    issue_descriptions.append(
                        f"{issue.value}: {self.last_payment.pub_eft_id} -> {self.payment.pub_eft_id}"
                    )

                elif issue == PreapprovalIssue.CHANGED_NAME and self.last_payment:
                    issue_descriptions.append(
                        f"{issue.value}: {self.last_payment.fineos_employee_first_name} {self.last_payment.fineos_employee_last_name} -> {self.payment.fineos_employee_first_name} {self.payment.fineos_employee_last_name}"
                    )

                elif issue == PreapprovalIssue.CHANGED_PAYMENT_PREFERENCE and self.last_payment:
                    issue_descriptions.append(
                        f"{issue.value}: {self.last_payment.disb_method.payment_method_description} -> {self.payment.disb_method.payment_method_description}"
                    )

                elif issue == PreapprovalIssue.PAYMENT_HAS_AUDIT_REPORT_DETAIL_RECORDS:
                    audit_report_details_descriptions = []
                    for audit_report_detail in self.audit_report_detail_records:
                        audit_report_details_descriptions.append(
                            audit_report_detail.audit_report_type.payment_audit_report_type_description
                        )
                    issue_descriptions.append(",".join(audit_report_details_descriptions))

                else:
                    issue_descriptions.append(issue.value)

            return ";".join(issue_descriptions)
        except Exception:
            logger.exception(
                "An error was encountered creating the preapproval issue description.", extra=extra
            )
            return PreapprovalIssue.UNKNOWN


def get_payment_preapproval_status(
    payment: Payment,
    staged_audit_report_details_list: List[PaymentAuditReportDetails],
    db_session: db.Session,
) -> PreapprovalStatus:
    preapproval_status = PreapprovalStatus(payment, staged_audit_report_details_list)

    # Tax witholdings should always be examined
    if (
        payment.payment_transaction_type_id
        == PaymentTransactionType.FEDERAL_TAX_WITHHOLDING.payment_transaction_type_id
        or payment.payment_transaction_type_id
        == PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id
    ):
        preapproval_status.add_issue(PreapprovalIssue.ORPHANED_TAX_WITHOLDING)
        return preapproval_status

    # Employer reimbursements are a new feature and these payments should always be examined
    if (
        payment.payment_transaction_type_id
        == PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id
    ):
        preapproval_status.add_issue(PreapprovalIssue.ORPHANED_EMPLOYER_REIMBURSEMENT)
        return preapproval_status

    previous_employer_reimbursement_payment_count = (
        db_session.query(Payment)
        .filter(Payment.claim_id == payment.claim_id)
        .filter(Payment.fineos_extract_import_log_id != payment.fineos_extract_import_log_id)
        .filter(
            Payment.payment_transaction_type_id
            == PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id
        )
        .count()
    )

    all_previous_payments: List[Payment] = (
        db_session.query(Payment)
        .filter(Payment.fineos_leave_request_id == payment.fineos_leave_request_id)
        .filter(
            Payment.payment_transaction_type_id
            == PaymentTransactionType.STANDARD.payment_transaction_type_id
        )
        .filter(Payment.exclude_from_payment_status != True)  # noqa: E712
        .order_by(Payment.fineos_pei_i_value, desc(Payment.fineos_extract_import_log_id))
        .distinct(Payment.fineos_pei_i_value)
        .all()
    )

    # Ignoring the mypy error since fineos_extract_import_log_id is technically Optional[int]
    # but since these records all come from the db, the import log will be present
    all_previous_payments.sort(
        key=lambda payment: (payment.fineos_extract_import_log_id), reverse=True  # type: ignore
    )
    relevant_previous_payments: List[Payment] = []
    for past_payment in all_previous_payments:
        if len(relevant_previous_payments) == 3:
            break
        if past_payment.fineos_extract_import_log_id == payment.fineos_extract_import_log_id:
            continue
        else:
            relevant_previous_payments.append(past_payment)

    last_payment = relevant_previous_payments[0] if len(relevant_previous_payments) > 0 else None
    preapproval_status.last_payment = last_payment

    # Employer reimbursements are a new feature and claims that have previously recorded one
    # should always have payments examined
    if previous_employer_reimbursement_payment_count != 0:
        preapproval_status.add_issue(PreapprovalIssue.CLAIM_CONTAINS_EMPLOYER_REIMBURSEMENT)

    if len(relevant_previous_payments) < 3:
        preapproval_status.add_issue(PreapprovalIssue.LESS_THAN_THREE_PREVIOUS_PAYMENTS)

    if len(staged_audit_report_details_list) != 0:
        preapproval_status.add_issue(PreapprovalIssue.PAYMENT_HAS_AUDIT_REPORT_DETAIL_RECORDS)

    for previous_payment in relevant_previous_payments:
        payment_state_log = state_log_util.get_latest_state_log_in_flow(
            previous_payment, Flow.DELEGATED_PAYMENT, db_session
        )
        if not payment_state_log:
            logger.error(
                "Payment was missing state log.", extra=get_traceable_payment_details(payment)
            )
            preapproval_status.add_issue(PreapprovalIssue.UNKNOWN)
        elif (
            payment_state_log
            and payment_state_log.end_state_id not in SharedPaymentConstants.PAID_STATE_IDS
        ):
            preapproval_status.add_issue(PreapprovalIssue.LAST_THREE_PAYMENTS_NOT_SUCCESSFUL)

    if last_payment:
        if payment.pub_eft_id != last_payment.pub_eft_id:
            preapproval_status.add_issue(PreapprovalIssue.CHANGED_EFT)

        if (
            payment.fineos_employee_first_name != last_payment.fineos_employee_first_name
            or payment.fineos_employee_last_name != last_payment.fineos_employee_last_name
        ):
            preapproval_status.add_issue(PreapprovalIssue.CHANGED_NAME)

        if payment.disb_method_id != last_payment.disb_method_id:
            preapproval_status.add_issue(PreapprovalIssue.CHANGED_PAYMENT_PREFERENCE)

        if payment.experian_address_pair_id != last_payment.experian_address_pair_id:
            preapproval_status.add_issue(PreapprovalIssue.CHANGED_ADDRESS)

    return preapproval_status
