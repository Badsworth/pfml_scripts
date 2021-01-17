# Test cases described in this Google Doc:
# https://docs.google.com/document/d/1232xwedUI6d2WNVavRAM8r1GempjSNDlFX7KgzC1va8/edit#

import decimal
import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

import faker

from massgov.pfml.db.models.employees import (
    BankAccountType,
    Claim,
    ClaimType,
    Employee,
    EmployeeAddress,
    Employer,
    LkBankAccountType,
    LkClaimType,
    LkPaymentMethod,
    Payment,
    PaymentMethod,
    ReferenceFileType,
    TaxIdentifier,
)
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ClaimFactory,
    CtrAddressPairFactory,
    CtrBatchIdentifierFactory,
    EftFactory,
    EmployeeFactory,
    EmployeeReferenceFileFactory,
    EmployerFactory,
    PaymentFactory,
    PaymentReferenceFileFactory,
)
from massgov.pfml.payments.fineos_payment_export import CiIndex

fake = faker.Faker()

# Constants
VALID_ROUTING_NUMBER = "211870935"
FAKE_ACCOUNT_NUMBER = "123456789"
VALID_ADDRESSES = [
    {
        "payment_address_1": "20 South Ave",
        "payment_address_2": "",
        "payment_address_4": "Burlington",
        "payment_address_6": "MA",
        "payment_post_code": "01803",
    }
]


class ScenarioName(Enum):
    SCENARIO_A = "A"
    SCENARIO_B = "B"
    SCENARIO_C = "C"
    SCENARIO_D = "D"
    SCENARIO_E = "E"
    SCENARIO_F = "F"
    SCENARIO_G = "G"
    SCENARIO_H = "H"
    SCENARIO_I = "I"
    SCENARIO_J = "J"
    SCENARIO_K = "K"
    SCENARIO_L = "L"
    SCENARIO_M = "M"
    SCENARIO_N = "N"
    SCENARIO_O = "O"
    SCENARIO_P = "P"
    SCENARIO_Q = "Q"
    SCENARIO_R = "R"
    SCENARIO_S = "S"
    SCENARIO_T = "T"
    SCENARIO_U = "U"
    SCENARIO_V = "V"
    SCENARIO_W = "W"
    SCENARIO_X = "X"
    SCENARIO_Y = "Y"
    SCENARIO_Z = "Z"


@dataclass
class ScenarioNameWithCount:
    name: ScenarioName
    count: int


# Scenario Descriptors
# TODO bring over data mart round responses into descriptor
@dataclass
class EmployeePaymentScenarioDescriptor:
    leave_type: LkClaimType
    payee_payment_method: Optional[LkPaymentMethod]
    account_type: Optional[LkBankAccountType] = None
    missing_city: bool = False
    valid_state: bool = True
    non_existent_address: bool = False
    missing_routing: bool = False
    valid_ssn: bool = True
    missing_ssn: bool = True
    default_payment_preference: bool = True
    evidence_satisfied: bool = True

    # Creates EmployeeReferenceFile and Comptroller IDs in the database.
    has_vcc_status_return: bool = False
    has_vcc_status_return_errors: bool = False

    # Creates PaymentReferenceFile and Comptroller IDs in the database.
    has_gax_status_return: bool = False
    has_gax_status_pending_ctr_action: bool = False
    has_gax_status_return_errors: bool = False

    has_outbound_vendor_return: bool = False
    has_broken_outbound_vendor_return: bool = False  # Requires above to also be true

    has_outbound_payment_return: bool = False

    has_payment_extract: bool = True
    missing_from_employee_feed: bool = False

    # Scenario information for in between extracts (vendor -> payment)
    payee_payment_method_update: Optional[LkPaymentMethod] = None
    non_existent_address_update: bool = False
    routing_number_ten_digits_update: bool = False
    negative_payment_update: bool = False
    future_payment_benefit_week_update: bool = False


SCENARIO_DESCRIPTORS: Dict[str, EmployeePaymentScenarioDescriptor] = {}

# 1. has some records that validate and should be saved.

# EmployeeA with real address, payment method is check, leave type is medical leave
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_A] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    has_outbound_vendor_return=True,
    has_gax_status_return=True,
    has_outbound_payment_return=True,
)

# EmployeeB with real address, payment method is check, leave type is bonding leave
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_B] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.FAMILY_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    has_outbound_vendor_return=True,
    has_gax_status_return=True,
    has_outbound_payment_return=True,
)

