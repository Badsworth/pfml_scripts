import logging  # noqa: B1
import os
from datetime import datetime
from unittest import mock

import pytest

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import ReferenceFile, ReferenceFileType
from massgov.pfml.db.models.payments import (
    FineosExtractCancelledPayments,
    FineosExtractEmployeeFeed,
    FineosExtractPaymentFullSnapshot,
    FineosExtractReplacedPayments,
    FineosExtractVbiLeavePlanRequestedAbsence,
    FineosExtractVbiRequestedAbsence,
    FineosExtractVbiRequestedAbsenceSom,
    FineosExtractVbiTaskReportSom,
    FineosExtractVPaidLeaveInstruction,
    FineosExtractVpei,
    FineosExtractVpeiClaimDetails,
    FineosExtractVpeiPaymentDetails,
    FineosExtractVpeiPaymentLine,
)
from massgov.pfml.delegated_payments.fineos_extract_step import (
    CLAIMANT_EXTRACT_CONFIG,
    IAWW_EXTRACT_CONFIG,
    PAYMENT_EXTRACT_CONFIG,
    PAYMENT_RECONCILIATION_EXTRACT_CONFIG,
    VBI_TASKREPORT_SOM_EXTRACT_CONFIG,
    FineosExtractStep,
)
from massgov.pfml.delegated_payments.mock.fineos_extract_data import (
    FineosIAWWData,
    FineosPaymentData,
    create_fineos_claimant_extract_files,
    create_fineos_payment_extract_files,
    generate_iaww_extract_files,
    generate_payment_reconciliation_extract_files,
    generate_vbi_taskreport_som_extract_files,
    get_vbi_taskreport_som_extract_filtered_records,
    get_vbi_taskreport_som_extract_records,
)

earlier_date_str = "2020-07-01-12-00-00"
date_str = "2020-08-01-12-00-00"


def create_malformed_file(extract, date_of_extract, folder_path, malformed_content=None):
    if malformed_content is None:
        malformed_content_line_one = "Some,Other,Column,Names"
        malformed_content_line_two = "1,2,3,4"
        malformed_content = "\n".join([malformed_content_line_one, malformed_content_line_two])

    date_prefix = date_of_extract.strftime("%Y-%m-%d-%H-%M-%S-")

    file_name = os.path.join(folder_path, f"{date_prefix}{extract.file_name}")
    with file_util.write_file(file_name) as outfile:
        outfile.write(malformed_content)


def upload_fineos_payment_data(
    mock_fineos_s3_bucket,
    fineos_dataset,
    timestamp=date_str,
    malformed_extract=None,
    malformed_content=None,
):
    folder_path = os.path.join(f"s3://{mock_fineos_s3_bucket}", "DT2/dataexports/")
    date_of_extract = datetime.strptime(timestamp, "%Y-%m-%d-%H-%M-%S")
    create_fineos_payment_extract_files(fineos_dataset, folder_path, date_of_extract)

    if malformed_extract:
        create_malformed_file(
            malformed_extract, date_of_extract, folder_path, malformed_content=malformed_content
        )


