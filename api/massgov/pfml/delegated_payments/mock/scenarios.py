from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from massgov.pfml.db.models.employees import (
    BankAccountType,
    ClaimType,
    LkBankAccountType,
    LkClaimType,
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

    # Non-Standard Payments
    ZERO_DOLLAR_PAYMENT = "ZERO_DOLLAR_PAYMENT"
    CANCELLATION_PAYMENT = "CANCELLATION_PAYMENT"
    OVERPAYMENT_PAYMENT_POSITIVE = "OVERPAYMENT_PAYMENT_POSITIVE"
    OVERPAYMENT_PAYMENT_NEGATIVE = "OVERPAYMENT_PAYMENT_NEGATIVE"
    OVERPAYMENT_MISSING_NON_VPEI_RECORDS = "OVERPAYMENT_MISSING_NON_VPEI_RECORDS"
    EMPLOYER_REIMBURSEMENT_PAYMENT = "EMPLOYER_REIMBURSEMENT_PAYMENT"

    # Payment Extract Validation
    CLAIM_NOT_ID_PROOFED = "CLAIM_NOT_ID_PROOFED"

    # Prenote
    NO_PRIOR_EFT_ACCOUNT_ON_EMPLOYEE = "NO_PRIOR_EFT_ACCOUNT_ON_EMPLOYEE"

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

    # TODO CLAIMANT_EXTRACT_EMPLOYEE_MISSING_IN_DB - PUB-165
    # TODO CLAIM_DOES_NOT_EXIST - PUB-165
    # TODO CLAIM_EXISTS_BUT_NOT_ID_PROOFED = PUB-165

    # Audit
    AUDIT_REJECTED = "AUDIT_REJECTED"
    AUDIT_REJECTED_THEN_ACCEPTED = "AUDIT_REJECTED_THEN_ACCEPTED"

    # Returns
    PUB_ACH_PRENOTE_RETURN = "PUB_ACH_PRENOTE_RETURN"
    PUB_ACH_PRENOTE_NOTIFICATION = "PUB_ACH_PRENOTE_NOTIFICATION"

    PUB_ACH_FAMILY_RETURN = "PUB_ACH_FAMILY_RETURN"
    PUB_ACH_FAMILY_NOTIFICATION = "PUB_ACH_FAMILY_NOTIFICATION"

    PUB_ACH_MEDICAL_RETURN = "PUB_ACH_MEDICAL_RETURN"
    PUB_ACH_MEDICAL_NOTIFICATION = "PUB_ACH_MEDICAL_NOTIFICATION"

    PUB_CHECK_FAMILY_RETURN_VOID = "PUB_CHECK_FAMILY_RETURN_VOID"
    PUB_CHECK_FAMILY_RETURN_STALE = "PUB_CHECK_FAMILY_RETURN_STALE"
    PUB_CHECK_FAMILY_RETURN_STOP = "PUB_CHECK_FAMILY_RETURN_STOP"


@dataclass
class ScenarioDescriptor:
    scenario_name: ScenarioName

    # general payment options
    employee_missing_in_db: bool = False

    claim_type: LkClaimType = ClaimType.FAMILY_LEAVE
    is_id_proofed: bool = True  # TODO - when claimant extract is file generation is ready, make this set the ID proofing field

    payment_method: LkPaymentMethod = PaymentMethod.ACH
    payment_transaction_type: LkPaymentTransactionType = PaymentTransactionType.STANDARD

    account_type: LkBankAccountType = BankAccountType.CHECKING

    no_prior_eft_account: bool = False
    prenoted: bool = True  # TODO add all prenote states

    invalid_address: bool = False
    invalid_address_fixed: bool = False

    # prior_verified_address: bool = False TODO add when available
    fineos_extract_address_valid: bool = True
    fineos_extract_address_valid_after_fix: bool = False
    fineos_extract_address_multiple_matches: bool = False

    leave_request_decision: str = "Approved"

    is_audit_approved: bool = True
    is_audit_approved_delayed: bool = False

    negative_payment_amount: bool = False

    include_non_vpei_records: bool = True

    # ACH Returns
    # https://lwd.atlassian.net/wiki/spaces/API/pages/1333364105/PUB+ACH+Return+File+Format

    pub_ach_response_return: bool = False
    pub_ach_return_reason_code: str = "RO1"

    pub_ach_response_change_notification: bool = False
    pub_ach_notification_reason_code: str = "CO1"

    # Check returns
    pub_check_response: bool = True
    pub_check_paid_response: bool = True
    pub_check_outstanding_response: bool = False
    pub_check_outstanding_response_status: PaidStatus = PaidStatus.OUTSTANDING


SCENARIO_DESCRIPTORS: List[ScenarioDescriptor] = [
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
        claim_type=ClaimType.MEDICAL_LEAVE,
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
        scenario_name=ScenarioName.NO_PRIOR_EFT_ACCOUNT_ON_EMPLOYEE,
        no_prior_eft_account=True,
        prenoted=False,
    ),
    ScenarioDescriptor(scenario_name=ScenarioName.CLAIM_NOT_ID_PROOFED, is_id_proofed=False),
    ScenarioDescriptor(scenario_name=ScenarioName.EFT_ACCOUNT_NOT_PRENOTED, prenoted=False),
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
        employee_missing_in_db=True,
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
        prenoted=False,
        pub_ach_response_return=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
        prenoted=False,
        pub_ach_response_change_notification=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_ACH_FAMILY_RETURN, pub_ach_response_return=True
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
        pub_ach_response_change_notification=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_ACH_MEDICAL_RETURN,
        claim_type=ClaimType.MEDICAL_LEAVE,
        pub_ach_response_return=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
        claim_type=ClaimType.MEDICAL_LEAVE,
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
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED,
        is_audit_approved=False,
        is_audit_approved_delayed=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN_FIXED,
        payment_method=PaymentMethod.CHECK,
        fineos_extract_address_valid=False,
        fineos_extract_address_valid_after_fix=True,
        pub_check_response=False,
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
