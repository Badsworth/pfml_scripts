import os

import faker
import pytest
from freezegun import freeze_time

import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.delegated_payments.pickup_response_files_step import (
    FILE_NAME_FORMAT,
    PickupResponseFilesStep,
)

fake = faker.Faker()


def generate_files(file_name, s3_path):
    # This creates various file names that should all be found
    file_names = [
        f"{file_name}.csv",  # File with extension
        file_name,  # Exact match
        f"PREFIX PREFIX 123 {file_name}".upper(),
        f"PREFIX-PREFIX-{file_name}-SUFFIX-SUFFIX".lower(),
        f"2021-01-01-12-00-00-{file_name}.txt",
        f"space         {file_name}          .png",
        f"{fake.random_int(min=1_000_000, max=9_999_999)}-{file_name}.csv.csv",
    ]

    for name in file_names:
        output_path = os.path.join(s3_path, name)
        with file_util.write_file(output_path) as output_file:
            output_file.write("Text")  # Contents don't matter for this test

    return file_names


def verify_files(directory, file_names, add_timestamps=False):
    directory_contents = file_util.list_files(directory)

    now = payments_util.get_now()
    expected_files = []
    for file_name in file_names:
        if add_timestamps:
            expected_file_name = FILE_NAME_FORMAT.format(
                now.strftime("%Y-%m-%d-%H-%M-%S"), file_name
            )
            expected_files.append(expected_file_name)
        else:
            expected_files.append(file_name)

    assert set(directory_contents) == set(expected_files)


def verify_metrics(step, expected_metrics):
    log_entry_metrics = step.log_entry.metrics
    for metric_key, expected_value in expected_metrics.items():
        assert log_entry_metrics.get(metric_key, None) == expected_value


@pytest.fixture
def pickup_response_file_step(initialize_factories_session, test_db_session, test_db_other_session):
    return PickupResponseFilesStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


@pytest.fixture
def setup_paths(monkeypatch, mock_s3_bucket):
    pfml_payment_rejects_archive_path = f"s3://{mock_s3_bucket}/audit/archive"
    monkeypatch.setenv("PFML_PAYMENT_REJECTS_ARCHIVE_PATH", pfml_payment_rejects_archive_path)

    dfml_response_inbound_path = f"s3://{mock_s3_bucket}/dfml-responses"
    monkeypatch.setenv("DFML_RESPONSE_INBOUND_PATH", dfml_response_inbound_path)

    check_archive_path = f"s3://{mock_s3_bucket}/pub/archive/check"
    monkeypatch.setenv("PFML_PUB_CHECK_ARCHIVE_PATH", check_archive_path)

    ach_archive_path = f"s3://{mock_s3_bucket}/pub/archive/ach"
    monkeypatch.setenv("PFML_PUB_ACH_ARCHIVE_PATH", ach_archive_path)

    moveit_inbound_path = f"s3://{mock_s3_bucket}/pub/inbound"
    monkeypatch.setenv("PUB_MOVEIT_INBOUND_PATH", moveit_inbound_path)


@pytest.fixture
def payment_reject_files(setup_paths):
    dfml_response_inbound_path = payments_config.get_s3_config().dfml_response_inbound_path
    return generate_files(
        payments_util.Constants.FILE_NAME_PAYMENT_AUDIT_REPORT, dfml_response_inbound_path
    )


@pytest.fixture
def pub_check_files(setup_paths):
    # We actually expect two different file names for PUB check, show that it'll move both
    file_name = payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY
    outstanding_file_name = f"Outstanding {file_name}"
    paid_file_name = f"Paid {file_name}"

    moveit_inbound_path = payments_config.get_s3_config().pub_moveit_inbound_path
    return generate_files(outstanding_file_name, moveit_inbound_path) + generate_files(
        paid_file_name, moveit_inbound_path
    )


@pytest.fixture
def pub_ach_files(setup_paths):
    moveit_inbound_path = payments_config.get_s3_config().pub_moveit_inbound_path
    return generate_files(payments_util.Constants.FILE_NAME_PUB_NACHA, moveit_inbound_path)


@pytest.fixture
def random_files_in_dfml_response_path(setup_paths):
    dfml_response_inbound_path = payments_config.get_s3_config().dfml_response_inbound_path
    # Add a few file names similar, but not a match to the files expected in this directory

    similar_to_positive_pay_file = payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY[2:]
    similar_to_audit_file = payments_util.Constants.FILE_NAME_PAYMENT_AUDIT_REPORT.replace("-", "_")
    return generate_files(
        similar_to_positive_pay_file, dfml_response_inbound_path
    ) + generate_files(similar_to_audit_file, dfml_response_inbound_path)


