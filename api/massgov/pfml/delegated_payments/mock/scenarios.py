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
from massgov.pfml.delegated_payments.delegated_payments_nacha import NachaBatchType
from massgov.pfml.delegated_payments.util.ach.nacha import Constants


class ScenarioName(Enum):
    # Happy path scenarios
    HAPPY_PATH_FAMILY_ACH_PRENOTED = "HAPPY_PATH_FAMILY_ACH_PRENOTED"
    HAPPY_PATH_FAMILY_CHECK_PRENOTED = "HAPPY_PATH_FAMILY_CHECK_PRENOTED"
    HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN = (
        "HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN"
    )
    HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN = (
        "HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN"
    )
    # TODO medical leave

    # Non-Standard Payments
    ZERO_DOLLAR_PAYMENT = "ZERO_DOLLAR_PAYMENT"
    CANCELLATION_PAYMENT = "CANCELLATION_PAYMENT"
    OVERPAYMENT_PAYMENT_POSITIVE = "OVERPAYMENT_PAYMENT_POSITIVE"
    OVERPAYMENT_PAYMENT_NEGATIVE = "OVERPAYMENT_PAYMENT_NEGATIVE"
    EMPLOYER_REIMBURSEMENT_PAYMENT = "EMPLOYER_REIMBURSEMENT_PAYMENT"

    # Prenote
    NO_PRIOR_EFT_ACCOUNT_ON_EMPLOYEE = "NO_PRIOR_EFT_ACCOUNT_ON_EMPLOYEE"
    EFT_ACCOUNT_NOT_PRENOTED = "EFT_ACCOUNT_NOT_PRENOTED"

    # Address Verification
    CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN = (
        "CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN"
    )

    # Automated Validation Rules (TODO add more validation issue scenarios)
    PAYMENT_EXTRACT_EMPLOYEE_MISSING_IN_DB = "PAYMENT_EXTRACT_EMPLOYEE_MISSING_IN_DB"
    # TODO CLAIMANT_EXTRACT_EMPLOYEE_MISSING_IN_DB
    # TODO CLAIM_DOES_NOT_EXIST
    PENDING_LEAVE_REQUEST_DECISION = "PENDING_LEAVE_REQUEST_DECISION"

    # Audit
    AUDIT_REJECTED = "AUDIT_REJECTED"

    # TODO PEI writeback error
    # TODO positive pay check outbound


@dataclass
class ScenarioDescriptor:
    scenario_name: ScenarioName

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

    # eft_returns_should_skip: bool = False
    # eft_returns_should_error: bool = False
    # eft_returns_no_response: bool = False
    # eft_returns_return_type: str = Constants.addendum_return_types[0]
    # eft_returns_reason_code: str = Constants.addendum_return_reason_codes[0]
    # eft_return_batch_type: NachaBatchType = NachaBatchType.MEDICAL_LEAVE

    # ACH Returns
    # https://lwd.atlassian.net/wiki/spaces/API/pages/1333364105/PUB+ACH+Return+File+Format

    pub_ach_response_return: bool = False
    pub_ach_return_reason_code: str = "RO1"

    pub_ach_response_change_notification: bool = False
    pub_ach_notification_reason_code: str = "CO1"


SCENARIO_DESCRIPTORS: List[ScenarioDescriptor] = [
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
        scenario_name=ScenarioName.PENDING_LEAVE_REQUEST_DECISION, leave_request_decision="Pending"
    ),
    ScenarioDescriptor(scenario_name=ScenarioName.AUDIT_REJECTED, is_audit_approved=False),
]

SCENARIO_DESCRIPTORS_BY_NAME: Dict[ScenarioName, ScenarioDescriptor] = {
    s.scenario_name: s for s in SCENARIO_DESCRIPTORS
}


def get_scenario_by_name(scenario_name: ScenarioName) -> Optional[ScenarioDescriptor]:
    return SCENARIO_DESCRIPTORS_BY_NAME[scenario_name]
