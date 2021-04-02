import os
import re

import faker
import pytest
import sqlalchemy

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    Employee,
    LkPaymentMethod,
    LkPrenoteState,
    PaymentMethod,
    PrenoteState,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployeeFactory,
    EmployeePubEftPairFactory,
    PaymentFactory,
    PubEftFactory,
)
from massgov.pfml.delegated_payments.ez_check import EzCheckFile
from massgov.pfml.delegated_payments.pub.transaction_file_creator import TransactionFileCreatorStep
from tests.delegated_payments.pub.test_pub_check import _random_valid_check_payment_with_state_log

fake = faker.Faker()


@pytest.fixture
def transaction_file_step(test_db_session, initialize_factories_session, test_db_other_session):
    return TransactionFileCreatorStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


def test_ach_file_creation(
    transaction_file_step: TransactionFileCreatorStep,
    test_db_session,
    initialize_factories_session,
    tmp_path,
    monkeypatch,
):
    # set environment variables
    output_folder_path = str(tmp_path)
    monkeypatch.setenv("PFML_PUB_OUTBOUND_PATH", output_folder_path)

    # setup data
    prenote_count = 5
    pub_eft_count = 7

    # create employees ready for prenote
    for _ in range(prenote_count):
        create_employee_for_prenote(test_db_session)

    # create payments ready for payment
    for _ in range(pub_eft_count):
        create_payment_for_pub_transaction(test_db_session, PaymentMethod.ACH)

    # generate the ach file
    transaction_file_step.run_step()

    # check that ach file were generated
    formatted_now = payments_util.get_now().strftime("%Y%m%d")
    pub_ach_file_name = f"PUB-NACHA-{formatted_now}"
    expected_ach_file_folder = os.path.join(
        output_folder_path, payments_util.Constants.S3_OUTBOUND_READY_DIR
    )
    assert pub_ach_file_name in file_util.list_files(expected_ach_file_folder)

    # check that no check file was created because no check payments were in the correct state.
    assert transaction_file_step.check_file is None
    assert (
        test_db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.PUB_EZ_CHECK.reference_file_type_id
        )
        .one_or_none()
        is None
    )

    # check that corresponding reference file was created
    assert (
        test_db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.file_location
            == str(os.path.join(expected_ach_file_folder, pub_ach_file_name)),
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.PUB_TRANSACTION.reference_file_type_id,
        )
        .one_or_none()
        is not None
    )

    # check that payment states were transitioned
    payment_pub_eft_sent_states = state_log_util.get_all_latest_state_logs_in_end_state(
        state_log_util.AssociatedClass.PAYMENT,
        State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
        test_db_session,
    )
    assert len(payment_pub_eft_sent_states) == pub_eft_count

    # check that prenote states were transitioned for employee
    prenote_sent_states = state_log_util.get_all_latest_state_logs_in_end_state(
        state_log_util.AssociatedClass.EMPLOYEE, State.DELEGATED_EFT_PRENOTE_SENT, test_db_session,
    )
    assert len(prenote_sent_states) == prenote_count

    # check that pubeft prenote state was transitioned
    for prenote_sent_state in prenote_sent_states:
        employee_pub_eft_pairs = prenote_sent_state.employee.pub_efts.all()
        pub_eft = employee_pub_eft_pairs[0].pub_eft
        assert pub_eft.prenote_state_id == PrenoteState.PENDING_WITH_PUB.prenote_state_id


def test_check_file_creation(
    transaction_file_step: TransactionFileCreatorStep,
    test_db_session,
    test_db_other_session,
    initialize_factories_session,
    tmp_path,
    monkeypatch,
):
    # set environment variables
    output_folder_path = str(tmp_path)
    accounting_number = str(fake.random_int(min=1_000_000_000_000_000, max=9_999_999_999_999_999))
    routing_number = str(fake.random_int(min=10_000_000_000, max=99_999_999_999))
    monkeypatch.setenv("PFML_PUB_OUTBOUND_PATH", output_folder_path)
    monkeypatch.setenv("DFML_PUB_ACCOUNT_NUMBER", accounting_number)
    monkeypatch.setenv("DFML_PUB_ROUTING_NUMBER", routing_number)

    # Stock the database with a handful of check payments in the correct state to be picked up.
    payments = []
    for _i in range(fake.random_int(min=6, max=15)):
        payments.append(_random_valid_check_payment_with_state_log(test_db_session))

    # generate the check file
    transaction_file_step.run_step()

    ez_check_file = transaction_file_step.check_file
    assert isinstance(ez_check_file, EzCheckFile)
    assert len(ez_check_file.records) == len(payments)

    file_location_pattern = os.path.join(
        output_folder_path, payments_util.Constants.S3_OUTBOUND_READY_DIR, "%"
    )
    ref_file = (
        test_db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.PUB_EZ_CHECK.reference_file_type_id
        )
        .filter(ReferenceFile.file_location.like(file_location_pattern))
        .one_or_none()
    )
    assert ref_file is not None

    filename_pattern = r"PUB-EZ-CHECK_\d{4}\d{2}\d{2}-\d{2}\d{2}\.csv"
    assert re.search(filename_pattern, ref_file.file_location)

    # Confirm output file has 2 rows for each record and 1 for the header.
    file_stream = file_util.open_stream(ref_file.file_location)
    assert len([line for line in file_stream]) == 1 + 2 * len(ez_check_file.records)

    # Confirm that we updated the state log for each payment.
    for payment in payments:
        assert (
            test_db_other_session.query(sqlalchemy.func.count(StateLog.state_log_id))
            .filter(
                StateLog.end_state_id == State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT.state_id
            )
            .filter(StateLog.payment_id == payment.payment_id)
            .scalar()
            == 1
        )


