# Test cases described in this Google Doc:
# https://docs.google.com/document/d/1232xwedUI6d2WNVavRAM8r1GempjSNDlFX7KgzC1va8/edit#

import decimal
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

import faker

import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.applications import LeaveReason
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
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
from massgov.pfml.types import TaxId

logger = logging.get_logger(__name__)
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
    # For Payments E2E test scenarios
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

    # For Payment Voucher testing
    SCENARIO_VOUCHER_A = "VA"
    SCENARIO_VOUCHER_B = "VB"
    SCENARIO_VOUCHER_C = "VC"
    SCENARIO_VOUCHER_D = "VD"
    SCENARIO_VOUCHER_E = "VE"
    SCENARIO_VOUCHER_F = "VF"
    SCENARIO_VOUCHER_G = "VG"
    SCENARIO_VOUCHER_H = "VH"
    SCENARIO_VOUCHER_I = "VI"
    SCENARIO_VOUCHER_J = "VJ"
    SCENARIO_VOUCHER_K = "VK"
    SCENARIO_VOUCHER_L = "VL"
    SCENARIO_VOUCHER_M = "VM"
    SCENARIO_VOUCHER_N = "VN"


@dataclass
class ScenarioNameWithCount:
    name: ScenarioName
    count: int


# Scenario Descriptors
# TODO bring over data mart round responses into descriptor
@dataclass
class EmployeePaymentScenarioDescriptor:
    scenario_name: ScenarioName
    leave_type: LkClaimType
    payee_payment_method: Optional[LkPaymentMethod]
    account_type: Optional[LkBankAccountType] = None
    missing_city: bool = False
    valid_state: bool = True
    non_existent_address: bool = False
    missing_routing: bool = False
    valid_ssn: bool = True
    missing_ssn: bool = False
    default_payment_preference: bool = True
    evidence_satisfied: bool = True
    absence_claims_count: int = 1

    has_payment_extract: bool = False
    missing_from_employee_feed: bool = False

    # Scenario information for in between extracts (vendor -> payment)
    payee_payment_method_update: Optional[LkPaymentMethod] = None
    non_existent_address_update: bool = False
    routing_number_ten_digits_update: bool = False
    negative_payment_update: bool = False
    future_payment_benefit_week_update: bool = False

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

    # To have multiple payments per absence claim
    payment_amounts_count: int = 0
    # To set a specific payment amounts
    payment_amounts: List[decimal.Decimal] = field(default_factory=list)
    # To set a missing payment
    missing_payment: bool = False
    # To specify a payment has multiple sub-payments (e.g. multiple rows in the vpeipaymentdetailscsv)
    has_multiple_payment_details: bool = False
    payment_details_count: int = 0
    # To make so that it is impossible to lookup the correct employee in the database
    employee_not_in_db: bool = False
    # To set VBI_REQUESTEDABSENCE.csv to be missing
    missing_from_vbi_requestedabsence: bool = False
    # To set VBI_REQUESTEDABSENCE_SOM.csv to be missing
    missing_from_vbi_requestedabsence_som: bool = False
    # To set vpeipaymentdetails.csv to be missing
    missing_from_vpeipaymentdetails: bool = False
    # To set vpeiclaimdetails.csv to be missing
    missing_from_vpeiclaimdetails: bool = False
    # To set missing payment start dates
    missing_payment_start_date: bool = False
    # To set missing payment end dates
    missing_payment_end_date: bool = False


SCENARIO_DESCRIPTORS: Dict[ScenarioName, EmployeePaymentScenarioDescriptor] = {}

# 1. has some records that validate and should be saved.

# EmployeeA with real address, payment method is check, leave type is medical leave
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_A] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_A,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    has_outbound_vendor_return=True,
    has_vcc_status_return=True,
    has_gax_status_return=True,
    has_outbound_payment_return=True,
    absence_claims_count=2,
)

# EmployeeB with real address, payment method is check, leave type is bonding leave
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_B] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_B,
    leave_type=ClaimType.FAMILY_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    has_outbound_vendor_return=True,
    has_vcc_status_return=True,
    has_gax_status_return=True,
    has_outbound_payment_return=True,
)

