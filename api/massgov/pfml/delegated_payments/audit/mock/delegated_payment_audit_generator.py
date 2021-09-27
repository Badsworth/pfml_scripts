import argparse
import decimal
import random
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

import faker

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    Claim,
    ClaimType,
    ExperianAddressPair,
    LkClaimType,
    LkPaymentMethod,
    LkState,
    Payment,
    PaymentMethod,
    State,
)
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
    ExperianAddressPairFactory,
    PaymentFactory,
)
from massgov.pfml.db.models.payments import PaymentAuditReportType
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_util import (
    PaymentAuditCSV,
    PaymentAuditData,
    build_audit_report_row,
    stage_payment_audit_report_details,
    write_audit_report_rows,
)
from massgov.pfml.delegated_payments.delegated_payments_util import Constants

logger = logging.get_logger(__name__)

fake = faker.Faker()
fake.seed_instance(1212)


# Setup command line generator args

parser = argparse.ArgumentParser(description="Generate fake payments files and data")
parser.add_argument(
    "--folder", type=str, default="payments_files", help="Output folder for generated files"
)


##############################
## Scenario Data Structures ##
##############################


class AuditScenarioName(Enum):
    FAMILY_LEAVE_ACH = "FAMILY_LEAVE_ACH"
    FAMILY_LEAVE_CHECK = "FAMILY_LEAVE_CHECK"
    MEDICAL_LEAVE_ACH = "MEDICAL_LEAVE_ACH"
    MEDICAL_LEAVE_CHECK = "MEDICAL_LEAVE_CHECK"

    SECOND_TIME_PAYMENT = "SECOND_TIME_PAYMENT"
    ERROR_PAYMENT = "ERROR_PAYMENT"
    ERROR_PAYMENT_RESTARTABLE = "ERROR_PAYMENT_RESTARTABLE"
    ADDRESS_VALIDATION_ERROR = "ADDRESS_VALIDATION_ERROR"
    REJECTED_PAYMENT = "REJECTED_PAYMENT"
    REJECTED_PAYMENT_RESTARTABLE = "REJECTED_PAYMENT_RESTARTABLE"
    MULTIPLE_DAYS_IN_ERROR_STATE = "MULTIPLE_DAYS_IN_ERROR_STATE"
    MULTIPLE_DAYS_IN_REJECTED_STATE = "MULTIPLE_DAYS_IN_REJECTED_STATE"
    MIXED_DAYS_IN_ERROR_OR_REJECTED_STATE = "MIXED_DAYS_IN_ERROR_OR_REJECTED_STATE"

    ADDRESS_PAIR_DOES_NOT_EXIST = "ADDRESS_PAIR_DOES_NOT_EXIST"
    ADDRESS_IS_NOT_VERIFIED = "ADDRESS_IS_NOT_VERIFIED"

    AUDIT_REPORT_DETAIL_REJECTED = "AUDIT_REPORT_DETAIL_REJECTED"
    AUDIT_REPORT_DETAIL_INFORMATIONAL = "AUDIT_REPORT_DETAIL_INFORMATIONAL"
    AUDIT_REPORT_DETAIL_MIXED = "AUDIT_REPORT_DETAIL_MIXED"


@dataclass
class AuditScenarioDescriptor:
    scenario_name: AuditScenarioName
    claim_type: LkClaimType = ClaimType.FAMILY_LEAVE
    payment_method: LkPaymentMethod = PaymentMethod.ACH

    is_first_time_payment: bool = True
    previous_error_states: List[LkState] = field(default_factory=list)
    previous_rejection_states: List[LkState] = field(default_factory=list)

    has_address_pair: bool = True
    is_address_verified: bool = True

    audit_report_detail_rejected: bool = False
    audit_report_detail_informational: bool = False


@dataclass
class AuditScenarioData:
    scenario_name: AuditScenarioName
    payment_audit_data: PaymentAuditData


@dataclass
class AuditScenarioNameWithCount:
    name: AuditScenarioName
    count: int


###############
## Scenarios ##
###############

