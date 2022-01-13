from datetime import date

import pytest
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from massgov.pfml.db.models.employees import State, UserLeaveAdministrator
from massgov.pfml.db.models.factories import (
    EmployerFactory,
    EmployerQuarterlyContributionFactory,
    UserFactory,
    VerificationFactory,
)
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory


def test_user_leave_admin_has_fineos_registration():
    user_leave_admin = UserLeaveAdministrator(
        user=UserFactory.build(), employer=EmployerFactory.build(),
    )
    assert user_leave_admin.has_fineos_registration is False

    user_leave_admin.fineos_web_id = "fake-fineos-web-id"
    assert user_leave_admin.has_fineos_registration is True


VERIFICATION_DATA_DATE = date(2021, 5, 1)


@freeze_time(VERIFICATION_DATA_DATE)
@pytest.mark.parametrize(
    "filing_period, amount, expect_verification_data",
    [
        (
            # Past non-zero contribution
            VERIFICATION_DATA_DATE - relativedelta(months=1),
            100,
            True,
        ),
        (
            # Past zero contribution
            VERIFICATION_DATA_DATE - relativedelta(months=1),
            0,
            False,
        ),
        (
            # Same day non-zero contribution
            VERIFICATION_DATA_DATE,
            100,
            True,
        ),
        (
            # Future non-zero contribution, with no past contributions
            VERIFICATION_DATA_DATE + relativedelta(months=1),
            100,
            True,
        ),
        (
            # Future zero contribution, with no past contributions
            VERIFICATION_DATA_DATE + relativedelta(months=1),
            0,
            False,
        ),
    ],
)
def test_employer_with_verification_data(
    filing_period, amount, expect_verification_data, initialize_factories_session
):
    employer = EmployerFactory.create()
    EmployerQuarterlyContributionFactory.create(
        employer=employer, employer_total_pfml_contribution=amount, filing_period=filing_period
    )

    assert employer.has_verification_data is expect_verification_data

    # This should be consistent with the above
    if employer.has_verification_data:
        assert employer.verification_data is not None
    else:
        assert employer.verification_data is None


def test_user_leave_admin_verified():
    user_leave_admin = UserLeaveAdministrator(
        user=UserFactory.build(), employer=EmployerFactory.build(),
    )
    assert user_leave_admin.verified is False

    user_leave_admin.verification_id = VerificationFactory.build().verification_id
    assert user_leave_admin.verified is True


def test_claim_has_paid_payments_returns_true_when_payments_exist(
    test_db_session, initialize_factories_session
):
    payment_factory = DelegatedPaymentFactory(test_db_session)
    claim = payment_factory.get_or_create_claim()
    assert claim.has_paid_payments is False
    payment_factory.get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT
    )

    assert claim.has_paid_payments is True


def test_claim_has_paid_payments_returns_false_when_payments_exist_not_in_paid_state(
    test_db_session, initialize_factories_session
):
    payment_factory = DelegatedPaymentFactory(test_db_session)
    claim = payment_factory.get_or_create_claim()
    assert claim.has_paid_payments is False

    payment_factory.get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT
    )
    assert claim.has_paid_payments is True

    # Test that the property updates with state changes
    payment_factory.get_or_create_payment_with_state(State.DELEGATED_PAYMENT_ERROR_FROM_BANK)
    assert claim.has_paid_payments is False
