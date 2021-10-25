import datetime
import os

import boto3
import pytest

import massgov.pfml.reductions.reports.consolidated_dia_payments.create as create_report
from massgov.pfml.db.models.employees import ReferenceFile, ReferenceFileType, State, StateLog
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    DiaReductionPaymentFactory,
    EmployeeFactory,
    EmployeeWithFineosNumberFactory,
)


def test_get_distinct_grouping_keys_returns_distinct_fineos_customer_id_and_board_no_tuples(
    test_db_session, initialize_factories_session
):
    employee_1 = EmployeeWithFineosNumberFactory.create()

    DiaReductionPaymentFactory.create_batch(
        size=2, fineos_customer_number=employee_1.fineos_customer_number, board_no="group1"
    )

    DiaReductionPaymentFactory.create_batch(
        size=2, fineos_customer_number=employee_1.fineos_customer_number, board_no="group2"
    )

    employee_2 = EmployeeWithFineosNumberFactory.create()
    DiaReductionPaymentFactory.create_batch(
        size=2, fineos_customer_number=employee_2.fineos_customer_number, board_no="group3"
    )

    # Test repeated groups are separated by fineos_customer_number
    DiaReductionPaymentFactory.create_batch(
        size=2, fineos_customer_number=employee_2.fineos_customer_number, board_no="group1"
    )

    # Duplicate data - will be discarded
    DiaReductionPaymentFactory.create_batch(
        size=2, fineos_customer_number=employee_1.fineos_customer_number, board_no="group1"
    )

    distinct_tuples = create_report._get_distinct_grouping_keys(test_db_session)

    assert len(distinct_tuples) == 4

    expected_pairs = {
        (employee_1.fineos_customer_number, "group1"),
        (employee_1.fineos_customer_number, "group2"),
        (employee_2.fineos_customer_number, "group3"),
        (employee_2.fineos_customer_number, "group1"),
    }

    assert set(distinct_tuples) == expected_pairs
    assert len(set(distinct_tuples)) == 4


def test_get_record_group_sorts_by_start_date_then_award_created(
    test_db_session, initialize_factories_session
):
    employee = EmployeeWithFineosNumberFactory.create()

    start_date = datetime.datetime(2021, 1, 1)

    payment_1 = DiaReductionPaymentFactory.create(
        fineos_customer_number=employee.fineos_customer_number,
        board_no="group1",
        start_date=start_date,
        award_created_date=start_date + datetime.timedelta(days=1),
        event_id="one",
    )

    # same start date as payment 1 but will appear in results first because tie is broken by award created
    payment_2 = DiaReductionPaymentFactory.create(
        fineos_customer_number=employee.fineos_customer_number,
        board_no="group1",
        start_date=start_date,
        award_created_date=start_date,
        event_id="two,",
    )

    # will appear last in query - start date is later than previous 2 records
    payment_3 = DiaReductionPaymentFactory.create(
        fineos_customer_number=employee.fineos_customer_number,
        board_no="group1",
        start_date=start_date + datetime.timedelta(days=1),
        award_created_date=start_date,
        event_id="three",
    )

    # This payment will be ignored by our query because it does not match the grouping criteria - board_no is different
    DiaReductionPaymentFactory.create(
        fineos_customer_number=employee.fineos_customer_number,
        board_no="group2",
        start_date=start_date + datetime.timedelta(days=1),
        award_created_date=start_date,
        event_id="four",
    )

    ClaimFactory.create(employee=employee)

    group_key = create_report.PaymentGroupKey(employee.fineos_customer_number, "group1")
    payment_data = create_report._get_record_group(test_db_session, group_key)

    assert len(payment_data) == 3
    assert payment_data[0].event_id == payment_2.event_id
    assert payment_data[1].event_id == payment_1.event_id
    assert payment_data[2].event_id == payment_3.event_id


