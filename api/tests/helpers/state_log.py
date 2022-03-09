from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional, Union

import factory  # this is from the factory_boy package
from freezegun import freeze_time

import massgov.pfml.api.util.state_log_util as state_log_util
from massgov.pfml.db.models.employees import (
    ClaimType,
    Employee,
    Payment,
    PaymentMethod,
    PrenoteState,
    StateLog,
    TaxIdentifier,
)
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EftFactory,
    EmployeeFactory,
    EmployeePubEftPairFactory,
    EmployerFactory,
    PaymentFactory,
    PubEftFactory,
    ReferenceFileFactory,
    TaxIdentifierFactory,
)


# Container class for returning the created values for tests
@dataclass
class StateLogSetupResult:
    state_logs: List[StateLog]
    associated_model: Union[Employee, Payment]


def default_outcome() -> Dict[str, Any]:
    return state_log_util.build_outcome("success")


@dataclass
class AdditionalParams:
    # Container class for additional params (really it's just fancy kwargs)
    outcome: Dict[str, Any] = field(default_factory=default_outcome)
    fineos_customer_num: Optional[str] = None
    fineos_absence_id: Optional[str] = None
    ctr_vendor_customer_code: Optional[str] = None
    tax_identifier: Optional[TaxIdentifier] = factory.SubFactory(TaxIdentifierFactory)
    add_claim_payment_for_employee: bool = False
    payment: Optional[Payment] = None
    add_eft: bool = False
    add_pub_eft: bool = False


def setup_db_for_state_log(associated_class, additional_params=None):
    if not additional_params:
        additional_params = AdditionalParams()
    if associated_class == state_log_util.AssociatedClass.EMPLOYEE:
        associated_model = EmployeeFactory.create(
            tax_identifier=additional_params.tax_identifier,
            fineos_customer_number=additional_params.fineos_customer_num,
            ctr_vendor_customer_code=additional_params.ctr_vendor_customer_code,
        )
        if additional_params.add_claim_payment_for_employee:
            employer = EmployerFactory.create()
            claim = ClaimFactory.create(
                employer_id=employer.employer_id,
                fineos_absence_id=additional_params.fineos_absence_id,
                employee=associated_model,
            )
            PaymentFactory.create(payment_date=date(2020, 1, 7), claim=claim)
        if additional_params.add_eft:
            eft = EftFactory.create()
            associated_model.eft = eft
            associated_model.payment_method_id = PaymentMethod.ACH.payment_method_id

    if associated_class == state_log_util.AssociatedClass.PAYMENT:
        employee = EmployeeFactory.create(
            tax_identifier=additional_params.tax_identifier,
            fineos_customer_number=additional_params.fineos_customer_num,
            ctr_vendor_customer_code=additional_params.ctr_vendor_customer_code,
        )

        if additional_params.add_eft:
            eft = EftFactory.create()
            employee.eft = eft
            employee.payment_method_id = PaymentMethod.ACH.payment_method_id

        employer = EmployerFactory.create()
        claim = ClaimFactory.create(
            employer_id=employer.employer_id,
            fineos_absence_id=additional_params.fineos_absence_id,
            claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
            employee=employee,
        )
        if additional_params.payment:
            associated_model = additional_params.payment
        else:
            associated_model = PaymentFactory.create(
                payment_date=date(2020, 1, 7),
                disb_method_id=PaymentMethod.ACH.payment_method_id,
                claim=claim,
            )

        if additional_params.add_pub_eft:
            pub_eft = PubEftFactory.build(prenote_state_id=PrenoteState.APPROVED.prenote_state_id)
            print(pub_eft.bank_account_type_id)

            EmployeePubEftPairFactory.build(employee=employee, pub_eft=pub_eft)
            associated_model.pub_eft = pub_eft
            associated_model.payment_method_id = PaymentMethod.ACH.payment_method_id

    if associated_class == state_log_util.AssociatedClass.REFERENCE_FILE:
        associated_model = ReferenceFileFactory.create()
    return associated_model


# Utility method for creating state logs
def setup_state_log(associated_class, end_states, test_db_session, additional_params=None):
    associated_model = setup_db_for_state_log(associated_class, additional_params)

    state_logs = []
    outcome = additional_params.outcome if additional_params and additional_params.outcome else {}

    for index, end_state in enumerate(end_states):

        with freeze_time(f"2020-01-0{index + 1} 00:00:00"):
            state_log = state_log_util.create_finished_state_log(
                end_state=end_state,
                outcome=outcome,
                associated_model=associated_model,
                db_session=test_db_session,
            )

            state_logs.append(state_log)

    test_db_session.flush()
    test_db_session.commit()
    return StateLogSetupResult(state_logs=state_logs, associated_model=associated_model)


def setup_state_log_only(*, associated_model, end_state, now, test_db_session):
    with freeze_time(now):
        state_log = state_log_util.create_finished_state_log(
            end_state=end_state,
            outcome={},
            associated_model=associated_model,
            db_session=test_db_session,
        )
    test_db_session.flush()
    test_db_session.commit()
    return state_log
