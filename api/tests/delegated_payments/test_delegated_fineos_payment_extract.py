import csv
import os
import tempfile
from collections import OrderedDict
from datetime import date

import boto3
import faker
import pytest
from freezegun import freeze_time

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_fineos_payment_extract as extractor
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
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
    PaymentFactory,
    ReferenceFileFactory,
)
from massgov.pfml.db.models.payments import (
    FineosExtractVpei,
    FineosExtractVpeiClaimDetails,
    FineosExtractVpeiPaymentDetails,
)
from massgov.pfml.delegated_payments.delegated_config import get_s3_config
from massgov.pfml.delegated_payments.delegated_payments_util import (
    ValidationIssue,
    ValidationReason,
)

# every test in here requires real resources

pytestmark = pytest.mark.integration

EXPECTED_OUTCOME = {"message": "Success"}

PEI_FIELD_NAMES = [
    "C",
    "I",
    "PAYEESOCNUMBE",
    "PAYMENTADD1",
    "PAYMENTADD2",
    "PAYMENTADD4",
    "PAYMENTADD6",
    "PAYMENTPOSTCO",
    "PAYMENTMETHOD",
    "PAYMENTDATE",
    "AMOUNT_MONAMT",
    "PAYEEBANKSORT",
    "PAYEEACCOUNTN",
    "PAYEEACCOUNTT",
    "EVENTTYPE",
]
PEI_PAYMENT_DETAILS_FIELD_NAMES = ["PECLASSID", "PEINDEXID", "PAYMENTSTARTP", "PAYMENTENDPER"]
PEI_CLAIM_DETAILS_FIELD_NAMES = ["PECLASSID", "PEINDEXID", "ABSENCECASENU"]

fake = faker.Faker()
fake.seed_instance(1212)

### UTILITY METHODS


@pytest.fixture
def payment_extract_step(initialize_factories_session, test_db_session, test_db_other_session):
    return extractor.PaymentExtractStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


def make_s3_file(s3_bucket, key, test_file_name):
    # Utility method to upload a test file to the mocked S3.
    # test_file_name corresponds to the name of the file in the test_files directory
    test_file_path = os.path.join(os.path.dirname(__file__), f"test_files/{test_file_name}")

    s3 = boto3.client("s3")
    s3.upload_file(test_file_path, s3_bucket, key)


def make_and_upload_extract_file(tmp_path, mock_s3_bucket, file_name, fieldnames, records):
    csv_file_path = tmp_path / file_name
    csv_file = file_util.write_file(str(csv_file_path))
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()

    for record in records:
        csv_writer.writerow(record)

    csv_file.close()

    s3 = boto3.client("s3")
    s3.upload_file(
        str(csv_file_path), mock_s3_bucket, f"cps/inbound/received/2020-01-01-11-30-00-{file_name}"
    )


def get_value(value, default, generate_defaults):
    if not value:
        if generate_defaults:
            return default
        return ""

    return value


def make_vpei_record(
    c_value,
    i_value,
    generate_defaults=True,
    tin=None,
    address1=None,
    address2=None,
    city=None,
    state=None,
    zip_code=None,
    payment_method=None,
    payment_date=None,
    payment_amount=None,
    routing_nbr=None,
    account_nbr=None,
    account_type=None,
    payment_type=None,
):
    vpei_record = OrderedDict()
    vpei_record["C"] = c_value
    vpei_record["I"] = i_value

    vpei_record["PAYEESOCNUMBE"] = get_value(tin, fake.ssn().replace("-", ""), generate_defaults)
    vpei_record["PAYMENTADD1"] = get_value(
        address1,
        f"{fake.building_number()} {fake.street_name()} {fake.street_suffix()}",
        generate_defaults,
    )
    vpei_record["PAYMENTADD2"] = get_value(address2, "", generate_defaults)
    vpei_record["PAYMENTADD4"] = get_value(city, fake.city(), generate_defaults)
    vpei_record["PAYMENTADD6"] = get_value(state, fake.state_abbr().upper(), generate_defaults)
    vpei_record["PAYMENTPOSTCO"] = get_value(
        zip_code, fake.zipcode_plus4().replace("-", ""), generate_defaults
    )
    vpei_record["PAYMENTMETHOD"] = get_value(
        payment_method, "Elec Funds Transfer", generate_defaults
    )
    vpei_record["PAYMENTDATE"] = get_value(payment_date, "2021-01-01 12:00:00", generate_defaults)
    vpei_record["AMOUNT_MONAMT"] = get_value(payment_amount, "100.00", generate_defaults)
    vpei_record["PAYEEBANKSORT"] = get_value(routing_nbr, "051000101", generate_defaults)
    vpei_record["PAYEEACCOUNTN"] = get_value(account_nbr, "12345678910", generate_defaults)
    vpei_record["PAYEEACCOUNTT"] = get_value(account_type, "Checking", generate_defaults)
    vpei_record["EVENTTYPE"] = get_value(payment_type, "PaymentOut", generate_defaults)

    return vpei_record