def test_consolidate_record_group_adds_156_weeks_to_start_date_if_no_end_date(
    test_db_session, initialize_factories_session
):
    employee_1 = EmployeeWithFineosNumberFactory.create()

    start_date = datetime.datetime(2021, 1, 1)

    DiaReductionPaymentFactory.create(
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date,
        termination_date=None,
    )

    ClaimFactory.create(employee=employee_1)

    consolidated_records, _ = create_report._get_consolidated_records(test_db_session)
    expected_termination_date = (start_date + datetime.timedelta(weeks=156)).date()

    assert consolidated_records[0].termination_date == expected_termination_date


def test_consolidate_record_group_tolerates_null_start_dates(
    test_db_session, initialize_factories_session
):
    employee_1 = EmployeeWithFineosNumberFactory.create()

    start_date = datetime.datetime(2021, 1, 1)

    DiaReductionPaymentFactory.create(
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        termination_date=None,
        start_date=None,
        award_created_date=None,
    )

    DiaReductionPaymentFactory.create(
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date,
        termination_date=None,
    )

    ClaimFactory.create(employee=employee_1)

    consolidated_records, _ = create_report._get_consolidated_records(test_db_session)
    expected_termination_date = (start_date + datetime.timedelta(weeks=156)).date()

    assert consolidated_records[0].termination_date == expected_termination_date


def test_get_consolidated_records_returns_group_as_failure_if_start_date_missing(
    test_db_session, initialize_factories_session
):
    employee_1 = EmployeeWithFineosNumberFactory.create()

    start_date = datetime.datetime(2021, 1, 1)

    DiaReductionPaymentFactory.create(
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        termination_date=None,
        start_date=start_date,
        award_created_date=None,
        weekly_amount=777,
    )

    DiaReductionPaymentFactory.create(
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=None,
        termination_date=None,
        weekly_amount=789,
    )

    ClaimFactory.create(employee=employee_1)

    consolidated_records, error_records = create_report._get_consolidated_records(test_db_session)

    assert len(consolidated_records) == 0
    assert len(error_records) == 2


def test_consolidate_rows_ignores_duplicate_records(test_db_session, initialize_factories_session):
    employee_1 = EmployeeWithFineosNumberFactory.create()

    start_date = datetime.datetime(2021, 1, 1)

    DiaReductionPaymentFactory.create_batch(
        size=3,
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date,
        termination_date=None,
        weekly_amount=750,
        event_description="Test",
    )

    ClaimFactory.create(employee=employee_1)

    consolidated_records, _ = create_report._get_consolidated_records(test_db_session)

    # Consolidates duplicated records into 1 record
    assert len(consolidated_records) == 1

    # Adds termination date
    expected_termination_date = (start_date + datetime.timedelta(weeks=156)).date()
    assert consolidated_records[0].termination_date == expected_termination_date


def test_consolidate_rows_uses_start_date_of_subsequent_records_for_termination_date_if_amount_changes(
    test_db_session, initialize_factories_session
):
    employee_1 = EmployeeWithFineosNumberFactory.create()

    start_date = datetime.datetime(2021, 1, 1)

    DiaReductionPaymentFactory.create(
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date,
        termination_date=None,
        weekly_amount=700,
    )

    # Award amount changes - first record will use start date of this record minus one day for end date.
    DiaReductionPaymentFactory.create(
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date + datetime.timedelta(weeks=4),
        termination_date=None,
        weekly_amount=750,
    )

    ClaimFactory.create(employee=employee_1)

    consolidated_records, _ = create_report._get_consolidated_records(test_db_session)

    # One day before start date of subsequent record with amount change
    expected_termination_date_first_record = (start_date + datetime.timedelta(days=27)).date()
    expected_termination_date_last_record = (start_date + datetime.timedelta(weeks=156)).date()

    assert consolidated_records[0].termination_date == expected_termination_date_first_record
    assert consolidated_records[1].termination_date == expected_termination_date_last_record