def upload_fineos_claimant_data(
    mock_fineos_s3_bucket,
    fineos_dataset,
    timestamp=date_str,
    malformed_extract=None,
    malformed_content=None,
):
    folder_path = os.path.join(f"s3://{mock_fineos_s3_bucket}", "DT2/dataexports/")
    date_of_extract = datetime.strptime(timestamp, "%Y-%m-%d-%H-%M-%S")
    create_fineos_claimant_extract_files(fineos_dataset, folder_path, date_of_extract)

    if malformed_extract:
        create_malformed_file(
            malformed_extract, date_of_extract, folder_path, malformed_content=malformed_content
        )


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
    claimant_data = [FineosPaymentData(), FineosPaymentData(), FineosPaymentData()]

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
        assert len(files) == 7

        claimant_prefix = f"{date_str}-claimant-extract/{date_str}"
        assert (
            f"{claimant_prefix}-{payments_util.Constants.REQUESTED_ABSENCE_SOM_FILE_NAME}" in files
        )
        assert f"{claimant_prefix}-{payments_util.Constants.EMPLOYEE_FEED_FILE_NAME}" in files
        assert f"{claimant_prefix}-{payments_util.Constants.REQUESTED_ABSENCE_FILE_NAME}" in files

        payment_prefix = f"{date_str}-payment-extract/{date_str}"
        assert f"{payment_prefix}-{payments_util.Constants.PEI_EXPECTED_FILE_NAME}" in files
        assert (
            f"{payment_prefix}-{payments_util.Constants.PAYMENT_DETAILS_EXPECTED_FILE_NAME}"
            in files
        )
        assert (
            f"{payment_prefix}-{payments_util.Constants.CLAIM_DETAILS_EXPECTED_FILE_NAME}" in files
        )

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
            record.get_requested_absence_som_record() for record in claimant_data
        ]
        validate_records(
            requested_absence_som_records,
            FineosExtractVbiRequestedAbsenceSom,
            "ABSENCE_CASENUMBER",
            local_test_db_session,
        )

        requested_absence_records = [
            record.get_requested_absence_record() for record in claimant_data
        ]
        validate_records(
            requested_absence_records,
            FineosExtractVbiRequestedAbsence,
            "LEAVEREQUEST_ID",
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

        payment_line_records = [record.get_payment_line_record() for record in payment_data]
        validate_records(
            payment_line_records,
            FineosExtractVpeiPaymentLine,
            "I",
            local_test_db_session,
        )

        ### and verify the skipped files as well
        expected_path_prefix = f"s3://{mock_s3_bucket}/cps/inbound/skipped/"
        files = file_util.list_files(expected_path_prefix, recursive=True)
        assert len(files) == 7

        claimant_prefix = f"{skipped_date_str}-claimant-extract/{skipped_date_str}"
        assert (
            f"{claimant_prefix}-{payments_util.Constants.REQUESTED_ABSENCE_SOM_FILE_NAME}" in files
        )
        assert f"{claimant_prefix}-{payments_util.Constants.EMPLOYEE_FEED_FILE_NAME}" in files
        assert f"{claimant_prefix}-{payments_util.Constants.REQUESTED_ABSENCE_FILE_NAME}" in files

        payment_prefix = f"{skipped_date_str}-payment-extract/{skipped_date_str}"
        assert f"{payment_prefix}-{payments_util.Constants.PEI_EXPECTED_FILE_NAME}" in files
        assert (
            f"{payment_prefix}-{payments_util.Constants.PAYMENT_DETAILS_EXPECTED_FILE_NAME}"
            in files
        )
        assert (
            f"{payment_prefix}-{payments_util.Constants.CLAIM_DETAILS_EXPECTED_FILE_NAME}" in files
        )
        assert (
            f"{payment_prefix}-{payments_util.Constants.PAYMENT_LINE_EXPECTED_FILE_NAME}" in files
        )

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


def test_payment_reconciliation_extracts(
    mock_s3_bucket,
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    local_test_db_session,
    local_test_db_other_session,
    monkeypatch,
):
    monkeypatch.setenv("FINEOS_PAYMENT_RECONCILIATION_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")

    # Create payment reconciliation extract files
    folder_path = os.path.join(f"s3://{mock_fineos_s3_bucket}", "DT2/dataExtracts/AdHocExtract/")
    extract_records = generate_payment_reconciliation_extract_files(folder_path, f"{date_str}-", 10)

    # Run the extract
    fineos_extract_step = FineosExtractStep(
        db_session=local_test_db_session,
        log_entry_db_session=local_test_db_other_session,
        extract_config=PAYMENT_RECONCILIATION_EXTRACT_CONFIG,
    )
    fineos_extract_step.run()

    # Verify files
    expected_path_prefix = f"s3://{mock_s3_bucket}/cps/inbound/processed/"
    files = file_util.list_files(expected_path_prefix, recursive=True)
    assert len(files) == 3

    payment_reconciliation_prefix = f"{date_str}-payment-reconciliation-extract/{date_str}"
    assert (
        f"{payment_reconciliation_prefix}-{payments_util.FineosExtractConstants.PAYMENT_FULL_SNAPSHOT.file_name}"
        in files
    )
    assert (
        f"{payment_reconciliation_prefix}-{payments_util.FineosExtractConstants.REPLACED_PAYMENTS_EXTRACT.file_name}"
        in files
    )
    assert (
        f"{payment_reconciliation_prefix}-{payments_util.FineosExtractConstants.CANCELLED_PAYMENTS_EXTRACT.file_name}"
        in files
    )

    payment_reference_file = (
        local_test_db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.file_location
            == expected_path_prefix + f"{date_str}-payment-reconciliation-extract"
        )
        .one_or_none()
    )
    assert payment_reference_file
    assert (
        payment_reference_file.reference_file_type_id
        == ReferenceFileType.FINEOS_PAYMENT_RECONCILIATION_EXTRACT.reference_file_type_id
    )

    validate_records(
        extract_records[payments_util.FineosExtractConstants.PAYMENT_FULL_SNAPSHOT.file_name],
        FineosExtractPaymentFullSnapshot,
        "I",
        local_test_db_session,
    )
    validate_records(
        extract_records[payments_util.FineosExtractConstants.CANCELLED_PAYMENTS_EXTRACT.file_name],
        FineosExtractCancelledPayments,
        "I",
        local_test_db_session,
    )
    validate_records(
        extract_records[payments_util.FineosExtractConstants.REPLACED_PAYMENTS_EXTRACT.file_name],
        FineosExtractReplacedPayments,
        "I",
        local_test_db_session,
    )


