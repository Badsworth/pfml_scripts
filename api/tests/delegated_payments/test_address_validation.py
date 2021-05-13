from datetime import timedelta
from decimal import Decimal
from typing import List, Optional
from unittest import mock

import faker
import pytest
import sqlalchemy

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
from massgov.pfml.db.models.employees import (
    Address,
    LkState,
    Payment,
    PaymentMethod,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ClaimFactory,
    EmployeeFactory,
    ExperianAddressPairFactory,
    PaymentFactory,
)
from massgov.pfml.delegated_payments.address_validation import (
    AddressValidationStep,
    Constants,
    _get_end_state_and_message_for_multiple_matches,
    _normalize_address_string,
)
from massgov.pfml.experian.physical_address.client.mock import MockClient
from massgov.pfml.experian.physical_address.client.models.search import Confidence

fake = faker.Faker()


def _random_valid_payment_with_state_log(db_session: db.Session, payment_method_id: int) -> Payment:
    # Create the employee and claim ourselves so the payment has an associated address.
    address_pair = ExperianAddressPairFactory(experian_address=AddressFactory())
    employee = EmployeeFactory()
    claim = ClaimFactory(employee=employee)

    # Set the dates to some reasonably recent dates in the past.
    start_date = fake.date_between("-10w", "-2w")
    end_date = start_date + timedelta(days=6)
    payment_date = end_date + timedelta(days=1)

    payment = PaymentFactory(
        claim=claim,
        period_start_date=start_date,
        period_end_date=end_date,
        payment_date=payment_date,
        amount=Decimal(fake.random_int(min=10, max=9_999)),
        disb_method_id=payment_method_id,
        experian_address_pair=address_pair,
    )

    state_log_util.create_finished_state_log(
        end_state=State.PAYMENT_READY_FOR_ADDRESS_VALIDATION,
        outcome=state_log_util.build_outcome("Payment ready for address validation"),
        associated_model=payment,
        db_session=db_session,
    )
    db_session.commit()

    return payment


def _set_up_payments(
    client: MockClient,
    db_session: db.Session,
    payment_count: int,
    confidence: Optional[Confidence] = None,
    payment_method_id: int = PaymentMethod.CHECK.payment_method_id,
    suggested_address_mismatch: bool = False,
) -> List[Payment]:
    payments = []
    for _i in range(payment_count):
        payment = _random_valid_payment_with_state_log(db_session, payment_method_id)

        if confidence is not None:
            # Unset the experian_address_pair.experian_address so _address_has_been_validated()
            # returns False and we make a request to the Experian API.
            payment.experian_address_pair.experian_address = None

            # Add experian_address_pair.fineos_address to mock client.
            address = payment.experian_address_pair.fineos_address

            # Mock client returns input address in suggestions list unless we explicitly
            # indicate that we want a mismatch.
            suggested_address = "Fake address string" if suggested_address_mismatch else None
            client.add_mock_address_response(address, confidence, suggested_address)

        payments.append(payment)

    return payments


def _assert_payment_state(db_session: db.Session, state: LkState, payments: List[Payment]) -> None:
    payment_ids = [payment.payment_id for payment in payments]
    assert db_session.query(sqlalchemy.func.count(StateLog.state_log_id)).filter(
        StateLog.end_state_id == state.state_id
    ).filter(StateLog.payment_id.in_(payment_ids)).scalar() == len(payments)


def _assert_payment_state_log_outcome(
    db_session: db.Session,
    payments: List[Payment],
    state: LkState,
    confidence: Optional[str] = None,
    match_count: int = 0,
) -> None:
    payment_ids = [payment.payment_id for payment in payments]

    # Payments with addresses that hit the Experian API have the expected fields.
    assert db_session.query(sqlalchemy.func.count(StateLog.state_log_id)).filter(
        StateLog.outcome[Constants.EXPERIAN_RESULT_KEY].isnot(None)
    ).filter(
        StateLog.outcome[Constants.EXPERIAN_RESULT_KEY][Constants.INPUT_ADDRESS_KEY].isnot(None)
    ).filter(
        StateLog.outcome[Constants.EXPERIAN_RESULT_KEY][Constants.CONFIDENCE_KEY].as_string()
        == confidence
    ).filter(
        StateLog.end_state_id == state.state_id
    ).filter(
        StateLog.payment_id.in_(payment_ids)
    ).scalar() == len(
        payments
    )

    # Expect addresses that returned multiple matches to have multiple output_addresses.
    if match_count > 0:
        key = Constants.OUTPUT_ADDRESS_KEY_PREFIX + str(match_count)
        assert db_session.query(sqlalchemy.func.count(StateLog.state_log_id)).filter(
            StateLog.outcome[Constants.EXPERIAN_RESULT_KEY][key].isnot(None)
        ).filter(StateLog.end_state_id == state.state_id).filter(
            StateLog.payment_id.in_(payment_ids)
        ).scalar() == len(
            payments
        )


