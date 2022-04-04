import csv
from datetime import date
from typing import Dict, List, Optional, Tuple

import faker

import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml import db
from massgov.pfml.db.models.employees import LkReferenceFileType, ReferenceFile, ReferenceFileType
from massgov.pfml.db.models.factories import ReferenceFileFactory
from massgov.pfml.delegated_payments.backfill.backfill_fineos_extract_step import (
    BackfillFineosExtractStep,
)

fake = faker.Faker()
fake.seed_instance(1111)


def get_random_fineos_timestamp() -> str:
    # Will look like "2022-03-10-12-00-00"
    fake_date = fake.unique.date_between(start_date=date(2020, 1, 1), end_date=date(2022, 12, 31))
    return f"{fake_date}-12-00-00"


def create_reference_file(
    rows: List[Dict[str, str]],
    reference_file_type: LkReferenceFileType,
    timestamp_str: str,
    fineos_extract: payments_util.FineosExtract,
    file_status: str = "processed",
    create_fineos_file: bool = True,
    reference_file: Optional[ReferenceFile] = None,
) -> ReferenceFile:

    if not reference_file:
        reference_file_location = f"s3://fake-bucket/cps/extracts/{file_status}/{payments_util.get_date_group_folder_name(timestamp_str, reference_file_type)}"
        reference_file = ReferenceFileFactory.create(
            file_location=reference_file_location,
            reference_file_type_id=reference_file_type.reference_file_type_id,
        )

    if create_fineos_file:
        # Make the FINEOS path
        s3_config = payments_config.get_s3_config()
        fineos_path = f"{s3_config.fineos_data_export_path}{timestamp_str}/{timestamp_str}-{fineos_extract.file_name}"

        # Generate a CSV file
        csv_file = file_util.write_file(fineos_path)
        csv_writer = csv.DictWriter(csv_file, fieldnames=fineos_extract.field_names)
        csv_writer.writeheader()
        csv_writer.writerows(rows)
        csv_file.close()

    return reference_file


def generate_rows(
    fineos_extract: payments_util.FineosExtract, num_rows: int, timestamp_str: str
) -> List[Dict[str, str]]:
    rows = []

    for i in range(num_rows):
        row = dict.fromkeys(fineos_extract.field_names, f"{timestamp_str}-{i}")
        rows.append(row)

    return rows


def add_rows_to_db(
    test_db_session: db.Session,
    rows: List[Dict[str, str]],
    fineos_extract: payments_util.FineosExtract,
    reference_file: ReferenceFile,
):
    for row in rows:
        test_db_session.add(
            payments_util.create_staging_table_instance(row, fineos_extract.table, reference_file)
        )
    test_db_session.commit()


def generate_test_data(
    test_db_session: db.Session,
    reference_file_type: LkReferenceFileType,
    fineos_extract: payments_util.FineosExtract,
    file_status: str = "processed",
    create_fineos_file: bool = True,
    populate_staging_table: bool = False,
    additional_extracts: Optional[List[payments_util.FineosExtract]] = None,
) -> Tuple[List[Dict[str, str]], List[ReferenceFile]]:
    rows = []
    reference_files = []

    # Generates 3 files with varying number of rows
    for i in range(1, 4):
        timestamp_str = get_random_fineos_timestamp()
        row_group = generate_rows(fineos_extract, i, timestamp_str)
        reference_file = create_reference_file(
            row_group,
            reference_file_type,
            timestamp_str,
            fineos_extract,
            file_status=file_status,
            create_fineos_file=create_fineos_file,
        )

        # Populate the staging table with the
        # data if configured to do so
        if populate_staging_table:
            add_rows_to_db(test_db_session, row_group, fineos_extract, reference_file)

        # Create additional extracts
        # in the DB and in FINEOS
        if additional_extracts:
            for additional_extract in additional_extracts:
                additional_row_group = generate_rows(additional_extract, i, timestamp_str)
                create_reference_file(
                    additional_row_group,
                    reference_file_type,
                    timestamp_str,
                    additional_extract,
                    file_status=file_status,
                    create_fineos_file=True,
                    reference_file=reference_file,
                )
                add_rows_to_db(
                    test_db_session, additional_row_group, additional_extract, reference_file
                )

        rows.extend(row_group)
        reference_files.append(reference_file)

    return rows, reference_files


def validate_rows_match_table_data(test_db_session, rows, fineos_extract, reference_files):
    reference_file_ids = [reference_file.reference_file_id for reference_file in reference_files]
    results = (
        test_db_session.query(fineos_extract.table)
        .filter(fineos_extract.table.reference_file_id.in_(reference_file_ids))
        .all()
    )

    assert len(results) == len(rows)

    for result in results:
        result_dict = result.for_json()
        # Filter the results to just the keys we generated
        filtered_result = {}
        for key in fineos_extract.field_names:
            filtered_result[key] = result_dict[key.lower()]

        assert filtered_result in rows


