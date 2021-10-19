from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional

import faker

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
from massgov.pfml.db.models.employees import (
    Address,
    BankAccountType,
    Claim,
    ClaimType,
    Employee,
    EmployeeAddress,
    Employer,
    Payment,
    PaymentCheck,
    PaymentTransactionType,
    PrenoteState,
    State,
)
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployeePubEftPairFactory,
    EmployerFactory,
    ExperianAddressPairFactory,
    PaymentFactory,
    PubEftFactory,
    TaxIdentifierFactory,
)
from massgov.pfml.db.models.payments import FineosWritebackDetails
from massgov.pfml.delegated_payments.mock.mock_util import MockData, generate_routing_nbr_from_ssn

fake = faker.Faker()
fake.seed_instance(2394)

KWARG_VALUE_NOT_SET = "KWARG_VALUE_NOT_SET"


# TODO consider adding the following
# employer.fineos_employer_id
# claim.fineos_notification_id
# add_extra_payment by period date
class DelegatedPaymentFactory(MockData):
    def __init__(
        self,
        db_session: db.Session,
        generate_defaults: bool = True,
        set_pub_eft_in_payment: bool = False,
        employee: Optional[Employee] = None,
        employer: Optional[Employer] = None,
        claim: Optional[Claim] = None,
        payment: Optional[Payment] = None,
        add_employee: bool = True,
        add_address: bool = True,
        add_employer: bool = True,
        add_claim: bool = True,
        add_pub_eft: bool = True,
        add_payment: bool = True,
        **kwargs: Any,
    ):
        super().__init__(generate_defaults, **kwargs)

        self.db_session = db_session
        self.set_pub_eft_in_payment = set_pub_eft_in_payment

        self.employee = employee
        self.employer = employer
        self.claim = claim
        self.payment = payment
        self.pub_eft = None
        self.mailing_address: Optional[Address] = None
        self.add_employee = add_employee
        self.add_address = add_address
        self.add_employer = add_employer
        self.add_claim = add_claim
        self.add_pub_eft = add_pub_eft
        self.add_payment = add_payment

        # employee
        self.fineos_customer_number = self.get_value("fineos_customer_number", None)
        self.employee_optional_kwargs: Dict[str, Any] = (
            {}
        )  # only set if value was passed in constructor, else defer to lazy factory initialization

        fineos_employee_first_name = self.get_value(
            "fineos_employee_first_name", KWARG_VALUE_NOT_SET
        )
        self.set_optional_kwargs(
            self.employee_optional_kwargs, "fineos_employee_first_name", fineos_employee_first_name,
        )

        fineos_employee_last_name = self.get_value("fineos_employee_last_name", KWARG_VALUE_NOT_SET)
        self.set_optional_kwargs(
            self.employee_optional_kwargs, "fineos_employee_last_name", fineos_employee_last_name
        )

        # pub eft defaults
        self.ssn = self.get_value(
            "ssn", str(fake.unique.random_int(min=100_000_000, max=200_000_000))
        )
        self.pub_individual_id = self.get_value("pub_individual_id", None)
        self.prenote_state = self.get_value("prenote_state", PrenoteState.PENDING_WITH_PUB)
        self.routing_nbr = self.get_value("routing_nbr", generate_routing_nbr_from_ssn(self.ssn))
        self.account_nbr = self.get_value("account_nbr", self.ssn)
        self.prenote_sent_at = self.get_value("prenote_sent_at", None)
        self.prenote_response_at = self.get_value("prenote_response_at", None)

        # claim defaults
        self.claim_type = self.get_value("claim_type", ClaimType.FAMILY_LEAVE)
        self.fineos_absence_id = self.get_value("fineos_absence_id", str(fake.unique.random_int()))
        self.is_id_proofed = self.get_value("is_id_proofed", True)

        # payment defaults
        self.payment_optional_kwargs: Dict[str, Any] = (
            {}
        )  # only set if value was passed in constructor, else defer to lazy factory initialization

        fineos_pei_c_value = self.get_value("fineos_pei_c_value", KWARG_VALUE_NOT_SET)
        self.set_optional_kwargs(
            self.payment_optional_kwargs, "fineos_pei_c_value", fineos_pei_c_value
        )

        fineos_pei_i_value = self.get_value("fineos_pei_i_value", KWARG_VALUE_NOT_SET)
        self.set_optional_kwargs(
            self.payment_optional_kwargs, "fineos_pei_i_value", fineos_pei_i_value
        )

        self.payment_method = self.get_value("payment_method", None)
        self.payment_end_state_message = self.get_value("payment_end_state_message", "test")
        self.period_start_date = self.get_value("period_start_date", date(2021, 1, 16))
        self.period_end_date = self.get_value("period_end_date", date(2021, 1, 28))
        self.payment_date = self.get_value("payment_date", date(2021, 1, 29))
        self.fineos_extraction_date = self.get_value("fineos_extraction_date", date(2021, 1, 28))
        self.is_adhoc_payment = self.get_value("is_adhoc_payment", False)
        self.payment_transaction_type = self.get_value(
            "payment_transaction_type", PaymentTransactionType.STANDARD
        )
        self.amount = self.get_value("amount", Decimal("0.00"))
        self.experian_address_pair = self.get_value("experian_address_pair", None)
        self.check_number = self.get_value("check_number", None)

    # only set if value was passed in constructor through kwarg
    # else defer to lazy factory initialization
    def set_optional_kwargs(self, kwargs_map, key, value):
        if value != KWARG_VALUE_NOT_SET:
            kwargs_map[key] = value

    def get_or_create_address(self):
        if self.mailing_address is None:
            self.mailing_address = AddressFactory()

        return self.mailing_address

    def get_or_create_employee(self):
        if self.employee is None and self.add_employee:
            self.employee = EmployeeFactory(
                fineos_customer_number=self.fineos_customer_number,
                tax_identifier=TaxIdentifierFactory.create(tax_identifier=self.ssn),
                **self.employee_optional_kwargs,
            )

            if self.add_address:
                self.employee.addresses = [
                    EmployeeAddress(employee=self.employee, address=self.get_or_create_address())
                ]

        return self.employee

    def get_or_create_pub_eft(self):
        if not self.add_pub_eft or self.pub_eft is not None:
            return self.pub_eft

        self.get_or_create_employee()

        pub_eft = PubEftFactory.create(
            routing_nbr=self.routing_nbr,
            account_nbr=self.account_nbr,
            bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
            prenote_state_id=self.prenote_state.prenote_state_id,
            pub_individual_id=self.pub_individual_id,
            prenote_response_at=self.prenote_response_at,
            prenote_sent_at=self.prenote_sent_at,
        )

        if self.employee:
            EmployeePubEftPairFactory.create(employee=self.employee, pub_eft=pub_eft)

        self.db_session.commit()
        self.db_session.refresh(pub_eft)

        self.pub_eft = pub_eft
        return pub_eft

    def get_or_create_pub_eft_with_state(self, employee_end_state):
        pub_eft = self.get_or_create_pub_eft()

        if self.employee:
            state_log_util.create_finished_state_log(
                end_state=employee_end_state,
                associated_model=self.employee,
                db_session=self.db_session,
                outcome=state_log_util.build_outcome(
                    f"Generated state {self.prenote_state.prenote_state_description}"
                ),
            )

        return pub_eft

    def get_or_create_claim(self):
        self.get_or_create_employee()

        if self.employer is None and self.add_employer:
            self.employer = EmployerFactory.create()

        if self.claim is None and self.add_claim:
            self.claim = ClaimFactory.create(
                claim_type_id=self.claim_type.claim_type_id,
                fineos_absence_id=self.fineos_absence_id,
                employee=self.employee,
                employer=self.employer,
                is_id_proofed=self.is_id_proofed,
                employee_id=self.employee.employee_id if self.employee else None,
            )

        return self.claim

    def get_or_create_payment(self):
        if self.payment or not self.add_payment:
            return self.payment

        self.get_or_create_claim()

        if self.add_address and self.experian_address_pair is None:
            self.experian_address_pair = ExperianAddressPairFactory.create(
                fineos_address=self.get_or_create_address()
            )

        self.payment = PaymentFactory.create(
            claim=self.claim,
            pub_individual_id=self.pub_individual_id,
            disb_method_id=self.payment_method.payment_method_id if self.payment_method else None,
            period_start_date=self.period_start_date,
            period_end_date=self.period_end_date,
            payment_date=self.payment_date,
            is_adhoc_payment=self.is_adhoc_payment,
            payment_transaction_type_id=self.payment_transaction_type.payment_transaction_type_id,
            amount=self.amount if self.amount else Decimal(0),
            pub_eft=self.pub_eft if self.set_pub_eft_in_payment else None,
            fineos_employee_first_name=self.employee.fineos_employee_first_name
            if self.employee
            else None,
            fineos_employee_last_name=self.employee.fineos_employee_last_name
            if self.employee
            else None,
            experian_address_pair=self.experian_address_pair,
            claim_type=self.claim.claim_type if self.claim else None,
            check=PaymentCheck(check_number=self.check_number) if self.check_number else None,
            fineos_extraction_date=self.fineos_extraction_date,
            **self.payment_optional_kwargs,
        )

        return self.payment

    def get_or_create_payment_with_state(self, payment_end_state):
        self.get_or_create_payment()

        if self.payment and payment_end_state:
            state_log_util.create_finished_state_log(
                self.payment,
                payment_end_state,
                state_log_util.build_outcome(self.payment_end_state_message),
                self.db_session,
            )

        return self.payment

    def get_or_create_payment_with_writeback(self, writeback_transaction_status):
        self.get_or_create_payment_with_state(State.DELEGATED_ADD_TO_FINEOS_WRITEBACK)

        if self.payment:
            writeback_details = FineosWritebackDetails(
                payment=self.payment,
                transaction_status_id=writeback_transaction_status.transaction_status_id,
            )
            self.db_session.add(writeback_details)

    def create_all(self):
        if self.add_pub_eft:
            self.get_or_create_pub_eft()

        # order matters - payments will check and create claims, claims -> employees
        if self.add_payment:
            self.get_or_create_payment()
        elif self.add_claim:
            self.get_or_create_claim()
        elif self.add_employee:
            self.get_or_create_employee()