AUDIT_SCENARIO_DESCRIPTORS: Dict[AuditScenarioName, AuditScenarioDescriptor] = OrderedDict()

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.FAMILY_LEAVE_ACH] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.FAMILY_LEAVE_ACH,
    claim_type=ClaimType.FAMILY_LEAVE,
    payment_method=PaymentMethod.ACH,
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.FAMILY_LEAVE_CHECK] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.FAMILY_LEAVE_CHECK,
    claim_type=ClaimType.FAMILY_LEAVE,
    payment_method=PaymentMethod.CHECK,
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.MEDICAL_LEAVE_ACH] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.MEDICAL_LEAVE_ACH,
    claim_type=ClaimType.MEDICAL_LEAVE,
    payment_method=PaymentMethod.ACH,
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.MEDICAL_LEAVE_CHECK] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.MEDICAL_LEAVE_CHECK,
    claim_type=ClaimType.MEDICAL_LEAVE,
    payment_method=PaymentMethod.CHECK,
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.SECOND_TIME_PAYMENT] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.SECOND_TIME_PAYMENT, is_first_time_payment=False
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.ERROR_PAYMENT] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.ERROR_PAYMENT,
    previous_error_states=[State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT],
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.ERROR_PAYMENT_RESTARTABLE] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.ERROR_PAYMENT_RESTARTABLE,
    previous_error_states=[State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE],
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.ADDRESS_VALIDATION_ERROR] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.ADDRESS_VALIDATION_ERROR,
    previous_error_states=[State.PAYMENT_FAILED_ADDRESS_VALIDATION],
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.REJECTED_PAYMENT] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.REJECTED_PAYMENT,
    previous_rejection_states=[State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT],
)

AUDIT_SCENARIO_DESCRIPTORS[
    AuditScenarioName.REJECTED_PAYMENT_RESTARTABLE
] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.REJECTED_PAYMENT_RESTARTABLE,
    previous_rejection_states=[State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE],
)

AUDIT_SCENARIO_DESCRIPTORS[
    AuditScenarioName.MULTIPLE_DAYS_IN_ERROR_STATE
] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.MULTIPLE_DAYS_IN_ERROR_STATE,
    previous_error_states=[
        State.PAYMENT_FAILED_ADDRESS_VALIDATION,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
    ],
)

AUDIT_SCENARIO_DESCRIPTORS[
    AuditScenarioName.MULTIPLE_DAYS_IN_REJECTED_STATE
] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.MULTIPLE_DAYS_IN_REJECTED_STATE,
    previous_rejection_states=[
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
    ],
)

AUDIT_SCENARIO_DESCRIPTORS[
    AuditScenarioName.MIXED_DAYS_IN_ERROR_OR_REJECTED_STATE
] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.MIXED_DAYS_IN_ERROR_OR_REJECTED_STATE,
    previous_error_states=[
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
    ],
    previous_rejection_states=[
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
    ],
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.ADDRESS_PAIR_DOES_NOT_EXIST] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.ADDRESS_PAIR_DOES_NOT_EXIST, has_address_pair=False,
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.ADDRESS_IS_NOT_VERIFIED] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.ADDRESS_IS_NOT_VERIFIED, is_address_verified=False,
)

AUDIT_SCENARIO_DESCRIPTORS[
    AuditScenarioName.AUDIT_REPORT_DETAIL_REJECTED
] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.AUDIT_REPORT_DETAIL_REJECTED, audit_report_detail_rejected=True
)

AUDIT_SCENARIO_DESCRIPTORS[
    AuditScenarioName.AUDIT_REPORT_DETAIL_INFORMATIONAL
] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.AUDIT_REPORT_DETAIL_INFORMATIONAL,
    audit_report_detail_informational=True,
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.AUDIT_REPORT_DETAIL_MIXED] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.AUDIT_REPORT_DETAIL_MIXED,
    audit_report_detail_rejected=True,
    audit_report_detail_informational=True,
)

DEFAULT_AUDIT_SCENARIO_DATA_SET = [
    AuditScenarioNameWithCount(scenario_name, 1)
    for scenario_name in AUDIT_SCENARIO_DESCRIPTORS.keys()
]

#######################
## Utility functions ##
#######################