# EmployeeC with real address, real routing number, fake bank account number, payment method is ACH, leave type is medical leave
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_C] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_C,
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
    scenario_name=ScenarioName.SCENARIO_D,
    leave_type=ClaimType.FAMILY_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.SAVINGS,
    has_payment_extract=True,
    has_outbound_vendor_return=True,
    has_vcc_status_return=True,
    has_gax_status_return=True,
    has_outbound_payment_return=True,
)

# 2. has some records that are so invalid that a state log entry cannot be created for them
# (https://github.com/EOLWD/pfml/pull/2483/files#r548455099).
# These should be captured in logger.error/logger.exception

# EmployeeE has non-existent SSN. No StateLog entry should be created.
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_E] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_E,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.CHECKING,
    valid_ssn=False,
)

# EmployeeE has non-existent SSN. No StateLog entry should be created.
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_F] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_F,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.CHECKING,
    missing_ssn=True,
)

# 3. has some records that are invalid, but a state log entry is created for them
# (https://github.com/EOLWD/pfml/pull/2483/files#r548463121)

# EmployeeG payment method is debit card
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_G] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_G,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.DEBIT,
)

# EmployeeH address is missing required field (such as city)
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_H] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_H,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.CHECKING,
    missing_city=True,
)

# EmployeeI address is improperly formatted (state is “Massachussetts” instead of “MA”)
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_I] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_I,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.CHECKING,
    valid_state=False,
)

# EmployeeJ has payment method is ACH, missing routing number
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_J] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_J,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.CHECKING,
    missing_routing=True,
)

# 4. Records that should be ignored

# EmployeeK is DEFPAYMENTPREF is “N”
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_K] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_K,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.CHECKING,
    default_payment_preference=False,
)

# EmployeeL LEAVEREQUEST_EVIDENCERESULTTYPE != “Satisfied” (don’t ID proof someone)
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_L] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_L,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    evidence_satisfied=False,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_M] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_M,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    non_existent_address=True,
    has_outbound_vendor_return=True,
    has_vcc_status_return=True,
    has_vcc_status_return_errors=True,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_N] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_N,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_O] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_O,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    payee_payment_method_update=PaymentMethod.DEBIT,
    has_payment_extract=True,
    has_outbound_vendor_return=True,
    has_vcc_status_return=True,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_P] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_P,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    non_existent_address_update=True,
    has_outbound_vendor_return=True,
    has_vcc_status_return=True,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_Q] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_Q,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.CHECKING,
    routing_number_ten_digits_update=True,
    has_payment_extract=True,
    has_outbound_vendor_return=True,
    has_vcc_status_return=True,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_R] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_R,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    negative_payment_update=True,
    has_payment_extract=True,
    has_outbound_vendor_return=True,
    has_vcc_status_return=True,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_S] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_S,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    future_payment_benefit_week_update=True,
    has_payment_extract=True,
    has_outbound_vendor_return=True,
    has_vcc_status_return=True,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_T] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_T,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=None,
    missing_from_employee_feed=True,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_U] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_U,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_V] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_V,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_W] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_W,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.CHECKING,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_X] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_X,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.CHECKING,
    has_outbound_vendor_return=True,
    has_vcc_status_return=True,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_Y] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_Y,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.CHECKING,
    has_outbound_vendor_return=True,
    has_vcc_status_return=True,
)

SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_Z] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_Z,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    has_outbound_vendor_return=True,
    has_vcc_status_return=True,
    has_gax_status_return=True,
    has_gax_status_return_errors=True,
    has_outbound_payment_return=False,
)

# Start Payment Voucher scenarios
# valid address, payment method is check, leave type is medical leave, 2 payments
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_VOUCHER_A] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_VOUCHER_A,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    payment_amounts_count=2,
)

# valid address, payment method is check, leave type is bonding leave, payment is zero dollars
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_VOUCHER_B] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_VOUCHER_B,
    leave_type=ClaimType.FAMILY_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    payment_amounts=[decimal.Decimal(0)],
)

# valid address, real routing number, fake bank account number, payment method is ACH, leave type is medical leave
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_VOUCHER_C] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_VOUCHER_C,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.CHECKING,
    has_payment_extract=True,
)

# valid address, real routing number, fake bank account number, payment method is ACH, leave type is bonding leave
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_VOUCHER_D] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_VOUCHER_D,
    leave_type=ClaimType.FAMILY_LEAVE,
    payee_payment_method=PaymentMethod.ACH,
    account_type=BankAccountType.SAVINGS,
    has_payment_extract=True,
)