def test_iaww_extracts(
    mock_s3_bucket,
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    local_test_db_session,
    local_test_db_other_session,
    monkeypatch,
):
    monkeypatch.setenv("FINEOS_IAWW_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")

    # Create IAWW extract files
    folder_path = os.path.join(f"s3://{mock_fineos_s3_bucket}", "DT2/dataexports/")
    extract_records = generate_iaww_extract_files(
        [
            FineosIAWWData(aww_value="1331.66"),
            FineosIAWWData(aww_value="1538"),
            FineosIAWWData(aww_value="1700.50"),
        ],
        folder_path,
        f"{date_str}-",
    )

    # Run the extract
    fineos_extract_step = FineosExtractStep(
        db_session=local_test_db_session,
        log_entry_db_session=local_test_db_other_session,
        extract_config=IAWW_EXTRACT_CONFIG,
    )
    fineos_extract_step.run()

    # Verify files
    expected_path_prefix = f"s3://{mock_s3_bucket}/cps/inbound/processed/"
    files = file_util.list_files(expected_path_prefix, recursive=True)
    assert len(files) == 2

    iaww_prefix = f"{date_str}-iaww-extract/{date_str}"
    assert (
        f"{iaww_prefix}-{payments_util.FineosExtractConstants.VBI_LEAVE_PLAN_REQUESTED_ABSENCE.file_name}"
        in files
    )
    assert (
        f"{iaww_prefix}-{payments_util.FineosExtractConstants.PAID_LEAVE_INSTRUCTION.file_name}"
        in files
    )

    iaww_reference_file = (
        local_test_db_session.query(ReferenceFile)
        .filter(ReferenceFile.file_location == expected_path_prefix + f"{date_str}-iaww-extract")
        .one_or_none()
    )
    assert iaww_reference_file
    assert (
        iaww_reference_file.reference_file_type_id
        == ReferenceFileType.FINEOS_IAWW_EXTRACT.reference_file_type_id
    )

    validate_records(
        extract_records[
            payments_util.FineosExtractConstants.VBI_LEAVE_PLAN_REQUESTED_ABSENCE.file_name
        ],
        FineosExtractVbiLeavePlanRequestedAbsence,
        "SELECTEDPLAN_INDEXID",
        local_test_db_session,
    )
    validate_records(
        extract_records[payments_util.FineosExtractConstants.PAID_LEAVE_INSTRUCTION.file_name],
        FineosExtractVPaidLeaveInstruction,
        "I",
        local_test_db_session,
    )


