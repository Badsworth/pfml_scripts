from decimal import Decimal
from typing import List, Optional

import pytest

from massgov.pfml.db.models.employees import ImportLog, Payment, ReferenceFile, ReferenceFileType
from massgov.pfml.db.models.factories import (
    FineosExtractVpeiFactory,
    FineosExtractVpeiPaymentDetailsFactory,
    FineosExtractVpeiPaymentLineFactory,
    ImportLogFactory,
    ReferenceFileFactory,
)
from massgov.pfml.db.models.payments import (
    FineosExtractVpeiPaymentDetails,
    FineosExtractVpeiPaymentLine,
    PaymentLine,
)
from massgov.pfml.delegated_payments.backfill.backfill_pay_period_lines_step import (
    BackfillPayPeriodLinesStep,
)
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory
from massgov.pfml.util.datetime import datetime_str_to_date


@pytest.fixture
def backfill_pay_period_lines_step(
    initialize_factories_session, test_db_session, test_db_other_session
):
    return BackfillPayPeriodLinesStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


def generate_fineos_details_and_lines(
    detail_count: int, line_count: int, has_payment_detail: bool = True
):
    payment_details = []
    payment_lines = []

    for i in range(1, detail_count + 1):
        if has_payment_detail:
            payment_detail = FineosExtractVpeiPaymentDetailsFactory.create(
                paymentstartp=f"2022-0{i}-01 12:00:00",
                paymentendper=f"2022-0{i}-28 12:00:00",
                balancingamou_monamt=f"100.0{i}",
            )
            payment_details.append(payment_detail)

        for j in range(line_count):
            payment_line = FineosExtractVpeiPaymentLineFactory.create(
                linetype=f"Line {i}-{j}",
                paymentdetailclassid=payment_detail.c if has_payment_detail else None,
                paymentdetailindexid=payment_detail.i if has_payment_detail else None,
                amount_monamt=f"100.{i}{j}",
            )
            payment_lines.append(payment_line)

    return payment_details, payment_lines


def get_ref_file() -> ReferenceFile:
    return ReferenceFileFactory.create(
        reference_file_type_id=ReferenceFileType.PAYMENT_EXTRACT.reference_file_type_id
    )


def get_import_log() -> ImportLog:
    return ImportLogFactory.create()


def setup_payment(
    test_db_session,
    payment_detail_rows: List[FineosExtractVpeiPaymentDetails],
    payment_line_rows: List[FineosExtractVpeiPaymentLine],
    reference_file: Optional[ReferenceFile] = None,
    import_log: Optional[ImportLog] = None,
    is_payment_detail_already_backfilled: bool = False,
    is_payment_line_already_backfilled: bool = False,
):
    if not reference_file:
        reference_file = get_ref_file()

    if not import_log:
        import_log = get_import_log()

    factory = DelegatedPaymentFactory(test_db_session, import_log=import_log)
    payment = factory.get_or_create_payment()

    # Create the VPEI record for the payment
    # And connect the payment to it
    vpei_record = FineosExtractVpeiFactory.create(
        c=payment.fineos_pei_c_value,
        i=payment.fineos_pei_i_value,
        reference_file_id=reference_file.reference_file_id,
        fineos_extract_import_log_id=import_log.import_log_id,
    )
    payment.vpei_id = vpei_record.vpei_id

    for payment_detail_row in payment_detail_rows:

        # Update the passed in rows to be able to connect to payment we just made
        payment_detail_row.peclassid = payment.fineos_pei_c_value
        payment_detail_row.peindexid = payment.fineos_pei_i_value
        payment_detail_row.reference_file_id = reference_file.reference_file_id
        payment_detail_row.fineos_extract_import_log_id = import_log.import_log_id

        payment_details_c_value = None
        payment_details_i_value = None
        vpei_payment_details_id = None

        if is_payment_detail_already_backfilled:
            payment_details_c_value = payment_detail_row.c
            payment_details_i_value = payment_detail_row.i
            vpei_payment_details_id = payment_detail_row.vpei_payment_details_id

        factory.create_payment_detail(
            payment_details_c_value=payment_details_c_value,
            payment_details_i_value=payment_details_i_value,
            vpei_payment_details_id=vpei_payment_details_id,
            # These below values are used for matching
            period_start_date=datetime_str_to_date(payment_detail_row.paymentstartp),
            period_end_date=datetime_str_to_date(payment_detail_row.paymentendper),
            amount=Decimal(payment_detail_row.balancingamou_monamt),
        )

    # Update the payment lines to be able to
    # connect them to the payment.
    for payment_line_row in payment_line_rows:
        payment_line_row.c_pymnteif_paymentlines = payment.fineos_pei_c_value
        payment_line_row.i_pymnteif_paymentlines = payment.fineos_pei_i_value
        payment_line_row.reference_file_id = reference_file.reference_file_id

        if is_payment_line_already_backfilled:
            payment_line = PaymentLine(
                vpei_payment_line_id=payment_line_row.vpei_payment_line_id,
                payment_id=payment.payment_id,
                payment_line_c_value=payment_line_row.c,
                payment_line_i_value=payment_line_row.i,
                amount=Decimal(payment_line_row.amount_monamt),
                line_type=payment_line_row.linetype,
            )
            test_db_session.add(payment_line)

    test_db_session.commit()

    return payment


