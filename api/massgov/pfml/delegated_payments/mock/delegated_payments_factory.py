import uuid
from datetime import date, timedelta
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
    ImportLog,
    Payment,
    PaymentCheck,
    PaymentTransactionType,
    PrenoteState,
    State,
)
from massgov.pfml.db.models.factories import (
    AbsencePeriodFactory,
    AddressFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployeePubEftPairFactory,
    EmployerFactory,
    ExperianAddressPairFactory,
    ImportLogFactory,
    OrganizationUnitFactory,
    PaymentDetailsFactory,
    PaymentFactory,
    PaymentLineFactory,
    PubEftFactory,
    TaxIdentifierFactory,
)
from massgov.pfml.db.models.payments import FineosExtractVpeiPaymentLine
from massgov.pfml.delegated_payments.mock.mock_util import MockData, generate_routing_nbr_from_ssn
from massgov.pfml.delegated_payments.util.fineos_writeback_util import (
    stage_payment_fineos_writeback,
)

fake = faker.Faker()
fake.seed_instance(2394)

KWARG_VALUE_NOT_SET = "KWARG_VALUE_NOT_SET"


def random_unique_int(min=1, max=999_999_999):
    return fake.unique.random_int(min=min, max=max)


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
        import_log: Optional[ImportLog] = None,
        add_employee: bool = True,
        add_address: bool = True,
        add_employer: bool = True,
        add_claim: bool = True,
        add_pub_eft: bool = True,
        add_payment: bool = True,
        add_import_log: bool = True,
        add_single_absence_period: bool = False,
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
        self.import_log = import_log
        self.mailing_address: Optional[Address] = None
        self.add_employee = add_employee
        self.add_address = add_address
        self.add_employer = add_employer
        self.add_claim = add_claim
        self.add_pub_eft = add_pub_eft
        self.add_payment = add_payment
        self.add_import_log = add_import_log
        self.add_single_absence_period = add_single_absence_period

        # employee
        self.fineos_customer_number = self.get_value("fineos_customer_number", None)
        self.employee_optional_kwargs: Dict[
            str, Any
        ] = (
            {}
        )  # only set if value was passed in constructor, else defer to lazy factory initialization

        fineos_employee_first_name = self.get_value(
            "fineos_employee_first_name", KWARG_VALUE_NOT_SET
        )
        self.set_optional_kwargs(
            self.employee_optional_kwargs, "fineos_employee_first_name", fineos_employee_first_name
        )

        fineos_employee_last_name = self.get_value("fineos_employee_last_name", KWARG_VALUE_NOT_SET)
        self.set_optional_kwargs(
            self.employee_optional_kwargs, "fineos_employee_last_name", fineos_employee_last_name
        )

        # employer
        self.employer_customer_num = self.get_value(
            "employer_customer_num", str(fake.unique.random_int(min=1, max=1_000_000))
        )
        self.employer_exempt_family = self.get_value("employer_exempt_family", False)
        self.employer_exempt_medical = self.get_value("employer_exempt_medical", False)
        self.employer_exempt_commence_date = self.get_value("employer_exempt_commence_date", None)
        self.employer_exempt_cease_date = self.get_value("employer_exempt_cease_date", None)

        # pub eft defaults
        self.ssn = self.get_value("ssn", str(random_unique_int(min=100_000_000, max=200_000_000)))
        self.pub_individual_id = self.get_value("pub_individual_id", None)
        self.prenote_state = self.get_value("prenote_state", PrenoteState.PENDING_WITH_PUB)
        self.routing_nbr = self.get_value("routing_nbr", generate_routing_nbr_from_ssn(self.ssn))
        self.account_nbr = self.get_value("account_nbr", self.ssn)
        self.prenote_sent_at = self.get_value("prenote_sent_at", None)
        self.prenote_response_at = self.get_value("prenote_response_at", None)

        # claim defaults
        self.claim_type = self.get_value("claim_type", ClaimType.FAMILY_LEAVE)
        self.fineos_absence_id = self.get_value(
            "fineos_absence_id", f"NTN-{random_unique_int()}-ABS-01"
        )
        self.is_id_proofed = self.get_value("is_id_proofed", True)
        self.fineos_absence_status_id = self.get_value("fineos_absence_status_id", None)
        self.absence_period_start_date = self.get_value(
            "absence_period_start_date", date(2021, 1, 7)
        )
        self.absence_period_end_date = self.get_value("absence_period_end_date", None)
        self.organization_unit_name = self.get_value("organization_unit_name", None)
        self.organization_unit = self.get_value("organization_unit", None)

        # Absence period defaults
        self.fineos_leave_request_id = self.get_value(
            "fineos_leave_request_id", random_unique_int()
        )

        # payment defaults
        self.payment_optional_kwargs: Dict[
            str, Any
        ] = (
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
        self.period_start_date = self.get_value("period_start_date", date(2021, 1, 21))
        self.period_end_date = self.get_value("period_end_date", date(2021, 1, 28))
        self.payment_date = self.get_value("payment_date", date(2021, 1, 29))
        self.fineos_extraction_date = self.get_value("fineos_extraction_date", date(2021, 1, 28))
        self.is_adhoc_payment = self.get_value("is_adhoc_payment", False)
        self.payment_transaction_type = self.get_value(
            "payment_transaction_type", PaymentTransactionType.STANDARD
        )
        self.amount = self.get_value("amount", Decimal("100.00"))
        self.experian_address_pair = self.get_value("experian_address_pair", None)
        self.check_number = self.get_value("check_number", None)
        self.fineos_extract_import_log_id = self.get_value(
            "fineos_extract_import_log_id",
            self.import_log.import_log_id if self.import_log else None,
        )
        self.exclude_from_payment_status = self.get_value("exclude_from_payment_status", None)

        # Only set this for legacy payments
        self.disb_check_eft_issue_date = self.get_value("disb_check_eft_issue_date", None)

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
                self.employee.employee_addresses = [
                    EmployeeAddress(employee=self.employee, address=self.get_or_create_address())
                ]

        return self.employee

    def get_or_create_employer(self):
        if self.employer is None and self.add_employer:
            self.employer = EmployerFactory.create(
                fineos_employer_id=self.employer_customer_num,
                family_exemption=self.employer_exempt_family,
                medical_exemption=self.employer_exempt_medical,
                exemption_commence_date=self.employer_exempt_commence_date,
                exemption_cease_date=self.employer_exempt_cease_date,
            )
            # Only adds organization unit if there is an employer on this claim
            if self.organization_unit_name is not None:
                self.organization_unit = OrganizationUnitFactory.create(
                    name=self.organization_unit_name, employer=self.employer
                )

        return self.employer

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

        self.get_or_create_employer()

        if self.claim is None and self.add_claim:
            self.claim = ClaimFactory.create(
                claim_type_id=self.claim_type.claim_type_id,
                fineos_absence_id=self.fineos_absence_id,
                employee=self.employee,
                employer=self.employer,
                is_id_proofed=self.is_id_proofed,
                employee_id=self.employee.employee_id if self.employee else None,
                fineos_absence_status_id=self.fineos_absence_status_id,
                absence_period_start_date=self.absence_period_start_date,
                absence_period_end_date=self.absence_period_end_date,
                organization_unit=self.organization_unit,
            )

        # Will add an absence period with length equal to claim
        if self.add_single_absence_period:
            self.create_absence_period()

        return self.claim

    def get_or_create_import_log(self):
        if self.fineos_extract_import_log_id is None and self.add_import_log:
            import_log = ImportLogFactory.create()
            self.import_log = import_log
            self.fineos_extract_import_log_id = import_log.import_log_id

        return self.import_log

    def _payment_factory_call(self, **overrides):
        args = (
            {
                "claim": self.claim,
                "pub_individual_id": self.pub_individual_id,
                "disb_method_id": self.payment_method.payment_method_id
                if self.payment_method
                else None,
                "period_start_date": self.period_start_date,
                "period_end_date": self.period_end_date,
                "payment_date": self.payment_date,
                "is_adhoc_payment": self.is_adhoc_payment,
                "payment_transaction_type_id": self.payment_transaction_type.payment_transaction_type_id,
                "amount": self.amount if self.amount else Decimal(0),
                "pub_eft": self.pub_eft if self.set_pub_eft_in_payment else None,
                "fineos_employee_first_name": self.employee.fineos_employee_first_name
                if self.employee
                else None,
                "fineos_employee_last_name": self.employee.fineos_employee_last_name
                if self.employee
                else None,
                "experian_address_pair": self.experian_address_pair,
                "claim_type": self.claim.claim_type if self.claim else None,
                "check": PaymentCheck(check_number=self.check_number)
                if self.check_number
                else None,
                "fineos_extraction_date": self.fineos_extraction_date,
                "fineos_extract_import_log_id": self.fineos_extract_import_log_id,
                "exclude_from_payment_status": self.exclude_from_payment_status,
                "disb_check_eft_issue_date": self.disb_check_eft_issue_date,
                "fineos_leave_request_id": self.fineos_leave_request_id,
            }
            | self.payment_optional_kwargs
            | overrides
        )
        return PaymentFactory.create(**args)

    def _create_state_call(self, payment, payment_end_state):
        state_log_util.create_finished_state_log(
            payment,
            payment_end_state,
            state_log_util.build_outcome(self.payment_end_state_message),
            self.db_session,
        )

    def get_or_create_payment(self):
        if self.payment or not self.add_payment:
            return self.payment

        self.get_or_create_import_log()
        self.get_or_create_claim()

        self.get_or_create_import_log()

        if self.add_address and self.experian_address_pair is None:
            self.experian_address_pair = ExperianAddressPairFactory.create(
                fineos_address=self.get_or_create_address()
            )

        self.payment = self._payment_factory_call()

        return self.payment

    def get_or_create_payment_with_state(self, payment_end_state):
        self.get_or_create_payment()

        if self.payment and payment_end_state:
            self._create_state_call(self.payment, payment_end_state)

        return self.payment

    def get_or_create_payment_with_writeback(
        self, writeback_transaction_status, writeback_sent_at=None
    ):
        self.get_or_create_payment()

        if self.payment and writeback_transaction_status:
            writeback_details = stage_payment_fineos_writeback(
                payment=self.payment,
                writeback_transaction_status=writeback_transaction_status,
                db_session=self.db_session,
            )
            if writeback_sent_at:
                # Move the state
                state_log_util.create_finished_state_log(
                    associated_model=self.payment,
                    end_state=State.DELEGATED_FINEOS_WRITEBACK_SENT,
                    outcome=state_log_util.build_outcome("Fake writeback send"),
                    db_session=self.db_session,
                )
                # Set the end time
                writeback_details.writeback_sent_at = writeback_sent_at

            return writeback_details

    def create_related_payment(
        self,
        weeks_later=0,
        amount=None,
        payment_transaction_type_id=None,
        import_log_id=None,
        payment_end_state=None,
        writeback_transaction_status=None,
        fineos_extraction_date=None,
        writeback_sent_at=None,
    ):
        """Roughly mimic creating another payment. Uses the original payment as a base
        with only the specified values + C/I values updated.
        """
        self.get_or_create_payment()

        if self.payment:
            delta = timedelta(days=7 * weeks_later)

            params = {
                "period_start_date": self.payment.period_start_date + delta,  # type: ignore
                "period_end_date": self.payment.period_end_date + delta,  # type: ignore
                "fineos_extraction_date": fineos_extraction_date
                if fineos_extraction_date
                else self.fineos_extraction_date,
                "amount": amount if amount is not None else self.payment.amount,
                "payment_transaction_type_id": payment_transaction_type_id
                if payment_transaction_type_id is not None
                else self.payment.payment_transaction_type_id,
                "fineos_extract_import_log_id": import_log_id
                if import_log_id is not None
                else self.payment.fineos_extract_import_log_id,
            }

            new_payment = self._payment_factory_call(**params)
            if payment_end_state:
                self._create_state_call(new_payment, payment_end_state)

            if writeback_transaction_status:
                writeback_details = stage_payment_fineos_writeback(
                    payment=new_payment,
                    writeback_transaction_status=writeback_transaction_status,
                    db_session=self.db_session,
                )
                if writeback_sent_at:
                    # Move the state
                    state_log_util.create_finished_state_log(
                        associated_model=new_payment,
                        end_state=State.DELEGATED_FINEOS_WRITEBACK_SENT,
                        outcome=state_log_util.build_outcome("Fake writeback send"),
                        db_session=self.db_session,
                    )
                    # Set the end time
                    writeback_details.writeback_sent_at = writeback_sent_at
            return new_payment

        return None

    def create_cancellation_payment(
        self, reissuing_payment=None, import_log=None, weeks_later=0, fineos_extraction_date=None
    ):
        self.get_or_create_payment()

        payment_to_reissue = reissuing_payment if reissuing_payment is not None else self.payment

        if not import_log:
            import_log = ImportLogFactory.create()

        return self.create_related_payment(
            weeks_later=weeks_later,
            amount=-payment_to_reissue.amount,
            payment_transaction_type_id=PaymentTransactionType.CANCELLATION.payment_transaction_type_id,
            import_log_id=import_log.import_log_id,
            fineos_extraction_date=fineos_extraction_date,
        )

    def create_reissued_payments(
        self,
        reissuing_payment=None,
        amount=None,
        import_log=None,
        payment_end_state=None,
        writeback_transaction_status=None,
        writeback_sent_at=None,
    ):
        """Create reissued equivalent payments.
        This will return a cancellation + new payment both with a new import log ID
        """
        self.get_or_create_payment()

        # If we call this a few times in a row, we might want to reissue
        # a different payment than the one associated with the factory
        payment_to_reissue = reissuing_payment if reissuing_payment is not None else self.payment

        if not import_log:
            import_log = ImportLogFactory.create()

        cancellation_payment = self.create_cancellation_payment(payment_to_reissue, import_log)
        successor_payment = self.create_related_payment(
            amount=amount if amount is not None else payment_to_reissue.amount,
            import_log_id=import_log.import_log_id,
            payment_end_state=payment_end_state,
            writeback_transaction_status=writeback_transaction_status,
            writeback_sent_at=writeback_sent_at,
        )

        return cancellation_payment, successor_payment

    def create_absence_period(self, **kwargs):
        claim = self.claim

        if claim:
            # Below are default params that can be overriden
            # by the kwargs. Default is to make an absence period
            # that matches the claim for similar fields
            params = {
                "claim": claim,
                "fineos_leave_request_id": self.fineos_leave_request_id,
                "absence_period_start_date": claim.absence_period_start_date,
                "absence_period_end_date": claim.absence_period_end_date,
                "is_id_proofed": claim.is_id_proofed,
                "fineos_absence_period_class_id": random_unique_int(),
                "fineos_absence_period_index_id": random_unique_int(),
            } | kwargs

            return AbsencePeriodFactory.create(**params)
        return None

    def create_payment_details(self, payment, **kwargs):
        params = {
            "payment": payment,
            "payment_id": payment.payment_id,
            "period_start_date": payment.period_start_date,
            "period_end_date": payment.period_end_date,
            "amount": payment.amount,
        } | kwargs
        return PaymentDetailsFactory.create(**params)

    def create_payment_line(self, payment, **kwargs):
        # need to add so that creating the PaymentLine in the db doesn't throw an invalid foreign key error
        vpei_payment_line_id = uuid.uuid4()
        self.db_session.add(FineosExtractVpeiPaymentLine(vpei_payment_line_id=vpei_payment_line_id))

        params = {
            "payment": payment,
            "payment_id": payment.payment_id,
            "vpei_payment_line_id": vpei_payment_line_id,
        } | kwargs
        return PaymentLineFactory.create(**params)

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

        if self.add_employer:
            self.get_or_create_employer()
