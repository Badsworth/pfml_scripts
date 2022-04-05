import dataclasses
import re
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

import faker
import pytest
from freezegun import freeze_time

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.delegated_payments.delegated_fineos_pei_writeback as writeback
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    LkPaymentMethod,
    Payment,
    PaymentMethod,
    PaymentReferenceFile,
    ReferenceFile,
    ReferenceFileType,
)
from massgov.pfml.db.models.payments import (
    ACTIVE_WRITEBACK_RECORD_STATUS,
    PENDING_ACTIVE_WRITEBACK_RECORD_STATUS,
    FineosWritebackTransactionStatus,
    LkFineosWritebackTransactionStatus,
)
from massgov.pfml.db.models.state import Flow, LkState, State
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory
from massgov.pfml.util.datetime import get_now_us_eastern

fake = faker.Faker()

check_number_provider = {"check_number": 1}


@pytest.fixture
def fineos_pei_writeback_step(initialize_factories_session, test_db_session):
    return writeback.FineosPeiWritebackStep(
        db_session=test_db_session, log_entry_db_session=test_db_session
    )


@dataclasses.dataclass
class WritebackTestConfig:

    end_state: LkState
    transaction_status: Optional[LkFineosWritebackTransactionStatus]
    payment_method: LkPaymentMethod = PaymentMethod.ACH
    has_check_posted_date: bool = False
    add_writeback_state: bool = True


class Scenarios:
    ZERO_DOLLAR = WritebackTestConfig(
        end_state=State.DELEGATED_PAYMENT_PROCESSED_ZERO_PAYMENT,
        transaction_status=FineosWritebackTransactionStatus.PROCESSED,
    )

    OVERPAYMENT = WritebackTestConfig(
        end_state=State.DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT,
        transaction_status=FineosWritebackTransactionStatus.PROCESSED,
    )

    PENDING_AUDIT = WritebackTestConfig(
        # This transaction status is "" (or Pending Active)
        end_state=State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
        transaction_status=FineosWritebackTransactionStatus.PENDING_PAYMENT_AUDIT,
    )

    ACCEPTED_CHECK = WritebackTestConfig(
        end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT,
        transaction_status=FineosWritebackTransactionStatus.PAID,
        payment_method=PaymentMethod.CHECK,
    )

    ACCEPTED_EFT = WritebackTestConfig(
        end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
        transaction_status=FineosWritebackTransactionStatus.PAID,
    )

    COMPLETED_CHECK = WritebackTestConfig(
        end_state=State.DELEGATED_PAYMENT_COMPLETE,
        transaction_status=FineosWritebackTransactionStatus.POSTED,
        payment_method=PaymentMethod.CHECK,
        has_check_posted_date=True,
    )

    CHANGE_NOTIFICATION_EFT = WritebackTestConfig(
        end_state=State.DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION,
        transaction_status=FineosWritebackTransactionStatus.POSTED,
    )

    CANCELLATION = WritebackTestConfig(
        end_state=State.DELEGATED_PAYMENT_PROCESSED_CANCELLATION,
        transaction_status=FineosWritebackTransactionStatus.PROCESSED,
    )

    ERRORED = WritebackTestConfig(
        end_state=State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
        transaction_status=FineosWritebackTransactionStatus.BANK_PROCESSING_ERROR,
    )

    PAYMENT_WITHOUT_WRITEBACK_STATE = WritebackTestConfig(
        end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
        transaction_status=None,
        add_writeback_state=False,
    )


def _generate_payments(
    db_session: db.Session, config: WritebackTestConfig, count: Optional[int] = None
) -> List[Tuple[Payment, WritebackTestConfig]]:

    if count is None:
        count = fake.random_int(min=2, max=5)

    payment_scenario_tuples = []

    for _ in range(count):
        check_number = None
        if config.payment_method.payment_method_id == PaymentMethod.CHECK.payment_method_id:
            check_number = check_number_provider["check_number"]
            check_number_provider["check_number"] += 1

        factory = DelegatedPaymentFactory(
            db_session,
            fineos_pei_i_value=str(fake.unique.random_int(min=1000, max=9999)),
            payment_method=config.payment_method,
            fineos_extraction_date=date.today() - timedelta(days=fake.random_int()),
            check_number=check_number,
        )

        payment = factory.get_or_create_payment_with_state(config.end_state)
        if config.add_writeback_state:
            factory.get_or_create_payment_with_writeback(config.transaction_status)

        if config.has_check_posted_date:
            payment.check.check_posted_date = payment.fineos_extraction_date + timedelta(days=10)

        payment_scenario_tuples.append((payment, config))

    return payment_scenario_tuples


