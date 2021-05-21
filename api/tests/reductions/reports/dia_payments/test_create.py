import csv
import datetime
import io
import os

import boto3
import pytest

import massgov.pfml.reductions.reports.dia_payments.create as dia_payments_reports_create
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    DiaReductionPaymentReferenceFile,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    DiaReductionPaymentFactory,
    EmployeeFactory,
    EmployeeWithFineosNumberFactory,
)
from massgov.pfml.util.batch.log import LogEntry


def test_write_dfml_report_rows_no_claim_info():
    output_file = io.StringIO()

    payment_data = (DiaReductionPaymentFactory.build(), None)
    payment_rows = [dia_payments_reports_create._make_report_row_from_payment(payment_data)]

    dia_payments_reports_create._write_dfml_report_rows(output_file, payment_rows)

    output_file.seek(0)
    rows = list(csv.DictReader(output_file))

    assert rows == [
        {
            "DFML_ID": payment_data[0].fineos_customer_number,
            "BOARD_NO": payment_data[0].board_no,
            "EVENT_ID": payment_data[0].event_id,
            "INS_FORM_OR_MEET": payment_data[0].event_description,
            "EVE_CREATED_DATE": payment_data[0].eve_created_date.strftime("%m/%d/%Y"),
            "FORM_RECEIVED_OR_DISPOSITION": payment_data[0].event_occurrence_date.strftime(
                "%m/%d/%Y"
            ),
            "AWARD_ID": payment_data[0].award_id,
            "AWARD_CODE": payment_data[0].award_code,
            "AWARD_AMOUNT": str(payment_data[0].award_amount),
            "AWARD_DATE": payment_data[0].award_date.strftime("%m/%d/%Y"),
            "START_DATE": payment_data[0].start_date.strftime("%m/%d/%Y"),
            "END_DATE": payment_data[0].end_date.strftime("%m/%d/%Y"),
            "WEEKLY_AMOUNT": str(payment_data[0].weekly_amount),
            "AWARD_CREATED_DATE": payment_data[0].award_created_date.strftime("%m/%d/%Y"),
            "TERMINATION_DATE": payment_data[0].termination_date.strftime("%m/%d/%Y"),
            "ABSENCE_CASE_ID": "",
            "ABSENCE_PERIOD_START_DATE": "",
            "ABSENCE_PERIOD_END_DATE": "",
            "ABSENCE_CASE_STATUS": "",
        }
    ]


def test_write_dfml_report_rows_some_claim_info():
    output_file = io.StringIO()

    payment_data = (DiaReductionPaymentFactory.build(), ClaimFactory.build())
    payment_rows = [dia_payments_reports_create._make_report_row_from_payment(payment_data)]

    dia_payments_reports_create._write_dfml_report_rows(output_file, payment_rows)

    output_file.seek(0)
    rows = list(csv.DictReader(output_file))

    assert rows == [
        {
            "DFML_ID": payment_data[0].fineos_customer_number,
            "BOARD_NO": payment_data[0].board_no,
            "EVENT_ID": payment_data[0].event_id,
            "INS_FORM_OR_MEET": payment_data[0].event_description,
            "EVE_CREATED_DATE": payment_data[0].eve_created_date.strftime("%m/%d/%Y"),
            "FORM_RECEIVED_OR_DISPOSITION": payment_data[0].event_occurrence_date.strftime(
                "%m/%d/%Y"
            ),
            "AWARD_ID": payment_data[0].award_id,
            "AWARD_CODE": payment_data[0].award_code,
            "AWARD_AMOUNT": str(payment_data[0].award_amount),
            "AWARD_DATE": payment_data[0].award_date.strftime("%m/%d/%Y"),
            "START_DATE": payment_data[0].start_date.strftime("%m/%d/%Y"),
            "END_DATE": payment_data[0].end_date.strftime("%m/%d/%Y"),
            "WEEKLY_AMOUNT": str(payment_data[0].weekly_amount),
            "AWARD_CREATED_DATE": payment_data[0].award_created_date.strftime("%m/%d/%Y"),
            "TERMINATION_DATE": payment_data[0].termination_date.strftime("%m/%d/%Y"),
            "ABSENCE_CASE_ID": payment_data[1].fineos_absence_id,
            "ABSENCE_PERIOD_START_DATE": "",
            "ABSENCE_PERIOD_END_DATE": "",
            "ABSENCE_CASE_STATUS": "",
        }
    ]