def test_get_eligible_eft_payments_error_states(
    transaction_file_step: TransactionFileCreatorStep, test_db_session, initialize_factories_session
):
    create_payment_for_pub_transaction(test_db_session, PaymentMethod.CHECK)

    test_db_session.commit()

    with pytest.raises(
        Exception, match=r"Non-ACH payment method detected in state log: .+",
    ):
        transaction_file_step._get_eligible_eft_payments()


def test_get_pub_efts_for_pre_note(
    transaction_file_step: TransactionFileCreatorStep, test_db_session, initialize_factories_session
):
    employee = EmployeeFactory.create()
    assert len(transaction_file_step._get_pub_efts_for_prenote(employee)) == 0

    pub_eft_1 = PubEftFactory.create(prenote_state_id=PrenoteState.PENDING_PRE_PUB.prenote_state_id)
    EmployeePubEftPairFactory.create(employee=employee, pub_eft=pub_eft_1)

    pub_eft_2 = PubEftFactory.create(
        prenote_state_id=PrenoteState.PENDING_WITH_PUB.prenote_state_id
    )
    EmployeePubEftPairFactory.create(employee=employee, pub_eft=pub_eft_2)

    pub_eft_3 = PubEftFactory.create(prenote_state_id=PrenoteState.APPROVED.prenote_state_id)
    EmployeePubEftPairFactory.create(employee=employee, pub_eft=pub_eft_3)

    pub_eft_4 = PubEftFactory.create(prenote_state_id=PrenoteState.REJECTED.prenote_state_id)
    EmployeePubEftPairFactory.create(employee=employee, pub_eft=pub_eft_4)

    pub_eft_5 = PubEftFactory.create(prenote_state_id=PrenoteState.PENDING_PRE_PUB.prenote_state_id)
    EmployeePubEftPairFactory.create(employee=employee, pub_eft=pub_eft_5)

    pub_efts = transaction_file_step._get_pub_efts_for_prenote(employee)
    pub_eft_ids = [pub_eft.pub_eft_id for pub_eft in pub_efts]

    assert len(pub_eft_ids) == 2
    assert pub_eft_1.pub_eft_id in pub_eft_ids
    assert pub_eft_5.pub_eft_id in pub_eft_ids


def test_get_eft_eligible_employees_with_eft_error_states(
    transaction_file_step: TransactionFileCreatorStep, test_db_session, initialize_factories_session
):
    employee = EmployeeFactory.create()

    state_log_util.create_finished_state_log(
        employee,
        State.DELEGATED_EFT_SEND_PRENOTE,
        state_log_util.build_outcome("test"),
        test_db_session,
    )

    with pytest.raises(
        Exception,
        match=f"No pending prenote pub efts associated with employee: {employee.employee_id}",
    ):
        transaction_file_step._get_eft_eligible_employees_with_eft()


def create_employee_with_eft(prenote_state: LkPrenoteState) -> Employee:
    employee = EmployeeFactory.create()
    pub_eft = PubEftFactory.create(prenote_state_id=prenote_state.prenote_state_id)
    EmployeePubEftPairFactory.create(employee=employee, pub_eft=pub_eft)

    return employee


def create_employee_for_prenote(db_session):
    employee = create_employee_with_eft(PrenoteState.PENDING_PRE_PUB)

    state_log_util.create_finished_state_log(
        employee,
        State.DELEGATED_EFT_SEND_PRENOTE,
        state_log_util.build_outcome("test"),
        db_session,
    )


def create_payment_for_pub_transaction(db_session, payment_method: LkPaymentMethod):
    employee = create_employee_with_eft(PrenoteState.APPROVED)
    employee_pub_eft_pairs = employee.pub_efts.all()
    pub_eft = employee_pub_eft_pairs[0].pub_eft

    claim = ClaimFactory.create(employee=employee)
    payment = PaymentFactory.create(
        claim=claim, pub_eft=pub_eft, disb_method_id=payment_method.payment_method_id
    )

    state_log_util.create_finished_state_log(
        payment,
        State.DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_EFT,
        state_log_util.build_outcome("test"),
        db_session,
    )

    return payment
