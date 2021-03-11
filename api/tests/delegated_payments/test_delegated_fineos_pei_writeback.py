import dataclasses
import re
from datetime import date, timedelta

import faker
import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.delegated_payments.delegated_fineos_pei_writeback as writeback
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    Flow,
    Payment,
    PaymentReferenceFile,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import PaymentFactory

# every test in here requires real resources
pytestmark = pytest.mark.integration

fake = faker.Faker()


def _generate_payment(test_db_session: db.Session) -> Payment:
    return PaymentFactory.create(
        fineos_pei_c_value=str(fake.random_int(min=1000, max=9999)),
        fineos_pei_i_value=str(fake.random_int(min=1000, max=9999)),
        fineos_extraction_date=date.today() - timedelta(days=fake.random_int()),
    )


def _generate_payment_and_state(test_db_session: db.Session, state: State) -> Payment:
    payment = _generate_payment(test_db_session)
    state_log_util.create_finished_state_log(
        associated_model=payment,
        end_state=state,
        outcome=state_log_util.build_outcome("Creating for test"),
        db_session=test_db_session,
    )
    return payment


def _generate_zero_dollar_payment(test_db_session: db.Session) -> Payment:
    return _generate_payment_and_state(
        test_db_session, State.DELEGATED_PAYMENT_ADD_ZERO_PAYMENT_TO_FINEOS_WRITEBACK
    )


def _generate_overpayment(test_db_session: db.Session) -> Payment:
    return _generate_payment_and_state(
        test_db_session, State.DELEGATED_PAYMENT_ADD_OVERPAYMENT_TO_FINEOS_WRITEBACK
    )


def _generate_accepted_payment(test_db_session: db.Session) -> Payment:
    return _generate_payment_and_state(
        test_db_session, State.DELEGATED_PAYMENT_ADD_ACCEPTED_PAYMENT_TO_FINEOS_WRITEBACK
    )


def _generate_cancelled_payment(test_db_session: db.Session) -> Payment:
    return _generate_payment_and_state(
        test_db_session, State.DELEGATED_PAYMENT_ADD_CANCELLATION_PAYMENT_TO_FINEOS_WRITEBACK
    )


@pytest.mark.parametrize(
    "zero_dollar_payment_count, overpayment_count, accepted_payment_count, cancelled_payment_count",
    (
        # Some payments in each state.
        (
            fake.random_int(min=1, max=4),
            fake.random_int(min=0, max=8),
            fake.random_int(min=2, max=6),
            fake.random_int(min=4, max=7),
        ),
    ),
)
def test_process_payments_for_writeback(
    initialize_factories_session,
    test_db_session,
    test_db_other_session,
    mock_s3_bucket,
    monkeypatch,
    zero_dollar_payment_count,
    overpayment_count,
    accepted_payment_count,
    cancelled_payment_count,
):
    s3_bucket_uri = "s3://" + mock_s3_bucket

    fineos_data_import_path = s3_bucket_uri + "/TEST/peiupdate/"
    monkeypatch.setenv("FINEOS_DATA_IMPORT_PATH", fineos_data_import_path)

    pfml_fineos_outbound_path = s3_bucket_uri + "/cps/outbound/"
    monkeypatch.setenv("PFML_FINEOS_OUTBOUND_PATH", pfml_fineos_outbound_path)

    # Create some small amount of Payments that are in a state other than the one we pick up
    # for the writeback.
    for _i in range(fake.random_int(min=2, max=7)):
        _generate_payment_and_state(
            test_db_session, State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT
        )

    zero_dollar_payments = []
    for _i in range(zero_dollar_payment_count):
        zero_dollar_payments.append(_generate_zero_dollar_payment(test_db_session))

    overpayments = []
    for _i in range(overpayment_count):
        overpayments.append(_generate_overpayment(test_db_session))

    accepted_payments = []
    for _i in range(accepted_payment_count):
        accepted_payments.append(_generate_accepted_payment(test_db_session))

    cancelled_payments = []
    for _i in range(cancelled_payment_count):
        cancelled_payments.append(_generate_cancelled_payment(test_db_session))

    all_payments = zero_dollar_payments + overpayments + accepted_payments + cancelled_payments

    writeback.process_payments_for_writeback(test_db_session)

    reference_files = (
        test_db_other_session.query(ReferenceFile)
        .filter(
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.PEI_WRITEBACK.reference_file_type_id
        )
        .all()
    )

    # Expect to have created a single ReferenceFile for our single writeback file.
    assert len(reference_files) == 1

    ref_file = reference_files[0]
    assert ref_file.file_location.endswith(writeback.WRITEBACK_FILE_SUFFIX)
    assert (
        ref_file
        == test_db_other_session.query(StateLog)
        .filter(StateLog.end_state_id == State.PEI_WRITEBACK_SENT.state_id)
        .one_or_none()
        .reference_file
    )

    # Expect there to be a single PaymentReferenceFile linking the payment and the reference file.
    for payment in all_payments:
        payment_reference_files = (
            test_db_other_session.query(PaymentReferenceFile)
            .filter(PaymentReferenceFile.reference_file_id == ref_file.reference_file_id)
            .filter(PaymentReferenceFile.payment_id == payment.payment_id)
            .all()
        )
        assert len(payment_reference_files) == 1

    # Each payment transitioned to the correct state.
    for payment in zero_dollar_payments:
        state_log = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, test_db_other_session
        )
        assert (
            state_log.end_state_id
            == State.DELEGATED_PAYMENT_ZERO_PAYMENT_FINEOS_WRITEBACK_SENT.state_id
        )

    for payment in overpayments:
        state_log = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, test_db_other_session
        )
        assert (
            state_log.end_state_id
            == State.DELEGATED_PAYMENT_OVERPAYMENT_FINEOS_WRITEBACK_SENT.state_id
        )

    for payment in accepted_payments:
        state_log = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, test_db_other_session
        )
        assert (
            state_log.end_state_id
            == State.DELEGATED_PAYMENT_ACCEPTED_PAYMENT_FINEOS_WRITEBACK_SENT.state_id
        )

    for payment in cancelled_payments:
        state_log = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, test_db_other_session
        )
        assert (
            state_log.end_state_id
            == State.DELEGATED_PAYMENT_CANCELLATION_PAYMENT_FINEOS_WRITEBACK_SENT.state_id
        )

    # Assert that the contents of the writeback file match our expectations.
    writeback_file_lines = list(file_util.read_file_lines(ref_file.file_location))
    header_row = writeback_file_lines.pop(0)
    assert header_row == ",".join(
        [f.name for f in dataclasses.fields(writeback.PeiWritebackRecord)]
    )

    assert len(all_payments) == len(writeback_file_lines)
    for line in writeback_file_lines:
        expected_line_pattern = "{},{},{},,,,{},,{},{}".format(
            r"\d\d\d\d",  # C value
            r"\d\d\d\d",  # I value
            writeback.ACTIVE_WRITEBACK_RECORD_STATUS,
            r"\d\d/\d\d/\d\d\d\d",  # Extraction date
            writeback.PENDING_WRITEBACK_RECORD_TRANSACTION_STATUS,
            r"\d\d/\d\d/\d\d\d\d",  # Transaction date
        )
        assert re.match(expected_line_pattern, line)