def test_write_dfml_report_rows_full_claim_info():
    output_file = io.StringIO()

    payment_data = (
        DiaReductionPaymentFactory.build(),
        ClaimFactory.build(
            absence_period_start_date=datetime.date(2021, 4, 15),
            absence_period_end_date=datetime.date(2021, 4, 16),
            fineos_absence_status_id=AbsenceStatus.ADJUDICATION.absence_status_id,
        ),
    )
    payment_rows = [dia_payments_reports_create._make_report_row_from_payment(payment_data)]

    dia_payments_reports_create._write_dfml_report_rows(output_file, payment_rows)

    output_file.seek(0)
    rows = list(csv.DictReader(output_file))

    assert rows == [
        {
            "DFML_ID": payment_data[0].fineos_customer_number,
            "BOARD_NO": payment_data[0].board_no,
            "EVENT_ID": payment_data[0].event_id,
            "INS_FORM_OR_MEET": payment_data[0].event_description,
            "EVE_CREATED_DATE": payment_data[0].eve_created_date.strftime("%m/%d/%Y"),
            "FORM_RECEIVED_OR_DISPOSITION": payment_data[0].event_occurrence_date.strftime(
                "%m/%d/%Y"
            ),
            "AWARD_ID": payment_data[0].award_id,
            "AWARD_CODE": payment_data[0].award_code,
            "AWARD_AMOUNT": str(payment_data[0].award_amount),
            "AWARD_DATE": payment_data[0].award_date.strftime("%m/%d/%Y"),
            "START_DATE": payment_data[0].start_date.strftime("%m/%d/%Y"),
            "END_DATE": payment_data[0].end_date.strftime("%m/%d/%Y"),
            "WEEKLY_AMOUNT": str(payment_data[0].weekly_amount),
            "AWARD_CREATED_DATE": payment_data[0].award_created_date.strftime("%m/%d/%Y"),
            "TERMINATION_DATE": payment_data[0].termination_date.strftime("%m/%d/%Y"),
            "ABSENCE_CASE_ID": payment_data[1].fineos_absence_id,
            "ABSENCE_PERIOD_START_DATE": "04/15/2021",
            "ABSENCE_PERIOD_END_DATE": "04/16/2021",
            "ABSENCE_CASE_STATUS": AbsenceStatus.ADJUDICATION.absence_status_description,
        }
    ]


def test_format_data_for_report_none():
    data = dia_payments_reports_create._format_data_for_report([])
    assert len(data) == 1
    for _, v in data[0].items():
        assert v == "NO NEW PAYMENTS"


@pytest.mark.integration
def test_get_data_for_report_none(test_db_session):
    payment_data = dia_payments_reports_create._get_data_for_report(test_db_session)

    assert payment_data == []


@pytest.mark.integration
def test_get_data_for_report_no_matching_employee(test_db_session, initialize_factories_session):
    reduction_payment = DiaReductionPaymentFactory.create()

    payment_data = dia_payments_reports_create._get_data_for_report(test_db_session)

    assert payment_data == [(reduction_payment, None)]


@pytest.mark.integration
def test_get_data_for_report_no_claim(test_db_session, initialize_factories_session):
    reduction_payment = DiaReductionPaymentFactory.create()

    EmployeeFactory.create(fineos_customer_number=reduction_payment.fineos_customer_number)

    payment_data = dia_payments_reports_create._get_data_for_report(test_db_session)

    assert payment_data == [(reduction_payment, None)]


@pytest.mark.integration
def test_get_data_for_report_single_claim(test_db_session, initialize_factories_session):
    reduction_payment = DiaReductionPaymentFactory.create()
    employee = EmployeeFactory.create(
        fineos_customer_number=reduction_payment.fineos_customer_number
    )
    claim = ClaimFactory.create(employee=employee)

    payment_data = dia_payments_reports_create._get_data_for_report(test_db_session)

    assert payment_data == [(reduction_payment, claim)]


