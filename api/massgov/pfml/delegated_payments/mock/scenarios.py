from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from massgov.pfml.db.models.absences import AbsencePeriodType
from massgov.pfml.db.models.employees import (
    BankAccountType,
    LkAbsencePeriodType,
    LkBankAccountType,
    LkPaymentMethod,
    LkPaymentTransactionType,
    PaymentMethod,
    PaymentTransactionType,
)
from massgov.pfml.db.models.payments import (
    AUDIT_REJECT_NOTE_TO_WRITEBACK_TRANSACTION_STATUS,
    AUDIT_SKIPPED_NOTE_TO_WRITEBACK_TRANSACTION_STATUS,
)
from massgov.pfml.delegated_payments.pub.check_return import PaidStatus


class ScenarioName(Enum):
    # Happy path scenarios
    HAPPY_PATH_MEDICAL_ACH_PRENOTED = "HAPPY_PATH_MEDICAL_ACH_PRENOTED"
    HAPPY_PATH_FAMILY_ACH_PRENOTED = "HAPPY_PATH_FAMILY_ACH_PRENOTED"
    HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN = (
        "HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN"
    )
    UNKNOWN_LEAVE_REQUEST_DECISION = "UNKNOWN_LEAVE_REQUEST_DECISION"
    IN_REVIEW_LEAVE_REQUEST_DECISION = "IN_REVIEW_LEAVE_REQUEST_DECISION"
    IN_REVIEW_LEAVE_REQUEST_ADHOC_PAYMENTS_DECISION = (
        "IN_REVIEW_LEAVE_REQUEST_ADHOC_PAYMENTS_DECISION"
    )

    HAPPY_PATH_FAMILY_CHECK_PRENOTED = "HAPPY_PATH_FAMILY_CHECK_PRENOTED"

    HAPPY_PATH_CHECK_FAMILY_RETURN_PAID = "PUB_CHECK_FAMILY_RETURN_PAID"
    HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING = "PUB_CHECK_FAMILY_RETURN_OUTSTANDING"
    HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE = "PUB_CHECK_FAMILY_RETURN_FUTURE"

    HAPPY_PATH_TWO_PAYMENTS_UNDER_WEEKLY_CAP = "HAPPY_PATH_TWO_PAYMENTS_UNDER_WEEKLY_CAP"
    HAPPY_PATH_TWO_ADHOC_PAYMENTS_OVER_CAP = "HAPPY_PATH_TWO_ADHOC_PAYMENTS_OVER_CAP"

    # Audit scenarios
    HAPPY_PATH_DOR_FINEOS_NAME_MISMATCH = "HAPPY_PATH_DOR_FINEOS_NAME_MISMATCH"
    HAPPY_PATH_DUA_ADDITIONAL_INCOME = "HAPPY_PATH_DUA_ADDITIONAL_INCOME"
    HAPPY_PATH_DIA_ADDITIONAL_INCOME = "HAPPY_PATH_DIA_ADDITIONAL_INCOME"
    HAPPY_PATH_MAX_LEAVE_DURATION_EXCEEDED = "HAPPY_PATH_MAX_LEAVE_DURATION_EXCEEDED"
    HAPPY_PATH_PAYMENT_DATE_MISMATCH = "HAPPY_PATH_PAYMENT_DATE_MISMATCH"
    HAPPY_PATH_PAYMENT_PREAPPROVED = "HAPPY_PATH_PAYMENT_PREAPPROVED"

    # Non-Standard Payments
    ZERO_DOLLAR_PAYMENT = "ZERO_DOLLAR_PAYMENT"
    CANCELLATION_PAYMENT = "CANCELLATION_PAYMENT"
    OVERPAYMENT_PAYMENT_POSITIVE = "OVERPAYMENT_PAYMENT_POSITIVE"
    OVERPAYMENT_PAYMENT_NEGATIVE = "OVERPAYMENT_PAYMENT_NEGATIVE"
    OVERPAYMENT_MISSING_NON_VPEI_RECORDS = "OVERPAYMENT_MISSING_NON_VPEI_RECORDS"

    # Prenote
    PRENOTE_WITH_EXISTING_EFT_ACCOUNT = "PRENOTE_WITH_EXISTING_EFT_ACCOUNT"
    CLAIMANT_PRENOTED_NO_PAYMENT_RECEIVED = "CLAIMANT_PRENOTED_NO_PAYMENT_RECEIVED"

    # TODO not a real scenario - remove
    EFT_ACCOUNT_NOT_PRENOTED = "EFT_ACCOUNT_NOT_PRENOTED"

    # Address Verification
    CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN = (
        "CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN"
    )
    CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN_FIXED = (
        "CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN_FIXED"
    )

    # Automated Validation Rules (TODO add more validation issue scenarios)
    INVALID_ADDRESS_FIXED = "INVALID_ADDRESS_FIXED"
    REJECTED_LEAVE_REQUEST_DECISION = "REJECTED_LEAVE_REQUEST_DECISION"
    PAYMENT_EXTRACT_EMPLOYEE_MISSING_IN_DB = "PAYMENT_EXTRACT_EMPLOYEE_MISSING_IN_DB"
    SECOND_PAYMENT_FOR_PERIOD_OVER_CAP = "SECOND_PAYMENT_FOR_PERIOD_OVER_CAP"

    HAPPY_PATH_CLAIM_MISSING_EMPLOYEE = "HAPPY_PATH_CLAIM_MISSING_EMPLOYEE"
    CLAIM_UNABLE_TO_SET_EMPLOYEE_FROM_EXTRACT = "CLAIM_UNABLE_TO_SET_EMPLOYEE_FROM_EXTRACT"
    CLAIM_NOT_ID_PROOFED = "CLAIM_NOT_ID_PROOFED"

    # Audit
    AUDIT_REJECTED = "AUDIT_REJECTED"
    AUDIT_REJECTED_WITH_NOTE = "AUDIT_REJECTED_WITH_NOTE"
    AUDIT_REJECTED_THEN_ACCEPTED = "AUDIT_REJECTED_THEN_ACCEPTED"

    AUDIT_SKIPPED = "AUDIT_SKIPPED"
    AUDIT_SKIPPED_WITH_NOTE = "AUDIT_SKIPPED_WITH_NOTE"
    AUDIT_SKIPPED_THEN_ACCEPTED = "AUDIT_SKIPPED_THEN_ACCEPTED"

    # Returns
    PUB_ACH_PRENOTE_RETURN = "PUB_ACH_PRENOTE_RETURN"
    PUB_ACH_PRENOTE_NOTIFICATION = "PUB_ACH_PRENOTE_NOTIFICATION"
    PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT = "PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT"
    PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND = "PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND"

    PUB_ACH_FAMILY_RETURN = "PUB_ACH_FAMILY_RETURN"
    PUB_ACH_FAMILY_NOTIFICATION = "PUB_ACH_FAMILY_NOTIFICATION"

    PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT = (
        "PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT"
    )
    PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND = "PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND"

    PUB_ACH_MEDICAL_RETURN = "PUB_ACH_MEDICAL_RETURN"
    PUB_ACH_MEDICAL_NOTIFICATION = "PUB_ACH_MEDICAL_NOTIFICATION"

    PUB_ACH_MANUAL_REJECT = "PUB_ACH_MANUAL_REJECT"

    PUB_CHECK_FAMILY_RETURN_VOID = "PUB_CHECK_FAMILY_RETURN_VOID"
    PUB_CHECK_FAMILY_RETURN_STALE = "PUB_CHECK_FAMILY_RETURN_STALE"
    PUB_CHECK_FAMILY_RETURN_STOP = "PUB_CHECK_FAMILY_RETURN_STOP"

    PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND = (
        "PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND"
    )

    # Employer Reimbursement Payments
    EMPLOYER_REIMBURSEMENT_PAYMENT = "EMPLOYER_REIMBURSEMENT_PAYMENT"
    # EMPLOYER_REIMBURSEMENT_WITH_INVALID_ADDRESS = "EMPLOYER_REIMBURSEMENT_WITH_INVALID_ADDRESS"
    # EMPLOYER_REIMBURSEMENT_WITH_STANDARD_PAYMENT = "EMPLOYER_REIMBURSEMENT_WITH_STANDARD_PAYMENT"
    # STANDARD_PAYMENT_WITH_TW_AND_ER = "STANDARD_PAYMENT_WITH_TW_AND_ER"
    # EMPLOYER_REIMBURSEMENT_WITH_STANDARD_PAYMENT_INVALID_ADDRESS = (
    #     "EMPLOYER_REIMBURSEMENT_WITH_STANDARD_PAYMENT_INVALID_ADDRESS"
    # )
    # EMPLOYER_REIMBURSEMENT_INVALID_ADDRESS_WITH_VALID_STANDARD_PAYMENT = (
    #     "EMPLOYER_REIMBURSEMENT_INVALID_ADDRESS_WITH_VALID_STANDARD_PAYMENT"
    # )
    # EMPLOYER_REIMBURSEMENT_PAYMENT_AMOUNT_OVER_CAP =("EMPLOYER_REIMBURSEMENT_PAYMENT_AMOUNT_OVER_CAP")
    # EMPLOYER_REIMBURSEMENT_PAYMENT_WITH_EFT = "EMPLOYER_REIMBURSEMENT_PAYMENT_WITH_EFT"

    # Tax withholding payments
    HAPPY_PATH_TAX_WITHHOLDING = "HAPPY_PATH_TAX_WITHHOLDING"
    TAX_WITHHOLDING_ADDRESS_NO_MATCHES_FROM_EXPERIAN = (
        "TAX_WITHHOLDING_ADDRESS_NO_MATCHES_FROM_EXPERIAN"
    )

    HAPPY_PATH_TAX_WITHHOLDING_PAYMENT_METHOD_CHECK = (
        "HAPPY_PATH_TAX_WITHHOLDING_PAYMENT_METHOD_CHECK"
    )

    TAX_WITHHOLDING_PRIMARY_PAYMENT_NOT_PRENOTED = "TAX_WITHHOLDING_PRIMARY_PAYMENT_NOT_PRENOTED"

    TAX_WITHHOLDING_MISSING_PRIMARY_PAYMENT = "TAX_WITHHOLDING_MISSING_PRIMARY_PAYMENT"

    TAX_WITHHOLDING_AUDIT_SKIPPED_THEN_ACCEPTED = "TAX_WITHHOLDING_AUDIT_SKIPPED_THEN_ACCEPTED"

    TAX_WITHHOLDING_CANCELLATION_PAYMENT = "TAX_WITHHOLDING_CANCELLATION_PAYMENT"


