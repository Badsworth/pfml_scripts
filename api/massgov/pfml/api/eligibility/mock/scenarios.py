from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Dict, List, Optional

from massgov.pfml.api.models.applications.common import EligibilityEmploymentStatus


class EligibilityScenarioName(Enum):
    NO_EXISTING_BENEFIT_YEAR = "NO_EXISTING_BENEFIT_YEAR"
    NO_EXISTING_BENEFIT_YEAR_MULTIPLE_EMPLOYERS = "NO_EXISTING_BENEFIT_YEAR_MULTIPLE_EMPLOYERS"
    NO_EXISTING_BENEFIT_YEAR_WAGES_UNDER_MIN = "NO_EXISTING_BENEFIT_YEAR_WAGES_UNDER_MIN"
    EXISTING_BENEFIT_YEAR_WAGES_UNDER_MIN = "EXISTING_BENEFIT_YEAR_WAGES_UNDER_MIN"
    EXISTING_BENEFIT_YEAR_CHANGES_IAWW = "EXISTING_BENEFIT_YEAR_CHANGES_IAWW "


@dataclass
class BenefitYearDescriptor:
    total_wages: str
    employer_IAWW: str


@dataclass
class EligibilityScenarioDescriptor:
    scenario_name: Optional[EligibilityScenarioName] = None

    last_six_quarters_wages: List[str] = field(
        default_factory=lambda: ["12000", "12000", "12000", "12000", "12000", "12000"]
    )
    last_six_quarters_wages_other_employer: Optional[List[str]] = None
    leave_start_date: date = date(2021, 6, 1)
    application_submitted_date: date = date(2021, 6, 1)
    employment_status: EligibilityEmploymentStatus = EligibilityEmploymentStatus.employed
    active_benefit_year: Optional[BenefitYearDescriptor] = None
    future_benefit_year: Optional[BenefitYearDescriptor] = None


SCENARIO_DESCRIPTORS: List[EligibilityScenarioDescriptor] = [
    EligibilityScenarioDescriptor(scenario_name=EligibilityScenarioName.NO_EXISTING_BENEFIT_YEAR,),
    EligibilityScenarioDescriptor(
        scenario_name=EligibilityScenarioName.NO_EXISTING_BENEFIT_YEAR_MULTIPLE_EMPLOYERS,
        last_six_quarters_wages_other_employer=["9000", "9000", "9000", "9000", "9000", "9000"],
    ),
    EligibilityScenarioDescriptor(
        scenario_name=EligibilityScenarioName.NO_EXISTING_BENEFIT_YEAR_WAGES_UNDER_MIN,
        last_six_quarters_wages=["1000", "1000", "1000", "1000", "12000", "12000"],
    ),
    EligibilityScenarioDescriptor(
        scenario_name=EligibilityScenarioName.EXISTING_BENEFIT_YEAR_WAGES_UNDER_MIN,
        last_six_quarters_wages=["1000", "1000", "1000", "1000", "12000", "12000"],
        active_benefit_year=BenefitYearDescriptor(total_wages="24000", employer_IAWW="1000"),
    ),
    EligibilityScenarioDescriptor(
        scenario_name=EligibilityScenarioName.EXISTING_BENEFIT_YEAR_CHANGES_IAWW,
        active_benefit_year=BenefitYearDescriptor(total_wages="30000", employer_IAWW="1250"),
    ),
]

SCENARIO_DESCRIPTORS_BY_NAME: Dict[EligibilityScenarioName, EligibilityScenarioDescriptor] = {
    s.scenario_name: s for s in SCENARIO_DESCRIPTORS if s.scenario_name
}


def get_eligibility_scenario_by_name(
    scenario_name: EligibilityScenarioName,
) -> Optional[EligibilityScenarioDescriptor]:
    return SCENARIO_DESCRIPTORS_BY_NAME.get(scenario_name)
