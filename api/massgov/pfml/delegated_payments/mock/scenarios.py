from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from massgov.pfml.db.models.employees import (
    BankAccountType,
    ClaimType,
    LkBankAccountType,
    LkClaimType,
    LkPaymentMethod,
    PaymentMethod,
)


class ScenarioName(Enum):
    # Happy path scenarios
    HAPPY_PATH_FAMILY_LEAVE = "HAPPY_PATH_FAMILY_LEAVE"
    HAPPY_PATH_MEDICAL_LEAVE = "HAPPY_PATH_MEDICAL_LEAVE"


@dataclass
class ScenarioDescriptor:
    scenario_name: ScenarioName

    # general payment options
    claim_type: LkClaimType = ClaimType.FAMILY_LEAVE
    payment_method: Optional[LkPaymentMethod] = PaymentMethod.ACH
    account_type: Optional[LkBankAccountType] = BankAccountType.CHECKING

    claims_count: int = 1


SCENARIO_DESCRIPTORS: List[ScenarioDescriptor] = [
    ScenarioDescriptor(scenario_name=ScenarioName.HAPPY_PATH_FAMILY_LEAVE),
    ScenarioDescriptor(
        scenario_name=ScenarioName.HAPPY_PATH_MEDICAL_LEAVE, claim_type=ClaimType.MEDICAL_LEAVE
    ),
]

SCENARIO_DESCRIPTORS_BY_NAME: Dict[ScenarioName, ScenarioDescriptor] = {
    s.scenario_name: s for s in SCENARIO_DESCRIPTORS
}


def get_scenario_by_name(scenario_name: ScenarioName) -> Optional[ScenarioDescriptor]:
    return SCENARIO_DESCRIPTORS_BY_NAME[scenario_name]