def make_claim_detail_record(pe_class_id, pe_index_id, absence_case_number=None):
    claim_detail_record = OrderedDict()
    claim_detail_record["PECLASSID"] = pe_class_id
    claim_detail_record["PEINDEXID"] = pe_index_id
    claim_detail_record["ABSENCECASENU"] = absence_case_number
    return claim_detail_record


def make_payment_details_record(
    pe_class_id, pe_index_id, generate_defaults=True, payment_start=None, payment_end=None
):
    payment_detail_record = OrderedDict()
    payment_detail_record["PECLASSID"] = pe_class_id
    payment_detail_record["PEINDEXID"] = pe_index_id

    payment_detail_record["PAYMENTSTARTP"] = get_value(
        payment_start, "2021-01-01 12:00:00", generate_defaults
    )
    payment_detail_record["PAYMENTENDPER"] = get_value(
        payment_end, "2021-01-08 12:00:00", generate_defaults
    )
    return payment_detail_record


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
    additional_payment_state=None,
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
        claim = ClaimFactory.create(fineos_absence_id=absence_case_id, employee=employee)

        # Payment needs to be attached to a claim
        if add_payment:
            payment = PaymentFactory.create(
                claim=claim, fineos_pei_c_value=c_value, fineos_pei_i_value=i_value
            )
            state_log_util.create_finished_state_log(
                payment, additional_payment_state, EXPECTED_OUTCOME, db_session
            )


def add_db_records_from_row(
    db_session,
    vpei_record,
    claimant_record,
    add_claim=True,
    add_address=True,
    add_eft=True,
    add_payment=False,
    add_employee=True,
    additional_payment_state=None,
):
    add_db_records(
        db_session,
        tin=vpei_record["PAYEESOCNUMBE"],
        absence_case_id=claimant_record["ABSENCECASENU"],
        c_value=vpei_record["C"],
        i_value=vpei_record["I"],
        add_claim=add_claim,
        add_address=add_address,
        add_eft=add_eft,
        add_payment=add_payment,
        add_employee=add_employee,
        additional_payment_state=additional_payment_state,
    )


def setup_process_tests(
    mock_s3_bucket,
    db_session,
    add_claim=True,
    add_address=True,
    add_eft=True,
    add_payment=False,
    add_second_employee=True,  # False = this'll cause the second record to fail
    additional_payment_state=None,
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
        db_session,
        "111111111",
        "NTN-01-ABS-02",
        add_claim=add_claim,
        add_address=add_address,
        add_eft=add_eft,
        add_payment=add_payment,
        c_value="7326",
        i_value="301",
        additional_payment_state=additional_payment_state,
    )
    add_db_records(
        db_session,
        "222222222",
        "NTN-02-ABS-03",
        add_claim=add_claim,
        add_address=add_address,
        add_eft=add_eft,
        add_payment=add_payment,
        add_employee=add_second_employee,
        c_value="7326",
        i_value="302",
        additional_payment_state=additional_payment_state,
    )
    add_db_records(
        db_session,
        "333333333",
        "NTN-03-ABS-04",
        add_claim=add_claim,
        add_address=add_address,
        add_eft=add_eft,
        add_payment=add_payment,
        c_value="7326",
        i_value="303",
        additional_payment_state=additional_payment_state,
    )


