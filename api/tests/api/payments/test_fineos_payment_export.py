import os
import tempfile
import zipfile
from datetime import date

import boto3
import pytest
from freezegun import freeze_time

import massgov.pfml.payments.fineos_payment_export as exporter
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    AddressType,
    BankAccountType,
    EmployeeAddress,
    GeoState,
    Payment,
    PaymentMethod,
    ReferenceFileType,
    TaxIdentifier,
)
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ClaimFactory,
    EftFactory,
    EmployeeFactory,
    EmployerFactory,
    PaymentFactory,
    ReferenceFileFactory,
)
from massgov.pfml.payments.payments_util import ValidationIssue, ValidationReason, get_s3_config

### UTILITY METHODS


def make_s3_zip_file(s3_bucket, key, test_file_name):
    # Utility method to convert one of our test files to a zipped
    # file in a temporary test directory and upload it to the mocked S3.
    # The name of the zip is based on the key passed in:
    # key: s3://test_bucket/path/to/file.csv.zip creates a zip named
    # file.csv.zip with the test file inside named file.csv
    # test_file_name corresponds to the name of the file in the test_files directory
    test_file_path = os.path.join(os.path.dirname(__file__), f"test_files/{test_file_name}")

    filename = key.split("/")[-1]
    if filename.endswith(".zip"):
        filename = filename[:-4]

    with tempfile.TemporaryDirectory() as directory:
        zip_path = f"{directory}/{filename}.zip"

        with zipfile.ZipFile(zip_path, "w") as zip_obj:
            zip_obj.write(test_file_path, arcname=filename)

        s3 = boto3.client("s3")
        s3.upload_file(zip_path, s3_bucket, key)


def add_db_records(
    db_session,
    tin,
    absence_case_id,
    add_claim=True,
    add_address=True,
    add_eft=True,
    add_payment=False,
    c_value=None,
    i_value=None,
):
    eft = None
    if add_eft:
        eft = EftFactory()

    mailing_address = None
    if add_address:
        mailing_address = AddressFactory()

    employee = EmployeeFactory.create(
        tax_identifier=TaxIdentifier(tax_identifier=tin), mailing_address=mailing_address, eft=eft
    )

    if add_address:
        employee.addresses = [EmployeeAddress(employee=employee, address=mailing_address)]

    if add_claim:
        employer = EmployerFactory.create()
        claim = ClaimFactory.create(
            employer_id=employer.employer_id,
            fineos_absence_id=absence_case_id,
            employee_id=employee.employee_id,
        )

        # Payment needs to be attached to a claim
        if add_payment:
            PaymentFactory.create(claim=claim)


def setup_process_tests(
    mock_s3_bucket,
    test_db_session,
    add_claim=True,
    add_address=True,
    add_eft=True,
    add_payment=False,
):
    """ This is a utility method for setting up a lot of boiler plate in the
        process_extract_data tests
    """
    s3_prefix = "cps/inbound/received/2020-01-01-11-30-00-"
    # Add the 3 expected files
    make_s3_zip_file(mock_s3_bucket, f"{s3_prefix}vpei.csv.zip", "vpei.csv")
    make_s3_zip_file(
        mock_s3_bucket, f"{s3_prefix}vpeipaymentdetails.csv.zip", "vpei_payment_details.csv",
    )
    make_s3_zip_file(
        mock_s3_bucket, f"{s3_prefix}vpeiclaimdetails.csv.zip", "vpei_claim_details.csv"
    )

    add_db_records(
        test_db_session,
        "111111111",
        "NTN-01-ABS-02",
        add_claim=add_claim,
        add_address=add_address,
        add_eft=add_eft,
        add_payment=add_payment,
        c_value="7326",
        i_value="301",
    )
    add_db_records(
        test_db_session,
        "222222222",
        "NTN-02-ABS-03",
        add_claim=add_claim,
        add_address=add_address,
        add_eft=add_eft,
        add_payment=add_payment,
        c_value="7326",
        i_value="302",
    )
    add_db_records(
        test_db_session,
        "333333333",
        "NTN-03-ABS-04",
        add_claim=add_claim,
        add_address=add_address,
        add_eft=add_eft,
        add_payment=add_payment,
        c_value="7326",
        i_value="303",
    )


