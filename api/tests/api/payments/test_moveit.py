import os

import massgov.pfml.payments.moveit as moveit
import massgov.pfml.payments.payments_util as payments_util


def test_pickup_files_from_moveit_transforms_s3path_correctly(monkeypatch, test_db_session):
    inbound_s3_path = "s3://massgov-pfml-test-agency-transfer/ctr/inbound/"
    s3_bucket_uri = "s3://massgov-pfml-test-agency-transfer"
    dest_dir = os.path.join("/ctr/inbound", payments_util.Constants.S3_INBOUND_RECEIVED_DIR)

    monkeypatch.setenv("PFML_CTR_INBOUND_PATH", inbound_s3_path)

    computed_transfer_configs = []
    monkeypatch.setattr(
        moveit,
        "copy_from_sftp_to_s3_and_archive_files",
        lambda config, db_session: computed_transfer_configs.append(config),
    )

    moveit.pickup_files_from_moveit(test_db_session)

    computed_transfer_config = computed_transfer_configs[0]
    assert computed_transfer_config.s3_bucket_uri == s3_bucket_uri
    assert computed_transfer_config.dest_dir == dest_dir


def test_send_files_to_moveit_transforms_s3path_correctly(monkeypatch, test_db_session):
    outbound_s3_path = "s3://massgov-pfml-test-agency-transfer/ctr/outbound/"
    s3_bucket_uri = "s3://massgov-pfml-test-agency-transfer"
    source_dir = os.path.join("ctr/outbound", payments_util.Constants.S3_OUTBOUND_READY_DIR)
    archive_dir = os.path.join("ctr/outbound", payments_util.Constants.S3_OUTBOUND_SENT_DIR)

    monkeypatch.setenv("PFML_CTR_OUTBOUND_PATH", outbound_s3_path)

    computed_transfer_configs = []
    monkeypatch.setattr(
        moveit,
        "copy_to_sftp_and_archive_s3_files",
        lambda config, db_session: computed_transfer_configs.append(config),
    )

    moveit.send_files_to_moveit(test_db_session)

    computed_transfer_config = computed_transfer_configs[0]
    assert computed_transfer_config.s3_bucket_uri == s3_bucket_uri
    assert computed_transfer_config.source_dir == source_dir
    assert computed_transfer_config.archive_dir == archive_dir
