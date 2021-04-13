from dataclasses import dataclass
from typing import List

import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    Claim,
    Employee,
    Employer,
    LkAbsenceStatus,
    LkClaimType,
    TaxIdentifier,
)
from massgov.pfml.db.models.factories import ClaimFactory, EmployeeFactory, EmployerFactory
from massgov.pfml.delegated_payments.mock.scenarios import (
    ScenarioDescriptor,
    ScenarioName,
    get_scenario_by_name,
)

logger = logging.get_logger(__name__)


# == Data structures ==


@dataclass
class ScenarioNameWithCount:
    scenario_name: ScenarioName
    count: int


@dataclass
class ScenarioData:
    scenario_descriptor: ScenarioDescriptor
    employer: Employer
    employee: Employee
    claims: List[Claim]


@dataclass
class ScenarioDataConfig:
    scenarios_with_count: List[ScenarioNameWithCount]
    ssn_id_base: int = 100000000
    fein_id_base: int = 250000000


# == Helpers ==


def create_employer(fein: str, fineos_employer_id: str) -> Employer:
    return EmployerFactory.create(employer_fein=fein, fineos_employer_id=fineos_employer_id)


def create_employee(ssn: str, fineos_customer_number: str) -> Employee:
    return EmployeeFactory.create(
        tax_identifier=TaxIdentifier(tax_identifier=ssn),
        fineos_customer_number=fineos_customer_number,
    )


def create_claim(
    employer: Employer,
    employee: Employee,
    claim_type: LkClaimType,
    absence_status: LkAbsenceStatus,
    fineos_absence_id: str,
) -> Claim:
    return ClaimFactory.create(
        employer=employer,
        employee=employee,
        claim_type_id=claim_type.claim_type_id,
        fineos_absence_status_id=absence_status.absence_status_id,
        fineos_absence_id=fineos_absence_id,
    )


# == Generators ==


def generate_scenario_data_in_db(
    scenario_descriptor: ScenarioDescriptor,
    ssn: str,
    fein: str,
    fineos_employer_id: str,
    fineos_notification_id: str,
    fineos_customer_number: str,
) -> ScenarioData:

    employer = create_employer(fein, fineos_employer_id)

    employee = create_employee(ssn, fineos_customer_number)

    # address

    claims: List[Claim] = []

    for c in range(scenario_descriptor.claims_count):
        absence_case_index = c + 1
        absence_case_id = (
            f"{fineos_notification_id}-ABS-{str(absence_case_index)}"  # maximum length of 19
        )

        claim = create_claim(
            employer=employer,
            employee=employee,
            claim_type=scenario_descriptor.claim_type,
            fineos_absence_id=absence_case_id,
            absence_status=AbsenceStatus.APPROVED,
        )

        claims.append(claim)

    return ScenarioData(
        scenario_descriptor=scenario_descriptor, employer=employer, employee=employee, claims=claims
    )


def generate_scenario_dataset(config: ScenarioDataConfig) -> List[ScenarioData]:
    try:
        scenario_dataset: List[ScenarioData] = []

        # provided unique keys, sequences etc
        ssn = config.ssn_id_base
        fein = config.fein_id_base

        for scenario_with_count in config.scenarios_with_count:
            scenario_name = scenario_with_count.scenario_name
            scenario_count = scenario_with_count.count

            scenario_descriptor = get_scenario_by_name(scenario_name)

            if scenario_descriptor is None:
                raise Exception(f"Could not find scenario descriptor by name: {scenario_name}")

            for _ in range(scenario_count):
                ssn_part_str = str(ssn)[2:]
                fein_part_str = str(fein)[2:]

                fineos_employer_id = fein_part_str.rjust(9, "3")
                fineos_notification_id = f"NTN-{ssn_part_str}"
                fineos_customer_number = ssn_part_str.rjust(9, "5")

                scenario_data = generate_scenario_data_in_db(
                    scenario_descriptor,
                    ssn=str(ssn),
                    fein=str(fein),
                    fineos_employer_id=fineos_employer_id,
                    fineos_notification_id=fineos_notification_id,
                    fineos_customer_number=fineos_customer_number,
                )

                scenario_dataset.append(scenario_data)

                # increment sequences
                ssn += 1
                fein += 1

        return scenario_dataset

    except Exception as e:
        logger.exception("Error generating scenario data set")
        raise e