def add_s3_files(mock_fineos_s3_bucket, s3_prefix):
    make_s3_file(mock_fineos_s3_bucket, f"{s3_prefix}vpei.csv", "vpei.csv")
    make_s3_file(
        mock_fineos_s3_bucket, f"{s3_prefix}vpeipaymentdetails.csv", "vpeipaymentdetails.csv",
    )
    make_s3_file(mock_fineos_s3_bucket, f"{s3_prefix}vpeiclaimdetails.csv", "vpeiclaimdetails.csv")


### TESTS BEGIN


def test_download_and_parse_data(mock_s3_bucket, tmp_path, payment_extract_step):
    make_s3_file(mock_s3_bucket, "path/to/file/test.csv", "small.csv")

    raw_data = payment_extract_step.download_and_parse_data(
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
    payment_extract_step,
    test_db_session,
    monkeypatch,
    create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_MAX_HISTORY_DATE", "2019-12-31")
    setup_process_tests(mock_s3_bucket, test_db_session)

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 6

    payment_extract_step.run()

    # Make sure files were copied to the processed directory
    moved_files = file_util.list_files(
        f"s3://{mock_s3_bucket}/cps/inbound/processed/{payments_util.get_date_group_folder_name('2020-01-01-11-30-00', ReferenceFileType.FINEOS_PAYMENT_EXTRACT)}/"
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
        assert payment.fineos_extract_import_log_id == payment_extract_step.get_import_log_id()

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
            == "s3://test_bucket/cps/inbound/processed/2020-01-01-11-30-00-payment-extract"
        )
        assert (
            reference_file.reference_file_type_id
            == ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id
        )
        # Verify that there is exactly one successful state log per payment
        state_logs = payment.state_logs
        assert len(state_logs) == 1
        state_log = state_logs[0]
        assert state_log.outcome == EXPECTED_OUTCOME
        assert (
            state_log.end_state_id
            == State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_id
        )

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


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_data_prior_payment_exists_is_being_processed(
    mock_s3_bucket,
    set_exporter_env_vars,
    payment_extract_step,
    test_db_session,
    monkeypatch,
    create_triggers,
    caplog,
):
    monkeypatch.setenv("FINEOS_PAYMENT_MAX_HISTORY_DATE", "2019-12-31")
    setup_process_tests(
        mock_s3_bucket,
        test_db_session,
        add_payment=True,
        additional_payment_state=State.DELEGATED_PAYMENT_COMPLETE,
    )

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 6

    payment_extract_step.run()

    for index in ["1", "2", "3"]:
        payments = (
            test_db_session.query(Payment)
            .filter(
                Payment.fineos_pei_c_value == "7326", Payment.fineos_pei_i_value == f"30{index}"
            )
            .all()
        )
        # There will be both a prior payment and a new payment
        assert len(payments) == 2

        new_payment = [
            payment
            for payment in payments
            if payment.state_logs[0].end_state_id
            == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id
        ][0]
        assert new_payment
        assert len(new_payment.state_logs) == 1
        state_log = new_payment.state_logs[0]

        assert state_log.outcome == {
            "message": "Error processing payment record",
            "validation_container": {
                "record_key": f"CiIndex(c='7326', i='30{index}')",
                "validation_issues": [
                    {
                        "reason": "ReceivedPaymentCurrentlyBeingProcessed",
                        "details": "We received a payment that is already being processed. It is currently in state Payment complete.",
                    }
                ],
            },
        }

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


def test_process_extract_data_one_bad_record(
    mock_s3_bucket,
    set_exporter_env_vars,
    payment_extract_step,
    test_db_session,
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

    payment_extract_step.run()

    # The second record will have failed and so no payment would have been created
    for index in ["1", "2", "3"]:
        payment = (
            test_db_session.query(Payment)
            .filter(
                Payment.fineos_pei_c_value == "7326", Payment.fineos_pei_i_value == f"30{index}"
            )
            .one_or_none()
        )
        # Payment+claim is created even when employee cannot be found
        assert payment
        assert payment.claim
        assert len(payment.state_logs) == 1
        state_log = payment.state_logs[0]
        if index == "2":
            assert (
                state_log.end_state_id
                == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id
            )
            assert state_log.outcome == {
                "message": "Error processing payment record",
                "validation_container": {
                    "record_key": "CiIndex(c='7326', i='302')",
                    "validation_issues": [{"reason": "MissingInDB", "details": "tax_identifier"}],
                },
            }
        else:
            assert (
                state_log.end_state_id
                == State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_id
            )
            assert state_log.outcome == EXPECTED_OUTCOME

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


def test_process_extract_data_rollback(
    mock_s3_bucket,
    set_exporter_env_vars,
    payment_extract_step,
    test_db_session,
    monkeypatch,
    create_triggers,
):
    setup_process_tests(mock_s3_bucket, test_db_session)

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 6

    # Override the method that moves files at the end to throw
    # an error so that everything will rollback
    def err_method(*args):
        raise Exception("Fake Error")

    monkeypatch.setenv("FINEOS_PAYMENT_MAX_HISTORY_DATE", "2019-12-31")
    monkeypatch.setattr(payment_extract_step, "move_files_from_received_to_processed", err_method)

    with pytest.raises(Exception, match="Fake Error"):
        payment_extract_step.run()
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
            == ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id
        )

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


def test_process_extract_unprocessed_folder_files(
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    payment_extract_step,
    test_db_session,
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
                "2020-01-01-11-30-00", ReferenceFileType.FINEOS_PAYMENT_EXTRACT
            ),
        ),
        reference_file_type_id=ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id,
    )
    ReferenceFileFactory.create(
        file_location=os.path.join(
            get_s3_config().pfml_fineos_inbound_path,
            "processed",
            payments_util.get_date_group_folder_name(
                "2020-01-03-11-30-00", ReferenceFileType.FINEOS_PAYMENT_EXTRACT
            ),
        ),
        reference_file_type_id=ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id,
    )

    payment_extract_step.run()
    processed_folder = os.path.join(
        get_s3_config().pfml_fineos_inbound_path, payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
    )
    skipped_folder = os.path.join(
        get_s3_config().pfml_fineos_inbound_path, payments_util.Constants.S3_INBOUND_SKIPPED_DIR,
    )
    processed_files = file_util.list_files(processed_folder, recursive=True)
    skipped_files = file_util.list_files(skipped_folder, recursive=True)
    assert len(processed_files) == 4
    assert len(skipped_files) == 2

    expected_file_names = []
    for date_file in ["vpei.csv", "vpeipaymentdetails.csv", "vpeiclaimdetails.csv"]:
        for unprocessed_date in ["2020-01-02-11-30-00", "2020-01-04-11-30-00"]:
            expected_file_names.append(
                f"{payments_util.get_date_group_folder_name(unprocessed_date, ReferenceFileType.FINEOS_PAYMENT_EXTRACT)}/{unprocessed_date}-{date_file}"
            )

    for processed_file in processed_files:
        assert processed_file in expected_file_names

    for file in skipped_files:
        assert file.startswith("2020-01-02-11-30-00")

    # confirm no files will be copied in a subsequent copy
    copied_files = payments_util.copy_fineos_data_to_archival_bucket(
        test_db_session, extractor.expected_file_names, ReferenceFileType.FINEOS_PAYMENT_EXTRACT
    )
    assert len(copied_files) == 1

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == 0