def test_get_consolidated_records_merges_records_if_amount_stays_the_same(
    test_db_session, initialize_factories_session
):
    employee_1 = EmployeeWithFineosNumberFactory.create()

    start_date = datetime.datetime(2021, 1, 1)

    DiaReductionPaymentFactory.create(
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date,
        termination_date=None,
        weekly_amount=750,
        event_description="Test",
    )

    DiaReductionPaymentFactory.create(
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date + datetime.timedelta(weeks=2),
        termination_date=None,
        weekly_amount=750,
        event_description="Test",
    )

    DiaReductionPaymentFactory.create(
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date + datetime.timedelta(weeks=4),
        termination_date=None,
        weekly_amount=750,
        event_description="Test",
    )

    ClaimFactory.create(employee=employee_1)

    consolidated_records, _ = create_report._get_consolidated_records(test_db_session)

    # Consolidates similar records into 1 record
    assert len(consolidated_records) == 1
    # Adds termination date
    expected_termination_date = (start_date + datetime.timedelta(weeks=156)).date()
    assert consolidated_records[0].termination_date == expected_termination_date
    assert consolidated_records[0].start_date == start_date.date()


def test_get_consolidated_records_uses_end_date_from_subsequent_record(
    test_db_session, initialize_factories_session
):
    employee_1 = EmployeeWithFineosNumberFactory.create()

    start_date = datetime.datetime(2021, 1, 1)

    DiaReductionPaymentFactory.create_batch(
        size=2,
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date,
        award_created_date=start_date + datetime.timedelta(days=1),
        termination_date=None,
        weekly_amount=750,
        event_description="Test",
    )

    termination_date = start_date + datetime.timedelta(weeks=5)

    DiaReductionPaymentFactory.create_batch(
        size=2,
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date,
        award_created_date=start_date + datetime.timedelta(days=2),
        termination_date=termination_date,
        weekly_amount=750,
        event_description="Test",
    )

    ClaimFactory.create(employee=employee_1)

    consolidated_records, _ = create_report._get_consolidated_records(test_db_session)

    # Consolidates all records
    assert len(consolidated_records) == 1

    # Adds termination date from the last record
    assert consolidated_records[0].termination_date == termination_date.date()


def test_get_consolidated_records_uses_end_date_from_termination_record_and_discards_termination(
    test_db_session, initialize_factories_session
):
    employee_1 = EmployeeWithFineosNumberFactory.create()

    start_date = datetime.datetime(2021, 1, 1)

    DiaReductionPaymentFactory.create_batch(
        size=2,
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date,
        award_created_date=start_date + datetime.timedelta(days=1),
        termination_date=None,
        weekly_amount=750,
        event_description="Test",
    )

    termination_date = start_date + datetime.timedelta(weeks=5)

    DiaReductionPaymentFactory.create(
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date,
        award_created_date=start_date + datetime.timedelta(days=2),
        termination_date=termination_date,
        weekly_amount=750,
        event_description="NT",
    )

    ClaimFactory.create(employee=employee_1)

    consolidated_records, _ = create_report._get_consolidated_records(test_db_session)

    # Consolidates all records
    assert len(consolidated_records) == 1

    # Adds termination date from the last record
    assert consolidated_records[0].termination_date == termination_date.date()


