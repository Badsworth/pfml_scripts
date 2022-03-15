import math
import random
from datetime import date, timedelta
from typing import List, NamedTuple, Optional, Tuple

from massgov.pfml.db.models.absences import AbsencePeriodType, AbsenceStatus
from massgov.pfml.db.models.employees import (
    BenefitYear,
    Claim,
    Employee,
    Employer,
    PaymentTransactionType,
    SharedPaymentConstants,
    State,
)
from massgov.pfml.db.models.factories import (
    AbsencePeriodFactory,
    ClaimFactory,
    EmployerFactory,
    PaymentDetailsFactory,
)
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_util import (
    PaymentContainer,
)


def _create_payment_periods(payment, total_amount, start_date, periods, length_of_period):
    amount_per_period = total_amount / periods

    payment_periods = []
    for _ in range(periods):
        end_date = start_date + timedelta(length_of_period - 1)

        payment_period = PaymentDetailsFactory.create(
            payment=payment,
            business_net_amount=amount_per_period,
            period_start_date=start_date,
            period_end_date=end_date,
            amount=100000,
        )
        payment_periods.append(payment_period)

        # Increment after as it starts on the first period's day
        start_date = start_date + timedelta(length_of_period)

    return payment_periods


def _create_absence_periods(
    claim, fineos_leave_request_id, absence_period_start_date=None, count=1, length_of_period=30
):
    if not absence_period_start_date:
        absence_period_start_date = claim.absence_period_start_date

    absence_periods = []
    for _ in range(count):
        absence_period_end_date = absence_period_start_date + timedelta(length_of_period - 1)

        absence_period = AbsencePeriodFactory.create(
            claim_id=claim,
            claim=claim,
            absence_period_start_date=absence_period_start_date,
            absence_period_end_date=absence_period_end_date,
            fineos_leave_request_id=fineos_leave_request_id,
        )
        absence_periods.append(absence_period)

    return absence_periods


def _create_payment_container(
    employee,
    amount,
    db_session,
    start_date=None,
    periods=1,
    length_of_period=7,
    skip_pay_periods=False,
    has_processed_state=False,
    has_errored_state=False,
    is_adhoc_payment=False,
    is_overpayment=False,
    is_ready_for_max_weekly_benefit_validation=False,
    later_failed=False,
    payment_transaction_type=PaymentTransactionType.STANDARD,
    claim=None,
    add_single_absence_period=True,
):

    if not start_date:
        # We use this day because it's a Sunday that starts on the 1st so easier to conceptualize
        start_date = date(2021, 8, 1)

    end_date = start_date + timedelta((periods * length_of_period) - 1)

    factory = DelegatedPaymentFactory(
        db_session,
        employee=employee,
        claim=claim,
        payment_transaction_type=payment_transaction_type,
        amount=amount,
        period_start_date=start_date,
        period_end_date=end_date,
        is_adhoc_payment=is_adhoc_payment,
        payment_transaction_type_id=payment_transaction_type.payment_transaction_type_id,
        fineos_employee_first_name=employee.first_name,
        fineos_employee_last_name=employee.last_name,
        add_single_absence_period=add_single_absence_period,
    )
    payment = factory.get_or_create_payment()

    if not skip_pay_periods:
        _create_payment_periods(payment, amount, start_date, periods, length_of_period)

    if has_processed_state:
        state = random.choice(list(SharedPaymentConstants.PAID_STATES))
    elif has_errored_state:
        state = State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT
    elif is_overpayment:
        state = State.DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT
    elif is_ready_for_max_weekly_benefit_validation:
        state = State.PAYMENT_READY_FOR_MAX_WEEKLY_BENEFIT_AMOUNT_VALIDATION
    else:
        state = State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK

    factory.get_or_create_payment_with_state(state)

    # To represent a payment that succeeded and then failed with the bank
    if has_processed_state and later_failed:
        factory.get_or_create_payment_with_state(State.DELEGATED_PAYMENT_ERROR_FROM_BANK)

    return PaymentContainer(payment)


class AbsenceConfig(NamedTuple):
    absence_period_start_date: date
    leave_duration: int
    fineos_absence_status: Optional[AbsenceStatus] = None
    absence_period_type: Optional[AbsencePeriodType] = None


def _create_absence_data(
    employee: Employee,
    absence_data: List[AbsenceConfig],
    use_employer: Optional[Employer] = None,
    fineos_absence_status: Optional[AbsenceStatus] = AbsenceStatus.APPROVED,
    absence_period_type: Optional[AbsencePeriodType] = AbsencePeriodType.CONTINUOUS,
) -> Tuple[Employer, list[Claim], int]:
    employer: Employer = use_employer if use_employer else EmployerFactory.create()
    claims: List[Claim] = []
    absence_data_sorted = sorted(
        list(map(lambda x: AbsenceConfig(*x), absence_data)),
        key=lambda x: x.absence_period_start_date,
    )
    leave_duration_total = 0
    for x in absence_data_sorted:
        fineos_absence_status = (
            x.fineos_absence_status if x.fineos_absence_status else fineos_absence_status
        )
        absence_period_type = (
            x.absence_period_type if x.fineos_absence_status else absence_period_type
        )
        absence_period_end_date = x.absence_period_start_date + timedelta(days=x.leave_duration - 1)
        claim = ClaimFactory.create(
            fineos_absence_status_id=fineos_absence_status.absence_status_id,
            absence_period_start_date=x.absence_period_start_date,
            absence_period_end_date=absence_period_end_date,
            employee=employee,
            employer=employer,
        )
        AbsencePeriodFactory.create(
            claim=claim,
            absence_period_start_date=x.absence_period_start_date,
            absence_period_end_date=absence_period_end_date,
            absence_period_type_id=absence_period_type.absence_period_type_id,
        )
        claims.append(claim)
        leave_duration_total += (absence_period_end_date - x.absence_period_start_date).days + 1

    return employer, claims, leave_duration_total


def _create_absence_periods_data(
    benefit_year: BenefitYear, total_leave_duration: int, absences: Optional[int] = 1, **kwargs
):
    start_date = benefit_year.start_date
    absence_data: List[AbsenceConfig] = []
    # total_leave_duration = max(total_leave_duration - 1, 0)
    remaining = total_leave_duration
    for i in range(absences):
        days_in_absence = math.ceil(remaining / (absences - i))
        absence_data.append((start_date + timedelta(days=days_in_absence * i), days_in_absence))
        remaining -= days_in_absence
    return _create_absence_data(benefit_year.employee, absence_data, **kwargs)