@dataclass
class ScenarioDescriptor:
    scenario_name: ScenarioName

    employee_in_payment_extract_missing_in_db: bool = False

    # missing claims will be created by the claimant extract
    has_existing_claim: bool = True

    # missing employee
    claim_missing_employee: bool = False

    # create payment
    create_payment: bool = True

    # unknown employee
    claim_extract_employee_identifier_unknown: bool = False

    claim_type: str = "Family"
    is_id_proofed: bool = True

    payment_method: LkPaymentMethod = PaymentMethod.ACH
    payment_transaction_type: LkPaymentTransactionType = PaymentTransactionType.STANDARD

    account_type: LkBankAccountType = BankAccountType.CHECKING

    existing_eft_account: bool = True
    prenoted: bool = True  # TODO add all prenote states

    invalid_address: bool = False
    invalid_address_fixed: bool = False

    # This adds a second payment that'll show up in round 2
    has_additional_payment_in_period: bool = False

    # prior_verified_address: bool = False TODO add when available
    fineos_extract_address_valid: bool = True
    fineos_extract_address_valid_after_fix: bool = False

    leave_request_decision: str = "Approved"

    dor_fineos_name_mismatch: bool = False
    dua_additional_income: bool = False
    dia_additional_income: bool = False
    payment_date_mismatch: bool = False

    # Payment date mismatch processor fails this check otherwise.
    has_absence_period: bool = True
    absence_period_type: LkAbsencePeriodType = AbsencePeriodType.CONTINUOUS

    max_leave_duration_exceeded: bool = False

    is_audit_rejected: bool = False
    is_audit_skipped: bool = False
    is_audit_approved_delayed: bool = False

    audit_response_note: str = ""

    negative_payment_amount: bool = False
    payment_close_to_cap: bool = False
    payment_over_cap: bool = False
    is_adhoc_payment: bool = False

    include_claim_details: bool = True

    # is_create_employee : bool = True
    # ACH Returns
    # https://lwd.atlassian.net/wiki/spaces/API/pages/1333364105/PUB+ACH+Return+File+Format

    pub_ach_response_return: bool = False
    pub_ach_return_reason_code: str = "RO1"

    pub_ach_return_invalid_payment_id_format: bool = False
    pub_ach_return_payment_id_not_found: bool = False

    pub_ach_return_invalid_prenote_payment_id_format: bool = False
    pub_ach_return_prenote_payment_id_not_found: bool = False

    pub_ach_response_change_notification: bool = False
    pub_ach_notification_reason_code: str = "CO1"

    # Check returns
    pub_check_response: bool = True
    pub_check_paid_response: bool = True
    pub_check_outstanding_response: bool = False
    pub_check_outstanding_response_status: PaidStatus = PaidStatus.OUTSTANDING

    pub_check_return_invalid_check_number: bool = False

    is_tax_withholding_records_exists: bool = False
    is_duplicate_tax_withholding_records_exists: bool = False
    is_tax_withholding_record_without_primary_payment: bool = False

    # Employer reimbursements
    is_employer_reimbursement_records_exists: bool = False
    is_employer_reimbursement_fineos_extract_address_valid: bool = True

    # Preapproval
    has_past_payments: bool = False

    # Manual rejects
    manual_pub_reject_response: bool = False
    manual_pub_reject_notes: str = "Manual Failure Test"