def test_test_get_consolidated_records_calculates_one_row_for_each_wage_change(
    test_db_session, initialize_factories_session
):
    employee_1 = EmployeeWithFineosNumberFactory.create()

    start_date = datetime.datetime(2021, 1, 1)

    # Will be kept because next record is a wage change.
    DiaReductionPaymentFactory.create_batch(
        size=2,
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date,
        award_created_date=start_date + datetime.timedelta(days=1),
        termination_date=None,
        weekly_amount=750,
        event_description="Test",
    )

    # Wage change record. Previous record will use this start date - 1 day as its end date.
    DiaReductionPaymentFactory.create(
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date + datetime.timedelta(weeks=4),
        award_created_date=start_date + datetime.timedelta(days=1),
        termination_date=None,
        weekly_amount=850,
        event_description="Test",
    )

    # Subsequent records from wage change - will be merged with other records with same wage.
    DiaReductionPaymentFactory.create_batch(
        size=2,
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date + datetime.timedelta(weeks=5),
        award_created_date=start_date + datetime.timedelta(days=1),
        termination_date=None,
        weekly_amount=850,
        event_description="Test",
    )

    # Another wage change. Previous records will become 1 record and use the start date minus 1 day of this record for end date.
    DiaReductionPaymentFactory.create_batch(
        size=2,
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date + datetime.timedelta(weeks=6),
        award_created_date=start_date + datetime.timedelta(days=1),
        termination_date=None,
        weekly_amount=700,
        event_description="Test",
    )

    termination_date = start_date + datetime.timedelta(weeks=10)
    # Termination record - Previous record will use this records end date. This record will be dropped.
    DiaReductionPaymentFactory.create(
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date + datetime.timedelta(weeks=7),
        award_created_date=start_date + datetime.timedelta(days=2),
        termination_date=termination_date,
        weekly_amount=700,
        event_description="NT",
    )

    ClaimFactory.create(employee=employee_1)

    consolidated_records, _ = create_report._get_consolidated_records(test_db_session)

    # Consolidates all records
    # Expect 3 records because there were 2 wage changes after first record
    assert len(consolidated_records) == 3

    # First record - uses start date from first wage change record
    assert consolidated_records[0].termination_date == (
        consolidated_records[1].start_date - datetime.timedelta(days=1)
    )
    assert consolidated_records[0].weekly_amount == 750

    # Second record - uses start date from second wage change record
    assert consolidated_records[1].termination_date == (
        consolidated_records[2].start_date - datetime.timedelta(days=1)
    )
    assert consolidated_records[1].weekly_amount == 850

    # Third record - uses end date from following termination record
    assert consolidated_records[2].termination_date == termination_date.date()
    assert consolidated_records[2].weekly_amount == 700
    # Termination record is dropped, so we see description from previous record
    assert consolidated_records[2].event_description == "Test"


def test_get_consolidated_records_calculates_one_row_for_each_termination(
    test_db_session, initialize_factories_session
):
    employee_1 = EmployeeWithFineosNumberFactory.create()

    start_date = datetime.datetime(2021, 1, 1)

    DiaReductionPaymentFactory.create_batch(
        size=2,
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date,
        award_created_date=start_date + datetime.timedelta(days=1),
        termination_date=None,
        weekly_amount=750,
        event_description="Test",
    )

    termination_date = start_date + datetime.timedelta(weeks=8)

    DiaReductionPaymentFactory.create(
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date,
        award_created_date=start_date + datetime.timedelta(days=2),
        termination_date=termination_date,
        weekly_amount=750,
        event_description="NT",
    )

    DiaReductionPaymentFactory.create_batch(
        size=2,
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date + datetime.timedelta(weeks=8),
        award_created_date=start_date + datetime.timedelta(days=1),
        termination_date=None,
        weekly_amount=750,
        event_description="Test",
    )

    second_termination_date = start_date + datetime.timedelta(weeks=16)

    DiaReductionPaymentFactory.create(
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        start_date=start_date + datetime.timedelta(weeks=8),
        award_created_date=start_date + datetime.timedelta(days=2),
        termination_date=second_termination_date,
        weekly_amount=750,
        event_description="NT",
    )

    ClaimFactory.create(employee=employee_1)

    consolidated_records, _ = create_report._get_consolidated_records(test_db_session)

    # Consolidates records
    assert len(consolidated_records) == 2

    # Adds termination date from first termination record, drops the termination record
    assert consolidated_records[0].termination_date == termination_date.date()
    assert consolidated_records[0].event_description == "Test"

    # Adds termination date from second termination record, drops the termination record
    assert consolidated_records[1].termination_date == second_termination_date.date()
    assert consolidated_records[1].event_description == "Test"


@pytest.fixture
def expected_error_csv():
    """
    The fixture file needs to be encoded with \r\n for newline characters.
    Saving the file in vscode will ruin this encoding and cause the test to fail.
    """
    return open(
        os.path.join(
            os.path.dirname(__file__), "test_files", "expected_consolidated_dia_report_errors.csv"
        ),
        "rb",
    ).read()


