import json
import os
import xml.dom.minidom as minidom
from datetime import datetime, timedelta

import boto3
import pytest

import massgov.pfml.db as db
import massgov.pfml.payments.config as payments_config
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    Country,
    CtrBatchIdentifier,
    GeoState,
    ReferenceFileType,
)
from massgov.pfml.db.models.factories import (
    AddressFactory,
    CtrBatchIdentifierFactory,
    CtrDocumentIdentifierFactory,
    EmployeeFactory,
    EmployeeReferenceFileFactory,
    ReferenceFileFactory,
)
from massgov.pfml.payments.payments_util import (
    get_fineos_vendor_customer_numbers_from_reference_file,
    get_inf_data_as_plain_text,
    get_inf_data_from_reference_file,
    is_same_address,
)
from tests.api.payments.conftest import upload_file_to_s3


@pytest.fixture
def set_source_path(tmp_path, mock_fineos_s3_bucket):
    file_name = "2020-12-21-11-30-00-expected_file_one.csv"
    test_file = tmp_path / file_name
    test_file.write_text("test, data, rowOne\ntest, data, rowTwo")

    upload_file_to_s3(
        test_file, mock_fineos_s3_bucket, f"DT2/dataexports/{file_name}",
    )

    file_name = "2020-12-21-11-30-00-expected_file_two.csv"
    test_file = tmp_path / file_name
    test_file.write_text("test, data, rowOne\ntest, data, rowTwo")

    upload_file_to_s3(
        test_file, mock_fineos_s3_bucket, f"DT2/dataexports/{file_name}",
    )


def make_s3_file(s3_bucket, key, test_file_name):
    # Utility method to upload a test file to the mocked S3.
    # test_file_name corresponds to the name of the file in the test_files directory
    test_file_path = os.path.join(os.path.dirname(__file__), f"test_files/{test_file_name}")

    s3 = boto3.client("s3")
    s3.upload_file(test_file_path, s3_bucket, key)


def test_get_date_group_str_from_path():
    assert (
        payments_util.get_date_group_str_from_path("2020-12-01-11-30-00-vpei.csv")
        == "2020-12-01-11-30-00"
    )
    assert (
        payments_util.get_date_group_str_from_path("/2020-12-01-11-30-00-vpei.csv")
        == "2020-12-01-11-30-00"
    )
    assert (
        payments_util.get_date_group_str_from_path("DT2/2020-12-01-11-30-00-vpei.csv")
        == "2020-12-01-11-30-00"
    )
    assert (
        payments_util.get_date_group_str_from_path("2020-12-01-11-30-00/2020-12-01-vpei.csv")
        == "2020-12-01-11-30-00"
    )
    assert (
        payments_util.get_date_group_str_from_path(
            "2020-12-01-11-30-00/2020-12-01-11-30-00-vpei.csv"
        )
        == "2020-12-01-11-30-00"
    )
    assert (
        payments_util.get_date_group_str_from_path(
            "2020-12-01-11-30-00/2020-12-01-11-45-00-vpei.csv"
        )
        == "2020-12-01-11-30-00"
    )
    assert (
        payments_util.get_date_group_str_from_path(
            "2020-12-01-11-30-00/2020-12-02-11-30-00-vpei.csv"
        )
        == "2020-12-01-11-30-00"
    )

    assert payments_util.get_date_group_str_from_path("2020-12-01-vpei.csv") is None
    assert payments_util.get_date_group_str_from_path("vpei.csv") is None


def test_payment_extract_reference_file_exists_by_date_group(
    test_db_session, initialize_factories_session, set_exporter_env_vars
):
    date_group = "2020-12-01-11-30-00"

    assert not payments_util.payment_extract_reference_file_exists_by_date_group(
        test_db_session, date_group, ReferenceFileType.PAYMENT_EXTRACT
    )

    file_location = os.path.join(
        payments_config.get_s3_config().pfml_fineos_inbound_path,
        payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
        date_group,
    )
    ReferenceFileFactory.create(
        file_location=file_location,
        reference_file_type_id=ReferenceFileType.PAYMENT_EXTRACT.reference_file_type_id,
    )

    assert payments_util.payment_extract_reference_file_exists_by_date_group(
        test_db_session, date_group, ReferenceFileType.PAYMENT_EXTRACT
    )