@pytest.mark.integration
def test_get_data_for_report_multiple_claim(test_db_session, initialize_factories_session):
    reduction_payment = DiaReductionPaymentFactory.create()
    employee = EmployeeFactory.create(
        fineos_customer_number=reduction_payment.fineos_customer_number
    )
    claims = ClaimFactory.create_batch(size=3, employee=employee)

    # claim not associated with the employee, should not be in data set
    ClaimFactory.create()

    payment_data = dia_payments_reports_create._get_data_for_report(test_db_session)

    assert payment_data == [(reduction_payment, claim) for claim in claims]


@pytest.mark.integration
def test_get_data_for_report_multiple_everything(test_db_session, initialize_factories_session):
    # first set
    employee_1 = EmployeeWithFineosNumberFactory.create()
    reduction_payments_1 = DiaReductionPaymentFactory.create_batch(
        size=3, fineos_customer_number=employee_1.fineos_customer_number
    )
    claim_1 = ClaimFactory.create(employee=employee_1)

    data_1 = [(payment, claim_1) for payment in reduction_payments_1]

    # second set
    employee_2 = EmployeeWithFineosNumberFactory.create()
    reduction_payment_2 = DiaReductionPaymentFactory.create(
        fineos_customer_number=employee_2.fineos_customer_number
    )
    claims_2 = ClaimFactory.create_batch(size=2, employee=employee_2)

    data_2 = [(reduction_payment_2, claim) for claim in claims_2]

    # third set
    reduction_payments_3 = DiaReductionPaymentFactory.create_batch(size=3)

    data_3 = list(map(lambda p: (p, None), reduction_payments_3))

    # see what it grabs
    payment_data = dia_payments_reports_create._get_data_for_report(test_db_session)

    assert payment_data == data_1 + data_2 + data_3


@pytest.mark.integration
def test_create_report_new_dia_payments_to_dfml(
    initialize_factories_session, monkeypatch, mock_s3_bucket, test_db_session
):
    s3_bucket_uri = "s3://" + mock_s3_bucket
    dest_dir = "reductions/dfml/outbound"
    monkeypatch.setenv("S3_BUCKET", s3_bucket_uri)
    monkeypatch.setenv("S3_DFML_OUTBOUND_DIRECTORY_PATH", dest_dir)

    reduction_payments = DiaReductionPaymentFactory.create_batch(size=8)

    # Create multiple claims for the employee of first payment, should still
    # only have one state log entry for the payment in the end
    employee = EmployeeFactory.create(
        fineos_customer_number=reduction_payments[0].fineos_customer_number
    )
    ClaimFactory.create_batch(size=2, employee=employee)

    # Associate employee with second payment, but no claims
    EmployeeFactory.create(fineos_customer_number=reduction_payments[1].fineos_customer_number)

    log_entry = LogEntry(test_db_session, "Test")
    dia_payments_reports_create.create_report_new_dia_payments_to_dfml(test_db_session, log_entry)

    # Expect that the file to appear in the mock_s3_bucket.
    s3 = boto3.client("s3")

    object_list = s3.list_objects(Bucket=mock_s3_bucket, Prefix=dest_dir)["Contents"]
    assert object_list
    assert len(object_list) == 1
    dest_filepath_prefix = os.path.join(
        dest_dir, dia_payments_reports_create.DFML_REPORT_FILENAME_PREFIX
    )
    assert object_list[0]["Key"].startswith(dest_filepath_prefix)

    ref_file = (
        test_db_session.query(ReferenceFile)
        .filter_by(
            reference_file_type_id=ReferenceFileType.DIA_REDUCTION_REPORT_FOR_DFML.reference_file_type_id
        )
        .all()
    )
    state_log = (
        test_db_session.query(StateLog)
        .filter_by(end_state_id=State.DIA_REPORT_FOR_DFML_CREATED.state_id)
        .all()
    )

    assert len(ref_file) == 1
    assert len(state_log) == 1
    assert ref_file[0].file_location == os.path.join(s3_bucket_uri, object_list[0]["Key"])

    for payment in reduction_payments:
        _ref_file = ref_file[0]
        dia_reduction_ref_file = (
            test_db_session.query(DiaReductionPaymentReferenceFile)
            .filter_by(
                dia_reduction_payment_id=payment.dia_reduction_payment_id,
                reference_file_id=_ref_file.reference_file_id,
            )
            .one_or_none()
        )
        assert dia_reduction_ref_file is not None
