from datetime import date
from decimal import Decimal

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.postprocessing.payment_post_processing_util as payment_post_processing_util
from massgov.pfml.db.models.employees import PaymentTransactionType, State
from massgov.pfml.db.models.factories import EmployeeFactory

from . import _create_payment_container


def test_get_all_paid_payments_associated_with_employee(
    local_test_db_session, local_initialize_factories_session
):
    # This test shows what does and doesn't get fetched by the method

    employee = EmployeeFactory.create()
    # New payment being processed
    payment_container = _create_payment_container(
        employee, Decimal("225.00"), local_test_db_session
    )

    # A previously sent-to-pub payment (will be found)
    payment_sent_to_pub_container = _create_payment_container(
        employee, Decimal("800.00"), local_test_db_session, has_processed_state=True
    )

    # A payment we have received payment confirmation from PUB (will be found)
    payment_success_with_pub_container = _create_payment_container(
        employee, Decimal("800.00"), local_test_db_session, has_processed_state=True
    )
    state_log_util.create_finished_state_log(
        payment_success_with_pub_container.payment,
        State.DELEGATED_PAYMENT_COMPLETE,
        state_log_util.build_outcome("MESSAGE"),
        local_test_db_session,
    )

    # A payment we have received a change notifications/successful payment with PUB (will be found)
    payment_change_notification_with_pub_container = _create_payment_container(
        employee, Decimal("800.00"), local_test_db_session, has_processed_state=True
    )
    state_log_util.create_finished_state_log(
        payment_change_notification_with_pub_container.payment,
        State.DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION,
        state_log_util.build_outcome("MESSAGE"),
        local_test_db_session,
    )

    # Another payment in the same state (won't be found)
    _create_payment_container(employee, Decimal("100.00"), local_test_db_session)

    # A previously errored payment (won't be found)
    _create_payment_container(
        employee, Decimal("100.00"), local_test_db_session, has_errored_state=True
    )

    # An adhoc payment in a success state (won't be found)
    _create_payment_container(
        employee,
        Decimal("100.00"),
        local_test_db_session,
        has_processed_state=True,
        is_adhoc_payment=True,
    )

    # Not technically possible, but an overpayment in the success state (won't be found)
    _create_payment_container(
        employee,
        Decimal("100.00"),
        local_test_db_session,
        has_processed_state=True,
        payment_transaction_type=PaymentTransactionType.OVERPAYMENT,
    )

    # A payment that succeeded then failed (won't be found)
    _create_payment_container(
        employee,
        Decimal("100.00"),
        local_test_db_session,
        has_processed_state=True,
        later_failed=True,
    )

    # A payment from another employee (won't be found)
    employee2 = EmployeeFactory.create()
    _create_payment_container(
        employee2, Decimal("800.00"), local_test_db_session, has_processed_state=True
    )

    active_payments = payment_post_processing_util.get_all_paid_payments_associated_with_employee(
        employee.employee_id, [payment_container.payment.payment_id], local_test_db_session
    )
    assert len(active_payments) == 3
    assert set([active_payment.payment.payment_id for active_payment in active_payments]) == set(
        [
            payment_sent_to_pub_container.payment.payment_id,
            payment_success_with_pub_container.payment.payment_id,
            payment_change_notification_with_pub_container.payment.payment_id,
        ]
    )