def test_process_payments_for_writeback_no_payments_ready_for_writeback(
    initialize_factories_session, test_db_session,
):
    # Create some small amount of Payments that are in a state other than the one we pick up
    # for the writeback.
    for _i in range(fake.random_int(min=2, max=7)):
        _generate_payment_and_state(
            test_db_session, State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT
        )

    writeback.process_payments_for_writeback(test_db_session)

    # Did not create any ReferenceFile objects since we did not create any writeback files.
    reference_files = (
        test_db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.PEI_WRITEBACK.reference_file_type_id
        )
        .all()
    )

    assert len(reference_files) == 0


@pytest.mark.parametrize(
    "zero_dollar_payment_count, overpayment_count, accepted_payment_count, cancelled_payment_count",
    (
        # No payments in any of the states we want to pick up for the writeback.
        (0, 0, 0, 0),
        # Some payments in each state.
        (
            fake.random_int(min=3, max=5),
            fake.random_int(min=1, max=8),
            fake.random_int(min=2, max=6),
            fake.random_int(min=4, max=7),
        ),
    ),
)
def test_get_writeback_items_for_state(
    initialize_factories_session,
    test_db_session,
    zero_dollar_payment_count,
    overpayment_count,
    accepted_payment_count,
    cancelled_payment_count,
):
    # Create some small amount of Payments that are in a state other than the one we pick up
    # for the writeback.
    for _i in range(fake.random_int(min=2, max=7)):
        _generate_payment_and_state(
            test_db_session, State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT
        )

    for _i in range(zero_dollar_payment_count):
        _generate_zero_dollar_payment(test_db_session)

    for _i in range(overpayment_count):
        _generate_overpayment(test_db_session)

    for _i in range(accepted_payment_count):
        _generate_accepted_payment(test_db_session)

    for _i in range(cancelled_payment_count):
        _generate_cancelled_payment(test_db_session)

    payments_ready_for_writeback_count = (
        zero_dollar_payment_count
        + overpayment_count
        + accepted_payment_count
        + cancelled_payment_count
    )
    writeback_records = writeback.get_records_to_writeback(test_db_session)
    assert len(writeback_records) == payments_ready_for_writeback_count


def test_extracted_payment_to_pei_writeback_record(initialize_factories_session, test_db_session):
    payment = _generate_payment(test_db_session)

    writeback_record = writeback._extracted_payment_to_pei_writeback_record(payment)

    assert writeback_record.status == writeback.ACTIVE_WRITEBACK_RECORD_STATUS
    assert (
        writeback_record.transactionStatus == writeback.PENDING_WRITEBACK_RECORD_TRANSACTION_STATUS
    )
    assert writeback_record.transStatusDate is not None
