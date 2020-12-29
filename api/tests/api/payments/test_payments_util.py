import xml.dom.minidom as minidom
from datetime import datetime, timedelta

import boto3

import massgov.pfml.db as db
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import CtrBatchIdentifier
from massgov.pfml.db.models.factories import CtrBatchIdentifierFactory


def _create_ctr_batch_identifier(
    now: datetime, batch_counter: int, db_session: db.Session
) -> CtrBatchIdentifier:
    batch_id = payments_util.BATCH_ID_TEMPLATE.format(now.strftime("%m%d"), "VCC", batch_counter)
    ctr_batch_id = CtrBatchIdentifierFactory(
        ctr_batch_identifier=batch_id,
        year=now.year,
        batch_date=now.date(),
        batch_counter=batch_counter,
    )
    db_session.add(ctr_batch_id)
    db_session.commit()

    return ctr_batch_id


def test_create_next_batch_id_first_batch_id(test_db_session):
    ctr_batch_id = payments_util.create_next_batch_id(datetime.now(), "VCC", test_db_session)
    assert (
        ctr_batch_id.batch_counter == 10
    ), "First batch ID today does not start with expected value"


def test_create_next_batch_id_with_existing_values(initialize_factories_session, test_db_session):
    now = datetime.now()
    yesterday = datetime.now() - timedelta(days=1)

    # Add several batches for today. range() does not include the stop value.
    # https://docs.python.org/3.8/library/stdtypes.html#ranges
    next_batch_counter = 13
    for batch_counter in range(10, next_batch_counter):
        _create_ctr_batch_identifier(now, batch_counter, test_db_session)

    # Add more batches for yesterday so that there are batch_counters larger than the one we
    # will be inserting.
    for batch_counter in range(10, 2 * next_batch_counter):
        _create_ctr_batch_identifier(yesterday, batch_counter, test_db_session)

    ctr_batch_id = payments_util.create_next_batch_id(now, "VCC", test_db_session)
    assert ctr_batch_id.batch_counter == next_batch_counter


def test_create_mmars_files_in_s3(mock_s3_bucket):
    bucket_path = f"s3://{mock_s3_bucket}"
    filename = "example_filename"
    dat_xml_document = minidom.Document()
    inf_dict = {"NewMmarsBatchDeptCode": payments_util.Constants.COMPTROLLER_DEPT_CODE}

    payments_util.create_mmars_files_in_s3(bucket_path, filename, dat_xml_document, inf_dict)

    # Expect the files to have been uploaded to S3.
    files_in_mock_s3_bucket = file_util.list_files(bucket_path)
    expected_filename_extensions = [".DAT", ".INF"]
    for filename_extension in expected_filename_extensions:
        assert f"{filename}{filename_extension}" in files_in_mock_s3_bucket

    # Expect the files to have the proper contents.
    #
    # Testing only the INF file here because it is simpler (does not involve XML formatting) and
    # the DAT file should follow a similar pattern.
    s3 = boto3.client("s3")
    inf_file = s3.get_object(Bucket=mock_s3_bucket, Key=f"{filename}.INF")
    assert inf_file["Body"].read() == b"NewMmarsBatchDeptCode = EOL;\n"
