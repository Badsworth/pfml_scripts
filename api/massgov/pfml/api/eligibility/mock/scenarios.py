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
    EXISTING_BENEFIT_YEAR_KEEP_HIGHER_IAWW = "EXISTING_BENEFIT_YEAR_KEEP_HIGHER_IAWW"
    EXISTING_BENEFIT_YEAR_KEEP_LOWER_IAWW = "EXISTING_BENEFIT_YEAR_KEEP_LOWER_IAWW"
    NO_EXISTING_DATA = "NO_EXISTING_DATA"


@dataclass
class BenefitYearDescriptor:
    total_wages: str
    employer_IAWW: str


@dataclass
class EligibilityScenarioDescriptor:
    scenario_name: Optional[EligibilityScenarioName] = None

    last_x_quarters_wages: List[str] = field(
        default_factory=lambda: ["12000", "12000", "12000", "12000", "12000", "12000"]
    )
    last_x_quarters_wages_other_employer: Optional[List[str]] = None
    leave_start_date: date = date(2021, 6, 1)
    application_submitted_date: date = date(2021, 6, 1)
    employment_status: EligibilityEmploymentStatus = EligibilityEmploymentStatus.employed
    active_benefit_year: Optional[BenefitYearDescriptor] = None
    future_benefit_year: Optional[BenefitYearDescriptor] = None
    # This flag controls how the wage models are created. When False,
    # the scenario will skip the first quarter when processing the wages
    # array. See: scenario_data_generator.py
    current_quarter_has_data: bool = True


SCENARIO_DESCRIPTORS: List[EligibilityScenarioDescriptor] = [
    EligibilityScenarioDescriptor(scenario_name=EligibilityScenarioName.NO_EXISTING_BENEFIT_YEAR),
    EligibilityScenarioDescriptor(
        scenario_name=EligibilityScenarioName.NO_EXISTING_BENEFIT_YEAR_MULTIPLE_EMPLOYERS,
        last_x_quarters_wages_other_employer=["9000", "9000", "9000", "9000", "9000", "9000"],
    ),
    EligibilityScenarioDescriptor(
        scenario_name=EligibilityScenarioName.NO_EXISTING_BENEFIT_YEAR_WAGES_UNDER_MIN,
        last_x_quarters_wages=["1000", "1000", "1000", "1000", "12000", "12000"],
    ),
    EligibilityScenarioDescriptor(
        scenario_name=EligibilityScenarioName.EXISTING_BENEFIT_YEAR_WAGES_UNDER_MIN,
        last_x_quarters_wages=["1000", "1000", "1000", "1000", "12000", "12000"],
        active_benefit_year=BenefitYearDescriptor(total_wages="24000", employer_IAWW="1000"),
    ),
    EligibilityScenarioDescriptor(
        scenario_name=EligibilityScenarioName.EXISTING_BENEFIT_YEAR_KEEP_HIGHER_IAWW,
        active_benefit_year=BenefitYearDescriptor(total_wages="30000", employer_IAWW="1250"),
    ),
    EligibilityScenarioDescriptor(
        scenario_name=EligibilityScenarioName.EXISTING_BENEFIT_YEAR_KEEP_LOWER_IAWW,
        last_x_quarters_wages=["15000", "15000", "12000", "12000", "12000", "12000"],
        active_benefit_year=BenefitYearDescriptor(total_wages="48000", employer_IAWW="923.08"),
    ),
    EligibilityScenarioDescriptor(
        scenario_name=EligibilityScenarioName.NO_EXISTING_DATA,
        last_x_quarters_wages=[],
        application_submitted_date=date(2021, 1, 5),
        leave_start_date=date(2021, 1, 5),
    ),
]

SCENARIO_DESCRIPTORS_BY_NAME: Dict[EligibilityScenarioName, EligibilityScenarioDescriptor] = {
    s.scenario_name: s for s in SCENARIO_DESCRIPTORS if s.scenario_name
}


def get_eligibility_scenario_by_name(
    scenario_name: EligibilityScenarioName,
) -> EligibilityScenarioDescriptor:
    scenario = SCENARIO_DESCRIPTORS_BY_NAME.get(scenario_name)
    if scenario:
        return scenario
    else:
        raise ValueError(f"Scenario with name: {scenario_name} does not exist")