def validate_payment_details(
    payment: Payment, raw_payment_details: List[FineosExtractVpeiPaymentDetails]
):
    payment_details = payment.payment_details

    assert len(payment_details) == len(raw_payment_details)

    raw_mapping = {
        raw_payment_detail.vpei_payment_details_id: raw_payment_detail
        for raw_payment_detail in raw_payment_details
    }

    for payment_detail in payment_details:
        assert payment_detail.vpei_payment_details_id

        raw_payment_detail = raw_mapping.get(payment_detail.vpei_payment_details_id)
        assert raw_payment_detail

        assert payment_detail.payment_details_c_value == raw_payment_detail.c
        assert payment_detail.payment_details_i_value == raw_payment_detail.i

        assert raw_payment_detail.peclassid == payment.fineos_pei_c_value
        assert raw_payment_detail.peindexid == payment.fineos_pei_i_value


def validate_payment_lines(
    payment: Payment,
    raw_payment_lines: List[FineosExtractVpeiPaymentLine],
    has_payment_details: bool = True,
):
    payment_lines = payment.payment_lines

    assert len(payment_lines) == len(raw_payment_lines)

    raw_mapping = {
        raw_payment_line.vpei_payment_line_id: raw_payment_line
        for raw_payment_line in raw_payment_lines
    }

    for payment_line in payment_lines:
        assert payment_line.vpei_payment_line_id

        raw_payment_line = raw_mapping.get(payment_line.vpei_payment_line_id)
        assert raw_payment_line

        assert payment_line.payment_line_c_value == raw_payment_line.c
        assert payment_line.payment_line_i_value == raw_payment_line.i
        assert str(payment_line.amount) == raw_payment_line.amount_monamt
        assert payment_line.line_type == raw_payment_line.linetype

        # Make sure it was associated with the right payment details
        if has_payment_details:
            assert (
                payment_line.payment_details_id
                and payment_line.payment_details.payment_id == payment.payment_id
            )
            assert (
                raw_payment_line.paymentdetailclassid
                == payment_line.payment_details.payment_details_c_value
            )
            assert (
                raw_payment_line.paymentdetailindexid
                == payment_line.payment_details.payment_details_i_value
            )
        else:
            assert payment_line.payment_details_id is None

        # Make sure it was associated with the right payment
        assert raw_payment_line.c_pymnteif_paymentlines == payment.fineos_pei_c_value
        assert raw_payment_line.i_pymnteif_paymentlines == payment.fineos_pei_i_value
        assert (
            raw_payment_line.fineos_extract_import_log_id
            == payment.vpei.fineos_extract_import_log_id
        )


def test_happy_path(test_db_session, backfill_pay_period_lines_step):
    # Create the raw staging table records
    # and setup the payments in the manner
    # we expect for a backfill
    reference_file = get_ref_file()
    import_log = get_import_log()

    payment_detail_rows1, payment_line_rows1 = generate_fineos_details_and_lines(
        detail_count=2,
        line_count=3,
    )
    payment1 = setup_payment(
        test_db_session, payment_detail_rows1, payment_line_rows1, reference_file, import_log
    )

    payment_detail_rows2, payment_line_rows2 = generate_fineos_details_and_lines(
        detail_count=1, line_count=5
    )
    payment2 = setup_payment(
        test_db_session, payment_detail_rows2, payment_line_rows2, reference_file, import_log
    )

    payment_detail_rows3, payment_line_rows3 = generate_fineos_details_and_lines(
        detail_count=5, line_count=2
    )
    payment3 = setup_payment(
        test_db_session, payment_detail_rows3, payment_line_rows3, reference_file, import_log
    )

    # Run
    backfill_pay_period_lines_step.run()

    # Refresh the payments so the payment_detail/lines get found
    test_db_session.refresh(payment1)
    test_db_session.refresh(payment2)
    test_db_session.refresh(payment3)

    # Verify everything was set as expected
    validate_payment_details(payment1, payment_detail_rows1)
    validate_payment_lines(payment1, payment_line_rows1)

    validate_payment_details(payment2, payment_detail_rows2)
    validate_payment_lines(payment2, payment_line_rows2)

    validate_payment_details(payment3, payment_detail_rows3)
    validate_payment_lines(payment3, payment_line_rows3)

    metrics = backfill_pay_period_lines_step.log_entry.metrics
    assert metrics[BackfillPayPeriodLinesStep.Metrics.TOTAL_BATCH_COUNT] == 1
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PROCESSED_BATCH_COUNT] == 1
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_PROCESSED_COUNT] == 3
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_DETAIL_PROCESSED_COUNT] == len(
        payment_detail_rows1 + payment_detail_rows2 + payment_detail_rows3
    )
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_LINE_PROCESSED_COUNT] == len(
        payment_line_rows1 + payment_line_rows2 + payment_line_rows3
    )