def test_run_happy_path(
    mock_s3_bucket,
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    initialize_factories_session,
    test_db_session,
):
    reference_file_type = ReferenceFileType.FINEOS_PAYMENT_EXTRACT
    extract = payments_util.FineosExtractConstants.PAYMENT_LINE

    # Generate a few other miscellaneous files
    # and populate some of those tables to show
    # they aren't going to be modified
    additional_extracts = [
        payments_util.FineosExtractConstants.VPEI,
        payments_util.FineosExtractConstants.PAYMENT_DETAILS,
    ]

    # Generate a few days to backfill
    rows, reference_files = generate_test_data(
        test_db_session, reference_file_type, extract, additional_extracts=additional_extracts
    )

    vpei_table_before = test_db_session.query(payments_util.FineosExtractConstants.VPEI.table).all()
    payment_details_table_before = test_db_session.query(
        payments_util.FineosExtractConstants.PAYMENT_DETAILS.table
    ).all()

    step = BackfillFineosExtractStep(test_db_session, test_db_session, reference_file_type, extract)
    step.run()

    validate_rows_match_table_data(test_db_session, rows, extract, reference_files)

    metrics = step.log_entry.metrics
    assert metrics[step.Metrics.RECORDS_PROCESSED_COUNT] == len(rows)
    assert metrics[step.Metrics.TOTAL_REFERENCE_FILE_COUNT] == len(reference_files)
    assert metrics[step.Metrics.SUCCESSFUL_REFERENCE_FILE_COUNT] == len(reference_files)
    assert metrics[step.Metrics.PROCESSED_REFERENCE_FILE_COUNT] == len(reference_files)
    assert metrics[step.Metrics.SKIPPED_REFERENCE_FILE_COUNT] == 0

    # Verify we didn't update the VPEI/payment details table
    vpei_table_after = test_db_session.query(payments_util.FineosExtractConstants.VPEI.table).all()
    payment_details_table_after = test_db_session.query(
        payments_util.FineosExtractConstants.PAYMENT_DETAILS.table
    ).all()

    assert len(vpei_table_before) == len(vpei_table_after)
    assert len(payment_details_table_before) == len(payment_details_table_after)


def test_run_prior_reference_files_processed(
    mock_s3_bucket,
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    initialize_factories_session,
    test_db_session,
):
    reference_file_type = ReferenceFileType.FINEOS_PAYMENT_EXTRACT
    extract = payments_util.FineosExtractConstants.PAYMENT_LINE

    # Create some data already in the table
    generate_test_data(test_db_session, reference_file_type, extract, populate_staging_table=True)

    # Generate a few days to backfill
    rows, reference_files = generate_test_data(test_db_session, reference_file_type, extract)

    step = BackfillFineosExtractStep(test_db_session, test_db_session, reference_file_type, extract)
    step.run()

    validate_rows_match_table_data(test_db_session, rows, extract, reference_files)

    metrics = step.log_entry.metrics
    assert metrics[step.Metrics.RECORDS_PROCESSED_COUNT] == len(rows)
    assert metrics[step.Metrics.TOTAL_REFERENCE_FILE_COUNT] == len(reference_files)
    assert metrics[step.Metrics.SUCCESSFUL_REFERENCE_FILE_COUNT] == len(reference_files)
    assert metrics[step.Metrics.PROCESSED_REFERENCE_FILE_COUNT] == len(reference_files)
    assert metrics[step.Metrics.SKIPPED_REFERENCE_FILE_COUNT] == 0


def test_run_with_skipped_reference_files(
    mock_s3_bucket,
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    initialize_factories_session,
    test_db_session,
):
    reference_file_type = ReferenceFileType.FINEOS_PAYMENT_EXTRACT
    extract = payments_util.FineosExtractConstants.PAYMENT_LINE

    # These reference files are marked
    # as something other than "processed"
    # and will be skipped by the processing
    _, skipped_reference_files = generate_test_data(
        test_db_session, reference_file_type, extract, file_status="skipped"
    )

    # Generate data to backfill
    rows, reference_files = generate_test_data(test_db_session, reference_file_type, extract)

    step = BackfillFineosExtractStep(test_db_session, test_db_session, reference_file_type, extract)
    step.run()

    validate_rows_match_table_data(test_db_session, rows, extract, reference_files)

    metrics = step.log_entry.metrics
    assert metrics[step.Metrics.RECORDS_PROCESSED_COUNT] == len(rows)
    assert metrics[step.Metrics.TOTAL_REFERENCE_FILE_COUNT] == len(
        reference_files + skipped_reference_files
    )
    assert metrics[step.Metrics.SUCCESSFUL_REFERENCE_FILE_COUNT] == len(reference_files)
    assert metrics[step.Metrics.PROCESSED_REFERENCE_FILE_COUNT] == len(
        reference_files + skipped_reference_files
    )
    assert metrics[step.Metrics.SKIPPED_REFERENCE_FILE_COUNT] == len(skipped_reference_files)


def test_run_with_missing_fineos_files(
    mock_s3_bucket,
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    initialize_factories_session,
    test_db_session,
):
    reference_file_type = ReferenceFileType.FINEOS_PAYMENT_EXTRACT
    extract = payments_util.FineosExtractConstants.PAYMENT_LINE

    # Create the reference files
    # but don't have a corresponding file in FINEOS
    _, reference_files = generate_test_data(
        test_db_session, reference_file_type, extract, create_fineos_file=False
    )

    step = BackfillFineosExtractStep(test_db_session, test_db_session, reference_file_type, extract)
    step.run()

    # No rows should have been populated
    validate_rows_match_table_data(test_db_session, [], extract, reference_files)

    metrics = step.log_entry.metrics
    assert metrics[step.Metrics.RECORDS_PROCESSED_COUNT] == 0
    assert metrics[step.Metrics.TOTAL_REFERENCE_FILE_COUNT] == len(reference_files)
    assert metrics[step.Metrics.SUCCESSFUL_REFERENCE_FILE_COUNT] == 0
    assert metrics[step.Metrics.PROCESSED_REFERENCE_FILE_COUNT] == len(reference_files)
    assert metrics[step.Metrics.FILE_NOT_FOUND_IN_FINEOS_COUNT] == len(reference_files)
