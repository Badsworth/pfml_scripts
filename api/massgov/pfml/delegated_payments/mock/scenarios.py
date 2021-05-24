from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from massgov.pfml.db.models.employees import (
    BankAccountType,
    LkBankAccountType,
    LkPaymentMethod,
    LkPaymentTransactionType,
    PaymentMethod,
    PaymentTransactionType,
)
from massgov.pfml.delegated_payments.pub.check_return import PaidStatus


class ScenarioName(Enum):
    # Happy path scenarios
    HAPPY_PATH_MEDICAL_ACH_PRENOTED = "HAPPY_PATH_MEDICAL_ACH_PRENOTED"
    HAPPY_PATH_FAMILY_ACH_PRENOTED = "HAPPY_PATH_FAMILY_ACH_PRENOTED"
    HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN = (
        "HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN"
    )
    HAPPY_PENDING_LEAVE_REQUEST_DECISION = "HAPPY_PENDING_LEAVE_REQUEST_DECISION"
    HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION = "HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION"

    HAPPY_PATH_FAMILY_CHECK_PRENOTED = "HAPPY_PATH_FAMILY_CHECK_PRENOTED"
    HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN = (
        "HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN"
    )
    HAPPY_PATH_CHECK_FAMILY_RETURN_PAID = "PUB_CHECK_FAMILY_RETURN_PAID"
    HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING = "PUB_CHECK_FAMILY_RETURN_OUTSTANDING"
    HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE = "PUB_CHECK_FAMILY_RETURN_FUTURE"

    HAPPY_PATH_TWO_PAYMENTS_UNDER_WEEKLY_CAP = "HAPPY_PATH_TWO_PAYMENTS_UNDER_WEEKLY_CAP"

    # Non-Standard Payments
    ZERO_DOLLAR_PAYMENT = "ZERO_DOLLAR_PAYMENT"
    CANCELLATION_PAYMENT = "CANCELLATION_PAYMENT"
    OVERPAYMENT_PAYMENT_POSITIVE = "OVERPAYMENT_PAYMENT_POSITIVE"
    OVERPAYMENT_PAYMENT_NEGATIVE = "OVERPAYMENT_PAYMENT_NEGATIVE"
    OVERPAYMENT_MISSING_NON_VPEI_RECORDS = "OVERPAYMENT_MISSING_NON_VPEI_RECORDS"
    EMPLOYER_REIMBURSEMENT_PAYMENT = "EMPLOYER_REIMBURSEMENT_PAYMENT"

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
    AUDIT_REJECTED_THEN_ACCEPTED = "AUDIT_REJECTED_THEN_ACCEPTED"

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

    PUB_CHECK_FAMILY_RETURN_VOID = "PUB_CHECK_FAMILY_RETURN_VOID"
    PUB_CHECK_FAMILY_RETURN_STALE = "PUB_CHECK_FAMILY_RETURN_STALE"
    PUB_CHECK_FAMILY_RETURN_STOP = "PUB_CHECK_FAMILY_RETURN_STOP"

    PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND = (
        "PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND"
    )


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
    fineos_extract_address_multiple_matches: bool = False

    leave_request_decision: str = "Approved"

    is_audit_approved: bool = True
    is_audit_approved_delayed: bool = False

    negative_payment_amount: bool = False
    payment_close_to_cap: bool = False

    include_non_vpei_records: bool = True

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


SCENARIO_DESCRIPTORS: List[ScenarioDescriptor] = [
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED, claim_type="Employee",
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
        include_non_vpei_records=False,
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
        scenario_name=ScenarioName.CLAIMANT_PRENOTED_NO_PAYMENT_RECEIVED, create_payment=False,
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
        scenario_name=ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
        payment_method=PaymentMethod.CHECK,
        fineos_extract_address_valid=False,
        fineos_extract_address_multiple_matches=True,
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
        scenario_name=ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
        leave_request_decision="Pending",
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
        leave_request_decision="In Review",
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.REJECTED_LEAVE_REQUEST_DECISION,
        leave_request_decision="Rejected",
    ),
    ScenarioDescriptor(scenario_name=ScenarioName.AUDIT_REJECTED, is_audit_approved=False),
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
        claim_type="Employee",
        pub_ach_response_change_notification=True,
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
        scenario_name=ScenarioName.HAPPY_PATH_CLAIM_MISSING_EMPLOYEE, claim_missing_employee=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.CLAIM_UNABLE_TO_SET_EMPLOYEE_FROM_EXTRACT,
        claim_missing_employee=True,
        claim_extract_employee_identifier_unknown=True,
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
        is_audit_approved=False,
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
        scenario_name=ScenarioName.SECOND_PAYMENT_FOR_PERIOD_OVER_CAP,
        payment_close_to_cap=True,
        has_additional_payment_in_period=True,
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