def test_happy_path_separate_batches(test_db_session, backfill_pay_period_lines_step):
    # Similar to the happy path test
    # but the payments are all in separate
    # batches and ref files.

    ref_file1, import_log1 = get_ref_file(), get_import_log()
    payment_detail_rows1, payment_line_rows1 = generate_fineos_details_and_lines(
        detail_count=2,
        line_count=3,
    )
    payment1 = setup_payment(
        test_db_session, payment_detail_rows1, payment_line_rows1, ref_file1, import_log1
    )

    ref_file2, import_log2 = get_ref_file(), get_import_log()
    payment_detail_rows2, payment_line_rows2 = generate_fineos_details_and_lines(
        detail_count=1, line_count=5
    )
    payment2 = setup_payment(
        test_db_session, payment_detail_rows2, payment_line_rows2, ref_file2, import_log2
    )

    ref_file3, import_log3 = get_ref_file(), get_import_log()
    payment_detail_rows3, payment_line_rows3 = generate_fineos_details_and_lines(
        detail_count=5, line_count=2
    )
    payment3 = setup_payment(
        test_db_session, payment_detail_rows3, payment_line_rows3, ref_file3, import_log3
    )

    # Run
    backfill_pay_period_lines_step.run()

    # Refresh the payments so the payment_detail/lines get found
    test_db_session.refresh(payment1)
    test_db_session.refresh(payment2)
    test_db_session.refresh(payment3)

    # Verify everything was set as expected
    validate_payment_details(payment1, payment_detail_rows1)
    validate_payment_lines(payment1, payment_line_rows1)

    validate_payment_details(payment2, payment_detail_rows2)
    validate_payment_lines(payment2, payment_line_rows2)

    validate_payment_details(payment3, payment_detail_rows3)
    validate_payment_lines(payment3, payment_line_rows3)

    # Only noteworthy difference is the number of batches
    metrics = backfill_pay_period_lines_step.log_entry.metrics
    assert metrics[BackfillPayPeriodLinesStep.Metrics.TOTAL_BATCH_COUNT] == 3
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PROCESSED_BATCH_COUNT] == 3
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_PROCESSED_COUNT] == 3
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_DETAIL_PROCESSED_COUNT] == len(
        payment_detail_rows1 + payment_detail_rows2 + payment_detail_rows3
    )
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_LINE_PROCESSED_COUNT] == len(
        payment_line_rows1 + payment_line_rows2 + payment_line_rows3
    )


def test_payments_already_backfilled(test_db_session, backfill_pay_period_lines_step):
    # Each of these payments already
    # has payment details and payment lines.

    payment_detail_rows1, payment_line_rows1 = generate_fineos_details_and_lines(
        detail_count=2,
        line_count=3,
    )
    setup_payment(
        test_db_session,
        payment_detail_rows1,
        payment_line_rows1,
        is_payment_detail_already_backfilled=True,
        is_payment_line_already_backfilled=True,
    )

    payment_detail_rows2, payment_line_rows2 = generate_fineos_details_and_lines(
        detail_count=1, line_count=5
    )
    setup_payment(
        test_db_session,
        payment_detail_rows2,
        payment_line_rows2,
        is_payment_detail_already_backfilled=True,
        is_payment_line_already_backfilled=True,
    )

    payment_detail_rows3, payment_line_rows3 = generate_fineos_details_and_lines(
        detail_count=5, line_count=2
    )
    setup_payment(
        test_db_session,
        payment_detail_rows3,
        payment_line_rows3,
        is_payment_detail_already_backfilled=True,
        is_payment_line_already_backfilled=True,
    )

    backfill_pay_period_lines_step.run()

    # Verify we didn't meaningfully process anything
    # and just skipped over updating the records
    metrics = backfill_pay_period_lines_step.log_entry.metrics
    assert metrics[BackfillPayPeriodLinesStep.Metrics.TOTAL_BATCH_COUNT] == 3
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PROCESSED_BATCH_COUNT] == 3
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_PROCESSED_COUNT] == 0
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_DETAIL_ALREADY_PRESENT_COUNT] == len(
        payment_detail_rows1 + payment_detail_rows2 + payment_detail_rows3
    )
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_LINE_ALREADY_PRESENT_COUNT] == len(
        payment_line_rows1 + payment_line_rows2 + payment_line_rows3
    )
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_DETAIL_PROCESSED_COUNT] == 0
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_LINE_PROCESSED_COUNT] == 0