### TESTS BEGIN


def test_get_date_group_str_from_path():
    assert (
        exporter.get_date_group_str_from_path("2020-12-01-11-30-00-vpei.csv.zip")
        == "2020-12-01-11-30-00"
    )
    assert (
        exporter.get_date_group_str_from_path("/2020-12-01-11-30-00-vpei.csv.zip")
        == "2020-12-01-11-30-00"
    )
    assert (
        exporter.get_date_group_str_from_path("DT2/2020-12-01-11-30-00-vpei.csv.zip")
        == "2020-12-01-11-30-00"
    )
    assert (
        exporter.get_date_group_str_from_path("2020-12-01-11-30-00/2020-12-01-vpei.csv.zip")
        == "2020-12-01-11-30-00"
    )
    assert (
        exporter.get_date_group_str_from_path(
            "2020-12-01-11-30-00/2020-12-01-11-30-00-vpei.csv.zip"
        )
        == "2020-12-01-11-30-00"
    )
    assert (
        exporter.get_date_group_str_from_path(
            "2020-12-01-11-30-00/2020-12-01-11-45-00-vpei.csv.zip"
        )
        == "2020-12-01-11-30-00"
    )
    assert (
        exporter.get_date_group_str_from_path(
            "2020-12-01-11-30-00/2020-12-02-11-30-00-vpei.csv.zip"
        )
        == "2020-12-01-11-30-00"
    )

    assert exporter.get_date_group_str_from_path("2020-12-01-vpei.csv.zip") is None
    assert exporter.get_date_group_str_from_path("vpei.csv.zip") is None


def test_copy_fineos_data_to_archival_bucket(
    test_db_session, mock_fineos_s3_bucket, mock_s3_bucket, set_exporter_env_vars
):
    date_prefix = "2020-01-02-11-30-00-"
    s3_prefix = "DT2/dataexports/"
    # Add 3 top level expected files
    make_s3_zip_file(mock_fineos_s3_bucket, f"{s3_prefix}{date_prefix}vpei.csv.zip", "vpei.csv")
    make_s3_zip_file(
        mock_fineos_s3_bucket,
        f"{s3_prefix}{date_prefix}vpeipaymentdetails.csv.zip",
        "vpei_payment_details.csv",
    )
    make_s3_zip_file(
        mock_fineos_s3_bucket,
        f"{s3_prefix}{date_prefix}vpeiclaimdetails.csv.zip",
        "vpei_claim_details.csv",
    )

    # Add a few other files in the same path with other names
    make_s3_zip_file(
        mock_fineos_s3_bucket, f"{s3_prefix}{date_prefix}vpeiclaimants.csv.zip", "small.csv"
    )
    make_s3_zip_file(
        mock_fineos_s3_bucket, f"{s3_prefix}{date_prefix}vpeiother.csv.zip", "small.csv"
    )
    make_s3_zip_file(
        mock_fineos_s3_bucket, f"{s3_prefix}{date_prefix}VBI_OTHER.csv.zip", "small.csv"
    )

    # Add 3 files in a date folder
    date_prefix = "2020-01-01-11-30-00-"
    s3_prefix = "DT2/dataexports/2020-01-01-11-30-00/"
    # Add 3 subfolder expected files
    make_s3_zip_file(mock_fineos_s3_bucket, f"{s3_prefix}{date_prefix}vpei.csv.zip", "vpei.csv")
    make_s3_zip_file(
        mock_fineos_s3_bucket,
        f"{s3_prefix}{date_prefix}vpeipaymentdetails.csv.zip",
        "vpei_payment_details.csv",
    )
    make_s3_zip_file(
        mock_fineos_s3_bucket,
        f"{s3_prefix}{date_prefix}vpeiclaimdetails.csv.zip",
        "vpei_claim_details.csv",
    )

    # Add a few more invalid files with the same suffix in other S3 "folders"
    make_s3_zip_file(mock_fineos_s3_bucket, f"{s3_prefix}yesterday/vpei.csv.zip", "vpei.csv")
    make_s3_zip_file(
        mock_fineos_s3_bucket,
        f"{s3_prefix}2020-11-21-11-30-00/vpeipaymentdetails.csv.zip",
        "vpei_payment_details.csv",
    )
    make_s3_zip_file(
        mock_fineos_s3_bucket, "DT2/vpeiclaimdetails.csv.zip", "vpei_claim_details.csv"
    )
    make_s3_zip_file(mock_fineos_s3_bucket, "IDT/dataexports/vpeiclaimdetails.csv.zip", "small.csv")
    copied_file_mapping_by_date = exporter.copy_fineos_data_to_archival_bucket(test_db_session)

    expected_prefix_1 = f"s3://{mock_s3_bucket}/cps/inbound/received/2020-01-02-11-30-00-"
    assert (
        copied_file_mapping_by_date["2020-01-02-11-30-00"]["vpei.csv.zip"]
        == f"{expected_prefix_1}vpei.csv.zip"
    )
    assert (
        copied_file_mapping_by_date["2020-01-02-11-30-00"]["vpeipaymentdetails.csv.zip"]
        == f"{expected_prefix_1}vpeipaymentdetails.csv.zip"
    )
    assert (
        copied_file_mapping_by_date["2020-01-02-11-30-00"]["vpeiclaimdetails.csv.zip"]
        == f"{expected_prefix_1}vpeiclaimdetails.csv.zip"
    )

    expected_prefix_2 = f"s3://{mock_s3_bucket}/cps/inbound/received/2020-01-01-11-30-00-"
    assert (
        copied_file_mapping_by_date["2020-01-01-11-30-00"]["vpei.csv.zip"]
        == f"{expected_prefix_2}vpei.csv.zip"
    )
    assert (
        copied_file_mapping_by_date["2020-01-01-11-30-00"]["vpeipaymentdetails.csv.zip"]
        == f"{expected_prefix_2}vpeipaymentdetails.csv.zip"
    )
    assert (
        copied_file_mapping_by_date["2020-01-01-11-30-00"]["vpeiclaimdetails.csv.zip"]
        == f"{expected_prefix_2}vpeiclaimdetails.csv.zip"
    )