def test_copy_fineos_data_to_archival_bucket(
    test_db_session, mock_fineos_s3_bucket, mock_s3_bucket, set_exporter_env_vars
):
    date_prefix = "2020-01-02-11-30-00-"
    s3_prefix = "DT2/dataexports/"
    # Add 3 top level expected files
    make_s3_file(mock_fineos_s3_bucket, f"{s3_prefix}{date_prefix}vpei.csv", "vpei.csv")
    make_s3_file(
        mock_fineos_s3_bucket,
        f"{s3_prefix}{date_prefix}vpeipaymentdetails.csv",
        "vpei_payment_details.csv",
    )
    make_s3_file(
        mock_fineos_s3_bucket,
        f"{s3_prefix}{date_prefix}vpeiclaimdetails.csv",
        "vpei_claim_details.csv",
    )

    # Add a few other files in the same path with other names
    make_s3_file(mock_fineos_s3_bucket, f"{s3_prefix}{date_prefix}vpeiclaimants.csv", "small.csv")
    make_s3_file(mock_fineos_s3_bucket, f"{s3_prefix}{date_prefix}vpeiother.csv", "small.csv")
    make_s3_file(mock_fineos_s3_bucket, f"{s3_prefix}{date_prefix}VBI_OTHER.csv", "small.csv")

    # Add 3 files in a date folder
    date_prefix = "2020-01-01-11-30-00-"
    s3_prefix = "DT2/dataexports/2020-01-01-11-30-00/"
    # Add 3 subfolder expected files
    make_s3_file(mock_fineos_s3_bucket, f"{s3_prefix}{date_prefix}vpei.csv", "vpei.csv")
    make_s3_file(
        mock_fineos_s3_bucket,
        f"{s3_prefix}{date_prefix}vpeipaymentdetails.csv",
        "vpei_payment_details.csv",
    )
    make_s3_file(
        mock_fineos_s3_bucket,
        f"{s3_prefix}{date_prefix}vpeiclaimdetails.csv",
        "vpei_claim_details.csv",
    )

    # Add a few more invalid files with the same suffix in other S3 "folders"
    make_s3_file(mock_fineos_s3_bucket, f"{s3_prefix}yesterday/vpei.csv", "vpei.csv")
    make_s3_file(
        mock_fineos_s3_bucket,
        f"{s3_prefix}2020-11-21-11-30-00/vpeipaymentdetails.csv",
        "vpei_payment_details.csv",
    )
    make_s3_file(mock_fineos_s3_bucket, "DT2/vpeiclaimdetails.csv", "vpei_claim_details.csv")
    make_s3_file(mock_fineos_s3_bucket, "IDT/dataexports/vpeiclaimdetails.csv", "small.csv")
    copied_file_mapping_by_date = payments_util.copy_fineos_data_to_archival_bucket(
        test_db_session,
        ["vpei.csv", "vpeipaymentdetails.csv", "vpeiclaimdetails.csv"],
        ReferenceFileType.PAYMENT_EXTRACT,
    )

    expected_prefix_1 = f"s3://{mock_s3_bucket}/cps/inbound/received/2020-01-02-11-30-00-"
    assert (
        copied_file_mapping_by_date["2020-01-02-11-30-00"]["vpei.csv"]
        == f"{expected_prefix_1}vpei.csv"
    )
    assert (
        copied_file_mapping_by_date["2020-01-02-11-30-00"]["vpeipaymentdetails.csv"]
        == f"{expected_prefix_1}vpeipaymentdetails.csv"
    )
    assert (
        copied_file_mapping_by_date["2020-01-02-11-30-00"]["vpeiclaimdetails.csv"]
        == f"{expected_prefix_1}vpeiclaimdetails.csv"
    )

    expected_prefix_2 = f"s3://{mock_s3_bucket}/cps/inbound/received/2020-01-01-11-30-00-"
    assert (
        copied_file_mapping_by_date["2020-01-01-11-30-00"]["vpei.csv"]
        == f"{expected_prefix_2}vpei.csv"
    )
    assert (
        copied_file_mapping_by_date["2020-01-01-11-30-00"]["vpeipaymentdetails.csv"]
        == f"{expected_prefix_2}vpeipaymentdetails.csv"
    )
    assert (
        copied_file_mapping_by_date["2020-01-01-11-30-00"]["vpeiclaimdetails.csv"]
        == f"{expected_prefix_2}vpeiclaimdetails.csv"
    )


def test_copy_fineos_data_to_archival_bucket_duplicate_suffix_error(
    test_db_session, mock_fineos_s3_bucket, mock_s3_bucket, set_exporter_env_vars
):
    date_prefix = "2020-12-01-11-30-00-"
    s3_prefix = f"DT2/dataexports/{date_prefix}"
    # Add the 3 expected files
    make_s3_file(mock_fineos_s3_bucket, f"{s3_prefix}vpei.csv", "vpei.csv")
    make_s3_file(
        mock_fineos_s3_bucket, f"{s3_prefix}vpeipaymentdetails.csv", "vpei_payment_details.csv",
    )
    make_s3_file(
        mock_fineos_s3_bucket, f"{s3_prefix}vpeiclaimdetails.csv", "vpei_claim_details.csv"
    )

    # Add an extra vpei.csv file in the same folder
    make_s3_file(mock_fineos_s3_bucket, f"{s3_prefix}ANOTHER-vpei.csv", "vpei.csv")

    with pytest.raises(
        Exception,
        match=f"Duplicate files found for vpei.csv: s3://test_bucket/cps/inbound/received/{date_prefix}ANOTHER-vpei.csv and s3://fineos_bucket/DT2/dataexports/{date_prefix}vpei.csv",
    ):
        payments_util.copy_fineos_data_to_archival_bucket(
            test_db_session,
            ["vpei.csv", "vpeipaymentdetails.csv", "vpeiclaimdetails.csv"],
            ReferenceFileType.PAYMENT_EXTRACT,
        )