@pytest.fixture
def random_files_in_moveit_response_path(setup_paths):
    moveit_inbound_path = payments_config.get_s3_config().pub_moveit_inbound_path
    # Add a few file names similar, but not a match to the files expected in this directory

    similar_file_1 = payments_util.Constants.FILE_NAME_PUB_NACHA[::-1]  # Reversed
    similar_file_2 = payments_util.Constants.FILE_NAME_PUB_NACHA.replace("NACHA", "NACHO")
    return generate_files(similar_file_1, moveit_inbound_path) + generate_files(
        similar_file_2, moveit_inbound_path
    )


@pytest.fixture
def ok_files_in_moveit_response_path(setup_paths):
    moveit_inbound_path = payments_config.get_s3_config().pub_moveit_inbound_path
    # Add a few files that end with .OK which don't get moved, but also don't increment
    # any sort of warning as they're expected and used for triggering the PUB responses ECS task

    ok_file_1 = "DONE.OK"
    ok_file_2 = ".ok-words"
    return generate_files(ok_file_1, moveit_inbound_path) + generate_files(
        ok_file_2, moveit_inbound_path
    )


@freeze_time("2021-01-01 12:00:00")
def test_run_step(pickup_response_file_step, payment_reject_files, pub_check_files, pub_ach_files):
    s3_config = payments_config.get_s3_config()
    # Construct the expected output directories
    payment_audit_received_path = os.path.join(
        s3_config.pfml_payment_rejects_archive_path, payments_util.Constants.S3_INBOUND_RECEIVED_DIR
    )
    pub_check_received_path = os.path.join(
        s3_config.pfml_pub_check_archive_path, payments_util.Constants.S3_INBOUND_RECEIVED_DIR
    )
    pub_ach_received_path = os.path.join(
        s3_config.pfml_pub_ach_archive_path, payments_util.Constants.S3_INBOUND_RECEIVED_DIR
    )

    # Verify all input directories contain the expected files
    verify_files(s3_config.pub_moveit_inbound_path, pub_check_files + pub_ach_files)
    verify_files(s3_config.dfml_response_inbound_path, payment_reject_files)
    # Verify the output directories are empty
    verify_files(payment_audit_received_path, [])
    verify_files(pub_check_received_path, [])
    verify_files(pub_ach_received_path, [])

    pickup_response_file_step.run()

    # Verify the output directories have the expected files
    verify_files(payment_audit_received_path, payment_reject_files, True)
    verify_files(pub_check_received_path, pub_check_files, True)
    verify_files(pub_ach_received_path, pub_ach_files, True)

    # Verify the input directories are now empty
    verify_files(s3_config.pub_moveit_inbound_path, [])
    verify_files(s3_config.dfml_response_inbound_path, [])

    verify_metrics(
        pickup_response_file_step,
        {
            "files_moved_count": len(payment_reject_files)
            + len(pub_check_files)
            + len(pub_ach_files),
            "unknown_files_count": 0,
            "Payment-Audit-Report_file_moved_count": len(payment_reject_files),
            "EOLWD-DFML-POSITIVE-PAY_file_moved_count": len(pub_check_files),
            "EOLWD-DFML-NACHA_file_moved_count": len(pub_ach_files),
        },
    )


@freeze_time("2021-01-01 12:00:00")
def test_run_step_miscellaneous_files_present(
    pickup_response_file_step,
    payment_reject_files,
    pub_check_files,
    pub_ach_files,
    random_files_in_dfml_response_path,
    random_files_in_moveit_response_path,
    ok_files_in_moveit_response_path,
):
    s3_config = payments_config.get_s3_config()
    # Construct the expected output directories
    payment_audit_received_path = os.path.join(
        s3_config.pfml_payment_rejects_archive_path, payments_util.Constants.S3_INBOUND_RECEIVED_DIR
    )
    pub_check_received_path = os.path.join(
        s3_config.pfml_pub_check_archive_path, payments_util.Constants.S3_INBOUND_RECEIVED_DIR
    )
    pub_ach_received_path = os.path.join(
        s3_config.pfml_pub_ach_archive_path, payments_util.Constants.S3_INBOUND_RECEIVED_DIR
    )

    # Verify all input directories contain the expected files
    verify_files(
        s3_config.pub_moveit_inbound_path,
        pub_check_files
        + pub_ach_files
        + random_files_in_moveit_response_path
        + ok_files_in_moveit_response_path,
    )
    verify_files(
        s3_config.dfml_response_inbound_path,
        payment_reject_files + random_files_in_dfml_response_path,
    )
    # Verify the output directories are empty
    verify_files(payment_audit_received_path, [])
    verify_files(pub_check_received_path, [])
    verify_files(pub_ach_received_path, [])

    pickup_response_file_step.run()

    # Verify the output directories have the expected files
    verify_files(payment_audit_received_path, payment_reject_files, True)
    verify_files(pub_check_received_path, pub_check_files, True)
    verify_files(pub_ach_received_path, pub_ach_files, True)

    # Verify the input directories contain just the random files
    verify_files(
        s3_config.pub_moveit_inbound_path,
        random_files_in_moveit_response_path + ok_files_in_moveit_response_path,
    )
    verify_files(s3_config.dfml_response_inbound_path, random_files_in_dfml_response_path)

    verify_metrics(
        pickup_response_file_step,
        {
            "files_moved_count": len(payment_reject_files)
            + len(pub_check_files)
            + len(pub_ach_files),
            "unknown_files_count": len(random_files_in_moveit_response_path)
            + len(random_files_in_dfml_response_path),
            "Payment-Audit-Report_file_moved_count": len(payment_reject_files),
            "EOLWD-DFML-POSITIVE-PAY_file_moved_count": len(pub_check_files),
            "EOLWD-DFML-NACHA_file_moved_count": len(pub_ach_files),
        },
    )