def test_copy_fineos_data_to_archival_bucket_duplicate_suffix_error(
    test_db_session, mock_fineos_s3_bucket, mock_s3_bucket, set_exporter_env_vars
):
    date_prefix = "2020-12-01-11-30-00-"
    s3_prefix = f"DT2/dataexports/{date_prefix}"
    # Add the 3 expected files
    make_s3_zip_file(mock_fineos_s3_bucket, f"{s3_prefix}vpei.csv.zip", "vpei.csv")
    make_s3_zip_file(
        mock_fineos_s3_bucket, f"{s3_prefix}vpeipaymentdetails.csv.zip", "vpei_payment_details.csv",
    )
    make_s3_zip_file(
        mock_fineos_s3_bucket, f"{s3_prefix}vpeiclaimdetails.csv.zip", "vpei_claim_details.csv"
    )

    # Add an extra vpei.csv file in the same folder
    make_s3_zip_file(mock_fineos_s3_bucket, f"{s3_prefix}ANOTHER-vpei.csv.zip", "vpei.csv")

    with pytest.raises(
        Exception,
        match=f"Duplicate files found for vpei.csv.zip: s3://test_bucket/cps/inbound/received/{date_prefix}ANOTHER-vpei.csv.zip and s3://fineos_bucket/DT2/dataexports/{date_prefix}vpei.csv.zip",
    ):
        exporter.copy_fineos_data_to_archival_bucket(test_db_session)


def test_copy_fineos_data_to_archival_bucket_missing_file_error(
    test_db_session, mock_fineos_s3_bucket, mock_s3_bucket, set_exporter_env_vars
):
    date_prefix = "2020-12-01-11-30-00-"
    s3_prefix = f"DT2/dataexports/{date_prefix}"
    # Add only one file
    make_s3_zip_file(mock_fineos_s3_bucket, f"{s3_prefix}vpei.csv.zip", "vpei.csv")

    with pytest.raises(
        Exception,
        match=f"The following files were not found in S3 {date_prefix}vpeipaymentdetails.csv.zip,{date_prefix}vpeiclaimdetails.csv.zip",
    ):
        exporter.copy_fineos_data_to_archival_bucket(test_db_session)