def test_copy_fineos_data_to_archival_bucket_missing_file_error(
    test_db_session, mock_fineos_s3_bucket, mock_s3_bucket, set_exporter_env_vars
):
    date_prefix = "2020-12-01-11-30-00-"
    s3_prefix = f"DT2/dataexports/{date_prefix}"
    # Add only one file
    make_s3_file(mock_fineos_s3_bucket, f"{s3_prefix}vpei.csv", "vpei.csv")

    with pytest.raises(
        Exception,
        match=f"The following files were not found in S3 {date_prefix}vpeipaymentdetails.csv,{date_prefix}vpeiclaimdetails.csv",
    ):
        payments_util.copy_fineos_data_to_archival_bucket(
            test_db_session,
            ["vpei.csv", "vpeipaymentdetails.csv", "vpeiclaimdetails.csv"],
            ReferenceFileType.PAYMENT_EXTRACT,
        )


def test_group_s3_files_by_date(mock_s3_bucket, set_exporter_env_vars):
    shared_prefix = "cps/inbound/received/"

    for prefix in [
        f"{shared_prefix}2020-01-01-11-30-00-",
        f"{shared_prefix}2020-01-02-11-30-00-",
        f"{shared_prefix}2020-01-03-11-30-00-",
    ]:
        # Add the 3 expected files
        make_s3_file(mock_s3_bucket, f"{prefix}vpei.csv", "vpei.csv")
        make_s3_file(
            mock_s3_bucket, f"{prefix}vpeipaymentdetails.csv", "vpei_payment_details.csv",
        )
        make_s3_file(mock_s3_bucket, f"{prefix}vpeiclaimdetails.csv", "vpei_claim_details.csv")
        # Add some other random files to the same folder
        make_s3_file(mock_s3_bucket, f"{prefix}somethingelse.csv", "small.csv")
        make_s3_file(mock_s3_bucket, f"{prefix}vpeiandsuch.csv", "small.csv")
        make_s3_file(mock_s3_bucket, f"{prefix}secretrecipe.csv", "small.csv")

    data_by_date = payments_util.group_s3_files_by_date(
        ["vpei.csv", "vpeipaymentdetails.csv", "vpeiclaimdetails.csv"]
    )
    assert set(data_by_date.keys()) == set(
        ["2020-01-01-11-30-00", "2020-01-02-11-30-00", "2020-01-03-11-30-00"]
    )
    for date_item, paths in data_by_date.items():
        expected_path_to_file = f"s3://{mock_s3_bucket}/{shared_prefix}{date_item}-"
        assert set(paths) == set(
            [
                f"{expected_path_to_file}vpei.csv",
                f"{expected_path_to_file}vpeiclaimdetails.csv",
                f"{expected_path_to_file}vpeipaymentdetails.csv",
            ]
        )


def _create_ctr_batch_identifier(
    now: datetime, batch_counter: int, db_session: db.Session
) -> CtrBatchIdentifier:
    batch_id = payments_util.Constants.BATCH_ID_TEMPLATE.format(
        now.strftime("%m%d"), "VCC", batch_counter
    )
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


def test_get_fineos_vendor_customer_numbers_from_reference_file(initialize_factories_session):
    ctr_doc_identfier = CtrDocumentIdentifierFactory.create()
    ref_file = ReferenceFileFactory.create()
    employee1 = EmployeeFactory.create(fineos_customer_number=111)
    employee2 = EmployeeFactory.create(fineos_customer_number=222)

    EmployeeReferenceFileFactory(
        reference_file=ref_file, ctr_document_identifier=ctr_doc_identfier, employee=employee1
    )
    EmployeeReferenceFileFactory(
        reference_file=ref_file, ctr_document_identifier=ctr_doc_identfier, employee=employee2
    )

    data = get_fineos_vendor_customer_numbers_from_reference_file(ref_file)

    assert len(data) == 2
    for d in data:
        assert {"fineos_customer_number", "ctr_vendor_customer_code"} == set(d.keys())
        assert d["fineos_customer_number"] in [111, 222]
        assert d["ctr_vendor_customer_code"] in [
            employee1.ctr_vendor_customer_code,
            employee2.ctr_vendor_customer_code,
        ]