SCENARIO_DESCRIPTORS: List[ScenarioDescriptor] = [
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED, claim_type="Employee"
    ),
    ScenarioDescriptor(scenario_name=ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED),
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
        payment_method=PaymentMethod.CHECK,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.ZERO_DOLLAR_PAYMENT,
        payment_transaction_type=PaymentTransactionType.ZERO_DOLLAR,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.CANCELLATION_PAYMENT,
        payment_transaction_type=PaymentTransactionType.CANCELLATION,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.OVERPAYMENT_PAYMENT_POSITIVE,
        payment_transaction_type=PaymentTransactionType.OVERPAYMENT,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.OVERPAYMENT_PAYMENT_NEGATIVE,
        payment_transaction_type=PaymentTransactionType.OVERPAYMENT,
        negative_payment_amount=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.OVERPAYMENT_MISSING_NON_VPEI_RECORDS,
        payment_transaction_type=PaymentTransactionType.OVERPAYMENT,
        include_claim_details=False,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.EMPLOYER_REIMBURSEMENT_PAYMENT,
        payment_transaction_type=PaymentTransactionType.EMPLOYER_REIMBURSEMENT,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PRENOTE_WITH_EXISTING_EFT_ACCOUNT,
        existing_eft_account=True,
        prenoted=False,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.CLAIMANT_PRENOTED_NO_PAYMENT_RECEIVED, create_payment=False
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.CLAIM_NOT_ID_PROOFED,
        has_existing_claim=False,
        is_id_proofed=False,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
        existing_eft_account=False,
        prenoted=False,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
        payment_method=PaymentMethod.CHECK,
        fineos_extract_address_valid=False,
        pub_check_response=False,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
        fineos_extract_address_valid=False,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PAYMENT_EXTRACT_EMPLOYEE_MISSING_IN_DB,
        employee_in_payment_extract_missing_in_db=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.UNKNOWN_LEAVE_REQUEST_DECISION, leave_request_decision="Pending"
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.IN_REVIEW_LEAVE_REQUEST_DECISION,
        leave_request_decision="In Review",
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.IN_REVIEW_LEAVE_REQUEST_ADHOC_PAYMENTS_DECISION,
        leave_request_decision="In Review",
        is_adhoc_payment=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.REJECTED_LEAVE_REQUEST_DECISION, leave_request_decision="Denied"
    ),
    ScenarioDescriptor(scenario_name=ScenarioName.AUDIT_REJECTED, is_audit_rejected=True),
    ScenarioDescriptor(
        scenario_name=ScenarioName.AUDIT_REJECTED_WITH_NOTE,
        is_audit_rejected=True,
        audit_response_note=list(AUDIT_REJECT_NOTE_TO_WRITEBACK_TRANSACTION_STATUS.keys())[0],
    ),
    ScenarioDescriptor(scenario_name=ScenarioName.AUDIT_SKIPPED, is_audit_skipped=True),
    ScenarioDescriptor(
        scenario_name=ScenarioName.AUDIT_SKIPPED_WITH_NOTE,
        is_audit_skipped=True,
        audit_response_note=list(AUDIT_SKIPPED_NOTE_TO_WRITEBACK_TRANSACTION_STATUS.keys())[0],
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_ACH_PRENOTE_RETURN,
        existing_eft_account=False,
        prenoted=False,
        pub_ach_response_return=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
        existing_eft_account=False,
        prenoted=False,
        pub_ach_response_change_notification=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
        pub_ach_response_return=True,
        pub_ach_return_invalid_prenote_payment_id_format=True,
        existing_eft_account=False,
        prenoted=False,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
        pub_ach_response_return=True,
        pub_ach_return_prenote_payment_id_not_found=True,
        existing_eft_account=False,
        prenoted=False,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_ACH_FAMILY_RETURN, pub_ach_response_return=True
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
        pub_ach_response_change_notification=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
        pub_ach_response_return=True,
        pub_ach_return_invalid_payment_id_format=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
        pub_ach_response_return=True,
        pub_ach_return_payment_id_not_found=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_ACH_MEDICAL_RETURN,
        claim_type="Employee",
        pub_ach_response_return=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
        pub_ach_response_change_notification=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_ACH_MANUAL_REJECT, manual_pub_reject_response=True
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
        payment_method=PaymentMethod.CHECK,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
        payment_method=PaymentMethod.CHECK,
        pub_check_paid_response=False,
        pub_check_outstanding_response=True,
        pub_check_outstanding_response_status=PaidStatus.OUTSTANDING,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
        payment_method=PaymentMethod.CHECK,
        pub_check_paid_response=False,
        pub_check_outstanding_response=True,
        pub_check_outstanding_response_status=PaidStatus.FUTURE,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
        payment_method=PaymentMethod.CHECK,
        pub_check_paid_response=False,
        pub_check_outstanding_response=True,
        pub_check_outstanding_response_status=PaidStatus.VOID,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
        payment_method=PaymentMethod.CHECK,
        pub_check_paid_response=False,
        pub_check_outstanding_response=True,
        pub_check_outstanding_response_status=PaidStatus.STALE,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
        payment_method=PaymentMethod.CHECK,
        pub_check_paid_response=False,
        pub_check_outstanding_response=True,
        pub_check_outstanding_response_status=PaidStatus.STOP,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND,
        payment_method=PaymentMethod.CHECK,
        pub_check_return_invalid_check_number=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_CLAIM_MISSING_EMPLOYEE, claim_missing_employee=True
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.CLAIM_UNABLE_TO_SET_EMPLOYEE_FROM_EXTRACT,
        claim_missing_employee=True,
        claim_extract_employee_identifier_unknown=True,
    ),
    # ScenarioDescriptor(
    #     scenario_name=ScenarioName.EMPLOYER_REIMBURSEMENT_PAYMENT,
    #     payment_transaction_type=PaymentTransactionType.EMPLOYER_REIMBURSEMENT,
    #     payment_method=PaymentMethod.CHECK,
    #     fineos_extract_address_valid=True,
    # ),
    # ScenarioDescriptor(
    #     scenario_name=ScenarioName.EMPLOYER_REIMBURSEMENT_WITH_INVALID_ADDRESS,
    #     payment_transaction_type=PaymentTransactionType.EMPLOYER_REIMBURSEMENT,
    #     payment_method=PaymentMethod.CHECK,
    #     fineos_extract_address_valid=False,
    # ),
    # ScenarioDescriptor(
    #     scenario_name=ScenarioName.EMPLOYER_REIMBURSEMENT_WITH_STANDARD_PAYMENT,
    #     payment_transaction_type=PaymentTransactionType.STANDARD,
    #     is_employer_reimbursement_records_exists = True,
    #     payment_method=PaymentMethod.CHECK,
    #     fineos_extract_address_valid=True,
    # ),
    # ScenarioDescriptor(
    #     scenario_name=ScenarioName.STANDARD_PAYMENT_WITH_TW_AND_ER,
    #     payment_transaction_type=PaymentTransactionType.STANDARD,
    #     is_employer_reimbursement_records_exists = True,
    #     is_tax_withholding_records_exists=True,
    #     payment_method=PaymentMethod.CHECK,
    #     fineos_extract_address_valid=True,
    # ),
    # ScenarioDescriptor(
    #     scenario_name=ScenarioName.EMPLOYER_REIMBURSEMENT_WITH_STANDARD_PAYMENT_INVALID_ADDRESS,
    #     payment_transaction_type=PaymentTransactionType.STANDARD,
    #     is_employer_reimbursement_records_exists = True,
    #     fineos_extract_address_valid=False,
    #     payment_method=PaymentMethod.CHECK,
    # ),
    # ScenarioDescriptor(
    #     scenario_name=ScenarioName.EMPLOYER_REIMBURSEMENT_INVALID_ADDRESS_WITH_VALID_STANDARD_PAYMENT,
    #     payment_transaction_type=PaymentTransactionType.STANDARD,
    #     is_employer_reimbursement_records_exists=True,
    #     fineos_extract_address_valid=True,
    #     is_employer_reimbursement_fineos_extract_address_valid=False,
    #     payment_method=PaymentMethod.CHECK,
    # ),
    # ScenarioDescriptor(
    #     scenario_name=ScenarioName.EMPLOYER_REIMBURSEMENT_PAYMENT_AMOUNT_OVER_CAP,
    #     payment_transaction_type=PaymentTransactionType.EMPLOYER_REIMBURSEMENT,
    #     payment_method=PaymentMethod.CHECK,
    #     fineos_extract_address_valid=True,
    #     payment_over_cap=True,
    # ),
    # ScenarioDescriptor(
    #     scenario_name=ScenarioName.EMPLOYER_REIMBURSEMENT_PAYMENT_WITH_EFT,
    #     payment_transaction_type=PaymentTransactionType.EMPLOYER_REIMBURSEMENT,
    #     fineos_extract_address_valid=True,
    #     payment_method=PaymentMethod.ACH,
    # ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_TAX_WITHHOLDING,
        is_tax_withholding_records_exists=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.TAX_WITHHOLDING_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
        payment_method=PaymentMethod.CHECK,
        is_tax_withholding_records_exists=True,
        fineos_extract_address_valid=False,
        pub_check_response=False,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_TAX_WITHHOLDING_PAYMENT_METHOD_CHECK,
        is_tax_withholding_records_exists=True,
        payment_method=PaymentMethod.CHECK,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.TAX_WITHHOLDING_PRIMARY_PAYMENT_NOT_PRENOTED,
        is_tax_withholding_records_exists=True,
        existing_eft_account=False,
        prenoted=False,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.TAX_WITHHOLDING_MISSING_PRIMARY_PAYMENT,
        is_tax_withholding_record_without_primary_payment=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.TAX_WITHHOLDING_CANCELLATION_PAYMENT,
        is_tax_withholding_records_exists=True,
        payment_transaction_type=PaymentTransactionType.CANCELLATION,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_DOR_FINEOS_NAME_MISMATCH,
        dor_fineos_name_mismatch=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_DUA_ADDITIONAL_INCOME, dua_additional_income=True
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_DIA_ADDITIONAL_INCOME, dia_additional_income=True
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_MAX_LEAVE_DURATION_EXCEEDED,
        max_leave_duration_exceeded=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_PAYMENT_DATE_MISMATCH,
        payment_date_mismatch=True,
        is_adhoc_payment=False,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_PAYMENT_PREAPPROVED,
        has_past_payments=True,
        payment_method=PaymentMethod.CHECK,
    ),
]

