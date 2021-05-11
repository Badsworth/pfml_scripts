import os
from datetime import date

import boto3
import pytest
from freezegun import freeze_time

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.fineos_payment_export as exporter
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    AddressType,
    BankAccountType,
    Employee,
    EmployeeAddress,
    EmployeeLog,
    GeoState,
    Payment,
    PaymentMethod,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
    TaxIdentifier,
)
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ClaimFactory,
    CtrAddressPairFactory,
    EftFactory,
    EmployeeFactory,
    EmployerFactory,
    PaymentFactory,
    ReferenceFileFactory,
)
from massgov.pfml.payments.config import get_s3_config
from massgov.pfml.payments.payments_util import ValidationIssue, ValidationReason

# every test in here requires real resources
pytestmark = pytest.mark.integration

EXPECTED_OUTCOME = {"message": "Success"}

### UTILITY METHODS


def make_s3_file(s3_bucket, key, test_file_name):
    # Utility method to upload a test file to the mocked S3.
    # test_file_name corresponds to the name of the file in the test_files directory
    test_file_path = os.path.join(os.path.dirname(__file__), f"test_files/{test_file_name}")

    s3 = boto3.client("s3")
    s3.upload_file(test_file_path, s3_bucket, key)


def add_db_records(
    db_session,
    tin,
    absence_case_id,
    add_claim=True,
    add_address=True,
    add_eft=True,
    add_payment=False,
    add_employee=True,
    c_value=None,
    i_value=None,
):
    eft = None
    if add_eft:
        eft = EftFactory()

    mailing_address = None
    ctr_address_pair = None
    if add_address:
        mailing_address = AddressFactory()
        ctr_address_pair = CtrAddressPairFactory(fineos_address=mailing_address)

    if add_employee:
        employee = EmployeeFactory.create(
            tax_identifier=TaxIdentifier(tax_identifier=tin),
            ctr_address_pair=ctr_address_pair,
            eft=eft,
        )
        if add_eft:
            employee.payment_method_id = PaymentMethod.ACH.payment_method_id

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
            PaymentFactory.create(
                claim=claim, fineos_pei_c_value=c_value, fineos_pei_i_value=i_value
            )


def setup_process_tests(
    mock_s3_bucket,
    test_db_session,
    add_claim=True,
    add_address=True,
    add_eft=True,
    add_payment=False,
    add_second_employee=True,  # False = this'll cause the second record to fail
):
    """ This is a utility method for setting up a lot of boiler plate in the
        process_extract_data tests
    """
    s3_prefix = "cps/inbound/received/2020-01-01-11-30-00-"
    # Add the 3 expected files
    make_s3_file(mock_s3_bucket, f"{s3_prefix}vpei.csv", "vpei.csv")
    make_s3_file(
        mock_s3_bucket, f"{s3_prefix}vpeipaymentdetails.csv", "vpeipaymentdetails.csv",
    )
    make_s3_file(mock_s3_bucket, f"{s3_prefix}vpeiclaimdetails.csv", "vpeiclaimdetails.csv")

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
        add_employee=add_second_employee,
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


def get_download_directory(tmp_path, directory_name):
    directory = tmp_path / directory_name
    directory.mkdir()
    return directory


def add_s3_files(mock_fineos_s3_bucket, s3_prefix):
    make_s3_file(mock_fineos_s3_bucket, f"{s3_prefix}vpei.csv", "vpei.csv")
    make_s3_file(
        mock_fineos_s3_bucket, f"{s3_prefix}vpeipaymentdetails.csv", "vpeipaymentdetails.csv",
    )
    make_s3_file(mock_fineos_s3_bucket, f"{s3_prefix}vpeiclaimdetails.csv", "vpeiclaimdetails.csv")


### TESTS BEGIN


