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

    # Prenote
    NO_PRIOR_EFT_ACCOUNT_ON_EMPLOYEE = "NO_PRIOR_EFT_ACCOUNT_ON_EMPLOYEE"
    EFT_ACCOUNT_NOT_PRENOTED = "EFT_ACCOUNT_NOT_PRENOTED"

    # Address Verification
    CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN = (
        "CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN"
    )
    CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND = "CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND"

    # Automated Validation Rules (TODO add more validation issue scenarios)
    REJECTED_LEAVE_REQUEST_DECISION = "REJECTED_LEAVE_REQUEST_DECISION"
    PAYMENT_EXTRACT_EMPLOYEE_MISSING_IN_DB = "PAYMENT_EXTRACT_EMPLOYEE_MISSING_IN_DB"

    # TODO CLAIMANT_EXTRACT_EMPLOYEE_MISSING_IN_DB - PUB-165
    # TODO CLAIM_DOES_NOT_EXIST - PUB-165

    # Audit
    AUDIT_REJECTED = "AUDIT_REJECTED"

    # Returns
    PUB_ACH_PRENOTE_RETURN = "PUB_ACH_PRENOTE_RETURN"
    PUB_ACH_PRENOTE_NOTIFICATION = "PUB_ACH_PRENOTE_NOTIFICATION"

    PUB_ACH_FAMILY_RETURN = "PUB_ACH_FAMILY_RETURN"
    PUB_ACH_FAMILY_NOTIFICATION = "PUB_ACH_FAMILY_NOTIFICATION"

    PUB_ACH_FAMILY_RETURN_INVALID_ID = "PUB_ACH_FAMILY_RETURN_INVALID_ID"
    PUB_ACH_FAMILY_RETURN_INVALID_EFT_PRENOTE_ID = "PUB_ACH_FAMILY_RETURN_INVALID_EFT_PRENOTE_ID"
    PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID = "PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID"

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

    payment_method: LkPaymentMethod = PaymentMethod.ACH
    payment_transaction_type: LkPaymentTransactionType = PaymentTransactionType.STANDARD

    account_type: LkBankAccountType = BankAccountType.CHECKING

    no_prior_eft_account: bool = False
    prenoted: bool = True  # TODO add all prenote states

    # prior_verified_address: bool = False TODO add when available
    fineos_extract_address_valid: bool = True
    fineos_extract_address_multiple_matches: bool = False

    leave_request_decision: str = "Approved"
    is_audit_approved: bool = True

    negative_payment_amount: bool = False

    include_non_vpei_records: bool = True

    # ACH Returns
    # https://lwd.atlassian.net/wiki/spaces/API/pages/1333364105/PUB+ACH+Return+File+Format

    pub_ach_response_return: bool = False
    pub_ach_return_reason_code: str = "RO1"
    pub_ach_return_invalid_id: bool = False
    pub_ach_return_invalid_payment_id: bool = False

    pub_ach_return_invalid_check_number: bool = False
    pub_ach_return_invalid_eft_prenote_id: bool = False

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
        scenario_name=ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
        pub_ach_response_return=True,
        pub_ach_return_invalid_id=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_EFT_PRENOTE_ID,
        pub_ach_response_return=True,
        pub_ach_return_invalid_eft_prenote_id=True,
        prenoted=False,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
        pub_ach_response_return=True,
        pub_ach_return_invalid_payment_id=True,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND,
        pub_ach_response_return=True,
        payment_method=PaymentMethod.CHECK,
        pub_ach_return_invalid_check_number=True,
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


def get_scenario_by_name(scenario_name: ScenarioName) -> Optional[ScenarioDescriptor]:
    return SCENARIO_DESCRIPTORS_BY_NAME[scenario_name]