def test_run_step_state_transitions(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    client = MockClient()

    check_payments_with_validated_addresses = _set_up_payments(
        client, local_test_db_session, fake.random_int(min=5, max=8)
    )
    check_payments_with_single_verified_matching_addresses = _set_up_payments(
        client, local_test_db_session, fake.random_int(min=7, max=11), Confidence.VERIFIED_MATCH
    )
    check_payments_with_non_matching_addresses = _set_up_payments(
        client, local_test_db_session, fake.random_int(min=1, max=6), Confidence.NO_MATCHES
    )
    check_payments_with_multiple_matching_addresses = _set_up_payments(
        client,
        local_test_db_session,
        fake.random_int(min=4, max=7),
        Confidence.MULTIPLE_MATCHES,
        suggested_address_mismatch=True,
    )
    check_payments_with_multiple_matching_addresses_and_near_match = _set_up_payments(
        client, local_test_db_session, fake.random_int(min=1, max=4), Confidence.MULTIPLE_MATCHES
    )

    # Commit the various experian_address_pair.experian_address = None changes to the database.
    local_test_db_session.commit()

    with mock.patch(
        "massgov.pfml.delegated_payments.address_validation._get_experian_client",
        return_value=client,
    ):
        AddressValidationStep(
            db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
        ).run()

    for payment in check_payments_with_validated_addresses:
        address_pair = payment.experian_address_pair
        assert address_pair.experian_address is not None

    # Expect to have received a newly formatted address in Experian /format response.
    for payment in check_payments_with_single_verified_matching_addresses:
        address_pair = payment.experian_address_pair
        assert address_pair.experian_address is not None
        assert address_pair.experian_address != address_pair.fineos_address

    # Expect payments with already valid addresses to transition into the
    # DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING state.
    _assert_payment_state(
        local_test_db_other_session,
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
        check_payments_with_validated_addresses,
    )

    # Expect payments with verified matching addresses according to Experian to transition into the
    # DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING state.
    _assert_payment_state(
        local_test_db_other_session,
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
        check_payments_with_single_verified_matching_addresses,
    )

    # Expect payments with no matching addresses according to Experian to transition into the
    # PAYMENT_FAILED_ADDRESS_VALIDATION state.
    _assert_payment_state(
        local_test_db_other_session,
        State.PAYMENT_FAILED_ADDRESS_VALIDATION,
        check_payments_with_non_matching_addresses,
    )

    # Expect payments with multiple matching addresses according to Experian to transition into the
    # PAYMENT_FAILED_ADDRESS_VALIDATION state.
    _assert_payment_state(
        local_test_db_other_session,
        State.PAYMENT_FAILED_ADDRESS_VALIDATION,
        check_payments_with_multiple_matching_addresses,
    )

    # Expect payments with a near match in the multiple matching addresses set to transition into
    # the DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING state.
    _assert_payment_state(
        local_test_db_other_session,
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
        check_payments_with_multiple_matching_addresses_and_near_match,
    )


def test_run_step_no_database_changes_on_exception(
    initialize_factories_session, test_db_session, test_db_other_session
):
    client = MockClient()

    _set_up_payments(client, test_db_session, fake.random_int(min=5, max=8))
    _set_up_payments(
        client, test_db_session, fake.random_int(min=7, max=11), Confidence.VERIFIED_MATCH
    )
    _set_up_payments(client, test_db_session, fake.random_int(min=1, max=6), Confidence.NO_MATCHES)
    _set_up_payments(
        client, test_db_session, fake.random_int(min=4, max=7), Confidence.MULTIPLE_MATCHES
    )

    # Commit the various experian_address_pair.experian_address = None changes to the database.
    test_db_session.commit()

    # Mock _get_payments_awaiting_address_validation() to raise an error so we can test rolling back
    # the changes we would have made previously to the claimant addresses.
    with mock.patch(
        "massgov.pfml.delegated_payments.address_validation._get_payments_awaiting_address_validation",
        side_effect=Exception("Raising error to test rollback"),
    ), mock.patch(
        "massgov.pfml.delegated_payments.address_validation._get_experian_client",
        return_value=client,
    ), pytest.raises(
        Exception, match="Raising error to test rollback"
    ):
        AddressValidationStep(
            db_session=test_db_session, log_entry_db_session=test_db_other_session
        ).run()

    # We expect to find no payments in either of the post-address validation states.
    post_address_validation_states = [
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_id,
        State.PAYMENT_FAILED_ADDRESS_VALIDATION.state_id,
    ]
    assert (
        test_db_other_session.query(sqlalchemy.func.count(StateLog.state_log_id))
        .filter(StateLog.end_state_id.in_(post_address_validation_states))
        .scalar()
        == 0
    )


def test_run_step_experian_exception(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    client = MockClient()

    valid_check_payments = _set_up_payments(
        client, local_test_db_session, fake.random_int(min=5, max=11), Confidence.VERIFIED_MATCH
    )
    eft_payments_with_multiple_matching_addresses = _set_up_payments(
        client,
        local_test_db_session,
        fake.random_int(min=4, max=7),
        Confidence.MULTIPLE_MATCHES,
        PaymentMethod.ACH.payment_method_id,
    )
    # Commit the various experian_address_pair.experian_address = None changes to the database.
    local_test_db_session.commit()

    with mock.patch(
        "massgov.pfml.delegated_payments.address_validation._experian_response_for_address",
        side_effect=Exception("Example error"),
    ), mock.patch(
        "massgov.pfml.delegated_payments.address_validation._get_experian_client",
        return_value=client,
    ):
        AddressValidationStep(
            db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
        ).run()

    # Despite having valid addresses, these payments failed because Experian threw an exception
    _assert_payment_state_log_outcome(
        local_test_db_other_session,
        valid_check_payments,
        State.PAYMENT_FAILED_ADDRESS_VALIDATION,
        Constants.UNKNOWN,
    )

    # EFT payments will always pass even if Experian throws an exception
    _assert_payment_state_log_outcome(
        local_test_db_other_session,
        eft_payments_with_multiple_matching_addresses,
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
        Constants.UNKNOWN,
    )


def test_run_step_state_log_outcome_field(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    experian_api_multiple_match_count = fake.random_int(min=2, max=9)
    client = MockClient(multiple_count=experian_api_multiple_match_count)

    check_payments_with_validated_addresses = _set_up_payments(
        client, local_test_db_session, fake.random_int(min=5, max=8)
    )
    check_payments_with_single_verified_matching_addresses = _set_up_payments(
        client, local_test_db_session, fake.random_int(min=7, max=11), Confidence.VERIFIED_MATCH
    )
    check_payments_with_non_matching_addresses = _set_up_payments(
        client, local_test_db_session, fake.random_int(min=1, max=6), Confidence.NO_MATCHES
    )
    check_payments_with_multiple_matching_addresses = _set_up_payments(
        client,
        local_test_db_session,
        fake.random_int(min=4, max=7),
        Confidence.MULTIPLE_MATCHES,
        suggested_address_mismatch=True,
    )
    check_payments_with_multiple_matching_addresses_and_near_match = _set_up_payments(
        client, local_test_db_session, fake.random_int(min=1, max=4), Confidence.MULTIPLE_MATCHES
    )

    eft_payments_with_multiple_matching_addresses = _set_up_payments(
        client,
        local_test_db_session,
        fake.random_int(min=4, max=7),
        Confidence.MULTIPLE_MATCHES,
        PaymentMethod.ACH.payment_method_id,
    )

    # Commit the various experian_address_pair.experian_address = None changes to the database.
    local_test_db_session.commit()

    with mock.patch(
        "massgov.pfml.delegated_payments.address_validation._get_experian_client",
        return_value=client,
    ):
        AddressValidationStep(
            db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
        ).run()

    # Expect payments with already valid addresses to not have any an experian_result element
    # of the state_log.outcome field.
    _assert_payment_state_log_outcome(
        local_test_db_other_session,
        check_payments_with_validated_addresses,
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
        Constants.PREVIOUSLY_VERIFIED,
    )

    # Expect payments with addresses that return a verified match to have a
    # state_log.outcome.experian_result element with the correct confidence level.
    _assert_payment_state_log_outcome(
        local_test_db_other_session,
        check_payments_with_single_verified_matching_addresses,
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
        Confidence.VERIFIED_MATCH.value,
    )

    # Expect payments with addresses that return no matches to have a
    # state_log.outcome.experian_result element with the correct confidence level.
    _assert_payment_state_log_outcome(
        local_test_db_other_session,
        check_payments_with_non_matching_addresses,
        State.PAYMENT_FAILED_ADDRESS_VALIDATION,
        Confidence.NO_MATCHES.value,
    )

    # Expect payments with addresses that return no matches to have a
    # state_log.outcome.experian_result element with multiple output_address_ elements.
    _assert_payment_state_log_outcome(
        local_test_db_other_session,
        check_payments_with_multiple_matching_addresses,
        State.PAYMENT_FAILED_ADDRESS_VALIDATION,
        Confidence.MULTIPLE_MATCHES.value,
        experian_api_multiple_match_count,
    )

    _assert_payment_state_log_outcome(
        local_test_db_other_session,
        check_payments_with_multiple_matching_addresses_and_near_match,
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
        Confidence.MULTIPLE_MATCHES.value,
        experian_api_multiple_match_count,
    )

    # Expect EFT payments with addresses that return multiple
    # state_log.outcome.experian_result element with multiple output_address_ elements.
    # BUT still go to the success state
    _assert_payment_state_log_outcome(
        local_test_db_other_session,
        eft_payments_with_multiple_matching_addresses,
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
        Confidence.MULTIPLE_MATCHES.value,
        experian_api_multiple_match_count,
    )


@pytest.mark.parametrize(
    "_description, suggested_address, expected_end_state, new_address_count",
    (
        (
            "Near match in multiple matches",
            None,
            State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
            1,
        ),
        (
            "Near match in multiple matches",
            "9999 Obviously fake BLVD",
            State.PAYMENT_FAILED_ADDRESS_VALIDATION,
            0,
        ),
    ),
)
def test_get_end_state_and_outcome_for_multiple_matches(
    local_initialize_factories_session,
    local_test_db_session,
    local_test_db_other_session,
    _description,
    suggested_address,
    expected_end_state,
    new_address_count,
):
    address_pair = ExperianAddressPairFactory()
    client = MockClient()
    mocked_response = client.add_mock_address_response(
        address_pair.fineos_address, Confidence.MULTIPLE_MATCHES, suggested_address
    )

    address_count_before = local_test_db_other_session.query(
        sqlalchemy.func.count(Address.address_id)
    ).scalar()

    end_state, _message = _get_end_state_and_message_for_multiple_matches(
        mocked_response.result, client, address_pair
    )

    # Commit the new address_pair.experian_address to the database.
    local_test_db_session.commit()

    assert end_state == expected_end_state

    # Either None (if no near match) or new Address.
    assert address_pair.experian_address != address_pair.fineos_address
    assert (
        address_count_before + new_address_count
        == local_test_db_other_session.query(sqlalchemy.func.count(Address.address_id)).scalar()
    )


@pytest.mark.parametrize(
    "_description, address_in, expected_address",
    (
        (
            "Excess spaces removed",
            " 4 S   Market St  , Boston MA 02109 ",
            "4 s market st, boston ma 02109",
        ),
        (
            "Address with no changes needed untouched",
            "1040 mass moca way, north adams ma 01247",
            "1040 mass moca way, north adams ma 01247",
        ),
    ),
)
def test_normalize_address_string(_description, address_in, expected_address):
    assert _normalize_address_string(address_in) == expected_address