def test_download_and_parse_data(mock_s3_bucket, tmp_path):
    make_s3_zip_file(mock_s3_bucket, "path/to/file/test.csv.zip", "small.csv")

    raw_data = exporter.download_and_parse_data(
        f"s3://{mock_s3_bucket}/path/to/file/test.csv.zip", tmp_path
    )

    # First verify the file was downloaded and named right
    downloaded_files = file_util.list_files(str(tmp_path))
    assert set(downloaded_files) == set(["test.csv.zip"])

    # Verify that it was parsed properly and handles new lines in a data column
    assert len(raw_data) == 2
    assert raw_data[0] == {
        "ColumnA": "Data1a",
        "ColumnB": "Data1b",
        "ColumnC": "Data\n1\nc",
        "ColumnD": "Data1d",
        "ColumnA_1": "x",
        "ColumnA_2": "y",
        "ColumnA_3": "z",
    }

    assert raw_data[1] == {
        "ColumnA": "",
        "ColumnB": "",
        "ColumnC": "",
        "ColumnD": "",
        "ColumnA_1": "",
        "ColumnA_2": "",
        "ColumnA_3": "",
    }


def test_group_s3_files_by_date(mock_s3_bucket, set_exporter_env_vars):
    shared_prefix = "cps/inbound/received/"

    for prefix in [
        f"{shared_prefix}2020-01-01-11-30-00-",
        f"{shared_prefix}2020-01-02-11-30-00-",
        f"{shared_prefix}2020-01-03-11-30-00-",
    ]:
        # Add the 3 expected files
        make_s3_zip_file(mock_s3_bucket, f"{prefix}vpei.csv.zip", "vpei.csv")
        make_s3_zip_file(
            mock_s3_bucket, f"{prefix}vpeipaymentdetails.csv.zip", "vpei_payment_details.csv",
        )
        make_s3_zip_file(
            mock_s3_bucket, f"{prefix}vpeiclaimdetails.csv.zip", "vpei_claim_details.csv"
        )
        # Add some other random files to the same folder
        make_s3_zip_file(mock_s3_bucket, f"{prefix}somethingelse.csv.zip", "small.csv")
        make_s3_zip_file(mock_s3_bucket, f"{prefix}vpeiandsuch.csv.zip", "small.csv")
        make_s3_zip_file(mock_s3_bucket, f"{prefix}secretrecipe.csv.zip", "small.csv")

    data_by_date = exporter.group_s3_files_by_date()
    assert set(data_by_date.keys()) == set(
        ["2020-01-01-11-30-00", "2020-01-02-11-30-00", "2020-01-03-11-30-00"]
    )
    for date_item, paths in data_by_date.items():
        expected_path_to_file = f"s3://{mock_s3_bucket}/{shared_prefix}{date_item}-"
        assert set(paths) == set(
            [
                f"{expected_path_to_file}vpei.csv.zip",
                f"{expected_path_to_file}vpeiclaimdetails.csv.zip",
                f"{expected_path_to_file}vpeipaymentdetails.csv.zip",
            ]
        )


