from datetime import timedelta
from decimal import Decimal
from typing import List, Optional
from unittest import mock

import faker
import pytest
import sqlalchemy

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.experian.address_validate_soap.client as soap_api
import massgov.pfml.experian.address_validate_soap.models as sm
from massgov.pfml.db.models.employees import LkState, Payment, PaymentMethod, State, StateLog
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ClaimFactory,
    EmployeeFactory,
    ExperianAddressPairFactory,
    PaymentFactory,
)
from massgov.pfml.db.models.payments import FineosWritebackDetails, FineosWritebackTransactionStatus
from massgov.pfml.delegated_payments.address_validation import AddressValidationStep, Constants
from massgov.pfml.experian.address_validate_soap.mock_caller import MockVerificationZeepCaller

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


def _setup_soap_payments(
    caller: MockVerificationZeepCaller,
    db_session: db.Session,
    payment_count: int,
    verify_level: Optional[sm.VerifyLevel] = None,
    payment_method_id: int = PaymentMethod.CHECK.payment_method_id,
) -> List[Payment]:
    payments = []
    for _ in range(payment_count):
        payment = _random_valid_payment_with_state_log(db_session, payment_method_id)

        if verify_level is not None:
            # Unset the experian_address_pair.experian_address so _address_has_been_validated()
            # returns False and we make a request to the Experian API.
            payment.experian_address_pair.experian_address = None

            # Add experian_address_pair.fineos_address to mock caller.
            address = payment.experian_address_pair.fineos_address

            caller.add_mock_search_response(address, verify_level)

        payments.append(payment)

    return payments


def _assert_payment_state(db_session: db.Session, state: LkState, payments: List[Payment]) -> None:
    payment_ids = [payment.payment_id for payment in payments]
    assert db_session.query(sqlalchemy.func.count(StateLog.state_log_id)).filter(
        StateLog.end_state_id == state.state_id
    ).filter(StateLog.payment_id.in_(payment_ids)).scalar() == len(payments)


def _assert_fineos_writeback_details(db_session: db.Session, payments: List[Payment]) -> None:
    payment_ids = [payment.payment_id for payment in payments]
    db_session.query(sqlalchemy.func.count(FineosWritebackDetails.payment_id)).filter(
        FineosWritebackDetails.transaction_status_id
        == FineosWritebackTransactionStatus.ADDRESS_VALIDATION_ERROR.transaction_status_id
    ).filter(FineosWritebackDetails.payment_id.in_(payment_ids)).scalar() == len(payments)


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


def test_run_step_state_transitions_soap(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session,
):
    mock_caller = MockVerificationZeepCaller()

    check_payments_with_validated_addresses = _setup_soap_payments(
        mock_caller, local_test_db_session, fake.random_int(min=2, max=4)
    )
    check_payments_with_verified_addresses = _setup_soap_payments(
        mock_caller, local_test_db_session, fake.random_int(min=2, max=4), sm.VerifyLevel.VERIFIED
    )
    check_payments_with_interaction_required_addresses = _setup_soap_payments(
        mock_caller,
        local_test_db_session,
        fake.random_int(min=2, max=4),
        sm.VerifyLevel.INTERACTION_REQUIRED,
    )
    check_payments_with_no_matching_addresses = _setup_soap_payments(
        mock_caller,
        local_test_db_session,
        fake.random_int(min=2, max=4),
        sm.VerifyLevel.STREET_PARTIAL,
    )
    no_match_eft_payments = _setup_soap_payments(
        mock_caller,
        local_test_db_session,
        fake.random_int(min=2, max=4),
        sm.VerifyLevel.NONE,
        PaymentMethod.ACH.payment_method_id,
    )
    # Commit the various experian_address_pair.experian_address = None changes to the database.
    local_test_db_session.commit()

    client = soap_api.Client(mock_caller)

    with mock.patch(
        "massgov.pfml.delegated_payments.address_validation._get_experian_soap_client",
        return_value=client,
    ):
        AddressValidationStep(
            db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
        ).run()

    for payment in check_payments_with_validated_addresses:
        address_pair = payment.experian_address_pair
        assert address_pair.experian_address is not None

    # Expect to have received a newly formatted address in Experian verification response
    for payment in check_payments_with_verified_addresses:
        address_pair = payment.experian_address_pair
        assert address_pair.experian_address is not None
        assert address_pair.experian_address != address_pair.fineos_address

    # Expect payments with already valid addresses to transition into the
    # DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING state.
    _assert_payment_state(
        local_test_db_other_session,
        State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK,
        check_payments_with_validated_addresses,
    )

    # Expect payments with verified matching addresses according to Experian to transition into the
    # DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING state.
    _assert_payment_state(
        local_test_db_other_session,
        State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK,
        check_payments_with_verified_addresses,
    )

    # Payments without a verified response according to Experian transition into the
    # PAYMENT_FAILED_ADDRESS_VALIDATION state and DELEGATED_ADD_TO_FINEOS_WRITEBACK state.
    _assert_payment_state(
        local_test_db_other_session,
        State.PAYMENT_FAILED_ADDRESS_VALIDATION,
        check_payments_with_interaction_required_addresses,
    )
    _assert_payment_state(
        local_test_db_other_session,
        State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
        check_payments_with_interaction_required_addresses,
    )
    _assert_fineos_writeback_details(
        local_test_db_other_session, check_payments_with_interaction_required_addresses
    )

    _assert_payment_state(
        local_test_db_other_session,
        State.PAYMENT_FAILED_ADDRESS_VALIDATION,
        check_payments_with_no_matching_addresses,
    )
    _assert_payment_state(
        local_test_db_other_session,
        State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
        check_payments_with_no_matching_addresses,
    )
    _assert_fineos_writeback_details(
        local_test_db_other_session, check_payments_with_no_matching_addresses
    )

    # EFT payments with validation issues will still transition to
    # DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING
    _assert_payment_state(
        local_test_db_other_session,
        State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK,
        no_match_eft_payments,
    )


