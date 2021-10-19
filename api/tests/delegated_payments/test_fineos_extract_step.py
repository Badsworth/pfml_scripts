import os
from datetime import datetime
from unittest import mock

import pytest

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import ReferenceFile, ReferenceFileType
from massgov.pfml.db.models.payments import (
    FineosExtractEmployeeFeed,
    FineosExtractVbiRequestedAbsence,
    FineosExtractVbiRequestedAbsenceSom,
    FineosExtractVpei,
    FineosExtractVpeiClaimDetails,
    FineosExtractVpeiPaymentDetails,
)
from massgov.pfml.delegated_payments.fineos_extract_step import (
    CLAIMANT_EXTRACT_CONFIG,
    PAYMENT_EXTRACT_CONFIG,
    FineosExtractStep,
)
from massgov.pfml.delegated_payments.mock.fineos_extract_data import (
    FineosClaimantData,
    FineosPaymentData,
    create_fineos_claimant_extract_files,
    create_fineos_payment_extract_files,
)

date_str = "2020-08-01-12-00-00"


def create_malformed_file(extract, date_of_extract, folder_path):
    bad_content_line_one = "Some,Other,Column,Names"
    bad_content_line_two = "1,2,3,4"
    bad_content = "\n".join([bad_content_line_one, bad_content_line_two])

    date_prefix = date_of_extract.strftime("%Y-%m-%d-%H-%M-%S-")

    file_name = os.path.join(folder_path, f"{date_prefix}{extract.file_name}")
    with file_util.write_file(file_name) as outfile:
        outfile.write(bad_content)


def upload_fineos_payment_data(
    mock_fineos_s3_bucket, fineos_dataset, timestamp=date_str, malformed_extract=None
):
    folder_path = os.path.join(f"s3://{mock_fineos_s3_bucket}", "DT2/dataexports/")
    date_of_extract = datetime.strptime(timestamp, "%Y-%m-%d-%H-%M-%S")
    create_fineos_payment_extract_files(fineos_dataset, folder_path, date_of_extract)

    if malformed_extract:
        create_malformed_file(malformed_extract, date_of_extract, folder_path)


def upload_fineos_claimant_data(
    mock_fineos_s3_bucket, fineos_dataset, timestamp=date_str, malformed_extract=None
):
    folder_path = os.path.join(f"s3://{mock_fineos_s3_bucket}", "DT2/dataexports/")
    date_of_extract = datetime.strptime(timestamp, "%Y-%m-%d-%H-%M-%S")
    create_fineos_claimant_extract_files(fineos_dataset, folder_path, date_of_extract)

    if malformed_extract:
        create_malformed_file(malformed_extract, date_of_extract, folder_path)


def validate_records(records, table, index_key, local_test_db_session):
    data = local_test_db_session.query(table).all()

    # Verify everything was loaded
    assert len(data) == len(records)

    # Index the records (which are dictionaries)
    # so we can compare the DB value
    indexed_records = {}
    for record in records:
        indexed_records[record.get(index_key)] = record

    for db_record in data:
        assert db_record.reference_file_id
        assert db_record.fineos_extract_import_log_id
        assert db_record.created_at
        assert db_record.updated_at

        # Figure out the dataset that corresponds
        # to the one in the DB
        key = getattr(db_record, index_key.lower())
        indexed_record = indexed_records.get(key, None)
        assert indexed_record

        # For each key in the dataset we made,
        # verify that value was accurately stored
        # into the DB
        for k, v in indexed_record.items():
            assert getattr(db_record, k.lower(), None) == v


