import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional

import faker

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.experian.address_validate_soap.client as soap_api
import massgov.pfml.experian.address_validate_soap.models as sm
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.absences import AbsenceStatus
from massgov.pfml.db.models.employees import (
    AbsencePeriod,
    Address,
    BenefitYear,
    Claim,
    Employee,
    Employer,
    LkAbsenceStatus,
    Payment,
    PaymentMethod,
    PrenoteState,
    State,
    TaxIdentifier,
)
from massgov.pfml.db.models.factories import (
    AbsencePeriodFactory,
    AddressFactory,
    BenefitYearFactory,
    ClaimFactory,
    CtrAddressPairFactory,
    DiaReductionPaymentFactory,
    DuaReductionPaymentFactory,
    EmployeeFactory,
    EmployeePubEftPairFactory,
    EmployerFactory,
    PubEftFactory,
)
from massgov.pfml.db.models.geo import GeoState
from massgov.pfml.delegated_payments.mock.mock_util import generate_routing_nbr_from_ssn
from massgov.pfml.delegated_payments.mock.scenarios import (
    ScenarioDescriptor,
    ScenarioName,
    get_scenario_by_name,
)
from massgov.pfml.experian.address_validate_soap.mock_caller import MockVerificationZeepCaller
from massgov.pfml.util.datetime import get_now_us_eastern

logger = logging.get_logger(__name__)

fake = faker.Faker()
fake.seed_instance(1212)


# == Constants ==

MATCH_ADDRESS = {
    "line_1": "20 South Ave",
    "line_2": "",
    "city": "Burlington",
    "state": "MA",
    "zip": "01803",
}

NO_MATCH_ADDRESS = {
    "line_1": "123 Main St",
    "line_2": "",
    "city": "Burlington",
    "state": "MA",
    "zip": "01803",
}

INVALID_ADDRESS = {
    "line_1": "20 South Ave",
    "line_2": "",
    "city": "Burlington",
    "state": "XA",
    "zip": "01803",
}


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
    claim: Optional[Claim]

    absence_case_id: str
    leave_request_id: int

    payment_c_value: Optional[str] = None
    payment_i_value: Optional[str] = None

    additional_payment_c_value: Optional[str] = None
    additional_payment_i_value: Optional[str] = None

    tax_withholding_payment_i_values: Optional[List[str]] = None

    additional_payment_absence_case_id: Optional[str] = None

    absence_period_c_value: Optional[str] = None
    absence_period_i_value: Optional[str] = None

    payment: Optional[Payment] = None
    additional_payment: Optional[Payment] = None

    tax_withholding_payments: Optional[List[Payment]] = None


@dataclass
class ScenarioDataConfig:
    scenarios_with_count: List[ScenarioNameWithCount]
    ssn_id_base: int = 100000000
    fein_id_base: int = 250000000


# == Common Utils ==


def get_mock_address_client() -> soap_api.Client:
    def parse_address(mock_address: Dict) -> Address:
        state = GeoState.description_to_db_instance.get(mock_address["state"], GeoState.MA)

        return AddressFactory.build(
            address_line_one=mock_address["line_1"],
            address_line_two=mock_address["line_2"],
            city=mock_address["city"],
            geo_state=state,
            zip_code=mock_address["zip"],
        )

    mock_caller = MockVerificationZeepCaller(sm.VerifyLevel.STREET_PARTIAL)

    # add valid address
    valid_address = parse_address(MATCH_ADDRESS)
    mock_caller.add_mock_search_response(valid_address, sm.VerifyLevel.VERIFIED)

    # add no match address
    no_match_address = parse_address(NO_MATCH_ADDRESS)
    mock_caller.add_mock_search_response(no_match_address, sm.VerifyLevel.NONE)

    return soap_api.Client(mock_caller)


# == Helpers ==


def create_employer(fein: str, fineos_employer_id: str, db_session: db.Session) -> Employer:
    employer = (
        db_session.query(Employer)
        .filter(Employer.employer_fein == fein, Employer.fineos_employer_id == fineos_employer_id)
        .one_or_none()
    )
    if employer is not None:
        logger.info(
            "reusing existing employer with fein %s %s and fineos_employer_id %s %s: %s",
            fein[:2],
            fein[2:],
            fineos_employer_id[:3],
            fineos_employer_id[3:],
            employer.employer_name,
        )
        return employer
    return EmployerFactory.create(
        employer_id=uuid.uuid4(), employer_fein=fein, fineos_employer_id=fineos_employer_id
    )


