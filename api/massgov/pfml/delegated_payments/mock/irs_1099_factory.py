from typing import Any, Optional

import faker
import massgov.pfml.db as db
from massgov.pfml.db.models.factories import (
    Pfml1099BatchFactory,
    Pfml1099FederalWithholdingFactory,
    Pfml1099MMARSPaymentFactory,
    Pfml1099PaymentFactory,
    Pfml1099RefundFactory,
    Pfml1099StateWithholdingFactory,
    Pfml1099Factory as Pfml1099ItemFactory
)
from massgov.pfml.db.models.payments import (
    Pfml1099Batch,
    Pfml1099MMARSPayment,
    Pfml1099Payment,
    Pfml1099Refund,
    Pfml1099Withholding,
    Pfml1099,
)
from massgov.pfml.delegated_payments.mock.mock_util import MockData


fake = faker.Faker()
fake.seed_instance(2394)

KWARG_VALUE_NOT_SET = "KWARG_VALUE_NOT_SET"


class Pfml1099Factory(MockData):
    def __init__(
        self,
        db_session: db.Session,
        generate_defaults: bool = True,
        batch: Optional[Pfml1099Batch] = None,
        mmars_payment: Optional[Pfml1099MMARSPayment] = None,
        payment: Optional[Pfml1099Payment] = None,
        refund: Optional[Pfml1099Refund] = None,
        state_withholding: Optional[Pfml1099Withholding] = None,
        federal_withholding: Optional[Pfml1099Withholding] = None,
        add_batch: bool = True,
        add_mmars_payment: bool = True,
        add_payment: bool = True,
        add_refund: bool = True,
        add_state_withholding: bool = True,
        add_federal_withholding: bool = True,
        pfml_1099: Optional[Pfml1099] = None,
        **kwargs: Any,
    ):
        super().__init__(generate_defaults, **kwargs)

        self.db_session = db_session

        self.batch = batch
        self.mmars_payment = mmars_payment
        self.payment = payment
        self.refund = refund
        self.state_withholding = state_withholding
        self.federal_withholding = federal_withholding
        self.add_batch = add_batch
        self.add_mmars_payment = add_mmars_payment
        self.add_payment = add_payment
        self.add_refund = add_refund
        self.add_state_withholding = add_state_withholding
        self.add_federal_withholding = add_federal_withholding
        self.pfml_1099 = pfml_1099

    # only set if value was passed in constructor through kwarg
    # else defer to lazy factory initialization
    def set_optional_kwargs(self, kwargs_map, key, value):
        if value != KWARG_VALUE_NOT_SET:
            kwargs_map[key] = value

    def get_or_create_batch(self):
        if self.batch is None:
            self.batch = Pfml1099BatchFactory()

        return self.batch

    def get_or_create_mmars_payment(self):
        if not self.add_mmars_payment or self.mmars_payment is not None:
            return self.mmars_payment

        self.get_or_create_batch()

        mmars_payment = Pfml1099MMARSPaymentFactory.create(batch=self.batch)

        self.mmars_payment = mmars_payment
        return self.mmars_payment

    def get_or_create_payment(self):
        if not self.add_payment or self.payment is not None:
            return self.payment

        self.get_or_create_batch()

        payment = Pfml1099PaymentFactory.create(batch=self.batch)

        self.payment = payment
        return self.payment

    def get_or_create_refund(self):
        if self.refund is None:
            self.refund = Pfml1099RefundFactory()

        return self.refund

    def get_or_create_state_withholding(self):
        if self.state_withholding is None:
            self.state_withholding = Pfml1099StateWithholdingFactory()

        return self.state_withholding

    def get_or_create_federal_withholding(self):
        if self.federal_withholding is None:
            self.federal_withholding = Pfml1099FederalWithholdingFactory()

        return self.federal_withholding

    def create_all(self):
        if self.add_batch:
            self.get_or_create_batch()

        if self.add_mmars_payment:
            self.get_or_create_mmars_payment()

        if self.add_payment:
            self.get_or_create_payment()

        if self.add_refund:
            self.get_or_create_refund()

        if self.add_state_withholding:
            self.get_or_create_state_withholding()

        if self.add_federal_withholding:
            self.get_or_create_federal_withholding()

    def get_or_create_pfml_1099(self):
        if self.pfml_1099 is not None:
            return self.pfml_1099

        self.get_or_create_batch()
        
        self.pfml_1099 = Pfml1099ItemFactory() #.create(pfml_1099_batch_id = self.batch.pfml_1099_batch_id)

        return self.pfml_1099