SCENARIO_DESCRIPTORS_BY_NAME: Dict[ScenarioName, ScenarioDescriptor] = {
    s.scenario_name: s for s in SCENARIO_DESCRIPTORS
}

DELAYED_SCENARIO_DESCRIPTORS: List[ScenarioDescriptor] = [
    ScenarioDescriptor(
        scenario_name=ScenarioName.INVALID_ADDRESS_FIXED,
        payment_method=PaymentMethod.CHECK,
        invalid_address=True,
        invalid_address_fixed=True,
        has_additional_payment_in_period=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED,
        is_audit_rejected=True,
        is_audit_approved_delayed=True,
        has_additional_payment_in_period=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.AUDIT_SKIPPED_THEN_ACCEPTED,
        is_audit_skipped=True,
        is_audit_approved_delayed=True,
        has_additional_payment_in_period=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN_FIXED,
        payment_method=PaymentMethod.CHECK,
        fineos_extract_address_valid=False,
        fineos_extract_address_valid_after_fix=True,
        pub_check_response=False,
        has_additional_payment_in_period=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_TWO_PAYMENTS_UNDER_WEEKLY_CAP,
        payment_close_to_cap=False,
        has_additional_payment_in_period=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_TWO_ADHOC_PAYMENTS_OVER_CAP,
        payment_close_to_cap=True,
        has_additional_payment_in_period=True,
        is_adhoc_payment=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.SECOND_PAYMENT_FOR_PERIOD_OVER_CAP,
        payment_close_to_cap=True,
        has_additional_payment_in_period=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.TAX_WITHHOLDING_AUDIT_SKIPPED_THEN_ACCEPTED,
        is_audit_skipped=True,
        is_audit_approved_delayed=True,
        has_additional_payment_in_period=True,
        is_tax_withholding_records_exists=True,
    ),
]

DELAYED_SCENARIO_DESCRIPTORS_BY_NAME: Dict[ScenarioName, ScenarioDescriptor] = {
    s.scenario_name: s for s in DELAYED_SCENARIO_DESCRIPTORS
}


def get_scenario_by_name(scenario_name: ScenarioName) -> Optional[ScenarioDescriptor]:
    scenario_descriptor = SCENARIO_DESCRIPTORS_BY_NAME.get(scenario_name)
    if scenario_descriptor is None:
        scenario_descriptor = DELAYED_SCENARIO_DESCRIPTORS_BY_NAME.get(scenario_name)

    return scenario_descriptor