def test_run_happy_path(
    mock_s3_bucket,
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    local_test_db_session,
    local_test_db_other_session,
    monkeypatch,
):
    # Show that we can run these steps back-to-back without any issue
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")

    payment_data = [FineosPaymentData(), FineosPaymentData(), FineosPaymentData()]
    claimant_data = [FineosClaimantData(), FineosClaimantData(), FineosClaimantData()]

    upload_fineos_payment_data(mock_fineos_s3_bucket, payment_data)
    upload_fineos_claimant_data(mock_fineos_s3_bucket, claimant_data)

    # Earlier timestamp will be moved to a skipped folder
    skipped_date_str = "2020-01-01-12-00-00"
    upload_fineos_payment_data(mock_fineos_s3_bucket, payment_data, skipped_date_str)
    upload_fineos_claimant_data(mock_fineos_s3_bucket, claimant_data, skipped_date_str)

    # Repeat running the task multiple times to show
    # it doesn't reprocess files it already processed
    # and that it effectively no-ops on subsequent runs
    for _ in range(3):
        fineos_extract_step = FineosExtractStep(
            db_session=local_test_db_session,
            log_entry_db_session=local_test_db_other_session,
            extract_config=CLAIMANT_EXTRACT_CONFIG,
        )
        fineos_extract_step.run()
        fineos_extract_step = FineosExtractStep(
            db_session=local_test_db_session,
            log_entry_db_session=local_test_db_other_session,
            extract_config=PAYMENT_EXTRACT_CONFIG,
        )
        fineos_extract_step.run()

        # Verify all files are present and in the expected processed paths
        expected_path_prefix = f"s3://{mock_s3_bucket}/cps/inbound/processed/"
        files = file_util.list_files(expected_path_prefix, recursive=True)
        assert len(files) == 6

        claimant_prefix = f"{date_str}-claimant-extract/{date_str}"
        assert (
            f"{claimant_prefix}-{payments_util.Constants.REQUESTED_ABSENCE_SOM_FILE_NAME}" in files
        )
        assert f"{claimant_prefix}-{payments_util.Constants.EMPLOYEE_FEED_FILE_NAME}" in files

        payment_prefix = f"{date_str}-payment-extract/{date_str}"
        assert f"{payment_prefix}-{payments_util.Constants.PEI_EXPECTED_FILE_NAME}" in files
        assert (
            f"{payment_prefix}-{payments_util.Constants.PAYMENT_DETAILS_EXPECTED_FILE_NAME}"
            in files
        )
        assert (
            f"{payment_prefix}-{payments_util.Constants.CLAIM_DETAILS_EXPECTED_FILE_NAME}" in files
        )
        assert f"{payment_prefix}-{payments_util.Constants.REQUESTED_ABSENCE_FILE_NAME}" in files

        claimant_reference_file = (
            local_test_db_session.query(ReferenceFile)
            .filter(
                ReferenceFile.file_location == expected_path_prefix + f"{date_str}-claimant-extract"
            )
            .one_or_none()
        )
        assert claimant_reference_file
        assert (
            claimant_reference_file.reference_file_type_id
            == ReferenceFileType.FINEOS_CLAIMANT_EXTRACT.reference_file_type_id
        )

        payment_reference_file = (
            local_test_db_session.query(ReferenceFile)
            .filter(
                ReferenceFile.file_location == expected_path_prefix + f"{date_str}-payment-extract"
            )
            .one_or_none()
        )
        assert payment_reference_file
        assert (
            payment_reference_file.reference_file_type_id
            == ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id
        )

        employee_feed_records = [record.get_employee_feed_record() for record in claimant_data]
        validate_records(
            employee_feed_records, FineosExtractEmployeeFeed, "I", local_test_db_session
        )

        requested_absence_som_records = [
            record.get_requested_absence_record() for record in claimant_data
        ]
        validate_records(
            requested_absence_som_records,
            FineosExtractVbiRequestedAbsenceSom,
            "ABSENCE_CASENUMBER",
            local_test_db_session,
        )

        vpei_records = [record.get_vpei_record() for record in payment_data]
        validate_records(vpei_records, FineosExtractVpei, "I", local_test_db_session)

        claim_details_records = [record.get_claim_details_record() for record in payment_data]
        validate_records(
            claim_details_records,
            FineosExtractVpeiClaimDetails,
            "LEAVEREQUESTI",
            local_test_db_session,
        )

        payment_details_records = [record.get_payment_details_record() for record in payment_data]
        validate_records(
            payment_details_records,
            FineosExtractVpeiPaymentDetails,
            "PEINDEXID",
            local_test_db_session,
        )

        requested_absence_records = [
            record.get_requested_absence_record() for record in payment_data
        ]
        validate_records(
            requested_absence_records,
            FineosExtractVbiRequestedAbsence,
            "LEAVEREQUEST_ID",
            local_test_db_session,
        )

        ### and verify the skipped files as well
        expected_path_prefix = f"s3://{mock_s3_bucket}/cps/inbound/skipped/"
        files = file_util.list_files(expected_path_prefix, recursive=True)
        assert len(files) == 6

        claimant_prefix = f"{skipped_date_str}-claimant-extract/{skipped_date_str}"
        assert (
            f"{claimant_prefix}-{payments_util.Constants.REQUESTED_ABSENCE_SOM_FILE_NAME}" in files
        )
        assert f"{claimant_prefix}-{payments_util.Constants.EMPLOYEE_FEED_FILE_NAME}" in files

        payment_prefix = f"{skipped_date_str}-payment-extract/{skipped_date_str}"
        assert f"{payment_prefix}-{payments_util.Constants.PEI_EXPECTED_FILE_NAME}" in files
        assert (
            f"{payment_prefix}-{payments_util.Constants.PAYMENT_DETAILS_EXPECTED_FILE_NAME}"
            in files
        )
        assert (
            f"{payment_prefix}-{payments_util.Constants.CLAIM_DETAILS_EXPECTED_FILE_NAME}" in files
        )
        assert f"{payment_prefix}-{payments_util.Constants.REQUESTED_ABSENCE_FILE_NAME}" in files

        # And the skipped reference files
        claimant_reference_file = (
            local_test_db_session.query(ReferenceFile)
            .filter(
                ReferenceFile.file_location
                == expected_path_prefix + f"{skipped_date_str}-claimant-extract"
            )
            .one_or_none()
        )
        assert claimant_reference_file
        assert (
            claimant_reference_file.reference_file_type_id
            == ReferenceFileType.FINEOS_CLAIMANT_EXTRACT.reference_file_type_id
        )

        payment_reference_file = (
            local_test_db_session.query(ReferenceFile)
            .filter(
                ReferenceFile.file_location
                == expected_path_prefix + f"{skipped_date_str}-payment-extract"
            )
            .one_or_none()
        )
        assert payment_reference_file
        assert (
            payment_reference_file.reference_file_type_id
            == ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id
        )