def test_run_step_state_transitions_malformed_address(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session,
):
    # Testing that if the address is missing pieces, it'll still move to the appropriate
    # state and that Experian will not be called at all.
    mock_caller = MockVerificationZeepCaller()

    check_payment = _random_valid_payment_with_state_log(
        local_test_db_session, PaymentMethod.CHECK.payment_method_id
    )
    check_payment.experian_address_pair.experian_address = None
    check_payment.experian_address_pair.fineos_address.address_line_one = ""

    eft_payment = _random_valid_payment_with_state_log(
        local_test_db_session, PaymentMethod.ACH.payment_method_id
    )
    eft_payment.experian_address_pair.experian_address = None
    eft_payment.experian_address_pair.fineos_address.address_line_one = None

    # Commit the various experian_address_pair.experian_address = None changes to the database.
    local_test_db_session.commit()

    client = soap_api.Client(mock_caller)

    with mock.patch(
        "massgov.pfml.delegated_payments.address_validation._get_experian_soap_client",
        return_value=client,
    ):
        AddressValidationStep(
            db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
        ).run()

    # mock_caller.DoSearch was never called
    assert mock_caller.call_count == 0

    # Check payment would have gone to the error state
    _assert_payment_state(
        local_test_db_other_session, State.PAYMENT_FAILED_ADDRESS_VALIDATION, [check_payment],
    )

    # EFT payment would have gone to the success state despite the issue
    _assert_payment_state(
        local_test_db_other_session, State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK, [eft_payment],
    )


def test_run_step_no_database_changes_on_exception_soap(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session,
):
    mock_caller = MockVerificationZeepCaller()

    _setup_soap_payments(mock_caller, local_test_db_session, fake.random_int(min=2, max=4))
    _setup_soap_payments(
        mock_caller, local_test_db_session, fake.random_int(min=2, max=4), sm.VerifyLevel.VERIFIED
    )
    _setup_soap_payments(
        mock_caller,
        local_test_db_session,
        fake.random_int(min=2, max=4),
        sm.VerifyLevel.INTERACTION_REQUIRED,
    )
    _setup_soap_payments(
        mock_caller,
        local_test_db_session,
        fake.random_int(min=2, max=4),
        sm.VerifyLevel.STREET_PARTIAL,
    )

    local_test_db_session.commit()

    client = soap_api.Client(mock_caller)

    with mock.patch(
        "massgov.pfml.delegated_payments.address_validation._get_payments_awaiting_address_validation",
        side_effect=Exception("Raising error to test rollback"),
    ), mock.patch(
        "massgov.pfml.delegated_payments.address_validation._get_experian_soap_client",
        return_value=client,
    ), pytest.raises(
        Exception, match="Raising error to test rollback"
    ):
        AddressValidationStep(
            db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
        ).run()

    # We expect to find no payments in any of the post-address validation states.
    post_address_validation_states = [
        State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK.state_id,
        State.PAYMENT_FAILED_ADDRESS_VALIDATION.state_id,
        State.DELEGATED_ADD_TO_FINEOS_WRITEBACK.state_id,
    ]
    assert (
        local_test_db_other_session.query(sqlalchemy.func.count(StateLog.state_log_id))
        .filter(StateLog.end_state_id.in_(post_address_validation_states))
        .scalar()
        == 0
    )


