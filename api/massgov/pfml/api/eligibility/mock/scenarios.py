from dataclasses import dataclass
from enum import Enum
from typing import List, Literal, Optional, Tuple

from massgov.pfml.util.datetime.quarter import Quarter


class EmployeeId(Enum):
    Al = "Al"
    Bo = "Bo"
    Ci = "Ci"
    Di = "Di"
    El = "El"
    Fi = "Fi"
    Gob = "Gob"
    Hu = "Hu"
    Ian = "Ian"
    Ka = "Ka"
    Li = "Li"
    Mo = "Mo"
    Nu = "Nu"


class EmployerId(Enum):
    E1 = "E1"
    E2 = "E2"
    E3 = "E3"
    E4 = "E4"
    E5 = "E5"
    E6 = "E6"
    E7 = "E7"
    E8 = "E8"
    E9 = "E9"
    E10 = "E10"
    E11 = "E11"
    E12 = "E12"
    E13 = "E13"


Q6Wages = str
Q5Wages = str
Q4Wages = str
Q3Wages = str
Q2Wages = str
Q1Wages = str
Q0Wages = str

Year = int
Month = int
Day = int
DateParts = Tuple[Year, Month, Day]

ClaimTypes = Literal["Family leave", "Medical leave", "Military leave"]

AbsenceStatuses = Literal[
    "Adjudication",
    "Approved",
    "Closed",
    "Completed",
    "Declined",
    "In Review",
    "Intake In Progress",
]


@dataclass
class MetricsDescriptor:
    effective_date: DateParts
    average_weekly_wage: str
    maximum_weekly_benefit_amount: str
    unemployment_minimum_earnings: str


@dataclass
class EmployerQuarterlyWagesDescriptor:
    employer: EmployeeId
    wages: Tuple[Q5Wages, Q4Wages, Q3Wages, Q2Wages, Q1Wages, Q0Wages]


@dataclass
class ClaimDescriptor:
    employer: EmployerId
    claim_type: ClaimTypes
    fineos_absence_status: AbsenceStatuses
    absence_period_start_date: DateParts
    absence_period_end_date: DateParts


@dataclass
class BenefitYearDescriptor:
    start_date: DateParts
    end_date: DateParts
    base_period_start_date: DateParts
    base_period_end_date: DateParts
    total_wages: str


@dataclass
class EligibiltyDescriptor:
    # Request
    employer: EmployerId
    leave_start_date: DateParts
    application_submitted_date: DateParts
    employment_status: str

    # Response
    financially_eligible: bool
    description: str
    total_wages: Optional[str]
    state_average_weekly_wage: Optional[str]
    unemployment_minimum: Optional[str]
    employer_average_weekly_wage: Optional[str]


@dataclass
class ScenarioDescriptor:
    description: str
    employee: EmployeeId
    Q0: Quarter
    employers: List[
        Tuple[EmployerId, Q6Wages, Q5Wages, Q4Wages, Q3Wages, Q2Wages, Q1Wages, Q0Wages]
    ]
    claims: List[ClaimDescriptor]
    benefit_years: List[BenefitYearDescriptor]
    eligibilty: List[EligibiltyDescriptor]


ScenarioDescriptor(
    "Wouldnt recalc benefit year",
    EmployeeId.Al,
    Q0=Quarter(2021, 1),
    employers=[
        (EmployerId.E1, "0", "0", "2000", "2000", "2000", "2000", "0"),
        (EmployerId.E2, "0", "0", "2000", "2000", "2000", "2000", "0"),
    ],
    claims=[
        ClaimDescriptor(
            EmployerId.E1,
            claim_type="Family leave",
            fineos_absence_status="Approved",
            absence_period_start_date=(2021, 1, 1),
            absence_period_end_date=(2021, 1, 1),
        )
    ],
    benefit_years=[
        BenefitYearDescriptor(
            start_date=(2021, 1, 1),
            end_date=(2021, 12, 31),
            base_period_start_date=(2021, 1, 1),
            base_period_end_date=(2021, 1, 2),
            total_wages="2000",
        )
    ],
    eligibilty=[
        EligibiltyDescriptor(
            EmployerId.E1,
            leave_start_date=(2021, 1, 1),
            application_submitted_date=(2021, 1, 1),
            employment_status="Employed",
            financially_eligible=False,
            description="",
            total_wages="123",
            state_average_weekly_wage="1234",
            unemployment_minimum="3434",
            employer_average_weekly_wage="232",
        )
    ],
)
