import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional, Tuple

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Claim,
    ClaimType,
    Employee,
    LkClaimType,
    LkPaymentMethod,
    Payment,
    PaymentMethod,
    PaymentTransactionType,
    State,
)
from massgov.pfml.db.models.payments import MmarsPaymentData
from massgov.pfml.delegated_payments.step import Step

logger = logging.get_logger(__name__)


class ConvertMmarsDataStep(Step):
    class Metrics(str, enum.Enum):
        PAYMENTS_PROCESSED_COUNT = "payments_processed_count"
        PAYMENT_CREATED_COUNT = "payment_created_count"
        PAYMENT_FAILED_VALIDATION_COUNT = "payment_failed_validation_count"

        EMPLOYEE_FOUND_BY_VENDOR_CODE_COUNT = "employee_found_by_vendor_code_count"
        EMPLOYEE_NOT_FOUND_FALLBACK_TO_CLAIM_COUNT = "employee_not_found_fallback_to_claim_count"

    validation_containers_with_issues: Optional[List[payments_util.ValidationContainer]]

    def run_step(self) -> None:
        mmars_payment_records = self.fetch_unprocessed_mmars_payment_records()
        self.process_mmars_payment_records(mmars_payment_records)

    def fetch_unprocessed_mmars_payment_records(self) -> Iterable[MmarsPaymentData]:
        # Because we will be processing ~150k records, we
        # want to be careful about blowing up memory, so we'll only yield 1000 records
        # before going back to the DB for more.

        # We also only fetch payments that don't have an attached payment ID
        return (
            self.db_session.query(MmarsPaymentData)
            .filter(MmarsPaymentData.payment_id == None)  # noqa: E711
            .yield_per(1000)
        )

    def process_mmars_payment_records(
        self, mmars_payment_records: Iterable[MmarsPaymentData]
    ) -> None:
        self.validation_containers_with_issues = []
        for mmars_payment_data in mmars_payment_records:
            self.process_mmars_payment_data(mmars_payment_data)
            self.increment(self.Metrics.PAYMENTS_PROCESSED_COUNT)

        logger.warning("The following records failed validation and were not created")
        for validation_container in self.validation_containers_with_issues:
            extra = {"vendor_invoice_number": validation_container.record_key}
            log_validation_issue(validation_container, extra)

    def process_mmars_payment_data(
        self, mmars_payment_data: MmarsPaymentData
    ) -> payments_util.ValidationContainer:
        # Don't add any PII to the validation container as we'll log them at the end.
        validation_container = payments_util.ValidationContainer(
            mmars_payment_data.vendor_invoice_no if mmars_payment_data.vendor_invoice_no else ""
        )
        extra = {
            "mmars_payment_data_id": mmars_payment_data.mmars_payment_data_id,
            "vendor_invoice_number": mmars_payment_data.vendor_invoice_no,
        }
        logger.info("Processing payment for %s", validation_container.record_key, extra=extra)

        absence_case_number, fineos_pei_i_value = self.get_absence_id_i_value(mmars_payment_data)
        if not absence_case_number:
            validation_container.add_validation_issue(
                payments_util.ValidationReason.INVALID_VALUE, "absence_case_number"
            )
        if not fineos_pei_i_value:
            validation_container.add_validation_issue(
                payments_util.ValidationReason.INVALID_VALUE, "fineos_pei_i_value"
            )

        # validate claim/employee exist
        claim = self.get_claim(absence_case_number)
        employee = self.get_employee(mmars_payment_data)
        if not claim:
            # Shouldn't happen based on prior data analysis, but just in case
            validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_IN_DB, "claim"
            )

        if claim and not employee:
            # About a dozen employees won't be found
            # Manual verification has confirmed that the payments
            # associated with these do in fact match with the claim
            # and that this is safe to do.
            employee = claim.employee
            self.increment(self.Metrics.EMPLOYEE_NOT_FOUND_FALLBACK_TO_CLAIM_COUNT)

        # Validate the employee we found is attached to the claim just in case
        if employee and claim and employee.employee_id != claim.employee_id:
            validation_container.add_validation_issue(
                payments_util.ValidationReason.CLAIMANT_MISMATCH,
                f"Claimant {claim.employee_id} is attached to claim {claim.fineos_absence_id}, but claimant {employee.employee_id} was found.",
            )

        payment = self.process_payment(
            mmars_payment_data, claim, employee, fineos_pei_i_value, validation_container
        )

        # If no validation issues, create the payment record in the DB
        if not validation_container.has_validation_issues() and payment:
            self.db_session.add(payment)
            mmars_payment_data.payment = payment
            self.increment(self.Metrics.PAYMENT_CREATED_COUNT)

            state_log_util.create_finished_state_log(
                end_state=State.LEGACY_MMARS_PAYMENT_PAID,
                associated_model=payment,
                outcome=state_log_util.build_outcome("Successfully backfilled MMARS payment"),
                db_session=self.db_session,
            )
        else:
            # don't create the payment, but log the validation issues.
            if not self.validation_containers_with_issues:
                self.validation_containers_with_issues = []
            self.validation_containers_with_issues.append(validation_container)
            log_validation_issue(validation_container, extra)
            self.increment(self.Metrics.PAYMENT_FAILED_VALIDATION_COUNT)

        # Return the validation container to make testing simpler
        return validation_container

    def get_absence_id_i_value(
        self, mmars_payment_data: MmarsPaymentData
    ) -> Tuple[Optional[str], Optional[str]]:
        # We expect the vendor invoice number to look like:
        # NTN-000001-ABS-01_12345
        # Where the first part is the absence case number:  NTN-000001-ABS-01
        # and the second is the I value: 12345
        if not mmars_payment_data.vendor_invoice_no:
            return None, None

        invoice_num_tokens = mmars_payment_data.vendor_invoice_no.split("_")
        if len(invoice_num_tokens) != 2:
            # OVERRIDE: There is a single payment without the I value portion
            #           but we have manually figured out what it should be
            if len(invoice_num_tokens) == 1 and invoice_num_tokens[0] == "NTN-246247-ABS-01":
                return invoice_num_tokens[0], "904"

            # Shouldn't ever happen
            return None, None

        absence_case_id, i_value = invoice_num_tokens

        if not i_value.isnumeric():
            # There are five records that have a non-numeric I value
            # KS01 - Duplicate of another payment we later sent again
            # KS02 - Same as KS01
            # EOLMRM1 - Duplicate of a payment, although this was later
            # EOLMRM2 - Same as EOLMRM1
            # EOLMME1 - This is actually 5 separate payments that were
            #           manually merged into one.

            # The first four will be handled by the duplicate,
            # the last one requires further thought to determine what
            # approach we want to take.

            return absence_case_id, None

        return absence_case_id, i_value

    def get_claim(self, absence_case_number: Optional[str]) -> Optional[Claim]:
        if not absence_case_number:
            return None
        return (
            self.db_session.query(Claim)
            .filter(Claim.fineos_absence_id == absence_case_number)
            .one_or_none()
        )

    def get_employee(self, mmars_payment_data: MmarsPaymentData) -> Optional[Employee]:
        if not mmars_payment_data.vendor_customer_code:
            return None

        # Most employee records should have a corresponding code in our DB
        # from the VCC vendor process
        employee = (
            self.db_session.query(Employee)
            .filter(Employee.ctr_vendor_customer_code == mmars_payment_data.vendor_customer_code)
            .first()
        )
        if employee:
            self.increment(self.Metrics.EMPLOYEE_FOUND_BY_VENDOR_CODE_COUNT)
            return employee

        return None

    def get_payment_method(self, mmars_payment_data: MmarsPaymentData) -> Optional[LkPaymentMethod]:
        if mmars_payment_data.disb_doc_code == "EFT":
            return PaymentMethod.ACH
        if mmars_payment_data.disb_doc_code == "AD":
            return PaymentMethod.CHECK

        # A single payment is expected to hit this
        return None

    def get_claim_type(self, mmars_payment_data: MmarsPaymentData) -> Optional[LkClaimType]:
        # 7246 -> Medical Leave
        # 7247 -> Family Leave
        # Just reversing how this was generated for the voucher/GAX
        if mmars_payment_data.activity == "7246":
            return ClaimType.FAMILY_LEAVE
        if mmars_payment_data.activity == "7247":
            return ClaimType.MEDICAL_LEAVE

        return None

    def process_payment(
        self,
        mmars_payment_data: MmarsPaymentData,
        claim: Optional[Claim],
        employee: Optional[Employee],
        fineos_pei_i_value: Optional[str],
        validation_container: payments_util.ValidationContainer,
    ) -> Optional[Payment]:

        # Verify that no prior payment exists with the same I value
        # Manual validation indicates this shouldn't happen
        existing_payment = (
            self.db_session.query(Payment)
            .filter(Payment.fineos_pei_i_value == fineos_pei_i_value)
            .first()
        )
        if existing_payment:
            validation_container.add_validation_issue(
                payments_util.ValidationReason.RECEIVED_PAYMENT_CURRENTLY_BEING_PROCESSED,
                f"Payment {existing_payment.payment_id} already exists, was consumed on {existing_payment.fineos_extraction_date}",
            )
            return None

        # Pre-verified that every payment in this dataset correlates to
        # a "StandardOut" event type in FINEOS (and aren't employer reimbursements either)
        payment_transaction_type = PaymentTransactionType.STANDARD_LEGACY_MMARS

        # Verify all required fields set

        period_start_date = mmars_payment_data.pymt_service_from_date
        if not period_start_date:
            validation_container.add_validation_issue(
                payments_util.ValidationReason.INVALID_VALUE, "pymt_service_from_date"
            )

        period_end_date = mmars_payment_data.pymt_service_to_date
        if not period_end_date:
            validation_container.add_validation_issue(
                payments_util.ValidationReason.INVALID_VALUE, "pymt_service_to_date"
            )

        payment_date = mmars_payment_data.warrant_select_date
        if not payment_date:
            validation_container.add_validation_issue(
                payments_util.ValidationReason.INVALID_VALUE, "warrant_select_date"
            )

        amount = mmars_payment_data.pymt_actg_line_amount
        if not amount:
            validation_container.add_validation_issue(
                payments_util.ValidationReason.INVALID_VALUE, "pymt_actg_line_amount"
            )

        disb_check_eft_number = mmars_payment_data.check_eft_no
        if not disb_check_eft_number:
            validation_container.add_validation_issue(
                payments_util.ValidationReason.INVALID_VALUE, "check_eft_no"
            )

        disb_check_eft_issue_date = mmars_payment_data.check_eft_issue_date
        if not disb_check_eft_issue_date:
            validation_container.add_validation_issue(
                payments_util.ValidationReason.INVALID_VALUE, "check_eft_issue_date"
            )

        disb_method = self.get_payment_method(mmars_payment_data)
        if not disb_method:
            validation_container.add_validation_issue(
                payments_util.ValidationReason.INVALID_VALUE, "disb_doc_code"
            )

        # Pre-verified, shouldn't fail
        claim_type = self.get_claim_type(mmars_payment_data)
        if not claim_type:
            validation_container.add_validation_issue(
                payments_util.ValidationReason.INVALID_VALUE, "activity"
            )

        # If any issues were present above, don't create the payment
        if validation_container.has_validation_issues():
            return None

        payment = Payment(
            payment_id=uuid.uuid4(),
            claim_id=claim.claim_id if claim else None,
            employee_id=employee.employee_id if employee else None,
            fineos_pei_c_value="7326",  # This is the same for all payments
            fineos_pei_i_value=fineos_pei_i_value,
            amount=amount if amount else Decimal(0),
            payment_transaction_type_id=payment_transaction_type.payment_transaction_type_id
            if payment_transaction_type
            else None,
            period_start_date=get_date(period_start_date),
            period_end_date=get_date(period_end_date),
            payment_date=get_date(payment_date),
            disb_check_eft_number=disb_check_eft_number,
            disb_check_eft_issue_date=get_date(disb_check_eft_issue_date),
            disb_method_id=disb_method.payment_method_id if disb_method else None,
            claim_type_id=claim_type.claim_type_id if claim_type else None,
            fineos_extract_import_log_id=self.get_import_log_id(),
        )
        return payment


def get_date(date_obj: Any) -> Optional[date]:
    # Utility method for handling dates, as we're dealing with
    # a weird mix of dates, datetime and so on.
    if not date_obj:
        return None
    if type(date_obj) == date:
        return date_obj
    if type(date_obj) == datetime:
        return date_obj.date()

    return None


def log_validation_issue(
    validation_container: payments_util.ValidationContainer, extra: Dict[str, Any]
) -> None:
    logger.warning(
        "The payment for %s failed validation", validation_container.record_key, extra=extra
    )

    for validation_issue in validation_container.validation_issues:
        logger.warning(
            "Payment %s failed validation %s: %s",
            validation_container.record_key,
            validation_issue.reason,
            validation_issue.details,
            extra=extra,
        )