def test_run_step_experian_soap_exception(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session,
):
    mock_caller = MockVerificationZeepCaller()

    valid_check_payments = _setup_soap_payments(
        mock_caller, local_test_db_session, fake.random_int(min=2, max=4), sm.VerifyLevel.VERIFIED
    )
    no_match_eft_payments = _setup_soap_payments(
        mock_caller,
        local_test_db_session,
        fake.random_int(min=2, max=4),
        sm.VerifyLevel.NONE,
        PaymentMethod.ACH.payment_method_id,
    )

    local_test_db_session.commit()

    client = soap_api.Client(mock_caller)

    with mock.patch(
        "massgov.pfml.delegated_payments.address_validation._experian_soap_response_for_address",
        side_effect=Exception("Example error"),
    ), mock.patch(
        "massgov.pfml.delegated_payments.address_validation._get_experian_soap_client",
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
    _assert_payment_state_log_outcome(
        local_test_db_other_session,
        valid_check_payments,
        State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
        Constants.UNKNOWN,
    )
    _assert_fineos_writeback_details(local_test_db_other_session, valid_check_payments)

    # EFT payments will always pass even if Experian throws an exception
    _assert_payment_state_log_outcome(
        local_test_db_other_session,
        no_match_eft_payments,
        State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK,
        Constants.UNKNOWN,
    )


def test_run_step_state_log_outcome_field_soap(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session,
):
    mock_caller = MockVerificationZeepCaller()

    check_payments_with_validated_addresses = _setup_soap_payments(
        mock_caller, local_test_db_session, fake.random_int(min=2, max=4)
    )
    check_payments_with_verified_addresses = _setup_soap_payments(
        mock_caller, local_test_db_session, fake.random_int(min=2, max=4), sm.VerifyLevel.VERIFIED
    )
    check_payments_with_interaction_required_addresses = _setup_soap_payments(
        mock_caller,
        local_test_db_session,
        fake.random_int(min=2, max=4),
        sm.VerifyLevel.INTERACTION_REQUIRED,
    )
    check_payments_with_no_matching_addresses = _setup_soap_payments(
        mock_caller,
        local_test_db_session,
        fake.random_int(min=2, max=4),
        sm.VerifyLevel.STREET_PARTIAL,
    )
    no_match_eft_payments = _setup_soap_payments(
        mock_caller,
        local_test_db_session,
        fake.random_int(min=2, max=4),
        sm.VerifyLevel.NONE,
        PaymentMethod.ACH.payment_method_id,
    )
    # Commit the various experian_address_pair.experian_address = None changes to the database.
    local_test_db_session.commit()

    client = soap_api.Client(mock_caller)
    with mock.patch(
        "massgov.pfml.delegated_payments.address_validation._get_experian_soap_client",
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
        State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK,
        Constants.PREVIOUSLY_VERIFIED,
    )

    # Expect payments with addresses that return a verified match to have a
    # state_log.outcome.experian_result element with the correct confidence level.
    _assert_payment_state_log_outcome(
        local_test_db_other_session,
        check_payments_with_verified_addresses,
        State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK,
        sm.VerifyLevel.VERIFIED.value,
        1,
    )

    # Expect payments with interaction required to have a potential result
    _assert_payment_state_log_outcome(
        local_test_db_other_session,
        check_payments_with_interaction_required_addresses,
        State.PAYMENT_FAILED_ADDRESS_VALIDATION,
        sm.VerifyLevel.INTERACTION_REQUIRED.value,
        1,  # Interaction required returns 1 possible address
    )

    # Payments without a matching address won't have any suggestions
    _assert_payment_state_log_outcome(
        local_test_db_other_session,
        check_payments_with_no_matching_addresses,
        State.PAYMENT_FAILED_ADDRESS_VALIDATION,
        sm.VerifyLevel.STREET_PARTIAL.value,
    )

    # EFT payments always pass
    _assert_payment_state_log_outcome(
        local_test_db_other_session,
        no_match_eft_payments,
        State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK,
        sm.VerifyLevel.NONE.value,
    )
