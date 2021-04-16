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


class ScenarioName(Enum):
    # Happy path scenarios
    HAPPY_PATH_FAMILY_ACH_PRENOTED = "HAPPY_PATH_FAMILY_ACH_PRENOTED"
    HAPPY_PATH_FAMILY_CHECK_PRENOTED = "HAPPY_PATH_FAMILY_CHECK_PRENOTED"
    HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN = (
        "HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN"
    )

    # Non-Standard Payments
    ZERO_DOLLAR_PAYMENT = "ZERO_DOLLAR_PAYMENT"
    CANCELLATION_PAYMENT = "CANCELLATION_PAYMENT"
    OVERPAYMENT_PAYMENT = "OVERPAYMENT_PAYMENT"
    EMPLOYER_REIMBURSEMENT_PAYMENT = "EMPLOYER_REIMBURSEMENT_PAYMENT"

    # Prenote
    NO_PRIOR_EFT_ACCOUNT_ON_EMPLOYEE = "NO_PRIOR_EFT_ACCOUNT_ON_EMPLOYEE"
    EFT_ACCOUNT_NOT_PRENOTED = "EFT_ACCOUNT_NOT_PRENOTED"

    # Address Verification
    CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN = (
        "CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN"
    )

    # Automated Validation Rules (TODO add more validation issue scenarios)
    PENDING_LEAVE_REQUEST_DECISION = "PENDING_LEAVE_REQUEST_DECISION"


@dataclass
class ScenarioDescriptor:
    scenario_name: ScenarioName

    claim_type: LkClaimType = ClaimType.FAMILY_LEAVE

    payment_method: LkPaymentMethod = PaymentMethod.ACH
    payment_transaction_type: LkPaymentTransactionType = PaymentTransactionType.STANDARD

    account_type: LkBankAccountType = BankAccountType.CHECKING

    no_prior_eft_account: bool = False
    prenoted: bool = True

    prior_verified_address: bool = False
    fineos_extract_address_valid: bool = True

    leave_request_decision: str = "Approved"

    should_skip: bool = False
    should_error: bool = False
    no_response: bool = False
    return_type: str = ""
    reason_code: str = ""


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
        scenario_name=ScenarioName.OVERPAYMENT_PAYMENT,
        payment_transaction_type=PaymentTransactionType.OVERPAYMENT,
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
        scenario_name=ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
        fineos_extract_address_valid=False,
    ),
    ScenarioDescriptor(
        scenario_name=ScenarioName.PENDING_LEAVE_REQUEST_DECISION, leave_request_decision="Pending"
    ),
]

SCENARIO_DESCRIPTORS_BY_NAME: Dict[ScenarioName, ScenarioDescriptor] = {
    s.scenario_name: s for s in SCENARIO_DESCRIPTORS
}


def get_scenario_by_name(scenario_name: ScenarioName) -> Optional[ScenarioDescriptor]:
    return SCENARIO_DESCRIPTORS_BY_NAME[scenario_name]