# valid address, payment method is check, leave type is medical leave, has multiple payment detail entries
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_VOUCHER_E] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_VOUCHER_E,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    has_multiple_payment_details=True,
)

# valid address, payment method is check, leave type is medical leave, payment is negative
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_VOUCHER_F] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_VOUCHER_F,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    payment_amounts=[decimal.Decimal(random.uniform(1, 1000)) * -1],
)

# valid address, payment method is check, leave type is medical leave, payment is missing
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_VOUCHER_G] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_VOUCHER_G,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    missing_payment=True,
)

# valid address, payment method is check, leave type is medical leave, employee is missing
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_VOUCHER_H] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_VOUCHER_H,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    employee_not_in_db=True,
)

# valid address, payment method is check, leave type is medical leave, vpeiclaimdetails.csv is missing
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_VOUCHER_I] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_VOUCHER_I,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    missing_from_vpeiclaimdetails=True,
)

# valid address, payment method is check, leave type is medical leave, VBI_REQUESTEDABSENCE.csv is missing
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_VOUCHER_J] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_VOUCHER_J,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    missing_from_vbi_requestedabsence=True,
)

# valid address, payment method is check, leave type is medical leave, VBI_REQUESTEDABSENCE_SOM.csv is missing
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_VOUCHER_K] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_VOUCHER_K,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    missing_from_vbi_requestedabsence_som=True,
)

# valid address, payment method is check, leave type is medical leave, vpeipaymentdetails.csv is missing
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_VOUCHER_L] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_VOUCHER_L,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    missing_from_vpeipaymentdetails=True,
)

# valid address, payment method is check, leave type is medical leave, vpeipaymentdetails.csv is missing start dates
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_VOUCHER_M] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_VOUCHER_M,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    missing_payment_start_date=True,
)

# valid address, payment method is check, leave type is medical leave, vpeipaymentdetails.csv is missing end dates
SCENARIO_DESCRIPTORS[ScenarioName.SCENARIO_VOUCHER_N] = EmployeePaymentScenarioDescriptor(
    scenario_name=ScenarioName.SCENARIO_VOUCHER_N,
    leave_type=ClaimType.MEDICAL_LEAVE,
    payee_payment_method=PaymentMethod.CHECK,
    has_payment_extract=True,
    missing_payment_end_date=True,
)


# Scenario Generation Config and Data
@dataclass
class ScenarioDataConfig:
    scenario_config: List[ScenarioNameWithCount]
    ssn_id_base: int = 100000000
    fein_id_base: int = 250000000


index_counter = {"index": 100}


def _new_index():
    index_counter["index"] += 1
    return index_counter["index"]


class CiProvider:
    vendor_c_i: CiIndex
    claim_ci: Optional[CiIndex]
    payment_ci: Optional[CiIndex]
    payment_period_ci: Optional[CiIndex]

    claim_ci_indices: List[CiIndex]
    payment_ci_indices: List[CiIndex]
    payment_period_ci_indices: List[CiIndex]

    def __init__(self):
        self.vendor_c_i = CiIndex(c="7000", i=str(_new_index()))
        self.claim_ci = None
        self.payment_ci = None
        self.payment_period_ci = None

        self.claim_ci_indices = []
        self.payment_ci_indices = []
        self.payment_period_ci_indices = []

    def get_vendor_ci(self):
        return self.vendor_c_i

    def get_claim_ci(self, next: bool = False) -> CiIndex:
        # TODO do we need to associate with vendor?
        if self.claim_ci is None or next:
            self.claim_ci = CiIndex(c="8000", i=str(_new_index()))
            self.claim_ci_indices.append(self.claim_ci)

        return self.claim_ci

    def get_payment_ci(self, next: bool = False) -> CiIndex:
        # TODO confirm I value should equal claim I value
        if self.payment_ci is None or next:
            self.payment_ci = CiIndex(c="9000", i=str((_new_index())))
            self.payment_ci_indices.append(self.payment_ci)

        return self.payment_ci