def test_vbi_taskreport_som_extracts(
    mock_s3_bucket,
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    local_test_db_session,
    local_test_db_other_session,
    monkeypatch,
):
    monkeypatch.setenv("FINEOS_VBI_TASKREPORT_SOM_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")

    records = get_vbi_taskreport_som_extract_records()

    # Create VBI Task Report Som extract files
    folder_path = os.path.join(f"s3://{mock_fineos_s3_bucket}", "DT2/dataexports/")
    generate_vbi_taskreport_som_extract_files(
        folder_path, datetime.strptime(date_str, "%Y-%m-%d-%H-%M-%S"), records=records
    )

    # Run the extract
    fineos_extract_step = FineosExtractStep(
        db_session=local_test_db_session,
        log_entry_db_session=local_test_db_other_session,
        extract_config=VBI_TASKREPORT_SOM_EXTRACT_CONFIG,
    )
    fineos_extract_step.run()

    # Verify file
    expected_path_prefix = f"s3://{mock_s3_bucket}/cps/inbound/processed/"
    files = file_util.list_files(expected_path_prefix, recursive=True)
    assert len(files) == 1

    file_prefix = f"{date_str}-vbi-taskreport-som-extract/{date_str}"
    assert (
        f"{file_prefix}-{payments_util.FineosExtractConstants.VBI_TASKREPORT_SOM.file_name}"
        in files
    )

    reference_file = (
        local_test_db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.file_location
            == expected_path_prefix + f"{date_str}-vbi-taskreport-som-extract"
        )
        .one_or_none()
    )
    assert reference_file
    assert (
        reference_file.reference_file_type_id
        == ReferenceFileType.FINEOS_VBI_TASKREPORT_SOM_EXTRACT.reference_file_type_id
    )

    filtered_records = get_vbi_taskreport_som_extract_filtered_records(records)
    validate_records(
        filtered_records, FineosExtractVbiTaskReportSom, "TASKID", local_test_db_session
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

    # Prior skipped data
    prior_payment_data = [FineosPaymentData()]
    upload_fineos_payment_data(
        mock_fineos_s3_bucket, prior_payment_data, timestamp=earlier_date_str
    )

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
    assert f"{payment_prefix}-{payments_util.Constants.PAYMENT_LINE_EXPECTED_FILE_NAME}" in files

    # Verify that the skipped file ended up in the right place
    expected_path_prefix = f"s3://{mock_s3_bucket}/cps/inbound/skipped/"
    files = file_util.list_files(expected_path_prefix, recursive=True)
    assert len(files) == 4

    payment_prefix = f"{earlier_date_str}-payment-extract/{earlier_date_str}"
    assert f"{payment_prefix}-{payments_util.Constants.PEI_EXPECTED_FILE_NAME}" in files
    assert f"{payment_prefix}-{payments_util.Constants.PAYMENT_DETAILS_EXPECTED_FILE_NAME}" in files
    assert f"{payment_prefix}-{payments_util.Constants.CLAIM_DETAILS_EXPECTED_FILE_NAME}" in files
    assert f"{payment_prefix}-{payments_util.Constants.PAYMENT_LINE_EXPECTED_FILE_NAME}" in files

    # No reference files are created for errored files
    # The skipped files' reference file was rolled back
    # so isn't present in the DB. We'd pick them up again next time
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
    validate_records([], FineosExtractVpeiPaymentLine, "I", local_test_db_session)


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

    claimant_data = [FineosPaymentData(), FineosPaymentData(), FineosPaymentData()]
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

    with pytest.raises(Exception, match="Expected to find files"):
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
    validate_records([], FineosExtractVpeiPaymentLine, "I", local_test_db_session)


def test_run_with_missing_files_skipped_run(
    mock_s3_bucket,
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    local_test_db_session,
    local_test_db_other_session,
    monkeypatch,
):
    # Validate that if we're missing files that are going to be skipped
    # that the process won't fail.
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")

    prior_claimant_data = [FineosPaymentData(), FineosPaymentData()]
    upload_fineos_claimant_data(
        mock_fineos_s3_bucket, prior_claimant_data, timestamp=earlier_date_str
    )

    claimant_data = [FineosPaymentData(), FineosPaymentData(), FineosPaymentData()]
    upload_fineos_claimant_data(mock_fineos_s3_bucket, claimant_data)

    # Delete the employee feed file for the older skipped record
    expected_fineos_path_prefix = f"s3://{mock_fineos_s3_bucket}/DT2/dataexports/"
    file_util.delete_file(
        expected_fineos_path_prefix
        + f"{earlier_date_str}-{payments_util.Constants.EMPLOYEE_FEED_FILE_NAME}"
    )

    fineos_extract_step = FineosExtractStep(
        db_session=local_test_db_session,
        log_entry_db_session=local_test_db_other_session,
        extract_config=CLAIMANT_EXTRACT_CONFIG,
    )

    fineos_extract_step.run()

    # Verify that the skipped file ended up in the right place
    expected_path_prefix = f"s3://{mock_s3_bucket}/cps/inbound/skipped/"
    files = file_util.list_files(expected_path_prefix, recursive=True)
    assert len(files) == 2

    claimant_prefix = f"{earlier_date_str}-claimant-extract/{earlier_date_str}"
    assert f"{claimant_prefix}-{payments_util.Constants.REQUESTED_ABSENCE_SOM_FILE_NAME}" in files
    assert f"{claimant_prefix}-{payments_util.Constants.REQUESTED_ABSENCE_FILE_NAME}" in files

    # Verify the unskipped file was still loaded properly
    employee_feed_records = [record.get_employee_feed_record() for record in claimant_data]
    validate_records(employee_feed_records, FineosExtractEmployeeFeed, "I", local_test_db_session)

    requested_absence_som_records = [
        record.get_requested_absence_som_record() for record in claimant_data
    ]
    validate_records(
        requested_absence_som_records,
        FineosExtractVbiRequestedAbsenceSom,
        "ABSENCE_CASENUMBER",
        local_test_db_session,
    )

    requested_absence_records = [record.get_requested_absence_record() for record in claimant_data]
    validate_records(
        requested_absence_records,
        FineosExtractVbiRequestedAbsence,
        "LEAVEREQUEST_ID",
        local_test_db_session,
    )


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

    claimant_data = [FineosPaymentData()]
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


# Test that if there are extra columns in the extract file,
# we log those only once if they're in the header row
def test_log_unconfigured_on_first_record(
    mock_s3_bucket,
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    local_test_db_session,
    local_test_db_other_session,
    monkeypatch,
    caplog,
):
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")

    # We add one unexpected column in the header, and we plant it, plus yet
    # another unexpected column, in two of the records. The first should only
    # be logged once. The second should be logged twice: once for each time
    # it shows up in a record.
    malformed_extract = payments_util.FineosExtractConstants.CLAIM_DETAILS
    malformed_content = (
        "PECLASSID,PEINDEXID,ABSENCECASENU,LEAVEREQUESTI,EXTRACOL\n"
        + "1,2,3,4,5\n"
        + "1,2,3,4,5,6\n"
        + "1,2,3,4,5,6"
    )

    payment_data = [FineosPaymentData()]
    upload_fineos_payment_data(
        mock_fineos_s3_bucket,
        payment_data,
        malformed_extract=malformed_extract,
        malformed_content=malformed_content,
    )

    fineos_extract_step = FineosExtractStep(
        db_session=local_test_db_session,
        log_entry_db_session=local_test_db_other_session,
        extract_config=PAYMENT_EXTRACT_CONFIG,
    )

    caplog.set_level(logging.INFO)  # noqa: B1
    fineos_extract_step.run()

    first_record_warnings = 0
    after_first_warnings = 0
    for record in caplog.records:
        if record.msg == "Unconfigured columns in FINEOS extract.":
            first_record_warnings += 1

        if record.msg == "Unconfigured columns in FINEOS extract after first record.":
            after_first_warnings += 1

    assert first_record_warnings == 1
    assert after_first_warnings == 2