@freeze_time("2021-01-03 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_data(
    mock_s3_bucket, set_exporter_env_vars, test_db_session, tmp_path, initialize_factories_session
):
    setup_process_tests(mock_s3_bucket, test_db_session)

    validation_errors = exporter.process_extract_data(tmp_path, test_db_session)
    assert len(validation_errors) == 0

    # First verify the files were downloaded
    downloaded_files = file_util.list_files(str(tmp_path))
    assert len(downloaded_files) == 3
    assert set(downloaded_files) == set(
        ["2020-01-01-11-30-00-" + file_name for file_name in exporter.expected_file_names]
    )

    # Make sure files were copied to the processed directory
    moved_files = file_util.list_files(
        f"s3://{mock_s3_bucket}/cps/inbound/processed/2020-01-01-11-30-00/"
    )
    assert len(moved_files) == 3

    # Grab all files in the bucket, verify there are no more
    all_files = file_util.list_files(f"s3://{mock_s3_bucket}/", recursive=True)
    assert len(all_files) == 3

    # For simplicity of testing so much, the datasets we're reading from use numbers
    # to signify what record they're from (eg. city of of City1)
    # These also correspond to row1/2/3 in the files used
    for index in ["1", "2", "3"]:
        payment = (
            test_db_session.query(Payment)
            .filter(
                Payment.fineos_pei_c_value == "7326", Payment.fineos_pei_i_value == f"30{index}"
            )
            .first()
        )

        # Validate all of the payment fields that were set
        assert payment.period_start_date.strftime("%Y-%m-%d") == f"2021-01-0{index}"
        assert payment.period_end_date.strftime("%Y-%m-%d") == f"2021-01-1{index}"
        assert payment.payment_date.strftime("%Y-%m-%d") == f"2021-01-0{index}"
        assert payment.fineos_extraction_date == date(2021, 1, 3)
        assert str(payment.amount) == f"{index * 3}.99"  # eg. 111.99

        claim = payment.claim
        assert claim

        employee = claim.employee
        assert employee

        mailing_address = employee.mailing_address
        assert mailing_address
        assert mailing_address.address_line_one == f"AddressLine1-{index}"
        assert mailing_address.city == f"City{index}"
        assert mailing_address.geo_state_id == GeoState.MA.geo_state_id
        assert mailing_address.zip_code == index * 5  # eg. 11111
        assert mailing_address.address_type_id == AddressType.MAILING.address_type_id

        employee_addresses = employee.addresses.all()
        assert len(employee_addresses) == 1  # Just the 1 already present
        assert employee_addresses[0].employee_id == employee.employee_id
        assert employee_addresses[0].address_id == mailing_address.address_id

        reference_files = payment.reference_files
        assert len(reference_files) == 1
        reference_file = reference_files[0].reference_file
        assert (
            reference_file.file_location
            == "s3://test_bucket/cps/inbound/processed/2020-01-01-11-30-00"
        )
        assert (
            reference_file.reference_file_type_id
            == ReferenceFileType.PAYMENT_EXTRACT.reference_file_type_id
        )

        eft = employee.eft

        # Payment 2 uses CHECK over ACH, so some logic differs for it.
        # The 2nd record is also family leave, the other two are medical leave
        if index == "2":
            assert payment.payment_method_id == PaymentMethod.CHECK.payment_method_id
            assert not mailing_address.address_line_two

        else:
            assert payment.payment_method_id == PaymentMethod.ACH.payment_method_id
            assert mailing_address.address_line_two == f"AddressLine2-{index}"
            assert str(eft.routing_nbr) == index * 9
            assert str(eft.account_nbr) == index * 9
            assert eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id