# EmployeeC with real address, real routing number, fake bank account number, payment method is ACH, leave type is medical leave
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_C] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.CHECKING,
    has_vcc_status_return=True,
    has_payment_extract=True,
    has_outbound_vendor_return=True,
    has_gax_status_return=True,
    has_outbound_payment_return=True,
)

# EmployeeD with real address, real routing number, fake bank account number, payment method is ACH, leave type is bonding leave
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_D] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.FAMILY_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.SAVINGS,
    has_payment_extract=True,
    has_outbound_vendor_return=True,
    has_gax_status_return=True,
    has_outbound_payment_return=True,
)

# 2. has some records that are so invalid that a state log entry cannot be created for them
# (https://github.com/EOLWD/pfml/pull/2483/files#r548455099).
# These should be captured in logger.error/logger.exception

# EmployeeE has non-existent SSN. No StateLog entry should be created.
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_E] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.CHECKING,
    valid_ssn=False,
)

# EmployeeE has non-existent SSN. No StateLog entry should be created.
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_F] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.CHECKING,
    missing_ssn=True,
)

# 3. has some records that are invalid, but a state log entry is created for them
# (https://github.com/EOLWD/pfml/pull/2483/files#r548463121)

# EmployeeG payment method is debit card
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_G] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE, payee_payment_method=PaymentMethod.DEBIT,
)

# EmployeeH address is missing required field (such as city)
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_H] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.CHECKING,
    missing_city=True,
)

# EmployeeI address is improperly formatted (state is “Massachussetts” instead of “MA”)
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_I] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.CHECKING,
    valid_state=False,
)

# EmployeeJ has payment method is ACH, missing routing number
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_J] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.CHECKING,
    missing_routing=True,
)

# 4. Records that should be ignored

# EmployeeK is DEFPAYMENTPREF is “N” (create multiple payment methods for EmployeeJ)
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_K] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.CHECKING,
    default_payment_preference=False,
)

# EmployeeL LEAVEREQUEST_EVIDENCERESULTTYPE != “Satisfied” (don’t ID proof someone)
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_L] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    evidence_satisfied=False,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_M] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    non_existent_address=True,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_N] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE, payee_payment_method=PaymentMethod.CHECK
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_O] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    payee_payment_method_update=PaymentMethod.DEBIT,
    has_payment_extract=True,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_P] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    non_existent_address_update=True,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_Q] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    routing_number_ten_digits_update=True,
    has_payment_extract=True,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_R] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    negative_payment_update=True,
    has_payment_extract=True,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_S] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    future_payment_benefit_week_update=True,
    has_payment_extract=True,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_T] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE, payee_payment_method=None, missing_from_employee_feed=True
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_U] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE, payee_payment_method=PaymentMethod.CHECK
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_V] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE, payee_payment_method=PaymentMethod.CHECK
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_W] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE, payee_payment_method=PaymentMethod.CHECK
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_X] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE, payee_payment_method=PaymentMethod.ACH
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_Y] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE, payee_payment_method=PaymentMethod.ACH
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_Z] = EmployeePaymentScenarioDescriptor(
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    has_outbound_vendor_return=True,
)


# Scenario Generation Config and Data
@dataclass
class ScenarioDataConfig:
    scenario_config: List[ScenarioNameWithCount]
    ssn_id_base: int = 100000000
    fein_id_base: int = 250000000


@dataclass
class ScenarioData:
    scenario_descriptor: EmployeePaymentScenarioDescriptor
    employee: Employee
    employer: Employer
    payment: Optional[Payment]
    claim: Claim
    employee_customer_number: str
    vendor_customer_code: str
    payment_amount: decimal.Decimal
    ci_index: CiIndex