def test_process_extract_data_no_existing_claim_address_eft(
    mock_s3_bucket,
    set_exporter_env_vars,
    payment_extract_step,
    test_db_session,
    monkeypatch,
    create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_MAX_HISTORY_DATE", "2019-12-31")
    setup_process_tests(
        mock_s3_bucket, test_db_session, add_claim=False, add_address=False, add_eft=False,
    )

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 3

    payment_extract_step.run()

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
        assert (
            state_log.end_state_id
            == State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_id
        )

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
    payment_extract_step,
    test_db_session,
    monkeypatch,
    create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_MAX_HISTORY_DATE", "2019-12-31")
    setup_process_tests(
        mock_s3_bucket,
        test_db_session,
        add_payment=True,
        additional_payment_state=State.DELEGATED_PAYMENT_ERROR_REPORT_SENT,
    )

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 6

    payment_extract_step.run()

    for index in ["1", "2", "3"]:
        payments = (
            test_db_session.query(Payment)
            .filter(
                Payment.fineos_pei_c_value == "7326", Payment.fineos_pei_i_value == f"30{index}"
            )
            .all()
        )

        # There will be both a prior payment and a new payment
        assert len(payments) == 2

        for payment in payments:
            # Verify that there is exactly one successful state log per payment
            state_logs = payment.state_logs
            assert len(state_logs) == 1
            state_log = state_logs[0]
            assert state_log.outcome == EXPECTED_OUTCOME
            # The state ID will be either the prior state ID or the new successful one
            assert state_log.end_state_id in [
                State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_id,
                State.DELEGATED_PAYMENT_ERROR_REPORT_SENT.state_id,
            ]

    payment_count_after = test_db_session.query(Payment).count()
    assert payment_count_after == 6  # 3 payments each with an old record and a new one

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_data_minimal_viable_payment(
    mock_s3_bucket,
    set_exporter_env_vars,
    payment_extract_step,
    test_db_session,
    tmp_path,
    monkeypatch,
    create_triggers,
):
    # This test creates a file with absolutely no data besides the bare
    # minimum to be viable to create a payment, this is done in order
    # to test that all of our validations work, and all of the missing data
    # edge cases are accounted for and handled appropriately. This shouldn't
    # ever be a real scenario, but might encompass small pieces of something real
    monkeypatch.setenv("FINEOS_PAYMENT_MAX_HISTORY_DATE", "2019-12-31")
    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 0

    vpei_record = make_vpei_record("1000", "1", generate_defaults=False)
    make_and_upload_extract_file(
        tmp_path, mock_s3_bucket, "vpei.csv", PEI_FIELD_NAMES, [vpei_record]
    )

    claim_record = make_claim_detail_record("1000", "1")
    make_and_upload_extract_file(
        tmp_path,
        mock_s3_bucket,
        "vpeiclaimdetails.csv",
        PEI_CLAIM_DETAILS_FIELD_NAMES,
        [claim_record],
    )

    payment_details_record = make_payment_details_record("1000", "1", generate_defaults=False)
    make_and_upload_extract_file(
        tmp_path,
        mock_s3_bucket,
        "vpeipaymentdetails.csv",
        PEI_PAYMENT_DETAILS_FIELD_NAMES,
        [payment_details_record],
    )

    # We deliberately do no DB setup, there will not be any prior employee or claim
    payment_extract_step.run()

    payment = test_db_session.query(Payment).one_or_none()
    assert payment
    assert payment.claim is None

    assert len(payment.state_logs) == 1
    state_log = payment.state_logs[0]
    state_log.end_state_id = State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id

    assert state_log.outcome["message"] == "Error processing payment record"
    assert state_log.outcome["validation_container"]["record_key"] == "CiIndex(c='1000', i='1')"
    # Not going to exactly match the errors here as there are many
    # and they may adjust in the future
    assert len(state_log.outcome["validation_container"]["validation_issues"]) >= 10

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_additional_payment_types(
    mock_s3_bucket,
    set_exporter_env_vars,
    test_db_session,
    payment_extract_step,
    tmp_path,
    initialize_factories_session,
    monkeypatch,
    create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_MAX_HISTORY_DATE", "2019-12-31")
    # Create a zero dollar payment
    vpei_record_zero_dollar = make_vpei_record("1000", "1", payment_amount="0.00")
    claim_record_zero_dollar = make_claim_detail_record("1000", "1", "NTN-01-ABS-01")
    payment_details_record_zero_dollar = make_payment_details_record("1000", "1")
    add_db_records_from_row(test_db_session, vpei_record_zero_dollar, claim_record_zero_dollar)

    # Create an overpayment
    vpei_record_overpayment = make_vpei_record("2000", "2", payment_type="Overpayment")
    claim_record_overpayment = make_claim_detail_record("2000", "2", "NTN-02-ABS-02")
    payment_details_record_overpayment = make_payment_details_record("2000", "2")
    add_db_records_from_row(test_db_session, vpei_record_overpayment, claim_record_overpayment)

    # Create an ACH cancellation
    vpei_record_ach_cancellation = make_vpei_record(
        "3000", "3", payment_method="Elec Funds Transfer", payment_type="PaymentOut Cancellation"
    )
    claim_record_ach_cancellation = make_claim_detail_record("3000", "3", "NTN-03-ABS-03")
    payment_details_record_ach_cancellation = make_payment_details_record("3000", "3")
    add_db_records_from_row(
        test_db_session, vpei_record_ach_cancellation, claim_record_ach_cancellation
    )

    # Create a check cancellation
    vpei_record_check_cancellation = make_vpei_record(
        "4000", "4", payment_method="Check", payment_type="PaymentOut Cancellation"
    )
    claim_record_check_cancellation = make_claim_detail_record("4000", "4", "NTN-04-ABS-04")
    payment_details_record_check_cancellation = make_payment_details_record("4000", "4")
    add_db_records_from_row(
        test_db_session, vpei_record_check_cancellation, claim_record_check_cancellation
    )

    # Unknown - negative payment but not a cancellation/overpayment
    vpei_record_unknown = make_vpei_record(
        "5000", "5", payment_type="Mystery", payment_amount="-50.00"
    )
    claim_record_unknown = make_claim_detail_record("5000", "5", "NTN-05-ABS-05")
    payment_details_record_unknown = make_payment_details_record("5000", "5")
    add_db_records_from_row(test_db_session, vpei_record_unknown, claim_record_unknown)

    make_and_upload_extract_file(
        tmp_path,
        mock_s3_bucket,
        "vpei.csv",
        PEI_FIELD_NAMES,
        [
            vpei_record_zero_dollar,
            vpei_record_overpayment,
            vpei_record_ach_cancellation,
            vpei_record_check_cancellation,
            vpei_record_unknown,
        ],
    )
    make_and_upload_extract_file(
        tmp_path,
        mock_s3_bucket,
        "vpeiclaimdetails.csv",
        PEI_CLAIM_DETAILS_FIELD_NAMES,
        [
            claim_record_zero_dollar,
            claim_record_overpayment,
            claim_record_ach_cancellation,
            claim_record_check_cancellation,
            claim_record_unknown,
        ],
    )
    make_and_upload_extract_file(
        tmp_path,
        mock_s3_bucket,
        "vpeipaymentdetails.csv",
        PEI_PAYMENT_DETAILS_FIELD_NAMES,
        [
            payment_details_record_zero_dollar,
            payment_details_record_overpayment,
            payment_details_record_ach_cancellation,
            payment_details_record_check_cancellation,
            payment_details_record_unknown,
        ],
    )

    # Run the extract process
    payment_extract_step.run()

    # Zero dollar payment should be in DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_ZERO_PAYMENT
    zero_dollar_payment = (
        test_db_session.query(Payment)
        .filter(Payment.fineos_pei_c_value == "1000", Payment.fineos_pei_i_value == "1")
        .one_or_none()
    )
    assert len(zero_dollar_payment.state_logs) == 1
    assert (
        zero_dollar_payment.state_logs[0].end_state_id
        == State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_ZERO_PAYMENT.state_id
    )

    # Overpayment should be in DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_OVERPAYMENT
    overpayment_payment = (
        test_db_session.query(Payment)
        .filter(Payment.fineos_pei_c_value == "2000", Payment.fineos_pei_i_value == "2")
        .one_or_none()
    )
    assert len(overpayment_payment.state_logs) == 1
    assert (
        overpayment_payment.state_logs[0].end_state_id
        == State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_OVERPAYMENT.state_id
    )

    # ACH Cancellation should be in DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_CANCELLATION
    ach_cancellation_payment = (
        test_db_session.query(Payment)
        .filter(Payment.fineos_pei_c_value == "3000", Payment.fineos_pei_i_value == "3")
        .one_or_none()
    )
    assert len(ach_cancellation_payment.state_logs) == 1
    assert (
        ach_cancellation_payment.state_logs[0].end_state_id
        == State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_CANCELLATION.state_id
    )

    # Check Cancellation should be in the normal path end state of DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING
    check_cancellation_payment = (
        test_db_session.query(Payment)
        .filter(Payment.fineos_pei_c_value == "4000", Payment.fineos_pei_i_value == "4")
        .one_or_none()
    )
    assert len(check_cancellation_payment.state_logs) == 1
    assert (
        check_cancellation_payment.state_logs[0].end_state_id
        == State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_id
    )

    # Unknown should be in the error report state DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT
    unknown_payment = (
        test_db_session.query(Payment)
        .filter(Payment.fineos_pei_c_value == "5000", Payment.fineos_pei_i_value == "5")
        .one_or_none()
    )
    assert len(unknown_payment.state_logs) == 1
    assert (
        unknown_payment.state_logs[0].end_state_id
        == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id
    )


def test_validation_missing_fields(initialize_factories_session, set_exporter_env_vars):
    # This test is specifically aimed at verifying we check for required parameters

    # We set it up so the datasets can be joined on ci_index, but don't set any
    # values that aren't specifically used for joining, so all required params
    # should subsequently be in the validation object
    # Note the isdata fields are just to avoid the dictionaries being empty
    ci_index = extractor.CiIndex("1", "1")
    extract_data = extractor.ExtractData(extractor.expected_file_names, "2020-01-01-11-30-00")
    extract_data.pei.indexed_data = {ci_index: {"PAYEECUSTOMER": "1234"}}
    extract_data.payment_details.indexed_data = {ci_index: [{"isdata": "1"}]}
    extract_data.claim_details.indexed_data = {ci_index: {"ABSENCECASENU": "NTN-01-ABS-01"}}

    payment_data = extractor.PaymentData(
        extract_data, ci_index, extract_data.pei.indexed_data.get(ci_index)
    )
    validation_container = payment_data.validation_container
    assert validation_container.record_key == str(ci_index)
    expected_missing_values = set(
        [
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEESOCNUMBE"),
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
        ]
    )
    assert set(validation_container.validation_issues) == expected_missing_values

    # We want to make sure missing, "" and Unknown are all treated the same
    # So update a few values, and expect the same result
    extract_data.pei.indexed_data[ci_index]["PAYEESOCNUMBE"] = ""
    extract_data.pei.indexed_data[ci_index]["PAYMENTADD1"] = ""
    extract_data.pei.indexed_data[ci_index]["PAYMENTADD4"] = "Unknown"
    extract_data.pei.indexed_data[ci_index]["PAYMENTPOSTCO"] = "Unknown"

    payment_data = extractor.PaymentData(
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

    payment_data = extractor.PaymentData(
        extract_data, ci_index, extract_data.pei.indexed_data.get(ci_index)
    )
    assert set(payment_data.validation_container.validation_issues) == expected_missing_values


def test_validation_param_length(set_exporter_env_vars):
    # We set it up so the datasets can be joined on ci_index, but don't set any
    # values that aren't specifically used for joining, We are only setting values
    # we are explicitly testing against here, the validation will have missing
    # errors as well, but we're not going to look at them.
    ci_index = extractor.CiIndex("1", "1")
    extract_data = extractor.ExtractData(extractor.expected_file_names, "2020-01-01-11-30-00")
    # First let's check if a field is too short
    extract_data.pei.indexed_data = {ci_index: {"PAYEEBANKSORT": "123", "PAYMENTPOSTCO": "123"}}
    extract_data.payment_details.indexed_data = {ci_index: [{"isdata": "1"}]}
    extract_data.claim_details.indexed_data = {ci_index: {"ABSENCECASENU": "NTN-01-ABS-01"}}

    payment_data = extractor.PaymentData(
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

    payment_data = extractor.PaymentData(
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
    ci_index = extractor.CiIndex("1", "1")
    extract_data = extractor.ExtractData(extractor.expected_file_names, "2020-01-01-11-30-00")
    extract_data.pei.indexed_data = {
        ci_index: {
            "PAYEECUSTOMER": "1234",
            "PAYEEACCOUNTT": "BadData",
            "PAYMENTMETHOD": "BadData",
            "PAYMENTADD6": "BadData",
        }
    }
    extract_data.payment_details.indexed_data = {ci_index: [{"isdata": "1"}]}
    extract_data.claim_details.indexed_data = {ci_index: {"ABSENCECASENU": "NTN-01-ABS-01"}}

    payment_data = extractor.PaymentData(
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
    # When doing validation, we verify that payment amount
    # must be a numeric value

    ci_index = extractor.CiIndex("1", "1")
    extract_data = extractor.ExtractData(extractor.expected_file_names, "2020-01-01-11-30-00")
    extract_data.pei.indexed_data = {ci_index: {"AMOUNT_MONAMT": "MONEY"}}
    extract_data.payment_details.indexed_data = {ci_index: [{"isdata": "1"}]}
    extract_data.claim_details.indexed_data = {ci_index: {"ABSENCECASENU": "NTN-01-ABS-01"}}

    payment_data = extractor.PaymentData(
        extract_data, ci_index, extract_data.pei.indexed_data.get(ci_index)
    )

    assert set([ValidationIssue(ValidationReason.INVALID_VALUE, "AMOUNT_MONAMT")]).issubset(
        set(payment_data.validation_container.validation_issues)
    )


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_update_eft_no_update(
    payment_extract_step, test_db_session, mock_s3_bucket, set_exporter_env_vars, monkeypatch,
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
    payment_extract_step.run()
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
    payment_extract_step, test_db_session, mock_s3_bucket, set_exporter_env_vars, monkeypatch,
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
    payment_extract_step.run()
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


def test_extract_to_staging_tables(payment_extract_step, test_db_session):
    tempdir = tempfile.mkdtemp()
    date_str = "2020-12-21-19-20-42"
    test_file_name1 = "vpei.csv"
    test_file_name2 = "vpeiclaimdetails.csv"
    test_file_name3 = "vpeipaymentdetails.csv"

    test_file_path1 = os.path.join(os.path.dirname(__file__), f"test_files/{test_file_name1}")
    test_file_path2 = os.path.join(os.path.dirname(__file__), f"test_files/{test_file_name2}")
    test_file_path3 = os.path.join(os.path.dirname(__file__), f"test_files/{test_file_name3}")

    test_file_names = [test_file_path1, test_file_path2, test_file_path3]

    extract_data = extractor.ExtractData(test_file_names, date_str)
    payment_extract_step.download_and_process_data(extract_data, tempdir)
    payment_extract_step.extract_to_staging_tables(extract_data)

    test_db_session.commit()

    pei_data = test_db_session.query(FineosExtractVpei).all()
    claim_details_data = test_db_session.query(FineosExtractVpeiClaimDetails).all()
    payment_details_data = test_db_session.query(FineosExtractVpeiPaymentDetails).all()

    assert len(pei_data) == 3
    assert len(claim_details_data) == 3
    assert len(payment_details_data) == 3

    ref_file = extract_data.reference_file

    for data in pei_data:
        assert data.reference_file_id == ref_file.reference_file_id
        assert data.fineos_extract_import_log_id == payment_extract_step.get_import_log_id()

    for data in claim_details_data:
        assert data.reference_file_id == ref_file.reference_file_id
        assert data.fineos_extract_import_log_id == payment_extract_step.get_import_log_id()

    for data in payment_details_data:
        assert data.reference_file_id == ref_file.reference_file_id
        assert data.fineos_extract_import_log_id == payment_extract_step.get_import_log_id()