def validate_writeback_sent_states(
    db_session: db.Session, payment: Payment, config: WritebackTestConfig
):
    # Verify the payment's delegated payment state is unchanged
    payment_state_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, db_session
    )
    assert payment_state_log.end_state_id == config.end_state.state_id

    # Verify the payment's writeback state has been updated to the sent state
    writeback_state_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PEI_WRITEBACK, db_session
    )
    assert writeback_state_log.end_state_id == State.DELEGATED_FINEOS_WRITEBACK_SENT.state_id


@freeze_time("2021-01-01 12:00:00")
def test_process_payments_for_writeback(
    fineos_pei_writeback_step,
    test_db_session,
    mock_s3_bucket,
    monkeypatch,
):
    s3_bucket_uri = "s3://" + mock_s3_bucket

    fineos_data_import_path = s3_bucket_uri + "/TEST/peiupdate/"
    monkeypatch.setenv("FINEOS_DATA_IMPORT_PATH", fineos_data_import_path)

    pfml_fineos_outbound_path = s3_bucket_uri + "/cps/outbound/"
    monkeypatch.setenv("PFML_FINEOS_WRITEBACK_ARCHIVE_PATH", pfml_fineos_outbound_path)

    # Create some small amount of Payments that are in a state other than the one we pick up
    # for the writeback.
    _generate_payments(test_db_session, Scenarios.PAYMENT_WITHOUT_WRITEBACK_STATE)

    # Generate the payments, these return
    # as a list of tuples of (payment, scenario)
    all_payments = []
    for scenario in [
        Scenarios.ZERO_DOLLAR,
        Scenarios.OVERPAYMENT,
        Scenarios.PENDING_AUDIT,
        Scenarios.ACCEPTED_CHECK,
        Scenarios.ACCEPTED_EFT,
        Scenarios.CANCELLATION,
        Scenarios.COMPLETED_CHECK,
        Scenarios.CHANGE_NOTIFICATION_EFT,
        Scenarios.ERRORED,
    ]:
        all_payments += _generate_payments(test_db_session, scenario)

    fineos_pei_writeback_step.process_payments_for_writeback()

    reference_files = (
        test_db_session.query(ReferenceFile)
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

    i_to_payment_scenarios: Dict[str, Tuple[Payment, WritebackTestConfig]] = {}
    # Iterate over the scenarios and verify the DB was changed correctly
    for payment_tup in all_payments:
        payment, scenario = payment_tup

        # Expect there to be a single PaymentReferenceFile linking the payment and the reference file.
        payment_reference_files = (
            test_db_session.query(PaymentReferenceFile)
            .filter(PaymentReferenceFile.reference_file_id == ref_file.reference_file_id)
            .filter(PaymentReferenceFile.payment_id == payment.payment_id)
            .all()
        )
        assert len(payment_reference_files) == 1

        # Each payment transitioned to the correct state.
        validate_writeback_sent_states(test_db_session, payment, scenario)

        # When testing the file below, we need to lookup the payment by the I value
        i_to_payment_scenarios[payment.fineos_pei_i_value] = payment_tup

    # Assert that the contents of the writeback file match our expectations.
    writeback_file_lines = list(file_util.read_file_lines(ref_file.file_location))
    header_row = writeback_file_lines.pop(0)
    assert header_row == ",".join(
        [f.name for f in dataclasses.fields(writeback.PeiWritebackRecord)]
    )
    assert len(writeback_file_lines) == len(all_payments)

    expected_line_pattern = "{},({}),({}|{}),({}),({}),({}|{}|{}|{}|{}),({})".format(
        r"\d\d\d\d",  # C value
        r"\d\d\d\d",  # I value
        ACTIVE_WRITEBACK_RECORD_STATUS,
        PENDING_ACTIVE_WRITEBACK_RECORD_STATUS,
        r"\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d",  # Extraction date
        r"\d*",  # Check number
        # Expect both transaction statuses in the writeback file.
        FineosWritebackTransactionStatus.PAID.transaction_status_description,
        FineosWritebackTransactionStatus.PROCESSED.transaction_status_description,
        FineosWritebackTransactionStatus.BANK_PROCESSING_ERROR.transaction_status_description,
        FineosWritebackTransactionStatus.POSTED.transaction_status_description,
        FineosWritebackTransactionStatus.PENDING_PAYMENT_AUDIT.transaction_status_description,
        r"\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d",  # Transaction date
    )
    prog = re.compile(expected_line_pattern)
    now = get_now_us_eastern().date()

    for line in writeback_file_lines:
        # Expect that each line will match our pattern.
        result = prog.match(line)
        assert result, f"Line did not match expected line pattern: {line}"

        # Expect that payment types will set the appropriate transaction status.
        i_value = result.group(1)
        record_status = result.group(2)
        extraction_date = datetime.strptime(result.group(3), "%Y-%m-%d %H:%M:%S")
        transaction_number = result.group(4)
        transaction_status = result.group(5)
        transaction_date = datetime.strptime(result.group(6), "%Y-%m-%d %H:%M:%S")

        payment_tup = i_to_payment_scenarios.get(i_value)
        assert payment_tup, f"I value {i_value} in writeback not found in generated scenarios"
        payment, writeback_scenario_config = payment_tup

        assert (
            transaction_status
            == writeback_scenario_config.transaction_status.transaction_status_description
        )
        assert record_status == writeback_scenario_config.transaction_status.writeback_record_status
        assert extraction_date.date() == payment.fineos_extraction_date

        # Checks should have a check number with how it was configured
        if (
            writeback_scenario_config.payment_method.payment_method_id
            == PaymentMethod.CHECK.payment_method_id
        ):
            assert transaction_number == str(payment.check.check_number)
        else:
            assert transaction_number == ""

        # We use the check posted date if the payment has one
        # otherwise we use "now"
        if payment.check and payment.check.check_posted_date:
            assert transaction_date.date() == payment.check.check_posted_date
        else:
            assert transaction_date.date() == now


def test_process_payments_for_writeback_no_payments_ready_for_writeback(
    fineos_pei_writeback_step, test_db_session
):
    # Create some small amount of Payments that are in a state other than the one we pick up
    # for the writeback.
    _generate_payments(test_db_session, Scenarios.PAYMENT_WITHOUT_WRITEBACK_STATE)
    fineos_pei_writeback_step.process_payments_for_writeback()

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


def test_get_writeback_items_for_state(fineos_pei_writeback_step, test_db_session):
    # Create some small amount of Payments that are in a state other than the one we pick up
    # for the writeback.
    _generate_payments(test_db_session, Scenarios.PAYMENT_WITHOUT_WRITEBACK_STATE)

    # We find no writeback records
    writeback_records = fineos_pei_writeback_step.get_records_to_writeback()
    assert len(writeback_records) == 0

    # Now add the scenarios and we'll find those
    all_payments = []
    for scenario in [
        Scenarios.ZERO_DOLLAR,
        Scenarios.OVERPAYMENT,
        Scenarios.PENDING_AUDIT,
        Scenarios.ACCEPTED_CHECK,
        Scenarios.ACCEPTED_EFT,
        Scenarios.CANCELLATION,
        Scenarios.COMPLETED_CHECK,
        Scenarios.CHANGE_NOTIFICATION_EFT,
        Scenarios.ERRORED,
    ]:
        all_payments += _generate_payments(test_db_session, scenario)

    writeback_records = fineos_pei_writeback_step.get_records_to_writeback()
    assert len(writeback_records) == len(all_payments)