def test_max_weekly_audit_builder(local_test_db_session, local_initialize_factories_session):
    start_date = date(2021, 8, 1)
    end_date = date(2021, 8, 7)
    employee = EmployeeFactory.create()

    # Create a pay period group
    pay_period_group = payment_post_processing_util.PayPeriodGroup(
        start_date=start_date, end_date=end_date
    )
    pay_period_group.maximum_weekly_amount = Decimal("850.00")

    # The payment that failed validation which is unpayable
    errored_payment_container = _create_payment_container(
        employee, Decimal("225.00"), local_test_db_session, start_date=start_date, periods=1
    )
    errored_payment = errored_payment_container.payment
    errored_payment_container.pay_periods_over_cap = [
        (pay_period_group, errored_payment.payment_details[0])
    ]
    errored_payment_container.payment_distribution = {
        pay_period_group: errored_payment.payment_details[0]
    }
    pay_period_group.add_payment_from_details(
        errored_payment.payment_details[0],
        payment_post_processing_util.PaymentScenario.UNPAYABLE_PAYMENT,
    )

    # Previous payment for the pay period
    prior_payment_container = _create_payment_container(
        employee,
        Decimal("500.00"),
        local_test_db_session,
        start_date=start_date,
        periods=1,
        has_processed_state=True,
    )
    prior_payment = prior_payment_container.payment
    pay_period_group.add_payment_from_details(
        prior_payment.payment_details[0],
        payment_post_processing_util.PaymentScenario.PREVIOUS_PAYMENT,
    )

    # Current payable payment for the period (In same claim as prior payment)
    additional_current_payment_container = _create_payment_container(
        employee,
        Decimal("250.00"),
        local_test_db_session,
        start_date=start_date,
        periods=1,
        has_processed_state=True,
        claim=prior_payment.claim,
    )
    additional_current_payment = additional_current_payment_container.payment
    pay_period_group.add_payment_from_details(
        additional_current_payment.payment_details[0],
        payment_post_processing_util.PaymentScenario.CURRENT_PAYABLE_PAYMENT,
    )

    builder = payment_post_processing_util.MaximumWeeklyBenefitsAuditMessageBuilder(
        errored_payment_container
    )
    msg = builder.build_complex_msg()

    # Verify the msg was constructed properly
    assert msg == "\n".join(
        [
            f"This payment for {payment_post_processing_util.make_payment_log(errored_payment, True)} exceeded the maximum amount allowable for a 7-day period.",
            "",
            f"The payment overlapped with the following other claim(s): {prior_payment.claim.fineos_absence_id}",
            "",
            "It exceeded the cap for the following weeks + pay periods:",
            "-" * 50,
            f"{pay_period_group}: Amount already paid=$750.00; AmountAvailable=$100.00",
            "",
            "Previous Payments ($500.00 total):",
            f"{payment_post_processing_util.make_payment_log(prior_payment)} with the following relevant pay periods:",
            f"\t{payment_post_processing_util.make_payment_detail_log(prior_payment.payment_details[0])}",
            "",
            "Current Payable Payments ($250.00 total):",
            f"{payment_post_processing_util.make_payment_log(additional_current_payment)} with the following relevant pay periods:",
            f"\t{payment_post_processing_util.make_payment_detail_log(additional_current_payment.payment_details[0])}",
            "",
            "Unpayable Payments ($225.00 total):",
            f"{payment_post_processing_util.make_payment_log(errored_payment)} with the following relevant pay periods:",
            f"\t{payment_post_processing_util.make_payment_detail_log(errored_payment.payment_details[0])} is over the cap by $125.00",
            "",
        ]
    )

    # Verify the simple msg for the audit log was also built right
    msg = builder.build_simple_msg()
    assert msg == "\n".join(
        [
            f"The payment overlapped with the following other claim(s): {prior_payment.claim.fineos_absence_id}",
            "",
            "It exceeded the cap for the following weeks + pay periods:",
            "-" * 50,
            f"{pay_period_group}: Amount already paid=$750.00; AmountAvailable=$100.00; Over the cap by $125.00",
            "",
        ]
    )