def create_payment_with_end_state(
    c_value: str,
    i_value: str,
    claim: Claim,
    address_pair: Optional[ExperianAddressPair],
    payment_method: LkPaymentMethod,
    end_state: LkState,
    db_session: db.Session,
) -> Payment:
    payment_date = datetime.now().date()
    period_start_date = payment_date - timedelta(days=7)
    period_end_date = payment_date - timedelta(days=1)
    absence_case_creation_date = payment_date - timedelta(days=30)

    payment_amount = round(decimal.Decimal(random.uniform(1, 1000)), 2)

    payment = PaymentFactory.create(
        fineos_pei_c_value=c_value,
        fineos_pei_i_value=i_value,
        claim=claim,
        disb_method_id=payment_method.payment_method_id,
        amount=payment_amount,
        payment_date=payment_date,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
        absence_case_creation_date=absence_case_creation_date,
        experian_address_pair=address_pair,
        leave_request_decision="Approved",
    )

    state_log_util.create_finished_state_log(
        payment, end_state, state_log_util.build_outcome("test"), db_session,
    )

    return payment


def _new_ci_value() -> str:
    return str(fake.unique.random_int())


def _is_restartable_state(state: Optional[LkState]) -> bool:
    if state is None:
        return False

    return state in Constants.RESTARTABLE_PAYMENT_STATES


def _create_previous_payments(
    claim: Claim,
    address_pair: Optional[ExperianAddressPair],
    payment_method: LkPaymentMethod,
    previous_states: List[LkState],
    db_session: db.Session,
) -> Tuple[Optional[str], Optional[str]]:

    previous_state: Optional[LkState] = None
    c_value = _new_ci_value()
    i_value = _new_ci_value()

    for state in previous_states:
        if not _is_restartable_state(previous_state):
            c_value = _new_ci_value()
            i_value = _new_ci_value()

        create_payment_with_end_state(
            c_value, i_value, claim, address_pair, payment_method, state, db_session,
        )

        previous_state = state

    # return last used ci value if last state was restartable
    if _is_restartable_state(previous_state):
        return (c_value, i_value)
    else:
        return (None, None)


def generate_scenario_data(
    scenario_descriptor: AuditScenarioDescriptor, db_session: db.Session
) -> AuditScenarioData:
    c_value = _new_ci_value()
    i_value = _new_ci_value()

    mailing_address = AddressFactory.create(
        address_line_one="20 South Ave", city="Burlington", geo_state_id=1, zip_code="01803",
    )

    verified_address = AddressFactory.create(
        address_line_one="20 South Avenue", city="Burlington", geo_state_id=1, zip_code="01803",
    )

    employer = EmployerFactory.create()

    employee = EmployeeFactory.create(fineos_customer_number=str(uuid.uuid4()))

    address_pair: Optional[ExperianAddressPair] = None
    if scenario_descriptor.has_address_pair:
        if scenario_descriptor.is_address_verified:
            address_pair = ExperianAddressPairFactory.create(
                fineos_address=mailing_address, experian_address=verified_address
            )
        else:
            address_pair = ExperianAddressPairFactory.create(fineos_address=mailing_address)

    claim = ClaimFactory.create(
        claim_id=uuid.uuid4(),
        employee=employee,
        employer=employer,
        claim_type_id=scenario_descriptor.claim_type.claim_type_id,
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
    )

    if not scenario_descriptor.is_first_time_payment:
        previously_audited_payment = create_payment_with_end_state(
            c_value,
            i_value,
            claim,
            address_pair,
            scenario_descriptor.payment_method,
            State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            db_session,
        )
        state_log_util.create_finished_state_log(
            previously_audited_payment,
            State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
            state_log_util.build_outcome("test"),
            db_session,
        )

    # Populate payments and state log for previous error and rejection scenarios
    restartable_c_value = None
    restartable_i_value = None

    if len(scenario_descriptor.previous_error_states) > 0:
        restartable_c_value, restartable_i_value = _create_previous_payments(
            claim,
            address_pair,
            scenario_descriptor.payment_method,
            scenario_descriptor.previous_error_states,
            db_session,
        )

    if len(scenario_descriptor.previous_rejection_states) > 0:
        restartable_c_value, restartable_i_value = _create_previous_payments(
            claim,
            address_pair,
            scenario_descriptor.payment_method,
            scenario_descriptor.previous_rejection_states,
            db_session,
        )

    # create the current payment staged for audit
    if restartable_c_value and restartable_i_value:
        c_value = restartable_c_value
        i_value = restartable_i_value
    else:
        c_value = _new_ci_value()
        i_value = _new_ci_value()

    payment = create_payment_with_end_state(
        c_value,
        i_value,
        claim,
        address_pair,
        scenario_descriptor.payment_method,
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
        db_session,
    )

    # create the payment data
    previous_error_count = len(scenario_descriptor.previous_error_states)
    previously_rejected_payment_count = len(
        list(
            filter(
                lambda s: s == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
                scenario_descriptor.previous_rejection_states,
            )
        )
    )
    previously_skipped_payment_count = len(
        list(
            filter(
                lambda s: s == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE,
                scenario_descriptor.previous_rejection_states,
            )
        )
    )

    payment_audit_data = PaymentAuditData(
        payment=payment,
        is_first_time_payment=scenario_descriptor.is_first_time_payment,
        previously_errored_payment_count=previous_error_count,
        previously_rejected_payment_count=previously_rejected_payment_count,
        previously_skipped_payment_count=previously_skipped_payment_count,
    )

    if scenario_descriptor.audit_report_detail_rejected:
        stage_payment_audit_report_details(
            payment, PaymentAuditReportType.MAX_WEEKLY_BENEFITS, "Test Message", None, db_session
        )

    if scenario_descriptor.audit_report_detail_informational:
        stage_payment_audit_report_details(
            payment, PaymentAuditReportType.DUA_DIA_REDUCTION, "Test Message", None, db_session
        )

    return AuditScenarioData(
        scenario_name=scenario_descriptor.scenario_name, payment_audit_data=payment_audit_data
    )