def create_employee(ssn: str, fineos_customer_number: str, db_session: db.Session) -> Employee:
    employee = (
        db_session.query(Employee)
        .join(TaxIdentifier)
        .filter(
            TaxIdentifier.tax_identifier == ssn,
            Employee.fineos_customer_number == fineos_customer_number,
        )
        .one_or_none()
    )
    if employee is not None:
        logger.info(
            "reusing existing employee with ssn %s %s and fineos_customer_number %s %s: %s %s",
            ssn[:3],
            ssn[3:],
            fineos_customer_number[:3],
            fineos_customer_number[3:],
            employee.first_name,
            employee.last_name,
        )
        return employee
    tax_identifier = TaxIdentifier(tax_identifier=ssn)
    return EmployeeFactory.create(
        employee_id=uuid.uuid4(),
        tax_identifier=tax_identifier,
        fineos_customer_number=fineos_customer_number,
        ctr_address_pair=CtrAddressPairFactory.create(),
    )


def create_dua_additional_income(fineos_customer_number: str) -> None:
    payment_date = get_now_us_eastern()

    DuaReductionPaymentFactory.create(
        fineos_customer_number=fineos_customer_number,
        request_week_begin_date=payment_date + timedelta(days=2),
    )


def create_dia_additional_income(fineos_customer_number: str) -> None:
    DiaReductionPaymentFactory.create(fineos_customer_number=fineos_customer_number)


def create_claim(
    employer: Employer,
    employee: Optional[Employee],
    absence_status: LkAbsenceStatus,
    fineos_absence_id: str,
    db_session: db.Session,
) -> Claim:
    claim = (
        db_session.query(Claim)
        .filter(
            Claim.employer == employer,
            Claim.employee == employee,
            Claim.fineos_absence_status_id == absence_status.absence_status_id,
            Claim.fineos_absence_id == fineos_absence_id,
        )
        .one_or_none()
    )
    if claim is not None:
        logger.info("reusing existing claim with fineos_absence_id %s", fineos_absence_id)
        return claim
    if employee is None:
        return ClaimFactory.create(
            employer=employer,
            employee=None,
            employee_id=None,
            fineos_absence_status_id=absence_status.absence_status_id,
            fineos_absence_id=fineos_absence_id,
        )
    return ClaimFactory.create(
        employer=employer,
        employee=employee,
        fineos_absence_status_id=absence_status.absence_status_id,
        fineos_absence_id=fineos_absence_id,
    )


# == Generators ==


def generate_scenario_data_in_db(
    scenario_descriptor: ScenarioDescriptor,
    ssn: str,
    fein: str,
    leave_request_id: int,
    fineos_employer_id: str,
    fineos_notification_id: str,
    fineos_customer_number: str,
    db_session: db.Session,
) -> ScenarioData:

    employer = create_employer(fein, fineos_employer_id, db_session)

    employee = create_employee(ssn, fineos_customer_number, db_session)

    construct_benefit_year(employee)

    if scenario_descriptor.dua_additional_income:
        create_dua_additional_income(fineos_customer_number)

    if scenario_descriptor.dia_additional_income:
        create_dia_additional_income(fineos_customer_number)

    add_eft = (
        scenario_descriptor.payment_method.payment_method_id == PaymentMethod.ACH.payment_method_id
        and scenario_descriptor.existing_eft_account
    )
    if add_eft:
        prenote_state = (
            PrenoteState.APPROVED if scenario_descriptor.prenoted else PrenoteState.PENDING_PRE_PUB
        )
        pub_eft = PubEftFactory.create(
            pub_eft_id=uuid.uuid4(),
            routing_nbr=generate_routing_nbr_from_ssn(ssn),
            account_nbr=ssn,
            bank_account_type_id=scenario_descriptor.account_type.bank_account_type_id,
            prenote_state_id=prenote_state.prenote_state_id,
        )
        EmployeePubEftPairFactory.create(employee=employee, pub_eft=pub_eft)

        if not scenario_descriptor.prenoted:
            state_log_util.create_finished_state_log(
                end_state=State.DELEGATED_EFT_SEND_PRENOTE,
                associated_model=employee,
                outcome=state_log_util.build_outcome(
                    "Initiated DELEGATED_EFT flow for employee associated with payment"
                ),
                db_session=db_session,
            )

    absence_case_id = f"{fineos_notification_id}-ABS-001"

    claim = construct_claim(scenario_descriptor, employee, employer, absence_case_id, db_session)
    construct_absence_period(scenario_descriptor, claim, leave_request_id)

    return ScenarioData(
        scenario_descriptor=scenario_descriptor,
        employer=employer,
        employee=employee,
        claim=claim,
        absence_case_id=absence_case_id,
        leave_request_id=leave_request_id,
    )


def construct_benefit_year(employee: Employee) -> BenefitYear:
    # We should assume Benefit Year data exists for all claimants
    # since this data has been backfilled in prod.
    #
    # The dates below were chosen to include claims that start
    # on 2021-1-1, with the exact values given from the benefit
    # year dates calculator as 2020-12-27 to 2021-12-25
    return BenefitYearFactory.create(
        employee=employee, start_date=date(2020, 12, 27), end_date=date(2021, 12, 25)
    )


