import json
import xml.dom.minidom as minidom
from datetime import datetime, timedelta

import boto3
import pytest

import massgov.pfml.db as db
import massgov.pfml.payments.config as payments_config
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import Country, CtrBatchIdentifier, GeoState
from massgov.pfml.db.models.factories import (
    AddressFactory,
    CtrBatchIdentifierFactory,
    ReferenceFileFactory,
)
from massgov.pfml.payments.payments_util import (
    get_inf_data_as_plain_text,
    get_inf_data_from_reference_file,
    is_same_address,
)
from tests.api.payments.conftest import upload_file_to_s3


@pytest.fixture
def set_source_path(tmp_path, mock_fineos_s3_bucket):
    file_name = "2020-12-21-expected_file_one.csv"
    test_file = tmp_path / file_name
    test_file.write_text("test, data, rowOne\ntest, data, rowTwo")

    upload_file_to_s3(
        test_file, mock_fineos_s3_bucket, f"DT2/dataexports/{file_name}",
    )

    file_name = "2020-12-21-expected_file_two.csv"
    test_file = tmp_path / file_name
    test_file.write_text("test, data, rowOne\ntest, data, rowTwo")

    upload_file_to_s3(
        test_file, mock_fineos_s3_bucket, f"DT2/dataexports/{file_name}",
    )


def test_copy_fineos_data_to_archival_bucket(tmp_path, set_source_path, set_exporter_env_vars):
    expected_file_names = ["expected_file_one.csv", "expected_file_two.csv"]
    payments_util.copy_fineos_data_to_archival_bucket(expected_file_names)

    copied_files = file_util.list_files(payments_config.get_s3_config().pfml_fineos_inbound_path)

    assert len(copied_files) == 2


def test_group_s3_files_by_date(set_source_path, set_exporter_env_vars):
    expected_file_names = ["expected_file_one.csv", "expected_file_two.csv"]
    payments_util.copy_fineos_data_to_archival_bucket(expected_file_names)
    data_by_date = payments_util.group_s3_files_by_date(expected_file_names)

    files_for_test_date = data_by_date["2020-12-21"]
    assert files_for_test_date is not None
    assert len(files_for_test_date) == 2


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


def test_same_address(initialize_factories_session):
    first = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110",
        country_id=Country.USA.country_id,
    )
    second = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110",
        country_id=Country.USA.country_id,
    )
    assert is_same_address(first, second) is True


def test_same_address_comparable(initialize_factories_session):
    first = AddressFactory(
        address_line_one=" 1234 MaIn sT ",
        address_line_two="   #827 uNIT",
        city="BOSTON",
        zip_code=" 02110  ",
    )
    second = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110",
    )
    assert is_same_address(first, second) is True

    # CTR normalized zip codes should be read as 5 digits
    fineos_address = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110",
    )
    ctr_address = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110-12345",
    )
    assert is_same_address(fineos_address, ctr_address) is True


def test_different_address(initialize_factories_session):
    first = AddressFactory()
    second = AddressFactory()
    assert is_same_address(first, second) is False

    # Different address line one
    third = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110",
    )
    fourth = AddressFactory(
        address_line_one="1234 main street",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110",
    )
    assert is_same_address(third, fourth) is False

    # Different city
    fifth = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="watertown",
        zip_code="02110",
    )
    assert is_same_address(third, fifth) is False

    # Different state
    sixth = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        geo_state_id=GeoState.CA.geo_state_id,
        zip_code="02111",
    )
    assert is_same_address(third, sixth) is False

    # Different zip code
    seventh = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02111",
    )
    assert is_same_address(third, seventh) is False

    # Different country
    eighth = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02111",
        country_id=Country.USA.country_id,
    )
    ninth = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02111",
        country_id=Country.TWN.country_id,
    )
    assert is_same_address(eighth, ninth) is False


def test_address_line_two(initialize_factories_session):
    first = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110",
    )
    second = AddressFactory(address_line_one="1234 main st", city="boston", zip_code="02110")
    assert is_same_address(first, second) is False

    third = AddressFactory(address_line_one="1234 main st", city="boston", zip_code="02110")
    fourth = AddressFactory(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110",
    )
    assert is_same_address(third, fourth) is False


def test_get_inf_data_from_reference_file(test_db_session, initialize_factories_session):
    ctr_batch_identifier = CtrBatchIdentifierFactory.create()
    reference_file = ReferenceFileFactory.create()
    reference_file.ctr_batch_identifier_id = ctr_batch_identifier.ctr_batch_identifier_id

    inf_data = get_inf_data_from_reference_file(reference_file, test_db_session)

    assert inf_data is not None
    assert inf_data == json.loads(ctr_batch_identifier.inf_data)


def test_get_inf_data_as_plain_text(test_db_session):
    inf_data_dict = {
        "NewMmarsBatchID": "EOL0101GAX11",
        "NewMmarsBatchDeptCode": "EOL",
        "NewMmarsUnitCode": "8770",
        "NewMmarsImportDate": "2020-01-01",
        "NewMmarsTransCode": "GAX",
        "NewMmarsTableName": "",
        "NewMmarsTransCount": "2",
        "NewMmarsTransDollarAmount": "2500.00",
    }
    inf_data_text = get_inf_data_as_plain_text(inf_data_dict)

    for key in inf_data_dict.keys():
        expected_line = f"{key} = {inf_data_dict[key]}"
        assert expected_line in inf_data_text