def test_download_and_parse_data(mock_s3_bucket, tmp_path):
    make_s3_file(mock_s3_bucket, "path/to/file/test.csv", "small.csv")

    raw_data = exporter.download_and_parse_data(
        f"s3://{mock_s3_bucket}/path/to/file/test.csv", tmp_path
    )

    # First verify the file was downloaded and named right
    downloaded_files = file_util.list_files(str(tmp_path))
    assert set(downloaded_files) == set(["test.csv"])

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


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_data(
    mock_s3_bucket,
    set_exporter_env_vars,
    test_db_session,
    tmp_path,
    initialize_factories_session,
    monkeypatch,
    create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_MAX_HISTORY_DATE", "2019-12-31")
    setup_process_tests(mock_s3_bucket, test_db_session)

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 9

    exporter.process_extract_data(tmp_path, test_db_session)

    # First verify the files were downloaded
    downloaded_files = file_util.list_files(str(tmp_path))
    assert len(downloaded_files) == 3
    assert set(downloaded_files) == set(
        ["2020-01-01-11-30-00-" + file_name for file_name in exporter.expected_file_names]
    )

    # Make sure files were copied to the processed directory
    moved_files = file_util.list_files(
        f"s3://{mock_s3_bucket}/cps/inbound/processed/{payments_util.get_date_group_folder_name('2020-01-01-11-30-00', ReferenceFileType.PAYMENT_EXTRACT)}/"
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
        assert payment.fineos_extraction_date == date(2021, 1, 13)
        assert str(payment.amount) == f"{index * 3}.99"  # eg. 111.99
        assert payment.has_address_update is True

        claim = payment.claim
        assert claim

        employee = claim.employee
        assert employee

        mailing_address = employee.ctr_address_pair.fineos_address
        assert mailing_address
        assert mailing_address.address_line_one == f"AddressLine1-{index}"
        assert mailing_address.city == f"City{index}"
        assert mailing_address.geo_state_id == GeoState.MA.geo_state_id
        assert mailing_address.zip_code == index * 5  # eg. 11111
        assert mailing_address.address_type_id == AddressType.MAILING.address_type_id

        employee_addresses = employee.addresses.all()
        assert (
            len(employee_addresses) == 2
        )  # 1 created in setup_process_tests, 1 created during process_extract_data
        assert employee_addresses[1].employee_id == employee.employee_id
        assert employee_addresses[1].address_id == mailing_address.address_id

        reference_files = payment.reference_files
        assert len(reference_files) == 1
        reference_file = reference_files[0].reference_file
        assert (
            reference_file.file_location
            == "s3://test_bucket/cps/inbound/processed/2020-01-01-11-30-00-payment-export"
        )
        assert (
            reference_file.reference_file_type_id
            == ReferenceFileType.PAYMENT_EXTRACT.reference_file_type_id
        )
        # Verify that there is exactly one successful state log per payment
        state_logs = payment.state_logs
        assert len(state_logs) == 1
        state_log = state_logs[0]
        assert state_log.outcome == EXPECTED_OUTCOME
        assert state_log.end_state_id == State.MARK_AS_EXTRACTED_IN_FINEOS.state_id

        eft = employee.eft

        # Payment 2 uses CHECK over ACH, so some logic differs for it.
        # The 2nd record is also family leave, the other two are medical leave
        if index == "2":
            assert employee.payment_method_id == PaymentMethod.CHECK.payment_method_id
            assert not mailing_address.address_line_two
            assert payment.has_eft_update is False

        else:
            assert employee.payment_method_id == PaymentMethod.ACH.payment_method_id
            assert mailing_address.address_line_two == f"AddressLine2-{index}"
            assert str(eft.routing_nbr) == index * 9
            assert str(eft.account_nbr) == index * 9
            assert eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
            assert payment.has_eft_update is True

            # Verify that there is exactly one successful state log per employee that uses ACH
            state_logs = employee.state_logs
            assert len(state_logs) == 1
            state_log = state_logs[0]
            assert "Initiated VENDOR_EFT flow for Employee" in state_log.outcome["message"]
            assert state_log.end_state_id == State.EFT_REQUEST_RECEIVED.state_id

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


def test_process_extract_data_one_bad_record(
    mock_s3_bucket,
    set_exporter_env_vars,
    test_db_session,
    tmp_path,
    initialize_factories_session,
    monkeypatch,
    create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_MAX_HISTORY_DATE", "2019-12-31")
    # This test will properly process record 1 & 3, but record 2 will
    # end up in an error state because we don't have an TIN/employee associated with them
    setup_process_tests(
        mock_s3_bucket,
        test_db_session,
        add_claim=False,
        add_address=False,
        add_eft=False,
        add_second_employee=False,
    )

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 2

    exporter.process_extract_data(tmp_path, test_db_session)

    # The second record will have failed and so no payment would have been created
    for index in ["1", "2", "3"]:
        payment = (
            test_db_session.query(Payment)
            .filter(
                Payment.fineos_pei_c_value == "7326", Payment.fineos_pei_i_value == f"30{index}"
            )
            .one_or_none()
        )
        if index == "2":
            assert payment is None
        else:
            assert payment

    # Get all the state logs from the DB that have a payment attached
    successful_state_logs = (
        test_db_session.query(StateLog).filter(StateLog.payment_id != None).all()  # noqa
    )
    assert len(successful_state_logs) == 2
    for state_log in successful_state_logs:
        assert state_log.outcome == EXPECTED_OUTCOME

    # Get the errored state log by querying for all state logs without a payment set
    # as it will have failed before getting to the payment logic
    unsuccessful_state_logs = (
        test_db_session.query(StateLog)
        .filter(StateLog.payment_id == None, StateLog.employee_id == None)  # noqa
        .all()
    )
    assert len(unsuccessful_state_logs) == 1
    assert unsuccessful_state_logs[0].outcome == {
        "message": "Error processing payment record",
        "validation_container": {
            "record_key": "CiIndex(c='7326', i='302')",
            "validation_issues": [{"reason": "MissingInDB", "details": "tax_identifier"}],
        },
    }

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


def test_process_extract_data_one_previously_in_gax(
    mock_s3_bucket,
    set_exporter_env_vars,
    test_db_session,
    tmp_path,
    initialize_factories_session,
    monkeypatch,
    create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_MAX_HISTORY_DATE", "2019-12-31")
    setup_process_tests(mock_s3_bucket, test_db_session, add_payment=True)

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 9

    # Grab the a payment and give it a previous state log entry
    # that indicates it has been in a GAX before
    payment = (
        test_db_session.query(Payment)
        .filter(Payment.fineos_pei_c_value == "7326", Payment.fineos_pei_i_value == "301")
        .one_or_none()
    )

    state_log_util.create_finished_state_log(
        end_state=State.GAX_SENT,
        outcome=state_log_util.build_outcome("GAX sent"),
        associated_model=payment,
        db_session=test_db_session,
    )

    exporter.process_extract_data(tmp_path, test_db_session)

    # It should have two state logs, the one we added
    # and one in ADD_TO_PAYMENT_EXPORT_ERROR_REPORT
    test_db_session.refresh(payment)
    assert len(payment.state_logs) == 2
    states = [state_log.end_state.state_id for state_log in payment.state_logs]
    assert set([State.GAX_SENT.state_id, State.ADD_TO_PAYMENT_EXPORT_ERROR_REPORT.state_id]) == set(
        states
    )

    # The other two payments should only have a single happy state
    payments = test_db_session.query(Payment).filter(Payment.payment_id != payment.payment_id).all()
    for payment in payments:
        assert len(payment.state_logs) == 1
        assert payment.state_logs[0].end_state_id == State.MARK_AS_EXTRACTED_IN_FINEOS.state_id


def test_process_extract_data_rollback(
    mock_s3_bucket,
    set_exporter_env_vars,
    test_db_session,
    tmp_path,
    initialize_factories_session,
    monkeypatch,
    create_triggers,
):
    test_db_session.begin_nested()
    setup_process_tests(mock_s3_bucket, test_db_session)

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 9

    # Override the method that moves files at the end to throw
    # an error so that everything will rollback
    def err_method(*args):
        raise Exception("Fake Error")

    monkeypatch.setenv("FINEOS_PAYMENT_MAX_HISTORY_DATE", "2019-12-31")
    monkeypatch.setattr(exporter, "move_files_from_received_to_processed", err_method)

    with pytest.raises(Exception, match="Fake Error"):
        test_db_session.begin_nested()
        exporter.process_extract_data(tmp_path, test_db_session)
        # Make certain that there are no payments or state logs in the DB
        payments = test_db_session.query(Payment).all()
        assert len(payments) == 0
        state_logs = test_db_session.query(StateLog).all()
        assert len(state_logs) == 0

        # The files should have been moved to the error folder
        files = file_util.list_files(f"s3://{mock_s3_bucket}/cps/inbound/error/")
        assert len(files) == 3

        # The reference file should have been created
        reference_files = test_db_session.query(ReferenceFile).all()
        assert len(reference_files) == 1
        assert reference_files[0].file_location == f"s3://{mock_s3_bucket}/cps/inbound/error/"
        assert (
            reference_files[0].reference_file_type_id
            == ReferenceFileType.PAYMENT_EXTRACT.reference_file_type_id
        )

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


def test_process_extract_unprocessed_folder_files(
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    test_db_session,
    tmp_path,
    initialize_factories_session,
    monkeypatch,
    create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_MAX_HISTORY_DATE", "2019-12-31")

    # add files
    add_s3_files(mock_fineos_s3_bucket, "DT2/dataexports/2020-01-01-11-30-00/2020-01-01-11-30-00-")
    add_s3_files(mock_fineos_s3_bucket, "DT2/dataexports/2020-01-02-11-30-00/2020-01-02-11-30-00-")
    add_s3_files(mock_fineos_s3_bucket, "DT2/dataexports/2020-01-03-11-30-00/2020-01-03-11-30-00-")
    add_s3_files(mock_fineos_s3_bucket, "DT2/dataexports/2020-01-04-11-30-00-")

    # add reference files for processed folders
    ReferenceFileFactory.create(
        file_location=os.path.join(
            get_s3_config().pfml_fineos_inbound_path,
            "processed",
            payments_util.get_date_group_folder_name(
                "2020-01-01-11-30-00", ReferenceFileType.PAYMENT_EXTRACT
            ),
        ),
        reference_file_type_id=ReferenceFileType.PAYMENT_EXTRACT.reference_file_type_id,
    )
    ReferenceFileFactory.create(
        file_location=os.path.join(
            get_s3_config().pfml_fineos_inbound_path,
            "processed",
            payments_util.get_date_group_folder_name(
                "2020-01-03-11-30-00", ReferenceFileType.PAYMENT_EXTRACT
            ),
        ),
        reference_file_type_id=ReferenceFileType.PAYMENT_EXTRACT.reference_file_type_id,
    )

    # confirm all unprocessed files were downloaded
    download_directory_1 = get_download_directory(tmp_path, "directory_1")
    exporter.process_extract_data(download_directory_1, test_db_session)
    destination_folder = os.path.join(
        get_s3_config().pfml_fineos_inbound_path, payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
    )
    processed_files = file_util.list_files(destination_folder, recursive=True)
    assert len(processed_files) == 6

    expected_file_names = []
    for date_file in ["vpei.csv", "vpeipaymentdetails.csv", "vpeiclaimdetails.csv"]:
        for unprocessed_date in ["2020-01-02-11-30-00", "2020-01-04-11-30-00"]:
            expected_file_names.append(
                f"{payments_util.get_date_group_folder_name(unprocessed_date, ReferenceFileType.PAYMENT_EXTRACT)}/{unprocessed_date}-{date_file}"
            )

    for processed_file in processed_files:
        assert processed_file in expected_file_names

    # confirm no files will be copied in a subsequent copy
    copied_files = payments_util.copy_fineos_data_to_archival_bucket(
        test_db_session, exporter.expected_file_names, ReferenceFileType.PAYMENT_EXTRACT
    )
    assert not copied_files

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == 0


def test_process_extract_data_no_existing_claim_address_eft(
    mock_s3_bucket,
    set_exporter_env_vars,
    test_db_session,
    tmp_path,
    initialize_factories_session,
    monkeypatch,
    create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_MAX_HISTORY_DATE", "2019-12-31")
    setup_process_tests(
        mock_s3_bucket, test_db_session, add_claim=False, add_address=False, add_eft=False
    )

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 3

    exporter.process_extract_data(tmp_path, test_db_session)

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

        mailing_address = employee.ctr_address_pair.fineos_address
        assert mailing_address
        assert mailing_address.address_line_one == f"AddressLine1-{index}"
        assert mailing_address.city == f"City{index}"
        assert mailing_address.geo_state_id == GeoState.MA.geo_state_id
        assert mailing_address.zip_code == index * 5  # eg. 11111
        assert mailing_address.address_type_id == AddressType.MAILING.address_type_id
        assert payment.has_address_update is True

        employee_addresses = employee.addresses.all()
        assert len(employee_addresses) == 1  # Just the 1 we added
        assert employee_addresses[0].employee_id == employee.employee_id
        assert employee_addresses[0].address_id == mailing_address.address_id

        # Verify that there is exactly one successful state log per payment
        state_logs = payment.state_logs
        assert len(state_logs) == 1
        state_log = state_logs[0]
        assert state_log.outcome == EXPECTED_OUTCOME
        assert state_log.end_state_id == State.MARK_AS_EXTRACTED_IN_FINEOS.state_id

        eft = employee.eft

        # Payment 2 uses CHECK over ACH, so some logic differs for it.
        if index == "2":
            assert employee.payment_method_id == PaymentMethod.CHECK.payment_method_id
            assert not mailing_address.address_line_two

            assert not eft  # Not set by factory logic, shouldn't be set at all now
            assert payment.has_eft_update is False

        else:
            assert employee.payment_method_id == PaymentMethod.ACH.payment_method_id
            assert mailing_address.address_line_two == f"AddressLine2-{index}"
            assert str(eft.routing_nbr) == index * 9
            assert str(eft.account_nbr) == index * 9
            assert eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
            assert payment.has_eft_update is True

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_data_existing_payment(
    mock_s3_bucket,
    set_exporter_env_vars,
    test_db_session,
    tmp_path,
    initialize_factories_session,
    monkeypatch,
    create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_MAX_HISTORY_DATE", "2019-12-31")
    setup_process_tests(mock_s3_bucket, test_db_session, add_payment=True)

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 9

    exporter.process_extract_data(tmp_path, test_db_session)

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
        assert payment.fineos_extraction_date == date(2021, 1, 13)
        assert str(payment.amount) == f"{index * 3}.99"  # eg. 111.99

        # Verify that there is exactly one successful state log per payment
        state_logs = payment.state_logs
        assert len(state_logs) == 1
        state_log = state_logs[0]
        assert state_log.outcome == EXPECTED_OUTCOME
        assert state_log.end_state_id == State.MARK_AS_EXTRACTED_IN_FINEOS.state_id

    payment_count_after = test_db_session.query(Payment).count()
    assert payment_count_after == 3

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


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
    assert (
        ValidationIssue(ValidationReason.MISSING_DATASET, "payment_details")
        in validation_container.validation_issues
    )
    assert (
        ValidationIssue(ValidationReason.MISSING_DATASET, "claim_details")
        in validation_container.validation_issues
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
    extract_data.payment_details.indexed_data = {ci_index: [{"isdata": "1"}]}
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
            ValidationIssue(ValidationReason.MISSING_FIELD, "EVENTTYPE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "LEAVEREQUESTI"),
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
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEEBANKSORT"),
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
    extract_data.pei.indexed_data = {ci_index: {"PAYEEBANKSORT": "123", "PAYMENTPOSTCO": "123"}}
    extract_data.payment_details.indexed_data = {ci_index: [{"isdata": "1"}]}
    extract_data.claim_details.indexed_data = {ci_index: {"isdata": "1"}}

    payment_data = exporter.PaymentData(
        extract_data, ci_index, extract_data.pei.indexed_data.get(ci_index)
    )

    assert set(
        [
            ValidationIssue(ValidationReason.FIELD_TOO_SHORT, "PAYEEBANKSORT"),
            ValidationIssue(ValidationReason.FIELD_TOO_SHORT, "PAYMENTPOSTCO"),
        ]
    ).issubset(set(payment_data.validation_container.validation_issues))

    # Now let's check if a field is too long
    extract_data.pei.indexed_data[ci_index]["PAYMENTPOSTCO"] = "012345-67890"
    extract_data.pei.indexed_data[ci_index]["PAYEEBANKSORT"] = "012345678910"
    extract_data.pei.indexed_data[ci_index]["PAYEEACCOUNTN"] = "0" * 50

    payment_data = exporter.PaymentData(
        extract_data, ci_index, extract_data.pei.indexed_data.get(ci_index)
    )

    assert set(
        [
            ValidationIssue(ValidationReason.FIELD_TOO_LONG, "PAYEEACCOUNTN"),
            ValidationIssue(ValidationReason.FIELD_TOO_LONG, "PAYEEBANKSORT"),
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
    extract_data.payment_details.indexed_data = {ci_index: [{"isdata": "1"}]}
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


def test_validation_payment_amount(set_exporter_env_vars):
    # When doing validation, we verify that payment amounts
    # are greater than 0

    ci_index = exporter.CiIndex("1", "1")
    extract_data = exporter.ExtractData(exporter.expected_file_names, "2020-01-01-11-30-00")
    extract_data.pei.indexed_data = {ci_index: {"AMOUNT_MONAMT": "0.00"}}
    extract_data.payment_details.indexed_data = {ci_index: [{"isdata": "1"}]}
    extract_data.claim_details.indexed_data = {ci_index: {"isdata": "1"}}

    payment_data = exporter.PaymentData(
        extract_data, ci_index, extract_data.pei.indexed_data.get(ci_index)
    )

    assert set([ValidationIssue(ValidationReason.INVALID_VALUE, "AMOUNT_MONAMT")]).issubset(
        set(payment_data.validation_container.validation_issues)
    )

    # Verify negatives are caught as well
    extract_data.pei.indexed_data[ci_index]["AMOUNT_MONAMT"] = "-0.01"
    payment_data = exporter.PaymentData(
        extract_data, ci_index, extract_data.pei.indexed_data.get(ci_index)
    )
    assert set([ValidationIssue(ValidationReason.INVALID_VALUE, "AMOUNT_MONAMT")]).issubset(
        set(payment_data.validation_container.validation_issues)
    )


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_update_eft_no_update(
    test_db_session,
    mock_s3_bucket,
    set_exporter_env_vars,
    monkeypatch,
    initialize_factories_session,
    tmp_path,
):
    # update_eft() has 3 possible outcomes:
    #   1. There is no change to EFT
    #   2. There is no existing EFT, so we add one
    #   3. There is an existing EFT, but it's different, so we update it
    # In this test, we cover #1. 2 & 3 are covered by other tests.

    monkeypatch.setenv("FINEOS_PAYMENT_MAX_HISTORY_DATE", "2019-12-31")
    setup_process_tests(mock_s3_bucket, test_db_session)

    # Set an employee to have the same EFT we know is going to be extracted
    employee = (
        test_db_session.query(Employee)
        .join(TaxIdentifier)
        .filter(TaxIdentifier.tax_identifier == "1" * 9)
        .first()
    )
    assert employee is not None
    assert employee.eft is not None
    employee.eft.routing_nbr = "1" * 9
    employee.eft.account_nbr = "1" * 9
    employee.eft.bank_account_type_id = BankAccountType.CHECKING.bank_account_type_id
    test_db_session.commit()

    # Run the process
    exporter.process_extract_data(tmp_path, test_db_session)
    test_db_session.expire_all()

    # Verify the payment isn't marked as having an EFT update
    payment = (
        test_db_session.query(Payment)
        .filter(Payment.fineos_pei_c_value == "7326", Payment.fineos_pei_i_value == "301")
        .first()
    )
    assert payment is not None
    assert payment.has_eft_update is False

    # There should not be a EFT_REQUEST_RECEIVED record
    employee_state_logs_after = (
        test_db_session.query(StateLog).filter(StateLog.employee_id == employee.employee_id).all()
    )
    assert len(employee_state_logs_after) == 0


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_update_ctr_address_pair_fineos_address_no_update(
    test_db_session,
    mock_s3_bucket,
    set_exporter_env_vars,
    monkeypatch,
    initialize_factories_session,
    tmp_path,
):
    # update_ctr_address_pair_fineos_address() has 2 possible outcomes:
    #   1. There is no change to address
    #   2. We create a new CtrAddressPair
    # In this test, we cover #1. #2 is covered by other tests.

    monkeypatch.setenv("FINEOS_PAYMENT_MAX_HISTORY_DATE", "2019-12-31")
    setup_process_tests(mock_s3_bucket, test_db_session)

    # Set an employee to have the same address we know is going to be extracted
    employee = (
        test_db_session.query(Employee)
        .join(TaxIdentifier)
        .filter(TaxIdentifier.tax_identifier == "1" * 9)
        .first()
    )
    assert employee is not None
    assert employee.ctr_address_pair is not None
    employee.ctr_address_pair.fineos_address.address_line_one = "AddressLine1-1"
    employee.ctr_address_pair.fineos_address.address_line_two = "AddressLine2-1"
    employee.ctr_address_pair.fineos_address.city = "City1"
    employee.ctr_address_pair.fineos_address.geo_state_id = GeoState.MA.geo_state_id
    employee.ctr_address_pair.fineos_address.zip_code = "11111"
    test_db_session.commit()

    # Run the process
    exporter.process_extract_data(tmp_path, test_db_session)
    test_db_session.expire_all()

    # Verify the payment isn't marked as having an address update
    payment = (
        test_db_session.query(Payment)
        .filter(Payment.fineos_pei_c_value == "7326", Payment.fineos_pei_i_value == "301")
        .first()
    )
    assert payment is not None
    assert payment.has_address_update is False

    # There should be a EFT_REQUEST_RECEIVED record
    employee_state_logs_after = (
        test_db_session.query(StateLog).filter(StateLog.employee_id == employee.employee_id).all()
    )
    assert len(employee_state_logs_after) == 1
    assert employee_state_logs_after[0].end_state_id == State.EFT_REQUEST_RECEIVED.state_id
