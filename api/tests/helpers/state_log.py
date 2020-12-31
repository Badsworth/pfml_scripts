from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional, Union

from freezegun import freeze_time

import massgov.pfml.api.util.state_log_util as state_log_util
from massgov.pfml.db.models.employees import Employee, Payment, StateLog
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
    PaymentFactory,
    ReferenceFileFactory,
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
    add_claim_payment_for_employee: bool = False


# Utility method for creating state logs
def setup_state_log(
    associated_class, start_states, end_states, test_db_session, additional_params=None,
):
    if not additional_params:
        additional_params = AdditionalParams()
    if associated_class == state_log_util.AssociatedClass.EMPLOYEE:
        associated_model = EmployeeFactory.create(
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

    if associated_class == state_log_util.AssociatedClass.PAYMENT:
        employee = EmployeeFactory.create(
            fineos_customer_number=additional_params.fineos_customer_num,
            ctr_vendor_customer_code=additional_params.ctr_vendor_customer_code,
        )
        employer = EmployerFactory.create()
        claim = ClaimFactory.create(
            employer_id=employer.employer_id,
            fineos_absence_id=additional_params.fineos_absence_id,
            employee=employee,
        )
        associated_model = PaymentFactory.create(payment_date=date(2020, 1, 7), claim=claim)
    if associated_class == state_log_util.AssociatedClass.REFERENCE_FILE:
        associated_model = ReferenceFileFactory.create()

    state_logs = []

    for index, start_state in enumerate(start_states):
        end_state = end_states[index]

        with freeze_time(f"2020-01-0{index + 1} 00:00:00"):
            state_log = state_log_util.create_state_log(
                start_state=start_state,
                associated_model=associated_model,
                db_session=test_db_session,
            )
            if end_state:
                state_log_util.finish_state_log(
                    state_log=state_log,
                    end_state=end_state,
                    outcome=additional_params.outcome,
                    db_session=test_db_session,
                )

            state_logs.append(state_log)

    test_db_session.flush()
    test_db_session.commit()
    return StateLogSetupResult(state_logs=state_logs, associated_model=associated_model)
