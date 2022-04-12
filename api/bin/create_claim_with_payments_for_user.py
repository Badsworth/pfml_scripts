#!/usr/bin/env python3
#
# Generate a user, claim, and set of payments
#
# Run via `make create-claim-with-payments-for-user`.
# View options: `make create-claim-with-payments-for-user args="--help"`
#
from datetime import date, timedelta
from decimal import Decimal
from typing import List

import click
from factory.faker import faker

import massgov.pfml.db as db
from massgov.pfml.db.models.employees import PaymentMethod, PaymentTransactionType, Role, State
from massgov.pfml.db.models.factories import ApplicationFactory, ClaimFactory, UserFactory
from massgov.pfml.db.models.payments import FineosWritebackDetails, FineosWritebackTransactionStatus
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory
from massgov.pfml.util.datetime import to_datetime

fake = faker.Faker()
# State log logic doesn't like being on a separate
# DB session, so make the factories share the session
# we are making here.
db_session = db.init(sync_lookups=True)
db.models.factories.db_session = db_session

ALLOWED_SCENARIOS = [
    "paid",
    "posted",
    "pending",
    "extra_payment_in_period",
    "successor",
    "cancelled",
    "zero_dollar",
    "long_period",
    "delayed_prenote",
    "delayed_reduction",
    "delayed_other",
]


def format_payment(payment, scenario):
    return f"{payment.payment_id} i={payment.fineos_pei_i_value} [{payment.period_start_date} - {payment.period_end_date}] for scenario {scenario}"


@click.command()
@click.option(
    "--total_payments", default=len(ALLOWED_SCENARIOS), help="Number of payments to create."
)
@click.option(
    "--scenarios", type=click.Choice(ALLOWED_SCENARIOS), default=ALLOWED_SCENARIOS, multiple=True
)
def main(total_payments: int, scenarios: List[str]) -> None:
    user = UserFactory.create(consented_to_data_sharing=True, roles=[Role.USER])

    claim = ClaimFactory.create(fineos_absence_id=f"NTN-{fake.unique.random_int()}-ABS-01")

    application = ApplicationFactory.create(claim=claim, user=user)

    click.secho(
        f"Created Claim {claim.claim_id} - {claim.fineos_absence_id} attached to application {application.application_id}",
        fg="yellow",
    )

    # Make payments that occur 7 days apart to simulate a real claim
    # This creates a series of payments setup to showcase
    # a variety of scenarios in the payment status API
    start_date = date(2021, 8, 1)
    for i in range(total_payments):
        # Determine which scenario we are doing
        scenario = scenarios[i % len(scenarios)]

        # Default values that can be overriden by scenarios below.
        transaction_status = FineosWritebackTransactionStatus.PAID
        payment_state = State.DELEGATED_PAYMENT_COMPLETE
        start_date = start_date + timedelta(days=7)
        end_date = start_date + timedelta(days=6)
        end_datetime = to_datetime(end_date)
        amount = Decimal("500.23")
        payment_transaction_type = PaymentTransactionType.STANDARD

        if scenario == "long_period":
            # This will overlap with later payments
            end_date = start_date + timedelta(days=30)

        if scenario == "zero_dollar":
            amount = Decimal("0.00")
            payment_transaction_type = PaymentTransactionType.ZERO_DOLLAR

        # Create the base payment
        factory = DelegatedPaymentFactory(
            db_session,
            claim=claim,
            employee=claim.employee,
            add_employer=False,
            period_start_date=start_date,
            period_end_date=end_date,
            payment_date=end_date,
            fineos_extraction_date=end_date,
            payment_method=PaymentMethod.ACH,
            amount=amount,
            payment_transaction_type=payment_transaction_type,
            set_pub_eft_in_payment=True,
            prenote_sent_at=date.today(),
        )
        payment = factory.get_or_create_payment()

        click.secho(f"Created Payment {format_payment(payment, scenario)}", fg="cyan")

        if scenario == "paid":
            payment_detail = factory.create_payment_detail()
            factory.create_payment_line(payment_detail=payment_detail)

        # Scenarios that add additional information
        if scenario == "posted":
            # Create a paid writeback status set to the prior day
            prior_day_datetime = to_datetime(end_date - timedelta(days=1))
            writeback_details = FineosWritebackDetails(
                payment=payment,
                transaction_status_id=FineosWritebackTransactionStatus.PAID.transaction_status_id,
                writeback_sent_at=prior_day_datetime,
                created_at=prior_day_datetime,
            )
            db_session.add(writeback_details)

            transaction_status = FineosWritebackTransactionStatus.POSTED

        elif scenario == "extra_payment_in_period":
            # Add an extra payment
            additional_payment = factory.create_related_payment(
                payment_end_state=State.DELEGATED_PAYMENT_COMPLETE,
                writeback_transaction_status=transaction_status,
                amount=Decimal("12.34"),
                writeback_sent_at=end_datetime,
            )

            click.secho(
                f"Created Additional Payment {format_payment(additional_payment, scenario)}",
                fg="bright_cyan",
            )

        elif scenario == "successor":
            # Reissue the payment (cancellation + new payment)
            cancellation_payment, successor_payment = factory.create_reissued_payments(
                payment_end_state=State.DELEGATED_PAYMENT_COMPLETE,
                writeback_transaction_status=transaction_status,
                writeback_sent_at=end_datetime,
            )
            click.secho(
                f"Created cancellation {format_payment(cancellation_payment, scenario)}",
                fg="bright_cyan",
            )

            click.secho(
                f"Created successor {format_payment(successor_payment, scenario)}", fg="bright_cyan"
            )

        elif scenario == "cancelled":
            cancellation_payment = factory.create_cancellation_payment(
                fineos_extraction_date=end_date + timedelta(days=1)
            )
            click.secho(
                f"Created cancellation {format_payment(cancellation_payment, scenario)}",
                fg="bright_cyan",
            )

        elif scenario == "delayed_prenote":
            transaction_status = FineosWritebackTransactionStatus.PENDING_PRENOTE

        elif scenario == "delayed_reduction":
            transaction_status = FineosWritebackTransactionStatus.DIA_ADDITIONAL_INCOME

        elif scenario == "delayed_other":
            transaction_status = FineosWritebackTransactionStatus.DATA_ISSUE_IN_SYSTEM

        # Pending payments have no writeback status
        if scenario != "pending":
            factory.get_or_create_payment_with_writeback(
                transaction_status, writeback_sent_at=end_datetime
            )

        factory.get_or_create_payment_with_state(payment_state)

    db_session.commit()
    click.secho(f"Created User {user.user_id}", fg="yellow")
    click.secho(
        f"You can create a JWT for this user by running `make jwt auth_id={user.sub_id}`",
        fg="green",
    )


if __name__ == "__main__":
    main()