def test_run_with_error_during_processing(
    mock_s3_bucket,
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    local_test_db_session,
    local_test_db_other_session,
    monkeypatch,
):
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")

    payment_data = [FineosPaymentData(), FineosPaymentData(), FineosPaymentData()]
    upload_fineos_payment_data(mock_fineos_s3_bucket, payment_data)

    fineos_extract_step = FineosExtractStep(
        db_session=local_test_db_session,
        log_entry_db_session=local_test_db_other_session,
        extract_config=PAYMENT_EXTRACT_CONFIG,
    )

    with mock.patch(
        "massgov.pfml.delegated_payments.fineos_extract_step.FineosExtractStep._download_and_index_data",
        side_effect=Exception("Raising error to test rollback"),
    ), pytest.raises(Exception, match="Raising error to test rollback"):
        fineos_extract_step.run()

    # Files were moved to error directory
    expected_path_prefix = f"s3://{mock_s3_bucket}/cps/inbound/error/"
    files = file_util.list_files(expected_path_prefix, recursive=True)
    assert len(files) == 4
    payment_prefix = f"{date_str}-payment-extract/{date_str}"
    assert f"{payment_prefix}-{payments_util.Constants.PEI_EXPECTED_FILE_NAME}" in files
    assert f"{payment_prefix}-{payments_util.Constants.PAYMENT_DETAILS_EXPECTED_FILE_NAME}" in files
    assert f"{payment_prefix}-{payments_util.Constants.CLAIM_DETAILS_EXPECTED_FILE_NAME}" in files
    assert f"{payment_prefix}-{payments_util.Constants.REQUESTED_ABSENCE_FILE_NAME}" in files

    # A reference file is present and pointing to the errored directory
    reference_files = local_test_db_session.query(ReferenceFile).all()
    assert len(reference_files) == 1
    assert reference_files[0].file_location == expected_path_prefix + f"{date_str}-payment-extract"

    # Verify nothing is in any of the tables
    validate_records([], FineosExtractEmployeeFeed, "I", local_test_db_session)
    validate_records(
        [], FineosExtractVbiRequestedAbsenceSom, "ABSENCE_CASENUMBER", local_test_db_session
    )
    validate_records([], FineosExtractVpei, "I", local_test_db_session)
    validate_records([], FineosExtractVpeiClaimDetails, "LEAVEREQUESTI", local_test_db_session)
    validate_records([], FineosExtractVpeiPaymentDetails, "PEINDEXID", local_test_db_session)
    validate_records([], FineosExtractVbiRequestedAbsence, "LEAVEREQUEST_ID", local_test_db_session)