def test_process_extract_unprocessed_folder_files(
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    test_db_session,
    tmp_path,
    initialize_factories_session,
):
    def get_download_directory(directory_name):
        directory = tmp_path / directory_name
        directory.mkdir()
        return directory

    def add_s3_files(s3_prefix):
        make_s3_zip_file(mock_fineos_s3_bucket, f"{s3_prefix}vpei.csv.zip", "vpei.csv")
        make_s3_zip_file(
            mock_fineos_s3_bucket,
            f"{s3_prefix}vpeipaymentdetails.csv.zip",
            "vpei_payment_details.csv",
        )
        make_s3_zip_file(
            mock_fineos_s3_bucket, f"{s3_prefix}vpeiclaimdetails.csv.zip", "vpei_claim_details.csv"
        )

    # add files
    add_s3_files("DT2/dataexports/2020-01-01-11-30-00/2020-01-01-11-30-00-")
    add_s3_files("DT2/dataexports/2020-01-02-11-30-00/2020-01-02-11-30-00-")
    add_s3_files("DT2/dataexports/2020-01-03-11-30-00/2020-01-03-11-30-00-")
    add_s3_files("DT2/dataexports/2020-01-04-11-30-00-")

    # add reference files for processed folders
    ReferenceFileFactory.create(
        file_location=os.path.join(
            get_s3_config().pfml_fineos_inbound_path, "processed", "2020-01-01-11-30-00"
        ),
        reference_file_type_id=ReferenceFileType.PAYMENT_EXTRACT.reference_file_type_id,
    )
    ReferenceFileFactory.create(
        file_location=os.path.join(
            get_s3_config().pfml_fineos_inbound_path, "processed", "2020-01-03-11-30-00"
        ),
        reference_file_type_id=ReferenceFileType.PAYMENT_EXTRACT.reference_file_type_id,
    )

    # confirm all unprocessed files were downloaded
    download_directory_1 = get_download_directory("directory_1")
    exporter.process_extract_data(download_directory_1, test_db_session)
    downloaded_files = file_util.list_files(str(download_directory_1))
    assert len(downloaded_files) == 6

    expected_file_names = []
    for date_file in ["vpei.csv.zip", "vpeipaymentdetails.csv.zip", "vpeiclaimdetails.csv.zip"]:
        for unprocessed_date in ["2020-01-02-11-30-00", "2020-01-04-11-30-00"]:
            expected_file_names.append(f"{unprocessed_date}-{date_file}")

    for downloaded_file in downloaded_files:
        assert downloaded_file in expected_file_names

    # confirm no files were downloaded on repeat run
    download_directory_2 = get_download_directory("directory_2")
    exporter.process_extract_data(download_directory_2, test_db_session)
    downloaded_files = file_util.list_files(str(download_directory_2))
    assert len(downloaded_files) == 0


def test_process_extract_data_no_existing_claim_address_eft(
    mock_s3_bucket, set_exporter_env_vars, test_db_session, tmp_path, initialize_factories_session
):
    setup_process_tests(
        mock_s3_bucket, test_db_session, add_claim=False, add_address=False, add_eft=False
    )

    validation_errors = exporter.process_extract_data(tmp_path, test_db_session)
    assert len(validation_errors) == 0

    for index in ["1", "2", "3"]:
        payment = (
            test_db_session.query(Payment)
            .filter(
                Payment.fineos_pei_c_value == "7326", Payment.fineos_pei_i_value == f"30{index}"
            )
            .first()
        )

        # Check the claim was created properly
        claim = payment.claim
        assert claim
        assert claim.fineos_absence_id == f"NTN-0{index}-ABS-0{index}"

        employee = claim.employee
        assert employee

        mailing_address = employee.mailing_address
        assert mailing_address
        assert mailing_address.address_line_one == f"AddressLine1-{index}"
        assert mailing_address.city == f"City{index}"
        assert mailing_address.geo_state_id == GeoState.MA.geo_state_id
        assert mailing_address.zip_code == index * 5  # eg. 11111
        assert mailing_address.address_type_id == AddressType.MAILING.address_type_id

        employee_addresses = employee.addresses.all()
        assert len(employee_addresses) == 1  # Just the 1 we added
        assert employee_addresses[0].employee_id == employee.employee_id
        assert employee_addresses[0].address_id == mailing_address.address_id

        eft = employee.eft

        # Payment 2 uses CHECK over ACH, so some logic differs for it.
        if index == "2":
            assert payment.payment_method_id == PaymentMethod.CHECK.payment_method_id
            assert not mailing_address.address_line_two

            assert not eft  # Not set by factory logic, shouldn't be set at all now

        else:
            assert payment.payment_method_id == PaymentMethod.ACH.payment_method_id
            assert mailing_address.address_line_two == f"AddressLine2-{index}"
            assert str(eft.routing_nbr) == index * 9
            assert str(eft.account_nbr) == index * 9
            assert eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id