def generate_audit_report_dataset(
    data_set_config: List[AuditScenarioNameWithCount], db_session: db.Session
) -> List[AuditScenarioData]:
    scenario_data_set: List[AuditScenarioData] = []

    for scenario_with_count in data_set_config:
        scenario_name = scenario_with_count.name
        scenario_count = scenario_with_count.count
        scenario_descriptor = AUDIT_SCENARIO_DESCRIPTORS[scenario_name]

        for i in range(scenario_count):  # noqa: B007
            scenario_data = generate_scenario_data(scenario_descriptor, db_session)
            scenario_data_set.append(scenario_data)

    return scenario_data_set


def generate_payment_audit_data_set_and_rejects_file(
    config: List[AuditScenarioNameWithCount],
    folder_path: str,
    db_session: db.Session,
    reject_rate: Optional[decimal.Decimal] = None,
    file_name: str = "Payment-Audit-Report-Response",
) -> List[AuditScenarioData]:
    if not reject_rate:
        reject_rate = decimal.Decimal(0.5)
    payment_audit_scenario_data_set: List[AuditScenarioData] = generate_audit_report_dataset(
        config, db_session
    )

    audit_report_time = datetime.now()
    payment_audit_report_rows: List[PaymentAuditCSV] = []

    for payment_audit_scenario_data in payment_audit_scenario_data_set:
        payment_audit_data: PaymentAuditData = payment_audit_scenario_data.payment_audit_data

        audit_report_row = build_audit_report_row(payment_audit_data, audit_report_time, db_session)

        audit_report_row.rejected_by_program_integrity = (
            "Y" if random.random() <= reject_rate else ""
        )
        audit_report_row.skipped_by_program_integrity = (
            ""  # clear this in case it was set by audit report details flow
        )

        payment_audit_report_rows.append(audit_report_row)

        # transition to sent state to simulate the payment audit report step
        state_log_util.create_finished_state_log(
            payment_audit_data.payment,
            State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            state_log_util.build_outcome("test"),
            db_session,
        )

    write_audit_report_rows(
        payment_audit_report_rows, folder_path, db_session, report_name=file_name
    )

    return payment_audit_scenario_data_set


def generate_payment_rejects_file():
    logging.init(__name__)

    logger.info("Generating payment rejects file.")

    db_session = db.init(sync_lookups=True)
    db.models.factories.db_session = db_session

    args = parser.parse_args()
    folder_path = args.folder

    config: List[AuditScenarioNameWithCount] = [
        AuditScenarioNameWithCount(scenario_name, 1)
        for scenario_name in AUDIT_SCENARIO_DESCRIPTORS.keys()
    ]

    generate_payment_audit_data_set_and_rejects_file(config, folder_path, db_session)

    logger.info("Done generating payment rejects file.")