@pytest.fixture
def expected_csv():
    """
    The fixture file needs to be encoded with \r\n for newline characters.
    Saving the file in vscode will ruin this encoding and cause the test to fail.
    """
    return open(
        os.path.join(
            os.path.dirname(__file__), "test_files", "expected_consolidated_dia_report.csv"
        ),
        "rb",
    ).read()


def test_create_report_consolidated_dia_payments_to_dfml(
    initialize_factories_session,
    monkeypatch,
    mock_s3_bucket,
    test_db_session,
    expected_csv,
    expected_error_csv,
):
    s3_bucket_uri = "s3://" + mock_s3_bucket
    dest_dir = "reductions/dfml/outbound"
    monkeypatch.setenv("S3_BUCKET", s3_bucket_uri)
    monkeypatch.setenv("S3_DFML_OUTBOUND_DIRECTORY_PATH", dest_dir)

    employee_1 = EmployeeFactory.create(fineos_customer_number="9787")

    # If first record in the group has no start date, the group will get saved to the error report
    DiaReductionPaymentFactory.create_batch(
        size=2,
        fineos_customer_number=employee_1.fineos_customer_number,
        board_no="group1",
        event_id=None,
        event_description="Test",
        eve_created_date=None,
        event_occurrence_date=None,
        award_id=None,
        award_code=None,
        award_amount=None,
        award_date=None,
        start_date=None,
        end_date=None,
        award_created_date=None,
        termination_date=None,
        weekly_amount=750,
    )

    employee_2 = EmployeeFactory.create(fineos_customer_number="1034")

    start_date = datetime.datetime(2021, 1, 1)
    termination_date = start_date + datetime.timedelta(weeks=5)
    DiaReductionPaymentFactory.create_batch(
        size=2,
        fineos_customer_number=employee_2.fineos_customer_number,
        board_no="group2",
        event_id=None,
        event_description="Test",
        eve_created_date=None,
        event_occurrence_date=None,
        award_id=None,
        award_code=None,
        award_amount=None,
        award_date=None,
        start_date=start_date,
        end_date=None,
        weekly_amount=750,
        award_created_date=None,
        termination_date=termination_date,
    )

    create_report.create_report_consolidated_dia_payments_to_dfml(test_db_session)

    # Expect that the file to appear in the mock_s3_bucket.
    s3 = boto3.client("s3")

    object_list = s3.list_objects(Bucket=mock_s3_bucket, Prefix=dest_dir)["Contents"]
    assert object_list
    assert len(object_list) == 2
    dest_filepath_prefix = os.path.join(dest_dir, create_report.DFML_REPORT_FILENAME_PREFIX)
    assert object_list[0]["Key"].startswith(dest_filepath_prefix)

    error_filename_prefix = dest_filepath_prefix + "ERRORS"
    assert object_list[1]["Key"].startswith(error_filename_prefix)

    ref_file = (
        test_db_session.query(ReferenceFile)
        .filter_by(
            reference_file_type_id=ReferenceFileType.DIA_CONSOLIDATED_REDUCTION_REPORT.reference_file_type_id
        )
        .all()
    )

    assert len(ref_file) == 1

    error_ref_file = (
        test_db_session.query(ReferenceFile)
        .filter_by(
            reference_file_type_id=ReferenceFileType.DIA_CONSOLIDATED_REDUCTION_REPORT_ERRORS.reference_file_type_id
        )
        .all()
    )
    assert len(error_ref_file) == 1

    uploaded_error_csv = s3.get_object(Bucket=mock_s3_bucket, Key=object_list[1]["Key"])[
        "Body"
    ].read()
    uploaded_csv = s3.get_object(Bucket=mock_s3_bucket, Key=object_list[0]["Key"])["Body"].read()

    assert uploaded_error_csv == expected_error_csv
    assert uploaded_csv == expected_csv

    state_log = (
        test_db_session.query(StateLog)
        .filter_by(end_state_id=State.DIA_CONSOLIDATED_REPORT_CREATED.state_id)
        .one()
    )
    assert state_log.outcome["message"] == "Created consolidated payments report for DIA"
    assert state_log.reference_file == ref_file[0]