@freeze_time("2021-01-03 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_data_existing_payment(
    mock_s3_bucket, set_exporter_env_vars, test_db_session, tmp_path, initialize_factories_session
):
    setup_process_tests(mock_s3_bucket, test_db_session, add_payment=True)

    validation_errors = exporter.process_extract_data(tmp_path, test_db_session)
    assert len(validation_errors) == 0

    for index in ["1", "2", "3"]:
        payment = (
            test_db_session.query(Payment)
            .filter(
                Payment.fineos_pei_c_value == "7326", Payment.fineos_pei_i_value == f"30{index}"
            )
            .first()
        )

        # Validate all of the payment fields that were updated
        # None of these are defaulted to similar values by our factory logic
        assert payment.period_start_date.strftime("%Y-%m-%d") == f"2021-01-0{index}"
        assert payment.period_end_date.strftime("%Y-%m-%d") == f"2021-01-1{index}"
        assert payment.payment_date.strftime("%Y-%m-%d") == f"2021-01-0{index}"
        assert payment.fineos_extraction_date == date(2021, 1, 3)
        assert str(payment.amount) == f"{index * 3}.99"  # eg. 111.99


def test_validation_of_joining_datasets(set_exporter_env_vars):
    # This test is targeted specifically at verifying the join logic of PaymentData

    # Extract data expects S3 paths that it uses to later download files and parse them
    # We don't want to deal with files in this test, so we'll make the indexed values ourselves
    extract_data = exporter.ExtractData(exporter.expected_file_names, "2020-01-01")
    extract_data.pei.indexed_data = {}
    extract_data.payment_details.indexed_data = {}
    extract_data.claim_details.indexed_data = {}

    ci_index = exporter.CiIndex("1", "1")
    payment_data = exporter.PaymentData(extract_data, ci_index, {})

    # Make sure the validation container has the expected index
    # and all of the non-PEI datasets
    validation_container = payment_data.validation_container
    assert validation_container.record_key == str(ci_index)
    assert set(validation_container.validation_issues) == set(
        [
            ValidationIssue(ValidationReason.MISSING_DATASET, "payment_details"),
            ValidationIssue(ValidationReason.MISSING_DATASET, "claim_details"),
        ]
    )


def test_validation_missing_fields(set_exporter_env_vars):
    # This test is specifically aimed at verifying we check for required parameters

    # We set it up so the datasets can be joined on ci_index, but don't set any
    # values that aren't specifically used for joining, so all required params
    # should subsequently be in the validation object
    # Note the isdata fields are just to avoid the dictionaries being empty
    ci_index = exporter.CiIndex("1", "1")
    extract_data = exporter.ExtractData(exporter.expected_file_names, "2020-01-01-11-30-00")
    extract_data.pei.indexed_data = {ci_index: {"PAYEECUSTOMER": "1234"}}
    extract_data.payment_details.indexed_data = {ci_index: {"isdata": "1"}}
    extract_data.claim_details.indexed_data = {ci_index: {"isdata": "1"}}

    payment_data = exporter.PaymentData(
        extract_data, ci_index, extract_data.pei.indexed_data.get(ci_index)
    )
    validation_container = payment_data.validation_container
    assert validation_container.record_key == str(ci_index)
    expected_missing_values = set(
        [
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEESOCNUMBE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCECASENU"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTMETHOD"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTADD1"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTADD4"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTADD6"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTPOSTCO"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTSTARTP"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTENDPER"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTDATE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "AMOUNT_MONAMT"),
        ]
    )
    assert set(validation_container.validation_issues) == expected_missing_values

    # We want to make sure missing, "" and Unknown are all treated the same
    # So update a few values, and expect the same result
    extract_data.pei.indexed_data[ci_index]["PAYEESOCNUMBE"] = ""
    extract_data.pei.indexed_data[ci_index]["PAYMENTADD1"] = ""
    extract_data.pei.indexed_data[ci_index]["PAYMENTADD4"] = "Unknown"
    extract_data.pei.indexed_data[ci_index]["PAYMENTPOSTCO"] = "Unknown"

    payment_data = exporter.PaymentData(
        extract_data, ci_index, extract_data.pei.indexed_data.get(ci_index)
    )
    assert set(payment_data.validation_container.validation_issues) == expected_missing_values

    # Some fields are conditional for EFT, make sure they're also checked
    extract_data.pei.indexed_data[ci_index][
        "PAYMENTMETHOD"
    ] = PaymentMethod.ACH.payment_method_description
    expected_missing_values.remove(
        ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTMETHOD")
    )  # No longer missing now
    expected_missing_values.update(
        [
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEEBANKCODE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEEACCOUNTN"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEEACCOUNTT"),
        ]
    )

    payment_data = exporter.PaymentData(
        extract_data, ci_index, extract_data.pei.indexed_data.get(ci_index)
    )
    assert set(payment_data.validation_container.validation_issues) == expected_missing_values