def construct_absence_period(
    scenario_descriptor: ScenarioDescriptor, claim: Optional[Claim], leave_request_id: int
) -> Optional[AbsencePeriod]:
    if claim is None or not scenario_descriptor.has_absence_period:
        return None

    absence_period_start_date = (
        # This default start date prevents the payment date mismatch processer to fail based on the payment period date
        claim.absence_period_start_date
        if claim.absence_period_start_date
        else date(2021, 5, 1)
    )

    absence_period_end_date = (
        # This default end date prevents the total leave duration processer to fail
        claim.absence_period_end_date
        if claim.absence_period_end_date
        else absence_period_start_date + timedelta(weeks=26, days=-1)
    )

    if scenario_descriptor.max_leave_duration_exceeded:
        absence_period_end_date = absence_period_start_date + timedelta(weeks=26)
    elif scenario_descriptor.payment_date_mismatch:
        absence_period_start_date = date(2021, 1, 5)
        absence_period_end_date = date(2021, 1, 12)
        scenario_descriptor.is_adhoc_payment = False

    claim.absence_period_start_date = absence_period_start_date
    claim.absence_period_end_date = absence_period_end_date

    absence_period = AbsencePeriodFactory.create(
        claim=claim,
        absence_period_start_date=absence_period_start_date,
        absence_period_end_date=absence_period_end_date,
        absence_period_type_id=scenario_descriptor.absence_period_type.absence_period_type_id,
        fineos_leave_request_id=leave_request_id,
    )

    return absence_period


def construct_claim(
    scenario_descriptor: ScenarioDescriptor,
    employee: Employee,
    employer: Employer,
    absence_case_id: str,
    db_session: db.Session,
) -> Optional[Claim]:
    if not scenario_descriptor.has_existing_claim:
        claim = None
    elif scenario_descriptor.claim_missing_employee:
        claim = create_claim(
            employer=employer,
            employee=None,
            fineos_absence_id=absence_case_id,
            absence_status=AbsenceStatus.APPROVED,
            db_session=db_session,
        )
    else:
        claim = create_claim(
            employer=employer,
            employee=employee,
            fineos_absence_id=absence_case_id,
            absence_status=AbsenceStatus.APPROVED,
            db_session=db_session,
        )

    return claim


def generate_scenario_dataset(
    config: ScenarioDataConfig, db_session: db.Session
) -> List[ScenarioData]:
    try:
        scenario_dataset: List[ScenarioData] = []

        # provided unique keys, sequences etc
        ssn = config.ssn_id_base + 1
        fein = config.fein_id_base + 1
        leave_request_id = 100

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

                # match with customer_number in fineos_extract_data.py
                fineos_customer_number = str(ssn)
                if not scenario_descriptor.is_tax_withholding_record_without_primary_payment:
                    fineos_customer_number = str(ssn)
                else:
                    fineos_customer_number = ""

                scenario_data = generate_scenario_data_in_db(
                    scenario_descriptor,
                    ssn=str(ssn),
                    fein=str(fein),
                    fineos_employer_id=fineos_employer_id,
                    fineos_notification_id=fineos_notification_id,
                    fineos_customer_number=fineos_customer_number,
                    leave_request_id=leave_request_id,
                    db_session=db_session,
                )

                scenario_data.payment_c_value = "7326"
                scenario_data.payment_i_value = str(fake.unique.random_int())

                scenario_data.absence_period_c_value = "14449"
                scenario_data.absence_period_i_value = str(
                    fake.unique.random_int(min=1_000_000, max=9_999_999)
                )

                if scenario_descriptor.has_additional_payment_in_period:
                    scenario_data.additional_payment_c_value = "7326"
                    scenario_data.additional_payment_i_value = str(fake.unique.random_int())

                    scenario_data.additional_payment_absence_case_id = (
                        f"{scenario_data.absence_case_id}_additional"
                    )
                    construct_claim(
                        scenario_descriptor,
                        scenario_data.employee,
                        scenario_data.employer,
                        scenario_data.additional_payment_absence_case_id,
                        db_session,
                    )

                if scenario_descriptor.is_tax_withholding_records_exists:
                    scenario_data.tax_withholding_payment_i_values = [
                        str(fake.unique.random_int()),
                        str(fake.unique.random_int()),
                    ]

                scenario_dataset.append(scenario_data)

                # increment sequences
                ssn += 1
                fein += 1
                leave_request_id += 1

        return scenario_dataset

    except Exception as e:
        logger.exception("Error generating scenario data set")
        raise e
