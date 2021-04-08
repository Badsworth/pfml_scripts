import argparse
import decimal
import random
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

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
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_util import (
    PaymentAuditData,
    write_audit_report,
)

logger = logging.get_logger(__name__)


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

    FIRST_TIME_PAYMENT = "First Time Payment"
    ERROR_PAYMENT = "Error Payment"
    REJECTED_PAYMENT = "Rejected Payment"
    MULTIPLE_DAYS_IN_ERROR_STATE = "Multiple Days in Error State"
    MULTIPLE_DAYS_IN_REJECTED_STATE = "Multiple Days in Rejected State"
    MIXED_DAYS_IN_ERROR_OR_REJECTED_STATE = "Mixed Days in Error or Rejected State"


@dataclass
class AuditScenarioDescriptor:
    scenario_name: AuditScenarioName
    claim_type: LkClaimType
    payment_method: LkPaymentMethod
    is_first_time_payment: bool
    is_previously_errored_payment: bool
    is_previously_rejected_payment: bool
    number_of_times_in_error_state: int
    number_of_times_in_rejected_state: int


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
    is_first_time_payment=True,
    is_previously_errored_payment=False,
    is_previously_rejected_payment=False,
    number_of_times_in_error_state=0,
    number_of_times_in_rejected_state=0,
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.FAMILY_LEAVE_CHECK] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.FAMILY_LEAVE_CHECK,
    claim_type=ClaimType.FAMILY_LEAVE,
    payment_method=PaymentMethod.CHECK,
    is_first_time_payment=True,
    is_previously_errored_payment=False,
    is_previously_rejected_payment=False,
    number_of_times_in_error_state=0,
    number_of_times_in_rejected_state=0,
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.MEDICAL_LEAVE_ACH] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.MEDICAL_LEAVE_ACH,
    claim_type=ClaimType.MEDICAL_LEAVE,
    payment_method=PaymentMethod.ACH,
    is_first_time_payment=True,
    is_previously_errored_payment=False,
    is_previously_rejected_payment=False,
    number_of_times_in_error_state=0,
    number_of_times_in_rejected_state=0,
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.MEDICAL_LEAVE_CHECK] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.MEDICAL_LEAVE_CHECK,
    claim_type=ClaimType.MEDICAL_LEAVE,
    payment_method=PaymentMethod.CHECK,
    is_first_time_payment=True,
    is_previously_errored_payment=False,
    is_previously_rejected_payment=False,
    number_of_times_in_error_state=0,
    number_of_times_in_rejected_state=0,
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.FIRST_TIME_PAYMENT] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.FIRST_TIME_PAYMENT,
    claim_type=ClaimType.FAMILY_LEAVE,
    payment_method=PaymentMethod.ACH,
    is_first_time_payment=True,
    is_previously_errored_payment=False,
    is_previously_rejected_payment=False,
    number_of_times_in_error_state=0,
    number_of_times_in_rejected_state=0,
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.ERROR_PAYMENT] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.ERROR_PAYMENT,
    claim_type=ClaimType.FAMILY_LEAVE,
    payment_method=PaymentMethod.ACH,
    is_first_time_payment=False,
    is_previously_errored_payment=True,
    is_previously_rejected_payment=False,
    number_of_times_in_error_state=1,
    number_of_times_in_rejected_state=0,
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.REJECTED_PAYMENT] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.REJECTED_PAYMENT,
    claim_type=ClaimType.FAMILY_LEAVE,
    payment_method=PaymentMethod.ACH,
    is_first_time_payment=False,
    is_previously_errored_payment=False,
    is_previously_rejected_payment=True,
    number_of_times_in_error_state=0,
    number_of_times_in_rejected_state=1,
)

AUDIT_SCENARIO_DESCRIPTORS[
    AuditScenarioName.MULTIPLE_DAYS_IN_ERROR_STATE
] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.MULTIPLE_DAYS_IN_ERROR_STATE,
    claim_type=ClaimType.FAMILY_LEAVE,
    payment_method=PaymentMethod.ACH,
    is_first_time_payment=False,
    is_previously_errored_payment=True,
    is_previously_rejected_payment=False,
    number_of_times_in_error_state=3,
    number_of_times_in_rejected_state=0,
)

AUDIT_SCENARIO_DESCRIPTORS[
    AuditScenarioName.MULTIPLE_DAYS_IN_REJECTED_STATE
] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.MULTIPLE_DAYS_IN_REJECTED_STATE,
    claim_type=ClaimType.FAMILY_LEAVE,
    payment_method=PaymentMethod.ACH,
    is_first_time_payment=False,
    is_previously_errored_payment=False,
    is_previously_rejected_payment=True,
    number_of_times_in_error_state=0,
    number_of_times_in_rejected_state=3,
)

