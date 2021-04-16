import uuid
from dataclasses import dataclass
from typing import List, Optional

import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    Claim,
    Employee,
    Employer,
    GeoState,
    LkAbsenceStatus,
    LkClaimType,
    Payment,
    PaymentMethod,
    PrenoteState,
    TaxIdentifier,
)
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployeePubEftPairFactory,
    EmployerFactory,
    PubEftFactory,
)
from massgov.pfml.delegated_payments.mock.scenarios import (
    ScenarioDescriptor,
    ScenarioName,
    get_scenario_by_name,
)
from massgov.pfml.experian.physical_address.client.mock import MockClient
from massgov.pfml.experian.physical_address.client.models import Confidence

logger = logging.get_logger(__name__)


# == Constants ==

VALID_ADDRESSES = [
    {"line_1": "20 South Ave", "line_2": "", "city": "Burlington", "state": "MA", "zip": "01803",}
]

INVALID_ADDRESSES = [
    {"line_1": "123 Main St", "line_2": "", "city": "Burlington", "state": "MA", "zip": "01803",}
]


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
    claim: Claim

    payment_c_value: Optional[str] = None
    payment_i_value: Optional[str] = None

    payment: Optional[Payment] = None


@dataclass
class ScenarioDataConfig:
    scenarios_with_count: List[ScenarioNameWithCount]
    ssn_id_base: int = 100000000
    fein_id_base: int = 250000000


# == Common Utils ==


def get_mock_address_client() -> MockClient:
    client = MockClient(fallback_confidence=Confidence.NO_MATCHES)

    for mock_address in VALID_ADDRESSES:
        state = GeoState.description_to_db_instance.get(mock_address["state"], GeoState.MA)

        address = AddressFactory.build(
            address_line_one=mock_address["line_1"],
            address_line_two=mock_address["line_2"],
            city=mock_address["city"],
            geo_state=state,
            zip_code=mock_address["zip"],
        )
        client.add_mock_address_response(address, Confidence.VERIFIED_MATCH)

    return client


# == Helpers ==


def create_employer(fein: str, fineos_employer_id: str) -> Employer:
    return EmployerFactory.create(
        employer_id=uuid.uuid4(), employer_fein=fein, fineos_employer_id=fineos_employer_id
    )


def create_employee(ssn: str, fineos_customer_number: str) -> Employee:
    return EmployeeFactory.create(
        employee_id=uuid.uuid4(),
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

    add_eft = (
        scenario_descriptor.payment_method == PaymentMethod.ACH
        and not scenario_descriptor.no_prior_eft_account
    )
    if add_eft:
        prenote_state = (
            PrenoteState.APPROVED if scenario_descriptor.prenoted else PrenoteState.PENDING_PRE_PUB
        )
        pub_eft = PubEftFactory.create(
            pub_eft_id=uuid.uuid4(),
            routing_nbr=ssn,
            account_nbr=ssn,
            bank_account_type_id=scenario_descriptor.account_type.bank_account_type_id,
            prenote_state_id=prenote_state.prenote_state_id,
        )
        EmployeePubEftPairFactory.create(employee=employee, pub_eft=pub_eft)

    absence_case_id = f"{fineos_notification_id}-ABS-001"

    claim = create_claim(
        employer=employer,
        employee=employee,
        claim_type=scenario_descriptor.claim_type,
        fineos_absence_id=absence_case_id,
        absence_status=AbsenceStatus.APPROVED,
    )

    return ScenarioData(
        scenario_descriptor=scenario_descriptor, employer=employer, employee=employee, claim=claim,
    )


def generate_scenario_dataset(config: ScenarioDataConfig) -> List[ScenarioData]:
    try:
        scenario_dataset: List[ScenarioData] = []

        # provided unique keys, sequences etc
        ssn = config.ssn_id_base + 1
        fein = config.fein_id_base + 1

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
