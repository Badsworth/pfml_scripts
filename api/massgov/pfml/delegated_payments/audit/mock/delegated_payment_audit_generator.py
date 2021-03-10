import argparse
import decimal
import random
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Tuple

import massgov.pfml.db as db
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    ClaimType,
    EmployeeAddress,
    LkClaimType,
    LkPaymentMethod,
    PaymentMethod,
)
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
    PaymentFactory,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_report import (
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
    UPDATED_PAYMENT = "Updated Payment"
    REJECTED_PAYMENT = "Rejected Payment"
    MULTIPLE_DAYS_IN_REJECTED_STATE = "Multiple Days in Rejected State"


@dataclass
class AuditScenarioDescriptor:
    scenario_name: AuditScenarioName
    claim_type: LkClaimType
    payment_method: LkPaymentMethod
    is_first_time_payment: bool
    is_updated_payment: bool
    is_rejected_payment: bool
    is_multiple_days_in_rejected_state: bool


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
    is_updated_payment=False,
    is_rejected_payment=False,
    is_multiple_days_in_rejected_state=False,
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.FAMILY_LEAVE_CHECK] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.FAMILY_LEAVE_CHECK,
    claim_type=ClaimType.FAMILY_LEAVE,
    payment_method=PaymentMethod.CHECK,
    is_first_time_payment=True,
    is_updated_payment=False,
    is_rejected_payment=False,
    is_multiple_days_in_rejected_state=False,
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.MEDICAL_LEAVE_ACH] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.MEDICAL_LEAVE_ACH,
    claim_type=ClaimType.MEDICAL_LEAVE,
    payment_method=PaymentMethod.ACH,
    is_first_time_payment=True,
    is_updated_payment=False,
    is_rejected_payment=False,
    is_multiple_days_in_rejected_state=False,
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.MEDICAL_LEAVE_CHECK] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.MEDICAL_LEAVE_CHECK,
    claim_type=ClaimType.MEDICAL_LEAVE,
    payment_method=PaymentMethod.CHECK,
    is_first_time_payment=True,
    is_updated_payment=False,
    is_rejected_payment=False,
    is_multiple_days_in_rejected_state=False,
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.FIRST_TIME_PAYMENT] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.FIRST_TIME_PAYMENT,
    claim_type=ClaimType.FAMILY_LEAVE,
    payment_method=PaymentMethod.ACH,
    is_first_time_payment=True,
    is_updated_payment=False,
    is_rejected_payment=False,
    is_multiple_days_in_rejected_state=False,
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.UPDATED_PAYMENT] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.UPDATED_PAYMENT,
    claim_type=ClaimType.FAMILY_LEAVE,
    payment_method=PaymentMethod.ACH,
    is_first_time_payment=False,
    is_updated_payment=True,
    is_rejected_payment=False,
    is_multiple_days_in_rejected_state=False,
)

AUDIT_SCENARIO_DESCRIPTORS[AuditScenarioName.REJECTED_PAYMENT] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.REJECTED_PAYMENT,
    claim_type=ClaimType.FAMILY_LEAVE,
    payment_method=PaymentMethod.ACH,
    is_first_time_payment=False,
    is_updated_payment=False,
    is_rejected_payment=True,
    is_multiple_days_in_rejected_state=False,
)

AUDIT_SCENARIO_DESCRIPTORS[
    AuditScenarioName.MULTIPLE_DAYS_IN_REJECTED_STATE
] = AuditScenarioDescriptor(
    scenario_name=AuditScenarioName.MULTIPLE_DAYS_IN_REJECTED_STATE,
    claim_type=ClaimType.FAMILY_LEAVE,
    payment_method=PaymentMethod.ACH,
    is_first_time_payment=False,
    is_updated_payment=False,
    is_rejected_payment=True,
    is_multiple_days_in_rejected_state=True,
)

#######################
## Utility functions ##
#######################


def generate_scenario_data(scenario_descriptor: AuditScenarioDescriptor) -> AuditScenarioData:
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

    employee = EmployeeFactory.create(
        payment_method_id=scenario_descriptor.payment_method.payment_method_id
    )
    employee.addresses = [EmployeeAddress(employee=employee, address=mailing_address)]

    claim = ClaimFactory.create(
        employee=employee,
        employer=employer,
        claim_type_id=scenario_descriptor.claim_type.claim_type_id,
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
    )

    payment_date = datetime.now()
    period_start_date = payment_date - timedelta(days=7)
    period_end_date = payment_date - timedelta(days=1)

    payment_amount = round(decimal.Decimal(random.uniform(1, 1000)), 2)

    payment = PaymentFactory.create(
        fineos_pei_c_value=c_value,
        fineos_pei_i_value=i_value,
        claim=claim,
        amount=payment_amount,
        payment_date=payment_date,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
    )

    # TODO implement other scenario descriptor flags after PUB-69 is complete
    # is_first_time_payment
    # is_updated_payment
    # is_rejected_payment
    # is_multiple_days_in_rejected_state

    payment_audit_data = PaymentAuditData(
        payment=payment,
        is_first_time_payment=scenario_descriptor.is_first_time_payment,
        is_updated_payment=scenario_descriptor.is_updated_payment,
        is_rejected_or_error=scenario_descriptor.is_rejected_payment,
        days_in_rejected_state=2 if scenario_descriptor.is_multiple_days_in_rejected_state else 0,
    )

    return AuditScenarioData(
        scenario_name=scenario_descriptor.scenario_name, payment_audit_data=payment_audit_data
    )


def generate_audit_report_dataset(
    data_set_config: List[AuditScenarioNameWithCount],
) -> List[AuditScenarioData]:
    scenario_data_set: List[Tuple[PaymentAuditData, AuditScenarioName]] = []

    for scenario_with_count in data_set_config:
        scenario_name = scenario_with_count.name
        scenario_count = scenario_with_count.count
        scenario_descriptor = AUDIT_SCENARIO_DESCRIPTORS[scenario_name]

        for i in range(scenario_count):  # noqa: B007
            scenario_data = generate_scenario_data(scenario_descriptor)
            scenario_data_set.append(scenario_data)

    return scenario_data_set


# TODO pass in batch id and separate data set generation piece (after PUB-76)
def generate_payment_audit_data_set_and_rejects_file(
    folder_path: str, db_session: db.Session
) -> List[AuditScenarioData]:
    test_scenarios_with_count: List[AuditScenarioNameWithCount] = [
        AuditScenarioNameWithCount(scenario_name, 10)
        for scenario_name in AUDIT_SCENARIO_DESCRIPTORS.keys()
    ]

    payment_audit_scenario_data_set: List[AuditScenarioData] = generate_audit_report_dataset(
        test_scenarios_with_count
    )

    payment_audit_data_set: List[PaymentAuditData] = []
    for payment_audit_scenario_data in payment_audit_scenario_data_set:
        payment_audit_data: PaymentAuditData = payment_audit_scenario_data.payment_audit_data
        payment_audit_data.rejected_by_program_integrity = True if random.random() < 0.3 else False
        payment_audit_data_set.append(payment_audit_data)

    write_audit_report(payment_audit_data_set, folder_path, db_session)
    return payment_audit_scenario_data_set


def generate_payment_rejects_file():
    logging.init(__name__)

    logger.info("Genrating payment rejects file.")

    db_session = db.init(sync_lookups=True)
    db.models.factories.db_session = db_session

    args = parser.parse_args()
    folder_path = args.folder

    generate_payment_audit_data_set_and_rejects_file(folder_path, db_session)

    logger.info("Done genrating payment rejects file.")