def test_run_with_missing_fineos_file(
    mock_s3_bucket,
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    local_test_db_session,
    local_test_db_other_session,
    monkeypatch,
):
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")

    claimant_data = [FineosClaimantData(), FineosClaimantData(), FineosClaimantData()]
    upload_fineos_claimant_data(mock_fineos_s3_bucket, claimant_data)

    # Delete the employee feed file
    expected_fineos_path_prefix = f"s3://{mock_fineos_s3_bucket}/DT2/dataexports/"
    file_util.delete_file(
        expected_fineos_path_prefix
        + f"{date_str}-{payments_util.Constants.EMPLOYEE_FEED_FILE_NAME}"
    )

    fineos_extract_step = FineosExtractStep(
        db_session=local_test_db_session,
        log_entry_db_session=local_test_db_other_session,
        extract_config=CLAIMANT_EXTRACT_CONFIG,
    )

    with pytest.raises(
        Exception,
        match="Error while copying fineos extracts - The following expected files were not found",
    ):
        fineos_extract_step.run()

    # No reference files created because it failed before that was created
    reference_files = local_test_db_session.query(ReferenceFile).all()
    assert len(reference_files) == 0

    # Verify nothing is in any of the tables
    validate_records([], FineosExtractEmployeeFeed, "I", local_test_db_session)
    validate_records(
        [], FineosExtractVbiRequestedAbsenceSom, "ABSENCE_CASENUMBER", local_test_db_session
    )
    validate_records([], FineosExtractVpei, "I", local_test_db_session)
    validate_records([], FineosExtractVpeiClaimDetails, "LEAVEREQUESTI", local_test_db_session)
    validate_records([], FineosExtractVpeiPaymentDetails, "PEINDEXID", local_test_db_session)
    validate_records([], FineosExtractVbiRequestedAbsence, "LEAVEREQUEST_ID", local_test_db_session)


@pytest.mark.parametrize(
    "claimant_extract_file",
    payments_util.CLAIMANT_EXTRACT_FILES,
    ids=payments_util.CLAIMANT_EXTRACT_FILE_NAMES,
)
def test_run_with_malformed_claimant_data(
    mock_s3_bucket,
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    local_test_db_session,
    local_test_db_other_session,
    monkeypatch,
    claimant_extract_file,
):
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")

    claimant_data = [FineosClaimantData()]
    upload_fineos_claimant_data(
        mock_fineos_s3_bucket, claimant_data, malformed_extract=claimant_extract_file
    )

    with pytest.raises(
        Exception,
        match=f"FINEOS extract {claimant_extract_file.file_name} is missing required fields",
    ):
        fineos_extract_step = FineosExtractStep(
            db_session=local_test_db_session,
            log_entry_db_session=local_test_db_other_session,
            extract_config=CLAIMANT_EXTRACT_CONFIG,
        )
        fineos_extract_step.run()


@pytest.mark.parametrize(
    "payment_extract_file",
    payments_util.PAYMENT_EXTRACT_FILES,
    ids=payments_util.PAYMENT_EXTRACT_FILE_NAMES,
)
def test_run_with_malformed_payment_data(
    mock_s3_bucket,
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    local_test_db_session,
    local_test_db_other_session,
    monkeypatch,
    payment_extract_file,
):
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")

    payment_data = [FineosPaymentData()]
    upload_fineos_payment_data(
        mock_fineos_s3_bucket, payment_data, malformed_extract=payment_extract_file
    )

    with pytest.raises(
        Exception,
        match=f"FINEOS extract {payment_extract_file.file_name} is missing required fields",
    ):
        fineos_extract_step = FineosExtractStep(
            db_session=local_test_db_session,
            log_entry_db_session=local_test_db_other_session,
            extract_config=PAYMENT_EXTRACT_CONFIG,
        )
        fineos_extract_step.run()