@freeze_time("2021-01-01 12:00:00")
def test_run_step_no_files(pickup_response_file_step, setup_paths):
    s3_config = payments_config.get_s3_config()
    # Construct the expected output directories
    payment_audit_received_path = os.path.join(
        s3_config.pfml_payment_rejects_archive_path, payments_util.Constants.S3_INBOUND_RECEIVED_DIR
    )
    pub_check_received_path = os.path.join(
        s3_config.pfml_pub_check_archive_path, payments_util.Constants.S3_INBOUND_RECEIVED_DIR
    )
    pub_ach_received_path = os.path.join(
        s3_config.pfml_pub_ach_archive_path, payments_util.Constants.S3_INBOUND_RECEIVED_DIR
    )

    # Verify all input directories are empty
    verify_files(s3_config.pub_moveit_inbound_path, [])
    verify_files(s3_config.dfml_response_inbound_path, [])
    # Verify the output directories are empty
    verify_files(payment_audit_received_path, [])
    verify_files(pub_check_received_path, [])
    verify_files(pub_ach_received_path, [])

    pickup_response_file_step.run()

    # Verify all input directories are still empty
    verify_files(s3_config.pub_moveit_inbound_path, [])
    verify_files(s3_config.dfml_response_inbound_path, [])
    # Verify the output directories are still empty
    verify_files(payment_audit_received_path, [])
    verify_files(pub_check_received_path, [])
    verify_files(pub_ach_received_path, [])

    verify_metrics(
        pickup_response_file_step,
        {
            "files_moved_count": 0,
            "unknown_files_count": 0,
            "Payment-Audit-Report_file_moved_count": 0,
            "EOLWD-DFML-POSITIVE-PAY_file_moved_count": 0,
            "EOLWD-DFML-NACHA_file_moved_count": 0,
        },
    )


@freeze_time("2021-01-01 12:00:00")
def test_run_step_only_irrelevant_files(
    pickup_response_file_step,
    random_files_in_dfml_response_path,
    random_files_in_moveit_response_path,
    ok_files_in_moveit_response_path,
):
    s3_config = payments_config.get_s3_config()
    # Construct the expected output directories
    payment_audit_received_path = os.path.join(
        s3_config.pfml_payment_rejects_archive_path, payments_util.Constants.S3_INBOUND_RECEIVED_DIR
    )
    pub_check_received_path = os.path.join(
        s3_config.pfml_pub_check_archive_path, payments_util.Constants.S3_INBOUND_RECEIVED_DIR
    )
    pub_ach_received_path = os.path.join(
        s3_config.pfml_pub_ach_archive_path, payments_util.Constants.S3_INBOUND_RECEIVED_DIR
    )

    # Verify all input directories contain the expected files
    verify_files(
        s3_config.pub_moveit_inbound_path,
        random_files_in_moveit_response_path + ok_files_in_moveit_response_path,
    )
    verify_files(s3_config.dfml_response_inbound_path, random_files_in_dfml_response_path)
    # Verify the output directories are empty
    verify_files(payment_audit_received_path, [])
    verify_files(pub_check_received_path, [])
    verify_files(pub_ach_received_path, [])

    pickup_response_file_step.run()

    # Verify the input directories are unchanged
    verify_files(
        s3_config.pub_moveit_inbound_path,
        random_files_in_moveit_response_path + ok_files_in_moveit_response_path,
    )
    verify_files(s3_config.dfml_response_inbound_path, random_files_in_dfml_response_path)
    # Verify the output directories are empty
    verify_files(payment_audit_received_path, [])
    verify_files(pub_check_received_path, [])
    verify_files(pub_ach_received_path, [])

    verify_metrics(
        pickup_response_file_step,
        {
            "files_moved_count": 0,
            # The .OK files aren't in the unknown count as per the logic
            "unknown_files_count": len(random_files_in_moveit_response_path)
            + len(random_files_in_dfml_response_path),
            "Payment-Audit-Report_file_moved_count": 0,
            "EOLWD-DFML-POSITIVE-PAY_file_moved_count": 0,
            "EOLWD-DFML-NACHA_file_moved_count": 0,
        },
    )