AUDIT_SCENARIO_DESCRIPTORS[
    AuditScenarioName.MIXED_DAYS_IN_ERROR_OR_REJECTED_STATE
] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.MIXED_DAYS_IN_ERROR_OR_REJECTED_STATE,
    claim_type=ClaimType.FAMILY_LEAVE,
    payment_method=PaymentMethod.ACH,
    is_first_time_payment=False,
    is_previously_errored_payment=True,
    is_previously_rejected_payment=True,
    number_of_times_in_error_state=2,
    number_of_times_in_rejected_state=3,
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
    address_pair: ExperianAddressPair,
    payment_method: LkPaymentMethod,
    end_state: LkState,
    db_session: db.Session,
) -> Payment:
    payment_date = datetime.now()
    period_start_date = payment_date - timedelta(days=7)
    period_end_date = payment_date - timedelta(days=1)

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
        experian_address_pair=address_pair,
    )

    state_log_util.create_finished_state_log(
        payment, end_state, state_log_util.build_outcome("test"), db_session,
    )

    return payment


def generate_scenario_data(
    scenario_descriptor: AuditScenarioDescriptor, db_session: db.Session
) -> AuditScenarioData:
    c_value = str(uuid.uuid4().int)
    i_value = str(uuid.uuid4().int)

    mailing_address = AddressFactory.create(
        address_line_one="20 South Ave",
        city="Burlington",
        geo_state_id=1,
        geo_state_text="Massachusetts",
        zip_code="01803",
    )

    employer = EmployerFactory.create()

    employee = EmployeeFactory.create()
    address_pair = ExperianAddressPairFactory.create(experian_address=mailing_address)

    claim = ClaimFactory.create(
        employee=employee,
        employer=employer,
        claim_type_id=scenario_descriptor.claim_type.claim_type_id,
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
    )

    # Populate payments and state log for previous error and rejection scenarios
    if scenario_descriptor.is_previously_errored_payment:
        for _ in range(scenario_descriptor.number_of_times_in_error_state):
            create_payment_with_end_state(
                c_value,
                i_value,
                claim,
                address_pair,
                scenario_descriptor.payment_method,
                State.DELEGATED_PAYMENT_ERROR_REPORT_SENT,
                db_session,
            )

    if scenario_descriptor.is_previously_rejected_payment:
        for _ in range(scenario_descriptor.number_of_times_in_rejected_state):
            create_payment_with_end_state(
                c_value,
                i_value,
                claim,
                address_pair,
                scenario_descriptor.payment_method,
                State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
                db_session,
            )

    # create the latest payment
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
    payment_audit_data = PaymentAuditData(
        payment=payment,
        is_first_time_payment=scenario_descriptor.is_first_time_payment,
        is_previously_errored_payment=scenario_descriptor.is_previously_errored_payment,
        is_previously_rejected_payment=scenario_descriptor.is_previously_rejected_payment,
        number_of_times_in_rejected_or_error_state=scenario_descriptor.number_of_times_in_error_state
        + scenario_descriptor.number_of_times_in_rejected_state,
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
) -> List[AuditScenarioData]:
    if not reject_rate:
        reject_rate = decimal.Decimal(0.5)
    payment_audit_scenario_data_set: List[AuditScenarioData] = generate_audit_report_dataset(
        config, db_session
    )

    payment_audit_data_set: List[PaymentAuditData] = []
    for payment_audit_scenario_data in payment_audit_scenario_data_set:
        payment_audit_data: PaymentAuditData = payment_audit_scenario_data.payment_audit_data
        payment_audit_data.rejected_by_program_integrity = (
            True if random.random() <= reject_rate else False
        )
        payment_audit_data_set.append(payment_audit_data)

        # transition to sent state to simulate the payment audit report step
        state_log_util.create_finished_state_log(
            payment_audit_data.payment,
            State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            state_log_util.build_outcome("test"),
            db_session,
        )

    write_audit_report(
        payment_audit_data_set, folder_path, db_session, report_name="Payment-Rejects"
    )
    return payment_audit_scenario_data_set


def generate_payment_rejects_file():
    logging.init(__name__)

    logger.info("Genrating payment rejects file.")

    db_session = db.init(sync_lookups=True)
    db.models.factories.db_session = db_session

    args = parser.parse_args()
    folder_path = args.folder

    config: List[AuditScenarioNameWithCount] = [
        AuditScenarioNameWithCount(scenario_name, 1)
        for scenario_name in AUDIT_SCENARIO_DESCRIPTORS.keys()
    ]

    generate_payment_audit_data_set_and_rejects_file(config, folder_path, db_session)

    logger.info("Done genrating payment rejects file.")