# Generate data in DB, return scenario
def generate_scenario_data_db(
    scenario_descriptor: EmployeePaymentScenarioDescriptor,
    ssn: str,
    fein: str,
    fineos_employer_id: str,
    absence_case_id: str,
    employee_customer_number: str,
    vendor_customer_code: str,
    ci_index: CiIndex,
    build_reference_files: bool = False,
) -> ScenarioData:
    eft = None

    if scenario_descriptor.payee_payment_method:
        payment_method_id = scenario_descriptor.payee_payment_method.payment_method_id

        if scenario_descriptor.payee_payment_method == PaymentMethod.ACH:
            if not scenario_descriptor.account_type:
                raise Exception("account type should not be empty for ACH payment method")

            account_type_id = scenario_descriptor.account_type.bank_account_type_id

            eft = EftFactory.create(
                routing_nbr=VALID_ROUTING_NUMBER,
                account_nbr=FAKE_ACCOUNT_NUMBER,
                bank_account_type_id=account_type_id,
            )

    mock_address = random.sample(VALID_ADDRESSES, 1)[0]
    mailing_address = AddressFactory.create(
        address_line_one=mock_address["payment_address_1"],
        address_line_two=mock_address["payment_address_2"],
        city="" if scenario_descriptor.missing_city else mock_address["payment_address_4"],
        geo_state_id=1 if scenario_descriptor.valid_state else None,
        geo_state_text="Massachusetts" if not scenario_descriptor.valid_state else None,
        zip_code=mock_address["payment_post_code"],
    )

    ctr_address_pair = CtrAddressPairFactory.create(fineos_address=mailing_address)
    employee = EmployeeFactory.create(
        first_name=fake.first_name(),
        tax_identifier=TaxIdentifier(tax_identifier=ssn),
        ctr_address_pair=ctr_address_pair,
        eft=eft,
        payment_method_id=payment_method_id,
    )

    employee.addresses = [EmployeeAddress(employee=employee, address=mailing_address)]

    employer = EmployerFactory.create(employer_fein=fein, fineos_employer_id=fineos_employer_id)
    claim = ClaimFactory.create(
        employer_id=employer.employer_id, employee=employee, fineos_absence_id=absence_case_id,
    )

    # Create a random payment amount between $1-1000
    payment_amount = decimal.Decimal(random.uniform(1, 1000))

    payment = None
    if build_reference_files:
        if (
            scenario_descriptor.has_vcc_status_return
            or scenario_descriptor.has_outbound_vendor_return
        ):
            emp_ref_file = EmployeeReferenceFileFactory.create(employee=employee)
            emp_ref_file.reference_file.ctr_batch_identifier = CtrBatchIdentifierFactory.create()

        if (
            scenario_descriptor.has_gax_status_return
            or scenario_descriptor.has_outbound_payment_return
        ):
            payment = PaymentFactory.create(claim=claim)
            payment_ref_file = PaymentReferenceFileFactory.create(payment=payment)
            payment_ref_file.reference_file.ctr_batch_identifier = (
                CtrBatchIdentifierFactory.create()
            )
            payment_ref_file.reference_file.reference_file_type_id = (
                ReferenceFileType.GAX.reference_file_type_id
            )

    return ScenarioData(
        scenario_descriptor=scenario_descriptor,
        employee=employee,
        employer=employer,
        payment=payment,
        claim=claim,
        employee_customer_number=employee_customer_number,
        vendor_customer_code=vendor_customer_code,
        payment_amount=payment_amount,
        ci_index=ci_index,
    )


# Generate scenario data set in DB, return data set
def generate_scenario_dataset(config: ScenarioDataConfig) -> List[ScenarioData]:
    try:
        scenario_dataset: List[ScenarioData] = []

        # generate scenario data
        ssn = config.ssn_id_base + 1
        fein = config.fein_id_base + 1

        for scenario_and_count in config.scenario_config:
            scenario_name = scenario_and_count.name
            scenario_count = scenario_and_count.count
            scenario_descriptor = SCENARIO_DESCRIPTORS[scenario_name]

            for i in range(scenario_count):  # noqa: B007
                ssn_part_str = str(ssn)[2:]
                fein_part_str = str(fein)[2:]

                ci_index = CiIndex(ssn_part_str.rjust(9, "1"), fein_part_str.rjust(9, "2"))
                fineos_employer_id = int(fein_part_str.rjust(9, "3"))
                absence_case_id = f"NTN-{ssn_part_str.rjust(9, '4')}-ABS-01"
                employee_customer_number = ssn_part_str.rjust(9, "5")
                vendor_customer_code = ssn_part_str.rjust(9, "6")

                scenario_data = generate_scenario_data_db(
                    scenario_descriptor,
                    ssn=ssn,
                    fein=fein,
                    fineos_employer_id=fineos_employer_id,
                    absence_case_id=absence_case_id,
                    vendor_customer_code=vendor_customer_code,
                    employee_customer_number=employee_customer_number,
                    ci_index=ci_index,
                )
                scenario_dataset.append(scenario_data)

                ssn += 1
                fein += 1

        return scenario_dataset
    except Exception as e:
        raise e