@dataclass
class ScenarioData:
    scenario_descriptor: EmployeePaymentScenarioDescriptor
    employee: Employee
    employer: Optional[Employer]
    claims: List[Claim]
    payment_amounts: List[decimal.Decimal]
    payments: Optional[List[Payment]]
    employee_customer_number: str
    vendor_customer_code: str
    ci_provider: CiProvider
    leave_request_id: str
    leave_request_decision: str
    payment_event_type: str
    absence_case_creation_date: str
    absence_reason_name: str
    leave_request_start: Optional[str]
    leave_request_end: Optional[str]

    def __repr__(self):
        return (
            f"Name: {self.scenario_descriptor.scenario_name}, Employee: {self.employee.employee_id}"
        )


# TODO validate scenario descriptor before starting generate
# Generate data in DB, return scenario
def generate_scenario_data_db(
    scenario_descriptor: EmployeePaymentScenarioDescriptor,
    ssn: str,
    fein: str,
    fineos_employer_id: str,
    fineos_notification_id: str,
    employee_customer_number: str,
    vendor_customer_code: str,
    leave_request_id: str,
    leave_request_decision: str,
    build_reference_files: bool = False,
) -> ScenarioData:
    eft = None
    payment_method_id = None

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

    # Note: if the employee is not in the database, then we should wipe out the vendor customer code.
    if scenario_descriptor.employee_not_in_db:
        vendor_customer_code = ""

    employee = EmployeeFactory.create(
        first_name=fake.first_name(),
        tax_identifier=TaxIdentifier(tax_identifier=TaxId(ssn)),
        ctr_address_pair=ctr_address_pair,
        eft=eft,
        payment_method_id=payment_method_id,
        ctr_vendor_customer_code=vendor_customer_code,
        fineos_customer_number=employee_customer_number,
    )

    employee.addresses = [EmployeeAddress(employee=employee, address=mailing_address)]

    employer = EmployerFactory.create(employer_fein=fein, fineos_employer_id=fineos_employer_id)

    claims: List[Claim] = []
    payment_amounts: List[decimal.Decimal] = []
    payments: List[Payment] = []
    ci_provider = CiProvider()

    # If the scenario has a payment extract, create at least 1 payment.
    if scenario_descriptor.has_payment_extract:
        if scenario_descriptor.payment_amounts_count == 0:
            scenario_descriptor.payment_amounts_count = 1
        if scenario_descriptor.payment_details_count == 0:
            scenario_descriptor.payment_details_count = 1

    for c in range(scenario_descriptor.absence_claims_count):
        if scenario_descriptor.missing_from_vpeiclaimdetails:
            absence_case_id = ""
        else:
            absence_case_index = c + 1
            absence_case_id = (
                f"{fineos_notification_id}-ABS-{str(absence_case_index)}"  # maximum length of 19
            )

        if (
            scenario_descriptor.missing_from_vbi_requestedabsence
            or scenario_descriptor.missing_from_vpeiclaimdetails
        ):
            claim_type_id = None
        else:
            claim_type_id = scenario_descriptor.leave_type.claim_type_id

        if (
            scenario_descriptor.missing_from_vbi_requestedabsence
            or scenario_descriptor.missing_from_vpeiclaimdetails
        ):
            fineos_absence_status_id = None
        else:
            fineos_absence_status_id = AbsenceStatus.APPROVED.absence_status_id

        claim = ClaimFactory.create(
            employer_id=employer.employer_id,
            employee=employee,
            fineos_absence_id=absence_case_id,
            claim_type_id=claim_type_id,
            fineos_absence_status_id=fineos_absence_status_id,
        )
        claims.append(claim)

        # For each claim, return the specified number of payments
        for i in range(scenario_descriptor.payment_amounts_count):
            # Use the specified payment amount if there is one
            # Otherwise, create a random payment amount between $1-1000
            if scenario_descriptor.payment_amounts and i < len(scenario_descriptor.payment_amounts):
                payment_amount = scenario_descriptor.payment_amounts[i]
            else:
                payment_amount = decimal.Decimal(random.uniform(1, 1000))
            payment_amounts.append(payment_amount)

            if scenario_descriptor.has_multiple_payment_details:
                scenario_descriptor.payment_details_count = random.randint(2, 5)

            payment_ci_index = ci_provider.get_payment_ci(next=True)
            payment = PaymentFactory.create(
                claim=claim,
                amount=payment_amount,
                fineos_pei_c_value=payment_ci_index.c,
                fineos_pei_i_value=payment_ci_index.i,
            )

            if (
                scenario_descriptor.missing_from_vpeipaymentdetails
                or scenario_descriptor.missing_payment_start_date
            ):
                payment.period_start_date = None

            if (
                scenario_descriptor.missing_from_vpeipaymentdetails
                or scenario_descriptor.missing_payment_end_date
            ):
                payment.period_end_date = None

            payment_ref_file = PaymentReferenceFileFactory.create(payment=payment)
            payment_ref_file.reference_file.ctr_batch_identifier = (
                CtrBatchIdentifierFactory.create()
            )
            payment_ref_file.reference_file.reference_file_type_id = (
                ReferenceFileType.GAX.reference_file_type_id
            )
            payments.append(payment)

        if (
            scenario_descriptor.has_vcc_status_return
            or scenario_descriptor.has_outbound_vendor_return
        ):
            emp_ref_file = EmployeeReferenceFileFactory.create(employee=employee)
            emp_ref_file.reference_file.ctr_batch_identifier = CtrBatchIdentifierFactory.create()

        leave_request_start = None  # fake.date_time()
        leave_request_end = None  # fake.date_time()

        if (
            scenario_descriptor.missing_from_vbi_requestedabsence
            or scenario_descriptor.missing_from_vpeiclaimdetails
        ):
            leave_request_id = ""
            leave_request_decision = ""
            absence_case_creation_date = ""
            absence_reason_name = ""
        else:
            absence_case_creation_date = fake.date_time()
            if (
                scenario_descriptor.leave_type.claim_type_id
                == ClaimType.MEDICAL_LEAVE.claim_type_id
            ):
                absence_reason_name = (
                    LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_description
                )
            else:
                absence_reason_name = random.choice(
                    [
                        LeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_description,
                        LeaveReason.PREGNANCY_MATERNITY.leave_reason_description,
                        LeaveReason.CHILD_BONDING.leave_reason_description,
                    ]
                )

        if (
            scenario_descriptor.missing_from_vbi_requestedabsence_som
            or scenario_descriptor.missing_from_vbi_requestedabsence
            or scenario_descriptor.missing_from_vpeiclaimdetails
        ):
            employer = None

        payment_event_type = "Some kind of event string"

    return ScenarioData(
        scenario_descriptor=scenario_descriptor,
        employee=employee,
        employer=employer,
        claims=claims,
        payment_amounts=payment_amounts,
        payments=payments,
        employee_customer_number=employee_customer_number,
        vendor_customer_code=vendor_customer_code,
        ci_provider=ci_provider,
        leave_request_id=leave_request_id,
        leave_request_decision=leave_request_decision,
        payment_event_type=payment_event_type,
        absence_case_creation_date=absence_case_creation_date,
        absence_reason_name=absence_reason_name,
        leave_request_start=leave_request_start,
        leave_request_end=leave_request_end,
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

            if scenario_name not in SCENARIO_DESCRIPTORS:
                logger.warning("Scenario %s is not defined", scenario_name)
                continue
            scenario_descriptor = SCENARIO_DESCRIPTORS[scenario_name]

            for i in range(scenario_count):  # noqa: B007
                ssn_part_str = str(ssn)[2:]
                fein_part_str = str(fein)[2:]

                fineos_employer_id = fein_part_str.rjust(9, "3")
                fineos_notification_id = f"NTN-{ssn_part_str}"
                employee_customer_number = ssn_part_str.rjust(9, "5")
                vendor_customer_code = ssn_part_str.rjust(9, "6")

                # Data for VBI_REQUSTEDABSENCE.csv (not _SOM), which is not
                # saved to the database
                leave_request_id = ssn_part_str.rjust(9, "7")
                leave_request_decision = "Approved"

                logger.info(
                    f"scenario_name: {scenario_name}, vendor_customer_code: {vendor_customer_code}"
                )

                scenario_data = generate_scenario_data_db(
                    scenario_descriptor,
                    ssn=str(ssn),
                    fein=str(fein),
                    fineos_employer_id=fineos_employer_id,
                    fineos_notification_id=fineos_notification_id,
                    vendor_customer_code=vendor_customer_code,
                    employee_customer_number=employee_customer_number,
                    leave_request_id=leave_request_id,
                    leave_request_decision=leave_request_decision,
                )
                scenario_dataset.append(scenario_data)

                ssn += 1
                fein += 1

        return scenario_dataset
    except Exception as e:
        raise e