def test_payment_has_no_payment_details(test_db_session, backfill_pay_period_lines_step):
    # Certain payments won't have payment details
    # and that is fine.
    payment_detail_rows, payment_line_rows = generate_fineos_details_and_lines(
        detail_count=2, line_count=3, has_payment_detail=False
    )
    assert not payment_detail_rows
    payment = setup_payment(test_db_session, payment_detail_rows, payment_line_rows)

    # Run
    backfill_pay_period_lines_step.run()

    # Refresh the payments so the payment_detail/lines get found
    test_db_session.refresh(payment)

    validate_payment_details(payment, payment_detail_rows)
    validate_payment_lines(payment, payment_line_rows, has_payment_details=False)

    metrics = backfill_pay_period_lines_step.log_entry.metrics
    assert metrics[BackfillPayPeriodLinesStep.Metrics.TOTAL_BATCH_COUNT] == 1
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_PROCESSED_COUNT] == 1
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_DETAIL_PROCESSED_COUNT] == 0
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_DETAIL_NO_RECORDS_COUNT] == 1
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_LINE_PROCESSED_COUNT] == len(
        payment_line_rows
    )
    assert metrics[
        BackfillPayPeriodLinesStep.Metrics.PAYMENT_LINE_DETAIL_MISSING_UNEXPECTED_COUNT
    ] == len(payment_line_rows)


def test_payment_no_details_or_lines(test_db_session, backfill_pay_period_lines_step):
    payment = setup_payment(test_db_session, [], [])
    backfill_pay_period_lines_step.run()

    test_db_session.refresh(payment)
    assert not payment.payment_details
    assert not payment.payment_lines

    metrics = backfill_pay_period_lines_step.log_entry.metrics
    assert metrics[BackfillPayPeriodLinesStep.Metrics.TOTAL_BATCH_COUNT] == 1
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_PROCESSED_COUNT] == 1
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_DETAIL_NO_RECORDS_COUNT] == 1
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_LINE_NO_RECORDS_COUNT] == 1
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_DETAIL_PROCESSED_COUNT] == 0
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_LINE_PROCESSED_COUNT] == 0


def test_no_vpei_record_attached(test_db_session, backfill_pay_period_lines_step):
    # Setup like normal as if
    # this was happy path
    payment_detail_rows1, payment_line_rows1 = generate_fineos_details_and_lines(
        detail_count=2,
        line_count=3,
    )
    payment = setup_payment(test_db_session, payment_detail_rows1, payment_line_rows1)

    # Unset the VPEI ID
    # the record still exists,
    # but we won't have a link
    payment.vpei_id = None
    test_db_session.commit()

    backfill_pay_period_lines_step.run()
    test_db_session.refresh(payment)

    # The initial payment query skips payments without a VPEI ID
    metrics = backfill_pay_period_lines_step.log_entry.metrics
    assert metrics[BackfillPayPeriodLinesStep.Metrics.TOTAL_BATCH_COUNT] == 0
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_PROCESSED_COUNT] == 0
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_MISSING_VPEI_ID_COUNT] == 0
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_DETAIL_PROCESSED_COUNT] == 0
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_LINE_PROCESSED_COUNT] == 0

    # Just for the sake of it, if we forced it to run through
    # the logic to see what would happen.
    backfill_pay_period_lines_step.process_payment(payment, payment.fineos_extract_import_log)
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_PROCESSED_COUNT] == 0
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_MISSING_VPEI_ID_COUNT] == 1
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_DETAIL_PROCESSED_COUNT] == 0
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_LINE_PROCESSED_COUNT] == 0