def test_validation_param_length(set_exporter_env_vars):
    # We set it up so the datasets can be joined on ci_index, but don't set any
    # values that aren't specifically used for joining, We are only setting values
    # we are explicitly testing against here, the validation will have missing
    # errors as well, but we're not going to look at them.
    ci_index = exporter.CiIndex("1", "1")
    extract_data = exporter.ExtractData(exporter.expected_file_names, "2020-01-01-11-30-00")
    # First let's check if a field is too short
    extract_data.pei.indexed_data = {ci_index: {"PAYEEBANKCODE": "123", "PAYMENTPOSTCO": "123"}}
    extract_data.payment_details.indexed_data = {ci_index: {"isdata": "1"}}
    extract_data.claim_details.indexed_data = {ci_index: {"isdata": "1"}}

    payment_data = exporter.PaymentData(
        extract_data, ci_index, extract_data.pei.indexed_data.get(ci_index)
    )

    assert set(
        [
            ValidationIssue(ValidationReason.FIELD_TOO_SHORT, "PAYEEBANKCODE"),
            ValidationIssue(ValidationReason.FIELD_TOO_SHORT, "PAYMENTPOSTCO"),
        ]
    ).issubset(set(payment_data.validation_container.validation_issues))

    # Now let's check if a field is too long
    extract_data.pei.indexed_data[ci_index]["PAYMENTPOSTCO"] = "012345-67890"
    extract_data.pei.indexed_data[ci_index]["PAYEEBANKCODE"] = "012345678910"
    extract_data.pei.indexed_data[ci_index]["PAYEEACCOUNTN"] = "0" * 50

    payment_data = exporter.PaymentData(
        extract_data, ci_index, extract_data.pei.indexed_data.get(ci_index)
    )

    assert set(
        [
            ValidationIssue(ValidationReason.FIELD_TOO_LONG, "PAYEEACCOUNTN"),
            ValidationIssue(ValidationReason.FIELD_TOO_LONG, "PAYEEBANKCODE"),
            ValidationIssue(ValidationReason.FIELD_TOO_LONG, "PAYMENTPOSTCO"),
        ]
    ).issubset(set(payment_data.validation_container.validation_issues))


def test_validation_lookup_validators(set_exporter_env_vars):
    # When doing the validation, we verify that the lookup values are
    # valid and will be convertable to their corresponding lookup values in the DB.
    ci_index = exporter.CiIndex("1", "1")
    extract_data = exporter.ExtractData(exporter.expected_file_names, "2020-01-01-11-30-00")
    extract_data.pei.indexed_data = {
        ci_index: {
            "PAYEECUSTOMER": "1234",
            "PAYEEACCOUNTT": "BadData",
            "PAYMENTMETHOD": "BadData",
            "PAYMENTADD6": "BadData",
        }
    }
    extract_data.payment_details.indexed_data = {ci_index: {"isdata": "1"}}
    extract_data.claim_details.indexed_data = {ci_index: {"isdata": "1"}}

    payment_data = exporter.PaymentData(
        extract_data, ci_index, extract_data.pei.indexed_data.get(ci_index)
    )

    assert set(
        [
            ValidationIssue(ValidationReason.INVALID_LOOKUP_VALUE, "PAYEEACCOUNTT"),
            ValidationIssue(ValidationReason.INVALID_LOOKUP_VALUE, "PAYMENTMETHOD"),
            ValidationIssue(ValidationReason.INVALID_LOOKUP_VALUE, "PAYMENTADD6"),
        ]
    ).issubset(set(payment_data.validation_container.validation_issues))
