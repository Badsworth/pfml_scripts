import csv
import os

from freezegun import freeze_time
from smart_open import open as smart_open

import massgov.pfml.payments.config as payments_config
import massgov.pfml.payments.reporting.error_reporting as error_reporting
import massgov.pfml.util.files as file_util


def parse_csv(path):
    with smart_open(path) as csv_file:
        dict_reader = csv.DictReader(csv_file, delimiter=",")
        return list(dict_reader)


@freeze_time("2020-01-01 12:00:00")
def test_error_reports(mock_ses, set_exporter_env_vars):
    record1 = error_reporting.ErrorRecord(
        description="desc1",
        fineos_customer_number="1",
        fineos_absence_id="1",
        ctr_vendor_customer_code="1",
        mmars_document_id="1",
        payment_date="1",
    )
    record2 = error_reporting.ErrorRecord(
        description="desc2",
        fineos_customer_number="2",
        fineos_absence_id="2",
        ctr_vendor_customer_code="2",
        mmars_document_id="2",
        payment_date="2",
    )
    error_report = error_reporting.initialize_error_report("test")
    error_report.add_record(record1)
    error_report.add_record(record2)

    error_report_group = error_reporting.initialize_ctr_payments_error_report_group()
    error_report_group.add_report(error_report)

    error_report_group.create_and_send_reports()

    s3_prefix = payments_config.get_s3_config().pfml_error_reports_path
    report_files = file_util.list_files(s3_prefix, recursive=True)
    assert len(report_files) == 1

    records = parse_csv(os.path.join(s3_prefix, report_files[0]))
    assert len(records) == 2
    assert records[0] == {
        error_reporting.DESCRIPTION_COLUMN: record1.description,
        error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: record1.fineos_customer_number,
        error_reporting.FINEOS_ABSENCE_ID_COLUMN: record1.fineos_absence_id,
        error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: record1.ctr_vendor_customer_code,
        error_reporting.MMARS_DOCUMENT_ID_COLUMN: record1.mmars_document_id,
        error_reporting.PAYMENT_DATE_COLUMN: record1.payment_date,
    }
    assert records[1] == {
        error_reporting.DESCRIPTION_COLUMN: record2.description,
        error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: record2.fineos_customer_number,
        error_reporting.FINEOS_ABSENCE_ID_COLUMN: record2.fineos_absence_id,
        error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: record2.ctr_vendor_customer_code,
        error_reporting.MMARS_DOCUMENT_ID_COLUMN: record2.mmars_document_id,
        error_reporting.PAYMENT_DATE_COLUMN: record2.payment_date,
    }


@freeze_time("2020-01-01 12:00:00")
def test_error_reports_to_disk(mock_ses, set_exporter_env_vars, tmp_path):
    record1 = error_reporting.ErrorRecord(
        description="desc1",
        fineos_customer_number="1",
        fineos_absence_id="1",
        ctr_vendor_customer_code="1",
        mmars_document_id="1",
        payment_date="1",
    )
    record2 = error_reporting.ErrorRecord(
        description="desc2",
        fineos_customer_number="2",
        fineos_absence_id="2",
        ctr_vendor_customer_code="2",
        mmars_document_id="2",
        payment_date="2",
    )
    error_report = error_reporting.initialize_error_report("test")
    error_report.add_record(record1)
    error_report.add_record(record2)

    error_report_group = error_reporting.initialize_ctr_payments_error_report_group()
    error_report_group.file_config.file_prefix = tmp_path  # Override to a local path

    error_report_group.add_report(error_report)

    error_report_group.create_and_send_reports()

    expected_directory_path = tmp_path / "2020-01-01"
    report_files = file_util.list_files(str(expected_directory_path))

    records = parse_csv(os.path.join(expected_directory_path, report_files[0]))
    assert len(records) == 2
    assert records[0] == {
        error_reporting.DESCRIPTION_COLUMN: record1.description,
        error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: record1.fineos_customer_number,
        error_reporting.FINEOS_ABSENCE_ID_COLUMN: record1.fineos_absence_id,
        error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: record1.ctr_vendor_customer_code,
        error_reporting.MMARS_DOCUMENT_ID_COLUMN: record1.mmars_document_id,
        error_reporting.PAYMENT_DATE_COLUMN: record1.payment_date,
    }
    assert records[1] == {
        error_reporting.DESCRIPTION_COLUMN: record2.description,
        error_reporting.FINEOS_CUSTOMER_NUM_COLUMN: record2.fineos_customer_number,
        error_reporting.FINEOS_ABSENCE_ID_COLUMN: record2.fineos_absence_id,
        error_reporting.MMARS_VENDOR_CUST_NUM_COLUMN: record2.ctr_vendor_customer_code,
        error_reporting.MMARS_DOCUMENT_ID_COLUMN: record2.mmars_document_id,
        error_reporting.PAYMENT_DATE_COLUMN: record2.payment_date,
    }


@freeze_time("2020-01-01 12:00:00")
def test_error_reports_empty_values(mock_ses, set_exporter_env_vars):
    record1 = error_reporting.ErrorRecord()
    record2 = error_reporting.ErrorRecord()
    error_report = error_reporting.initialize_error_report("test")
    error_report.add_record(record1)
    error_report.add_record(record2)

    error_report_group = error_reporting.initialize_ctr_payments_error_report_group()
    error_report_group.add_report(error_report)

    error_report_group.create_and_send_reports()

    s3_prefix = payments_config.get_s3_config().pfml_error_reports_path
    report_files = file_util.list_files(s3_prefix, recursive=True)
    assert len(report_files) == 1

    records = parse_csv(os.path.join(s3_prefix, report_files[0]))
    assert len(records) == 2
    # The results will be empty strings for each value
    expected_record = {header: "" for header in error_reporting.CSV_HEADER}
    assert records[0] == expected_record
    assert records[1] == expected_record