def test_payment_details_same_periods(test_db_session, backfill_pay_period_lines_step):
    # Test what happens if the payment details
    # have the same dates and can't be distinguished
    # by just making the same payment details twice
    payment_detail_rows1, payment_line_rows1 = generate_fineos_details_and_lines(
        detail_count=2,
        line_count=3,
    )
    payment_detail_rows2, _ = generate_fineos_details_and_lines(
        detail_count=2,
        line_count=0,
    )
    payment = setup_payment(
        test_db_session, payment_detail_rows1 + payment_detail_rows2, payment_line_rows1
    )

    backfill_pay_period_lines_step.run()
    test_db_session.refresh(payment)

    # Every payment detail record still gets
    # attached because we effectively have two
    # copies of each and there was nothing to distinguish them
    # We're fine with this in the unlikely case it happens
    validate_payment_details(payment, payment_detail_rows1 + payment_detail_rows2)
    validate_payment_lines(payment, payment_line_rows1)

    metrics = backfill_pay_period_lines_step.log_entry.metrics
    assert metrics[BackfillPayPeriodLinesStep.Metrics.TOTAL_BATCH_COUNT] == 1
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_PROCESSED_COUNT] == 1
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_DETAIL_PROCESSED_COUNT] == len(
        payment_detail_rows1 + payment_detail_rows2
    )
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_DETAIL_MULTIPLE_MATCH_COUNT] == len(
        payment_detail_rows2
    )


def test_non_numeric_payment_line_amount(test_db_session, backfill_pay_period_lines_step):
    # Verify if we get a payment line amount
    # that can't be converted to a decimal,
    # we don't fail the process, but do skip the line
    payment_detail_rows, payment_line_rows = generate_fineos_details_and_lines(
        detail_count=2, line_count=3
    )
    for payment_line_row in payment_line_rows:
        payment_line_row.amount_monamt = "text"

    payment = setup_payment(test_db_session, payment_detail_rows, payment_line_rows)

    backfill_pay_period_lines_step.run()
    test_db_session.refresh(payment)

    # Payment lines not created on the payment
    validate_payment_details(payment, payment_detail_rows)
    validate_payment_lines(payment, [])

    metrics = backfill_pay_period_lines_step.log_entry.metrics
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_LINE_PROCESSED_COUNT] == len(
        payment_line_rows
    )
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_LINE_AMOUNT_NON_NUMERIC_COUNT] == len(
        payment_line_rows
    )


def test_payment_detail_count_mismatch(test_db_session, backfill_pay_period_lines_step):
    # Show what happens when the number of payment
    # line records doesn't match
    payment_detail_rows, payment_line_rows = generate_fineos_details_and_lines(
        detail_count=2, line_count=3
    )
    payment = setup_payment(test_db_session, payment_detail_rows, payment_line_rows)

    # Delete one of the staging table rows from the DB
    test_db_session.delete(payment_detail_rows[1])

    backfill_pay_period_lines_step.run()
    test_db_session.refresh(payment)

    # Verify the payment details were not updated
    for payment_detail in payment.payment_details:
        assert payment_detail.vpei_payment_details_id is None

    metrics = backfill_pay_period_lines_step.log_entry.metrics
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_DETAIL_PROCESSED_COUNT] == len(
        payment_detail_rows
    )
    assert (
        metrics[BackfillPayPeriodLinesStep.Metrics.RAW_PAYMENT_DETAIL_PROCESSED_COUNT]
        == len(payment_detail_rows) - 1
    )
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_DETAIL_MISMATCH_COUNT] == 1


def test_payment_detail_no_match(test_db_session, backfill_pay_period_lines_step):
    payment_detail_rows, payment_line_rows = generate_fineos_details_and_lines(
        detail_count=2, line_count=3
    )
    payment = setup_payment(test_db_session, payment_detail_rows, payment_line_rows)

    # Modify the date on the payment detail after
    # we setup the payment so they don't match in processing
    payment_detail_rows[0].paymentstartp = "1999-0{i}-01 12:00:00"
    test_db_session.commit()

    backfill_pay_period_lines_step.run()
    test_db_session.refresh(payment)

    # Find the payment detail that wasn't updated
    not_updated_payment_details = [
        payment_detail
        for payment_detail in payment.payment_details
        if payment_detail.vpei_payment_details_id is None
    ]
    assert len(not_updated_payment_details) == 1
    # Verify the non-updated one is the same by the amount that does match
    assert str(not_updated_payment_details[0].amount) == payment_detail_rows[0].balancingamou_monamt

    metrics = backfill_pay_period_lines_step.log_entry.metrics
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_DETAIL_PROCESSED_COUNT] == len(
        payment_detail_rows
    )
    assert metrics[BackfillPayPeriodLinesStep.Metrics.PAYMENT_DETAIL_NO_MATCH_COUNT] == 1