def test_max_weekly_audit_builder_multiple_pay_periods(
    local_test_db_session, local_initialize_factories_session
):
    # Create 2 sequential pay period groups
    start_date1 = date(2021, 8, 1)
    end_date1 = date(2021, 8, 7)

    pay_period_group1 = payment_post_processing_util.PayPeriodGroup(
        start_date=start_date1, end_date=end_date1
    )
    pay_period_group1.maximum_weekly_amount = Decimal("850.00")

    start_date2 = date(2021, 8, 8)
    end_date2 = date(2021, 8, 14)

    pay_period_group2 = payment_post_processing_util.PayPeriodGroup(
        start_date=start_date2, end_date=end_date2
    )
    pay_period_group2.maximum_weekly_amount = Decimal("850.00")

    employee = EmployeeFactory.create()

    # This errored payment will have two pay periods, $250 in each week
    # Week 1 will have no overlap and not require a reduction
    # Week 2 will overlap with a payment that fills the week
    errored_payment_container = _create_payment_container(
        employee, Decimal("500.00"), local_test_db_session, start_date=start_date1, periods=2
    )
    errored_payment = errored_payment_container.payment
    errored_payment_container.pay_periods_over_cap = [
        (pay_period_group2, errored_payment.payment_details[1])
    ]
    errored_payment_container.payment_distribution = {
        pay_period_group1: errored_payment.payment_details[0],
        pay_period_group2: errored_payment.payment_details[1],
    }
    pay_period_group1.add_payment_from_details(
        errored_payment.payment_details[0],
        payment_post_processing_util.PaymentScenario.UNPAYABLE_PAYMENT,
    )
    pay_period_group2.add_payment_from_details(
        errored_payment.payment_details[1],
        payment_post_processing_util.PaymentScenario.UNPAYABLE_PAYMENT,
    )

    # Previous payment for the second pay period
    prior_payment_container = _create_payment_container(
        employee,
        Decimal("850.00"),
        local_test_db_session,
        start_date=start_date2,
        periods=1,
        has_processed_state=True,
    )
    prior_payment = prior_payment_container.payment
    pay_period_group2.add_payment_from_details(
        prior_payment.payment_details[0],
        payment_post_processing_util.PaymentScenario.PREVIOUS_PAYMENT,
    )

    builder = payment_post_processing_util.MaximumWeeklyBenefitsAuditMessageBuilder(
        errored_payment_container
    )
    msg = builder.build_complex_msg()

    # Verify the msg was constructed properly
    assert msg == "\n".join(
        [
            f"This payment for {payment_post_processing_util.make_payment_log(errored_payment, True)} exceeded the maximum amount allowable for a 7-day period.",
            "",
            f"The payment overlapped with the following other claim(s): {prior_payment.claim.fineos_absence_id}",
            "",
            "It exceeded the cap for the following weeks + pay periods:",
            "-" * 50,
            f"{pay_period_group1}: Amount already paid=$0.00; AmountAvailable=$850.00",
            "",
            "Unpayable Payments ($250.00 total):",
            f"{payment_post_processing_util.make_payment_log(errored_payment)} with the following relevant pay periods:",
            f"\t{payment_post_processing_util.make_payment_detail_log(errored_payment.payment_details[0])} does not require a reduction for this pay period.",
            "",
            "-" * 50,
            f"{pay_period_group2}: Amount already paid=$850.00; AmountAvailable=$0.00",
            "",
            "Previous Payments ($850.00 total):",
            f"{payment_post_processing_util.make_payment_log(prior_payment)} with the following relevant pay periods:",
            f"\t{payment_post_processing_util.make_payment_detail_log(prior_payment.payment_details[0])}",
            "",
            "Unpayable Payments ($250.00 total):",
            f"{payment_post_processing_util.make_payment_log(errored_payment)} with the following relevant pay periods:",
            f"\t{payment_post_processing_util.make_payment_detail_log(errored_payment.payment_details[1])} is over the cap by $250.00",
            "",
        ]
    )

    # Verify the simple msg for the audit log was also built right
    # note that only pay periods over the cap are written out
    msg = builder.build_simple_msg()
    assert msg == "\n".join(
        [
            f"The payment overlapped with the following other claim(s): {prior_payment.claim.fineos_absence_id}",
            "",
            "It exceeded the cap for the following weeks + pay periods:",
            "-" * 50,
            f"{pay_period_group2}: Amount already paid=$850.00; AmountAvailable=$0.00; Over the cap by $250.00",
            "",
        ]
    )


def test_max_weekly_audit_builder_no_info(
    local_test_db_session, local_initialize_factories_session
):
    # Verify that in the unlikely scenario that we somehow
    # end up in the message builder without any pay period
    # info, the builder won't fail
    employee = EmployeeFactory.create()
    payment_container = _create_payment_container(
        employee, Decimal("225.00"), local_test_db_session
    )
    builder = payment_post_processing_util.MaximumWeeklyBenefitsAuditMessageBuilder(
        payment_container
    )
    msg = builder.build_complex_msg()

    # Verify the msg was constructed
    # with the payment info, but the other sections blank
    payment = payment_container.payment

    assert msg == "\n".join(
        [
            f"This payment for [C={payment.fineos_pei_c_value},I={payment.fineos_pei_i_value},AbsenceCaseId={payment.claim.fineos_absence_id},Amount={payment.amount}] exceeded the maximum amount allowable for a 7-day period.",
            "",
            "The payment overlapped with the following other claim(s): ",
            "",
            "It exceeded the cap for the following weeks + pay periods:",
        ]
    )

    # Verify the simple msg for the audit log was also built right
    msg = builder.build_simple_msg()
    assert msg == "\n".join(
        [
            "The payment overlapped with the following other claim(s): ",
            "",
            "It exceeded the cap for the following weeks + pay periods:",
        ]
    )
