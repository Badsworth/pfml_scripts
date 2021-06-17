import json
import os
from datetime import date, datetime, timedelta

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
    ClaimType,
    Employee,
    EmployeeAddress,
    EmployeeLog,
    Flow,
    GeoState,
    LkState,
    Payment,
    PaymentMethod,
    PaymentTransactionType,
    PrenoteState,
    PubEft,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
    TaxIdentifier,
)
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployeePubEftPairFactory,
    ExperianAddressPairFactory,
    PaymentFactory,
    PubEftFactory,
    ReferenceFileFactory,
)
from massgov.pfml.db.models.payments import (
    FineosExtractVbiRequestedAbsence,
    FineosExtractVpei,
    FineosExtractVpeiClaimDetails,
    FineosExtractVpeiPaymentDetails,
    FineosWritebackDetails,
    FineosWritebackTransactionStatus,
)
from massgov.pfml.delegated_payments.delegated_config import get_s3_config
from massgov.pfml.delegated_payments.delegated_fineos_payment_extract import (
    PRENOTE_PRENDING_WAITING_PERIOD,
)
from massgov.pfml.delegated_payments.delegated_payments_util import (
    ValidationIssue,
    ValidationReason,
    get_now,
)
from massgov.pfml.delegated_payments.mock.fineos_extract_data import (
    FineosPaymentData,
    create_fineos_payment_extract_files,
)

# every test in here requires real resources

pytestmark = pytest.mark.integration

EXPECTED_OUTCOME = {"message": "Success"}

fake = faker.Faker()
fake.seed_instance(1212)


### UTILITY METHODS


@pytest.fixture
def payment_extract_step(initialize_factories_session, test_db_session, test_db_other_session):
    return extractor.PaymentExtractStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


@pytest.fixture
def local_payment_extract_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    return extractor.PaymentExtractStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


def make_s3_file(s3_bucket, key, test_file_name):
    # Utility method to upload a test file to the mocked S3.
    # test_file_name corresponds to the name of the file in the test_files directory
    test_file_path = os.path.join(os.path.dirname(__file__), f"test_files/{test_file_name}")

    s3 = boto3.client("s3")
    s3.upload_file(test_file_path, s3_bucket, key)


def upload_fineos_data(tmp_path, mock_s3_bucket, fineos_dataset):
    folder_path = os.path.join(f"s3://{mock_s3_bucket}", "cps/inbound/received")
    date_of_extract = datetime.strptime("2020-01-01-11-30-00", "%Y-%m-%d-%H-%M-%S")
    create_fineos_payment_extract_files(fineos_dataset, folder_path, date_of_extract)


def add_db_records(
    db_session,
    tin,
    absence_case_id,
    add_claim=True,
    add_claim_type=True,
    is_id_proofed=True,
    add_address=True,
    add_eft=True,
    add_payment=False,
    add_employee=True,
    c_value=None,
    i_value=None,
    additional_payment_state=None,
    claim_type=None,
):
    mailing_address = None
    experian_address_pair = None
    if add_address:
        mailing_address = AddressFactory()
        experian_address_pair = ExperianAddressPairFactory(fineos_address=mailing_address)

    if add_employee:
        employee = EmployeeFactory.create(tax_identifier=TaxIdentifier(tax_identifier=tin))
        if add_eft:
            pub_eft = PubEftFactory.create(
                routing_nbr=tin,
                account_nbr=tin,
                prenote_state_id=PrenoteState.APPROVED.prenote_state_id,
            )
            EmployeePubEftPairFactory.create(employee=employee, pub_eft=pub_eft)

        if add_address:
            employee.addresses = [EmployeeAddress(employee=employee, address=mailing_address)]

        if add_claim:
            if not claim_type:
                claim_type_id = ClaimType.FAMILY_LEAVE.claim_type_id if add_claim_type else None
            else:
                claim_type_id = ClaimType.MEDICAL_LEAVE.claim_type_id

            claim = ClaimFactory.create(
                fineos_absence_id=absence_case_id,
                employee=employee,
                claim_type_id=claim_type_id,
                is_id_proofed=is_id_proofed,
            )

            # Payment needs to be attached to a claim
            if add_payment:
                payment = PaymentFactory.create(
                    claim=claim,
                    claim_type=claim.claim_type,
                    fineos_pei_c_value=c_value,
                    fineos_pei_i_value=i_value,
                    experian_address_pair=experian_address_pair,
                )
                state_log_util.create_finished_state_log(
                    payment, additional_payment_state, EXPECTED_OUTCOME, db_session
                )


def add_db_records_from_fineos_data(
    db_session,
    fineos_data,
    add_claim=True,
    add_claim_type=True,
    is_id_proofed=True,
    add_address=True,
    add_eft=True,
    add_payment=False,
    add_employee=True,
    additional_payment_state=None,
):
    add_db_records(
        db_session,
        tin=fineos_data.tin,
        absence_case_id=fineos_data.absence_case_number,
        c_value=fineos_data.c_value,
        i_value=fineos_data.i_value,
        add_claim=add_claim,
        add_claim_type=add_claim_type,
        is_id_proofed=is_id_proofed,
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
    make_s3_file(mock_s3_bucket, f"{s3_prefix}VBI_REQUESTEDABSENCE.csv", "VBI_REQUESTEDABSENCE.csv")

    add_db_records(
        db_session,
        "111111111",
        "NTN-01-ABS-01",
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
        "NTN-02-ABS-02",
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
        "NTN-03-ABS-03",
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
    make_s3_file(
        mock_fineos_s3_bucket, f"{s3_prefix}VBI_REQUESTEDABSENCE.csv", "VBI_REQUESTEDABSENCE.csv"
    )


def validate_pei_writeback_state_for_payment(
    payment,
    db_session,
    is_invalid=False,
    is_issue_in_system=False,
    is_pending_prenote=False,
    is_rejected_prenote=False,
):
    state_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PEI_WRITEBACK, db_session
    )

    writeback_details = (
        db_session.query(FineosWritebackDetails)
        .filter(FineosWritebackDetails.payment_id == payment.payment_id)
        .one_or_none()
    )

    assert state_log
    assert state_log.end_state_id == State.DELEGATED_ADD_TO_FINEOS_WRITEBACK.state_id

    assert writeback_details

    if is_invalid:
        assert (
            writeback_details.transaction_status_id
            == FineosWritebackTransactionStatus.FAILED_AUTOMATED_VALIDATION.transaction_status_id
        )
    elif is_issue_in_system:
        assert (
            writeback_details.transaction_status_id
            == FineosWritebackTransactionStatus.DATA_ISSUE_IN_SYSTEM.transaction_status_id
        )
    elif is_pending_prenote:
        assert (
            writeback_details.transaction_status_id
            == FineosWritebackTransactionStatus.PENDING_PRENOTE.transaction_status_id
        )
    elif is_rejected_prenote:
        assert (
            writeback_details.transaction_status_id
            == FineosWritebackTransactionStatus.PRENOTE_ERROR.transaction_status_id
        )


def validate_non_standard_payment_state(non_standard_payment: Payment, payment_state: LkState):
    assert len(non_standard_payment.state_logs) == 2
    assert set([state_log.end_state_id for state_log in non_standard_payment.state_logs]) == set(
        [payment_state.state_id, State.DELEGATED_ADD_TO_FINEOS_WRITEBACK.state_id,]
    )


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
    local_payment_extract_step,
    local_test_db_session,
    monkeypatch,
    local_create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    setup_process_tests(mock_s3_bucket, local_test_db_session)

    employee_log_count_before = local_test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 3

    local_payment_extract_step.run()

    # Make sure files were copied to the processed directory
    moved_files = file_util.list_files(
        f"s3://{mock_s3_bucket}/cps/inbound/processed/{payments_util.get_date_group_folder_name('2020-01-01-11-30-00', ReferenceFileType.FINEOS_PAYMENT_EXTRACT)}/"
    )
    assert len(moved_files) == 4

    # Grab all files in the bucket, verify there are no more
    all_files = file_util.list_files(f"s3://{mock_s3_bucket}/", recursive=True)
    assert len(all_files) == 4

    # For simplicity of testing so much, the datasets we're reading from use numbers
    # to signify what record they're from (eg. city of of City1)
    # These also correspond to row1/2/3 in the files used
    for index in ["1", "2", "3"]:
        payment = (
            local_test_db_session.query(Payment)
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
        assert (
            payment.fineos_extract_import_log_id == local_payment_extract_step.get_import_log_id()
        )

        claim = payment.claim
        assert claim

        employee = claim.employee
        assert employee

        mailing_address = payment.experian_address_pair.fineos_address
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
        assert state_log.end_state_id == State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK.state_id

        pub_efts = employee.pub_efts.all()

        # Payment 2 uses CHECK over ACH, so some logic differs for it.
        # The 2nd record is also family leave, the other two are medical leave
        if index == "2":
            assert not mailing_address.address_line_two

            assert payment.disb_method_id == PaymentMethod.CHECK.payment_method_id
            assert payment.pub_eft_id is None
            assert payment.has_eft_update is False
            assert len(pub_efts) == 1  # One prior one created by setup logic

        else:
            assert mailing_address.address_line_two == f"AddressLine2-{index}"

            assert payment.disb_method_id == PaymentMethod.ACH.payment_method_id
            assert payment.pub_eft
            assert str(payment.pub_eft.routing_nbr) == index * 9
            assert str(payment.pub_eft.account_nbr) == index * 9
            assert (
                payment.pub_eft.bank_account_type_id
                == BankAccountType.CHECKING.bank_account_type_id
            )
            assert payment.has_eft_update is False

            assert len(pub_efts) == 1  # A prior one from setup logic
            assert payment.pub_eft_id in [pub_eft.pub_eft_id for pub_eft in employee.pub_efts]

    # Verify a few of the metrics were added to the import log table
    import_log_report = json.loads(payment.fineos_extract_import_log.report)
    assert import_log_report["standard_valid_payment_count"] == 3

    employee_log_count_after = local_test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_data_prior_payment_exists_is_being_processed(
    mock_s3_bucket,
    set_exporter_env_vars,
    local_payment_extract_step,
    local_test_db_session,
    monkeypatch,
    local_create_triggers,
    caplog,
):
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    setup_process_tests(
        mock_s3_bucket,
        local_test_db_session,
        add_payment=True,
        additional_payment_state=State.DELEGATED_PAYMENT_COMPLETE,
    )

    employee_log_count_before = local_test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 3

    local_payment_extract_step.run()

    for index in ["1", "2", "3"]:
        payments = (
            local_test_db_session.query(Payment)
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
            if payment.state_logs[0].end_state_id != State.DELEGATED_PAYMENT_COMPLETE.state_id
        ][0]
        assert new_payment

        state_log = state_log_util.get_latest_state_log_in_flow(
            new_payment, Flow.DELEGATED_PAYMENT, local_test_db_session
        )
        assert (
            state_log.end_state_id == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id
        )

        assert state_log.outcome == {
            "message": "Error processing payment record",
            "validation_container": {
                "record_key": f"CiIndex(c='7326', i='30{index}')",
                "validation_issues": [
                    {
                        "reason": "ReceivedPaymentCurrentlyBeingProcessed",
                        "details": "We received a payment that is already being processed. It is currently in state [Payment complete].",
                    }
                ],
            },
        }
        validate_pei_writeback_state_for_payment(
            new_payment, local_test_db_session, is_invalid=True
        )

    employee_log_count_after = local_test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


def test_process_extract_data_one_bad_record(
    mock_s3_bucket,
    set_exporter_env_vars,
    local_payment_extract_step,
    local_test_db_session,
    monkeypatch,
    local_create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    # This test will properly process record 1 & 3, but record 2 will
    # end up in an error state because we don't have an TIN/employee/claim associated with them
    setup_process_tests(
        mock_s3_bucket,
        local_test_db_session,
        add_address=False,
        add_eft=True,
        add_second_employee=False,
    )

    employee_log_count_before = local_test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 2

    local_payment_extract_step.run()

    # The second record will have failed and so no payment would have been created
    for index in ["1", "2", "3"]:
        payment = (
            local_test_db_session.query(Payment)
            .filter(
                Payment.fineos_pei_c_value == "7326", Payment.fineos_pei_i_value == f"30{index}"
            )
            .one_or_none()
        )
        # Payment is created even when employee cannot be found
        assert payment

        state_log = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, local_test_db_session
        )
        if index == "2":
            assert payment.claim_id is None
            assert (
                state_log.end_state_id
                == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE.state_id
            )
            assert state_log.outcome == {
                "message": "Error processing payment record",
                "validation_container": {
                    "record_key": "CiIndex(c='7326', i='302')",
                    "validation_issues": [
                        {"reason": "MissingInDB", "details": "tax_identifier: 222222222"},
                        {"reason": "MissingInDB", "details": "claim: NTN-02-ABS-02"},
                    ],
                },
            }
            validate_pei_writeback_state_for_payment(
                payment, local_test_db_session, is_issue_in_system=True
            )
        else:
            assert state_log.end_state_id == State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK.state_id
            assert state_log.outcome == EXPECTED_OUTCOME
            assert payment.claim_id

    employee_log_count_after = local_test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


def test_process_extract_data_rollback(
    mock_s3_bucket,
    set_exporter_env_vars,
    local_payment_extract_step,
    local_test_db_session,
    monkeypatch,
    local_create_triggers,
):
    setup_process_tests(mock_s3_bucket, local_test_db_session)

    employee_log_count_before = local_test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 3

    # Override the method that moves files at the end to throw
    # an error so that everything will rollback
    def err_method(*args):
        raise Exception("Fake Error")

    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    monkeypatch.setattr(
        local_payment_extract_step, "move_files_from_received_to_processed", err_method
    )

    with pytest.raises(Exception, match="Fake Error"):
        local_payment_extract_step.run()

    # Make certain that there are no payments or state logs in the DB
    payments = local_test_db_session.query(Payment).all()
    assert len(payments) == 0
    state_logs = local_test_db_session.query(StateLog).all()
    assert len(state_logs) == 0

    # The files should have been moved to the error folder
    expected_path = f"s3://{mock_s3_bucket}/cps/inbound/error/2020-01-01-11-30-00-payment-extract/"
    files = file_util.list_files(expected_path)
    assert len(files) == 4

    # The reference file should have been created
    reference_files = local_test_db_session.query(ReferenceFile).all()
    assert len(reference_files) == 1
    assert reference_files[0].file_location == expected_path
    assert (
        reference_files[0].reference_file_type_id
        == ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id
    )

    employee_log_count_after = local_test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


def test_process_extract_unprocessed_folder_files(
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    local_payment_extract_step,
    local_test_db_session,
    monkeypatch,
    local_create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")

    # add files
    add_s3_files(mock_fineos_s3_bucket, "DT2/dataexports/2020-01-01-11-30-00/2020-01-01-11-30-00-")
    add_s3_files(mock_fineos_s3_bucket, "DT2/dataexports/2020-01-02-11-30-00/2020-01-02-11-30-00-")
    add_s3_files(mock_fineos_s3_bucket, "DT2/dataexports/2020-01-03-11-30-00/2020-01-03-11-30-00-")
    add_s3_files(mock_fineos_s3_bucket, "DT2/dataexports/2020-01-04-11-30-00-")

    # add reference files for processed folders
    ReferenceFileFactory.create(
        file_location=os.path.join(
            get_s3_config().pfml_fineos_extract_archive_path,
            "processed",
            payments_util.get_date_group_folder_name(
                "2020-01-01-11-30-00", ReferenceFileType.FINEOS_PAYMENT_EXTRACT
            ),
        ),
        reference_file_type_id=ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id,
    )
    ReferenceFileFactory.create(
        file_location=os.path.join(
            get_s3_config().pfml_fineos_extract_archive_path,
            "processed",
            payments_util.get_date_group_folder_name(
                "2020-01-03-11-30-00", ReferenceFileType.FINEOS_PAYMENT_EXTRACT
            ),
        ),
        reference_file_type_id=ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id,
    )

    local_payment_extract_step.run()
    processed_folder = os.path.join(
        get_s3_config().pfml_fineos_extract_archive_path,
        payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
    )
    skipped_folder = os.path.join(
        get_s3_config().pfml_fineos_extract_archive_path,
        payments_util.Constants.S3_INBOUND_SKIPPED_DIR,
    )
    processed_files = file_util.list_files(processed_folder, recursive=True)
    skipped_files = file_util.list_files(skipped_folder, recursive=True)
    assert len(processed_files) == 4
    assert len(skipped_files) == 4

    expected_file_names = []
    for date_file in [
        "vpei.csv",
        "vpeipaymentdetails.csv",
        "vpeiclaimdetails.csv",
        "VBI_REQUESTEDABSENCE.csv",
    ]:
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
        local_test_db_session,
        extractor.expected_file_names,
        ReferenceFileType.FINEOS_PAYMENT_EXTRACT,
    )
    assert len(copied_files) == 0

    employee_log_count_after = local_test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == 0


def test_process_extract_data_no_existing_address_eft(
    mock_s3_bucket,
    set_exporter_env_vars,
    local_payment_extract_step,
    local_test_db_session,
    monkeypatch,
    local_create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    setup_process_tests(
        mock_s3_bucket, local_test_db_session, add_address=False, add_eft=False,
    )

    employee_log_count_before = local_test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 3

    local_payment_extract_step.run()

    for index in ["1", "2", "3"]:
        payment = (
            local_test_db_session.query(Payment)
            .filter(
                Payment.fineos_pei_c_value == "7326", Payment.fineos_pei_i_value == f"30{index}"
            )
            .first()
        )

        employee = payment.claim.employee
        assert employee

        mailing_address = payment.experian_address_pair.fineos_address
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

        state_log = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, local_test_db_session
        )

        pub_efts = employee.pub_efts.all()

        # Payment 2 uses CHECK over ACH, so some logic differs for it.
        if index == "2":
            assert not mailing_address.address_line_two

            assert payment.disb_method_id == PaymentMethod.CHECK.payment_method_id
            assert payment.pub_eft_id is None
            assert payment.has_eft_update is False
            assert len(pub_efts) == 0  # Not set by setup logic, shouldn't be set at all now
            assert state_log.outcome == EXPECTED_OUTCOME
            assert state_log.end_state_id == State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK.state_id

        else:
            assert mailing_address.address_line_two == f"AddressLine2-{index}"

            assert payment.disb_method_id == PaymentMethod.ACH.payment_method_id
            assert payment.pub_eft
            assert str(payment.pub_eft.routing_nbr) == index * 9
            assert str(payment.pub_eft.account_nbr) == index * 9
            assert (
                payment.pub_eft.bank_account_type_id
                == BankAccountType.CHECKING.bank_account_type_id
            )
            assert payment.pub_eft.prenote_state_id == PrenoteState.PENDING_PRE_PUB.prenote_state_id
            assert payment.has_eft_update is True

            assert len(pub_efts) == 1
            assert payment.pub_eft_id == pub_efts[0].pub_eft_id

            # The EFT info was new, so the payment is in an error state
            assert state_log.outcome == {
                "message": "Error processing payment record",
                "validation_container": {
                    "record_key": f"CiIndex(c='7326', i='30{index}')",
                    "validation_issues": [
                        {"reason": "EFTPending", "details": "New EFT info found, prenote required"}
                    ],
                },
            }
            assert (
                state_log.end_state_id
                == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE.state_id
            )

            # There is also a state log for the payment in the PEI writeback flow
            validate_pei_writeback_state_for_payment(
                payment, local_test_db_session, is_pending_prenote=True
            )

            # Verify that there is exactly one successful state log per employee that uses ACH
            state_logs = employee.state_logs
            assert len(state_logs) == 1
            state_log = state_logs[0]
            assert "Initiated DELEGATED_EFT flow for employee" in state_log.outcome["message"]
            assert state_log.end_state_id == State.DELEGATED_EFT_SEND_PRENOTE.state_id

    employee_log_count_after = local_test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_data_existing_payment(
    mock_s3_bucket,
    set_exporter_env_vars,
    local_payment_extract_step,
    local_test_db_session,
    monkeypatch,
    local_create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    setup_process_tests(
        mock_s3_bucket,
        local_test_db_session,
        add_payment=True,
        additional_payment_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE,
    )

    employee_log_count_before = local_test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 3

    local_payment_extract_step.run()

    for index in ["1", "2", "3"]:
        payments = (
            local_test_db_session.query(Payment)
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
                State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK.state_id,
                State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE.state_id,
            ]

    payment_count_after = local_test_db_session.query(Payment).count()
    assert payment_count_after == 6  # 3 payments each with an old record and a new one

    employee_log_count_after = local_test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_data_minimal_viable_payment(
    mock_s3_bucket,
    set_exporter_env_vars,
    local_payment_extract_step,
    local_test_db_session,
    tmp_path,
    monkeypatch,
    local_create_triggers,
):
    # This test creates a file with absolutely no data besides the bare
    # minimum to be viable to create a payment, this is done in order
    # to test that all of our validations work, and all of the missing data
    # edge cases are accounted for and handled appropriately. This shouldn't
    # ever be a real scenario, but might encompass small pieces of something real
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    employee_log_count_before = local_test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 0

    # C & I value are the bare minimum to have a payment
    fineos_data = FineosPaymentData(False, c_value="1000", i_value="1")
    upload_fineos_data(tmp_path, mock_s3_bucket, [fineos_data])
    # We deliberately do no DB setup, there will not be any prior employee or claim
    local_payment_extract_step.run()

    payment = local_test_db_session.query(Payment).one_or_none()
    assert payment
    assert payment.claim is None

    state_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert state_log.end_state_id == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id

    assert state_log.outcome["message"] == "Error processing payment record"
    assert state_log.outcome["validation_container"]["record_key"] == "CiIndex(c='1000', i='1')"
    # Not going to exactly match the errors here as there are many
    # and they may adjust in the future
    assert len(state_log.outcome["validation_container"]["validation_issues"]) >= 7

    # Payment is not added to the PEI writeback flow because we don't know the type of payment
    validate_pei_writeback_state_for_payment(payment, local_test_db_session, is_invalid=True)

    employee_log_count_after = local_test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_data_minimal_viable_standard_payment(
    mock_s3_bucket,
    set_exporter_env_vars,
    local_payment_extract_step,
    local_test_db_session,
    tmp_path,
    monkeypatch,
    local_create_triggers,
):
    # Same as the above test, but we setup enough to make a "standard" payment
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    employee_log_count_before = local_test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 0

    # C & I value are the bare minimum to have a payment
    fineos_data = FineosPaymentData(
        False, c_value="1000", i_value="1", event_type="PaymentOut", payment_amount="100.00"
    )
    upload_fineos_data(tmp_path, mock_s3_bucket, [fineos_data])
    # We deliberately do no DB setup, there will not be any prior employee or claim
    local_payment_extract_step.run()

    payment = local_test_db_session.query(Payment).one_or_none()
    assert payment
    assert payment.claim is None

    state_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert state_log.end_state_id == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id

    assert state_log.outcome["message"] == "Error processing payment record"
    assert state_log.outcome["validation_container"]["record_key"] == "CiIndex(c='1000', i='1')"
    # Not going to exactly match the errors here as there are many
    # and they may adjust in the future
    assert len(state_log.outcome["validation_container"]["validation_issues"]) >= 11

    # Payment is also added to the PEI writeback error flow
    validate_pei_writeback_state_for_payment(payment, local_test_db_session, is_invalid=True)

    employee_log_count_after = local_test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_data_leave_request_decision_validation(
    mock_s3_bucket,
    set_exporter_env_vars,
    local_payment_extract_step,
    local_test_db_session,
    local_initialize_factories_session,
    tmp_path,
    monkeypatch,
    local_create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    employee_log_count_before = local_test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 0

    medical_claim_type_record = FineosPaymentData(claim_type="Employee")
    approved_record = FineosPaymentData(leave_request_decision="Approved")
    pending_record = FineosPaymentData(leave_request_decision="Pending")
    in_review_record = FineosPaymentData(leave_request_decision="In Review")
    rejected_record = FineosPaymentData(leave_request_decision="Rejected")

    # setup both payments in DB
    add_db_records_from_fineos_data(local_test_db_session, approved_record)
    add_db_records_from_fineos_data(local_test_db_session, pending_record)
    add_db_records_from_fineos_data(local_test_db_session, in_review_record)
    add_db_records_from_fineos_data(local_test_db_session, rejected_record)
    add_db_records_from_fineos_data(local_test_db_session, medical_claim_type_record)

    upload_fineos_data(
        tmp_path,
        mock_s3_bucket,
        [
            approved_record,
            pending_record,
            in_review_record,
            rejected_record,
            medical_claim_type_record,
        ],
    )

    # We deliberately do no DB setup, there will not be any prior employee or claim
    local_payment_extract_step.run()

    approved_payment = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == approved_record.c_value,
            Payment.fineos_pei_i_value == approved_record.i_value,
        )
        .one_or_none()
    )
    assert approved_payment
    assert len(approved_payment.state_logs) == 1
    assert (
        approved_payment.state_logs[0].end_state_id
        == State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK.state_id
    )

    pending_payment = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == pending_record.c_value,
            Payment.fineos_pei_i_value == pending_record.i_value,
        )
        .one_or_none()
    )
    assert pending_payment
    assert len(pending_payment.state_logs) == 1
    assert (
        pending_payment.state_logs[0].end_state_id
        == State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK.state_id
    )

    in_review_payment = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == in_review_record.c_value,
            Payment.fineos_pei_i_value == in_review_record.i_value,
        )
        .one_or_none()
    )
    assert in_review_payment
    assert len(in_review_payment.state_logs) == 1
    assert (
        in_review_payment.state_logs[0].end_state_id
        == State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK.state_id
    )

    rejected_payment = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == rejected_record.c_value,
            Payment.fineos_pei_i_value == rejected_record.i_value,
        )
        .one_or_none()
    )
    assert rejected_payment
    assert len(rejected_payment.state_logs) == 2
    state_log = state_log_util.get_latest_state_log_in_flow(
        rejected_payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert state_log.end_state_id == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id
    validate_pei_writeback_state_for_payment(
        rejected_payment, local_test_db_session, is_invalid=True
    )

    medical_claim_type_record = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == medical_claim_type_record.c_value,
            Payment.fineos_pei_i_value == medical_claim_type_record.i_value,
        )
        .one_or_none()
    )

    assert medical_claim_type_record
    assert len(medical_claim_type_record.state_logs) == 1
    assert (
        medical_claim_type_record.state_logs[0].end_state_id
        == State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK.state_id
    )

    import_log_report = json.loads(rejected_payment.fineos_extract_import_log.report)
    assert import_log_report["not_pending_or_approved_leave_request_count"] == 1
    assert import_log_report["standard_valid_payment_count"] == 4


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_not_id_proofed(
    mock_s3_bucket,
    set_exporter_env_vars,
    local_test_db_session,
    local_payment_extract_step,
    tmp_path,
    local_initialize_factories_session,
    monkeypatch,
    local_create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    datasets = []
    # This tests that a payment with a claim missing ID proofing with be rejected

    standard_payment_data = FineosPaymentData()
    add_db_records_from_fineos_data(
        local_test_db_session, standard_payment_data, is_id_proofed=False
    )
    datasets.append(standard_payment_data)

    upload_fineos_data(tmp_path, mock_s3_bucket, datasets)

    # Run the extract process
    local_payment_extract_step.run()

    standard_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == standard_payment_data.i_value)
        .one_or_none()
    )
    state_log = state_log_util.get_latest_state_log_in_flow(
        standard_payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert (
        state_log.end_state_id
        == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE.state_id
    )

    issues = state_log.outcome["validation_container"]["validation_issues"]
    assert len(issues) == 1
    assert issues[0] == {
        "reason": "ClaimNotIdProofed",
        "details": f"Claim {standard_payment_data.absence_case_number} has not been ID proofed",
    }
    validate_pei_writeback_state_for_payment(
        standard_payment, local_test_db_session, is_issue_in_system=True
    )


def test_process_extract_is_adhoc(
    mock_s3_bucket,
    set_exporter_env_vars,
    local_payment_extract_step,
    local_test_db_session,
    local_initialize_factories_session,
    tmp_path,
    monkeypatch,
    local_create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    fineos_adhoc_data = FineosPaymentData(amalgamationc="Adhoc")
    add_db_records_from_fineos_data(local_test_db_session, fineos_adhoc_data)
    fineos_standard_data = FineosPaymentData(amalgamationc="Some other value")
    add_db_records_from_fineos_data(local_test_db_session, fineos_standard_data)

    upload_fineos_data(tmp_path, mock_s3_bucket, [fineos_adhoc_data, fineos_standard_data])

    local_payment_extract_step.run()

    # The adhoc payment should be valid and have that column set to True
    adhoc_payment = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == fineos_adhoc_data.c_value,
            Payment.fineos_pei_i_value == fineos_adhoc_data.i_value,
        )
        .one_or_none()
    )
    assert adhoc_payment.is_adhoc_payment
    assert len(adhoc_payment.state_logs) == 1
    assert (
        adhoc_payment.state_logs[0].end_state_id
        == State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK.state_id
    )

    # Any other value for that column will create a valid payment with the column False
    standard_payment = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == fineos_standard_data.c_value,
            Payment.fineos_pei_i_value == fineos_standard_data.i_value,
        )
        .one_or_none()
    )
    assert not standard_payment.is_adhoc_payment
    assert len(standard_payment.state_logs) == 1
    assert (
        standard_payment.state_logs[0].end_state_id
        == State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK.state_id
    )


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_additional_payment_types(
    mock_s3_bucket,
    set_exporter_env_vars,
    local_test_db_session,
    local_payment_extract_step,
    tmp_path,
    local_initialize_factories_session,
    monkeypatch,
    local_create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    datasets = []
    # This tests that the behavior of non-standard payment types are handled properly
    # All of these are setup as EFT payments, but we won't create EFT information for them
    # or reject them for not being prenoted yet.

    # Create a zero dollar payment
    zero_dollar_data = FineosPaymentData(
        payment_amount="0.00", payment_method="Elec Funds Transfer"
    )
    add_db_records_from_fineos_data(local_test_db_session, zero_dollar_data)
    datasets.append(zero_dollar_data)

    # Create an overpayment
    # note that the event reason for an overpayment is Unknown which is treated as
    # None in our approach, setting it here to make sure that doesn't cause a validation issue.
    overpayment_data = FineosPaymentData(
        event_type="Overpayment", event_reason="Unknown", payment_method="Elec Funds Transfer"
    )

    add_db_records_from_fineos_data(local_test_db_session, overpayment_data)
    datasets.append(overpayment_data)

    # Create a cancellation
    cancellation_data = FineosPaymentData(
        event_type="PaymentOut Cancellation",
        payment_amount="-123.45",
        payment_method="Elec Funds Transfer",
    )
    add_db_records_from_fineos_data(local_test_db_session, cancellation_data)
    datasets.append(cancellation_data)

    # Unknown - negative payment amount, but PaymentOut
    negative_payment_out_data = FineosPaymentData(
        event_type="PaymentOut", payment_amount="-100.00", payment_method="Elec Funds Transfer"
    )
    add_db_records_from_fineos_data(local_test_db_session, negative_payment_out_data)
    datasets.append(negative_payment_out_data)

    # Unknown - missing payment amount
    no_payment_out_data = FineosPaymentData(
        payment_amount=None, payment_method="Elec Funds Transfer"
    )
    add_db_records_from_fineos_data(local_test_db_session, no_payment_out_data)
    datasets.append(no_payment_out_data)

    # Unknown - missing event type
    missing_event_payment_out_data = FineosPaymentData(
        event_type=None, payment_method="Elec Funds Transfer"
    )
    add_db_records_from_fineos_data(local_test_db_session, missing_event_payment_out_data)
    datasets.append(missing_event_payment_out_data)

    # Create a record for an employer reimbursement
    employer_reimbursement_data = FineosPaymentData(
        event_reason=extractor.AUTO_ALT_EVENT_REASON,
        event_type=extractor.PAYMENT_OUT_TRANSACTION_TYPE,
        payee_identifier=extractor.TAX_IDENTIFICATION_NUMBER,
        payment_method="Elec Funds Transfer",
    )
    add_db_records_from_fineos_data(local_test_db_session, employer_reimbursement_data)
    datasets.append(employer_reimbursement_data)

    upload_fineos_data(tmp_path, mock_s3_bucket, datasets)

    # Run the extract process
    local_payment_extract_step.run()

    # No PUB EFT records should exist
    assert len(local_test_db_session.query(PubEft).all()) == 0

    # Zero dollar payment should be in DELEGATED_PAYMENT_PROCESSED_ZERO_PAYMENT
    zero_dollar_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == zero_dollar_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        zero_dollar_payment, State.DELEGATED_PAYMENT_PROCESSED_ZERO_PAYMENT
    )

    # Overpayment should be in DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT
    overpayment_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == overpayment_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        overpayment_payment, State.DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT
    )

    # ACH Cancellation should be in DELEGATED_PAYMENT_PROCESSED_CANCELLATION
    cancellation_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == cancellation_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        cancellation_payment, State.DELEGATED_PAYMENT_PROCESSED_CANCELLATION
    )

    # Negative payment will cause an unknown transaction type which is restartable
    # DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE and
    # DELEGATED_ADD_TO_FINEOS_WRITEBACK
    negative_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == negative_payment_out_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        negative_payment, State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE
    )

    # No payment amount means the payment needs to be updated, so we error
    # the payment and add it to two states.
    # DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT and
    # DELEGATED_ADD_TO_FINEOS_WRITEBACK
    no_amount_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == no_payment_out_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        no_amount_payment, State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT
    )

    # No event type means the payment needs to be updated, so we error
    # the payment and add it to two states.
    # DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT and
    # DELEGATED_ADD_TO_FINEOS_WRITEBACK
    missing_event_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == missing_event_payment_out_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        missing_event_payment, State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT
    )

    # Employer reimbursement should be in DELEGATED_PAYMENT_PROCESSED_EMPLOYER_REIMBURSEMENT
    employer_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == employer_reimbursement_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        employer_payment, State.DELEGATED_PAYMENT_PROCESSED_EMPLOYER_REIMBURSEMENT
    )


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_additional_payment_types_can_be_missing_other_files(
    mock_s3_bucket,
    set_exporter_env_vars,
    local_test_db_session,
    local_payment_extract_step,
    tmp_path,
    local_initialize_factories_session,
    monkeypatch,
    local_create_triggers,
):
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    # This tests that the behavior of non-standard payment types are handled properly
    # In every scenario, only the VPEI file contains information for the records, and it will
    # fail to find anything in the other files. For non-standard payments, this will not
    # error them, and they will be moved to their respective success states, albeit without
    # finding a claim to attach to, and with several pieces of information missing. It is however
    # enough for our purposes of creating reports and sending them in a writeback.
    datasets = []

    # Create a zero dollar payment
    zero_dollar_data = FineosPaymentData(
        payment_amount="0.00",
        payment_method="Elec Funds Transfer",
        include_claim_details=False,
        include_payment_details=False,
        include_requested_absence=False,
    )
    add_db_records_from_fineos_data(local_test_db_session, zero_dollar_data)
    datasets.append(zero_dollar_data)

    # Create an overpayment
    # note that the event reason for an overpayment is Unknown which is treated as
    # None in our approach, setting it here to make sure that doesn't cause a validation issue.
    overpayment_data = FineosPaymentData(
        event_type="Overpayment Adjustment",
        event_reason="Unknown",
        payment_method="Elec Funds Transfer",
        include_claim_details=False,
        include_payment_details=False,
        include_requested_absence=False,
    )
    add_db_records_from_fineos_data(local_test_db_session, overpayment_data)
    datasets.append(overpayment_data)

    # Create a cancellation
    cancellation_data = FineosPaymentData(
        event_type="PaymentOut Cancellation",
        payment_amount="-123.45",
        payment_method="Elec Funds Transfer",
        include_claim_details=False,
        include_payment_details=False,
        include_requested_absence=False,
    )
    add_db_records_from_fineos_data(local_test_db_session, cancellation_data)
    datasets.append(cancellation_data)

    # Create a record for an employer reimbursement
    employer_reimbursement_data = FineosPaymentData(
        event_reason=extractor.AUTO_ALT_EVENT_REASON,
        event_type=extractor.PAYMENT_OUT_TRANSACTION_TYPE,
        payee_identifier=extractor.TAX_IDENTIFICATION_NUMBER,
        payment_method="Elec Funds Transfer",
        include_claim_details=False,
        include_payment_details=False,
        include_requested_absence=False,
    )
    add_db_records_from_fineos_data(local_test_db_session, employer_reimbursement_data)
    datasets.append(employer_reimbursement_data)

    upload_fineos_data(tmp_path, mock_s3_bucket, datasets)

    # Run the extract process
    local_payment_extract_step.run()

    # No PUB EFT records should exist
    assert len(local_test_db_session.query(PubEft).all()) == 0

    # Zero dollar payment should be in DELEGATED_PAYMENT_PROCESSED_ZERO_PAYMENT
    zero_dollar_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == zero_dollar_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        zero_dollar_payment, State.DELEGATED_PAYMENT_PROCESSED_ZERO_PAYMENT
    )
    assert zero_dollar_payment.claim_id is None

    # Overpayment should be in DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT
    overpayment_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == overpayment_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        overpayment_payment, State.DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT
    )
    assert overpayment_payment.claim_id is None

    # ACH Cancellation should be in DELEGATED_PAYMENT_PROCESSED_CANCELLATION
    cancellation_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == cancellation_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        cancellation_payment, State.DELEGATED_PAYMENT_PROCESSED_CANCELLATION
    )
    assert cancellation_payment.claim_id is None

    # Employer reimbursement should be in DELEGATED_PAYMENT_PROCESSED_EMPLOYER_REIMBURSEMENT
    employer_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == employer_reimbursement_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        employer_payment, State.DELEGATED_PAYMENT_PROCESSED_EMPLOYER_REIMBURSEMENT
    )
    assert employer_payment.claim_id is None


def make_payment_data_from_fineos_data(fineos_data):
    extract_data = extractor.ExtractData(extractor.expected_file_names, "2020-01-01-11-30-00")
    ci_index = extractor.CiIndex(fineos_data.c_value, fineos_data.i_value)

    extract_data.pei.indexed_data = {ci_index: fineos_data.get_vpei_record()}
    extract_data.payment_details.indexed_data = {
        ci_index: [fineos_data.get_payment_details_record()]
    }
    extract_data.claim_details.indexed_data = {ci_index: fineos_data.get_claim_details_record()}
    extract_data.requested_absence.indexed_data = {
        extractor.CiIndex(
            fineos_data.leave_request_id, ""
        ): fineos_data.get_requested_absence_record()
    }

    return (
        ci_index,
        extractor.PaymentData(extract_data, ci_index, extract_data.pei.indexed_data.get(ci_index)),
    )


def test_validation_missing_fields(initialize_factories_session, set_exporter_env_vars):
    # This test is specifically aimed at verifying we check for required parameters

    # Create a fineos dataset that only contains C/I values with all other values empty
    # We want to make sure "" and Unknown are treated the same, so set a few to Unknown
    fineos_data = FineosPaymentData(
        False,
        c_value="1000",
        i_value="1",
        leave_request_id="1001",
        leave_request_decision="Unknown",
        payment_amount="Unknown",
    )
    ci_index, payment_data = make_payment_data_from_fineos_data(fineos_data)

    validation_container = payment_data.validation_container
    assert validation_container.record_key == str(ci_index)
    expected_missing_values = set(
        [
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEESOCNUMBE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTDATE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "AMOUNT_MONAMT"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "EVENTTYPE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEEIDENTIFI"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCEREASON_COVERAGE"),
            ValidationIssue(
                ValidationReason.UNEXPECTED_PAYMENT_TRANSACTION_TYPE,
                "Unknown payment scenario encountered. Payment Amount: None, Event Type: None, Event Reason: ",
            ),
        ]
    )
    assert expected_missing_values == set(validation_container.validation_issues)

    # Set the event type to PaymentOut and give it a valid amount so that
    # it expects it to be a valid payment that requires payment method and several
    # payment detail and claim detail related fields
    fineos_data.event_type = "PaymentOut"
    fineos_data.payment_amount = "100.00"
    ci_index, payment_data = make_payment_data_from_fineos_data(fineos_data)

    validation_container = payment_data.validation_container
    assert validation_container.record_key == str(ci_index)
    expected_missing_values = set(
        [
            ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCECASENU"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "LEAVEREQUEST_DECISION"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEESOCNUMBE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTSTARTP"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTENDPER"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTDATE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTMETHOD"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEEIDENTIFI"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCEREASON_COVERAGE"),
        ]
    )
    assert expected_missing_values == set(validation_container.validation_issues)

    # Set the payment method to Check and verify it additionally adds errors for those missing
    fineos_data.payment_method = "Check"
    ci_index, payment_data = make_payment_data_from_fineos_data(fineos_data)

    validation_container = payment_data.validation_container
    assert validation_container.record_key == str(ci_index)
    expected_missing_values = set(
        [
            ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCECASENU"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "LEAVEREQUEST_DECISION"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEESOCNUMBE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTSTARTP"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTENDPER"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTDATE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEEIDENTIFI"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTADD1"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTADD4"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTADD6"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTPOSTCO"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCEREASON_COVERAGE"),
        ]
    )
    assert expected_missing_values == set(validation_container.validation_issues)

    # Set the payment method to EFT and verify it additionally adds errors for those missing
    fineos_data.payment_method = "Elec Funds Transfer"
    ci_index, payment_data = make_payment_data_from_fineos_data(fineos_data)

    validation_container = payment_data.validation_container
    assert validation_container.record_key == str(ci_index)
    expected_missing_values = set(
        [
            ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCECASENU"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "LEAVEREQUEST_DECISION"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEESOCNUMBE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTSTARTP"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTENDPER"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTDATE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEEIDENTIFI"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEEBANKSORT"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEEACCOUNTN"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEEACCOUNTT"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCEREASON_COVERAGE"),
        ]
    )

    assert expected_missing_values == set(validation_container.validation_issues)


def test_validation_param_length(initialize_factories_session, set_exporter_env_vars):
    # Create a fineos dataset that is generated with happy values, but override
    # ones we want to test the length.

    # Routing number too short
    fineos_data = FineosPaymentData(payment_method="Elec Funds Transfer", routing_nbr="123")
    ci_index, payment_data = make_payment_data_from_fineos_data(fineos_data)
    assert set([ValidationIssue(ValidationReason.FIELD_TOO_SHORT, "PAYEEBANKSORT: 123")]) == set(
        payment_data.validation_container.validation_issues
    )

    # Routing/account number too long
    long_num = "1" * 50
    fineos_data = FineosPaymentData(
        payment_method="Elec Funds Transfer", routing_nbr=long_num, account_nbr=long_num
    )
    ci_index, payment_data = make_payment_data_from_fineos_data(fineos_data)
    assert set(
        [
            ValidationIssue(ValidationReason.FIELD_TOO_LONG, f"PAYEEBANKSORT: {long_num}"),
            ValidationIssue(ValidationReason.FIELD_TOO_LONG, f"PAYEEACCOUNTN: {long_num}"),
        ]
    ) == set(payment_data.validation_container.validation_issues)

    # ZIP too short + formatted incorrectly
    fineos_data = FineosPaymentData(payment_method="Check", zip_code="123")
    ci_index, payment_data = make_payment_data_from_fineos_data(fineos_data)
    assert set(
        [
            ValidationIssue(ValidationReason.FIELD_TOO_SHORT, "PAYMENTPOSTCO: 123"),
            ValidationIssue(ValidationReason.INVALID_VALUE, "PAYMENTPOSTCO: 123"),
        ]
    ) == set(payment_data.validation_container.validation_issues)

    # ZIP too long + formatted incorrectly
    fineos_data = FineosPaymentData(payment_method="Check", zip_code="1234567890123456")
    ci_index, payment_data = make_payment_data_from_fineos_data(fineos_data)
    assert set(
        [
            ValidationIssue(ValidationReason.FIELD_TOO_LONG, "PAYMENTPOSTCO: 1234567890123456"),
            ValidationIssue(ValidationReason.INVALID_VALUE, "PAYMENTPOSTCO: 1234567890123456"),
        ]
    ) == set(payment_data.validation_container.validation_issues)


def test_validation_lookup_validators(initialize_factories_session, set_exporter_env_vars):
    # Create a fineos dataset that is generated with happy values, but override
    # ones we want to test the lookup validators.

    # Verify payment method lookup validator
    fineos_data = FineosPaymentData(payment_method="Gold")
    ci_index, payment_data = make_payment_data_from_fineos_data(fineos_data)
    assert set(
        [ValidationIssue(ValidationReason.INVALID_LOOKUP_VALUE, "PAYMENTMETHOD: Gold")]
    ) == set(payment_data.validation_container.validation_issues)

    # Verify account type lookup validator
    fineos_data = FineosPaymentData(payment_method="Elec Funds Transfer", account_type="Vault")
    ci_index, payment_data = make_payment_data_from_fineos_data(fineos_data)
    assert set(
        [ValidationIssue(ValidationReason.INVALID_LOOKUP_VALUE, "PAYEEACCOUNTT: Vault")]
    ) == set(payment_data.validation_container.validation_issues)

    # Verify state lookup validator
    fineos_data = FineosPaymentData(payment_method="Check", state="NotAState")
    ci_index, payment_data = make_payment_data_from_fineos_data(fineos_data)
    assert set(
        [ValidationIssue(ValidationReason.INVALID_LOOKUP_VALUE, "PAYMENTADD6: NotAState")]
    ) == set(payment_data.validation_container.validation_issues)


def test_validation_payment_amount(initialize_factories_session, set_exporter_env_vars):
    # When doing validation, we verify that payment amount
    # must be a numeric value
    invalid_payment_amounts = ["words", "300-00", "400.xx", "-----5"]

    for invalid_payment_amount in invalid_payment_amounts:
        fineos_data = FineosPaymentData(payment_amount=invalid_payment_amount)
        ci_index, payment_data = make_payment_data_from_fineos_data(fineos_data)
        assert set(
            [
                ValidationIssue(
                    ValidationReason.INVALID_VALUE, f"AMOUNT_MONAMT: {invalid_payment_amount}"
                ),
                ValidationIssue(
                    ValidationReason.UNEXPECTED_PAYMENT_TRANSACTION_TYPE,
                    "Unknown payment scenario encountered. Payment Amount: None, Event Type: PaymentOut, Event Reason: Automatic Main Payment",
                ),
            ]
        ) == set(payment_data.validation_container.validation_issues)


def test_validation_zip_code(initialize_factories_session, set_exporter_env_vars):
    # When doing validation, we verify that payment amount
    # must be a numeric value
    invalid_zips = ["abcde", "1234567", "-12345", "12345-000"]

    for invalid_zip in invalid_zips:
        fineos_data = FineosPaymentData(payment_method="Check", zip_code=invalid_zip)
        ci_index, payment_data = make_payment_data_from_fineos_data(fineos_data)
        assert set(
            [ValidationIssue(ValidationReason.INVALID_VALUE, f"PAYMENTPOSTCO: {invalid_zip}")]
        ) == set(payment_data.validation_container.validation_issues)


def test_get_payment_transaction_type(initialize_factories_session, set_exporter_env_vars):
    # get_payment_transaction_type is called as part of the constructor
    # and sets payment_transaction_type accordingly.

    # note the defaults for FineosPaymentData make a standard payment
    standard_data = FineosPaymentData()
    _, payment_data = make_payment_data_from_fineos_data(standard_data)
    assert not payment_data.validation_container.has_validation_issues()
    assert (
        payment_data.payment_transaction_type.payment_transaction_type_id
        == PaymentTransactionType.STANDARD.payment_transaction_type_id
    )

    # Zero Dollar Payment
    zero_dollar_data = FineosPaymentData(payment_amount="0.00")
    _, payment_data = make_payment_data_from_fineos_data(zero_dollar_data)
    assert not payment_data.validation_container.has_validation_issues()
    assert (
        payment_data.payment_transaction_type.payment_transaction_type_id
        == PaymentTransactionType.ZERO_DOLLAR.payment_transaction_type_id
    )

    # Employer Reimbursement
    employer_reimbursement_data = FineosPaymentData(
        event_reason=extractor.AUTO_ALT_EVENT_REASON,
        event_type=extractor.PAYMENT_OUT_TRANSACTION_TYPE,
        payee_identifier=extractor.TAX_IDENTIFICATION_NUMBER,
    )
    _, payment_data = make_payment_data_from_fineos_data(employer_reimbursement_data)
    assert not payment_data.validation_container.has_validation_issues()
    assert (
        payment_data.payment_transaction_type.payment_transaction_type_id
        == PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id
    )

    # There are multiple values that can create an overpayment
    for overpayment_event_type in extractor.OVERPAYMENT_PAYMENT_TRANSACTION_TYPES:
        # Event reason is always unknown for overpayments in the real data
        overpayment_data = FineosPaymentData(
            event_type=overpayment_event_type, event_reason="Unknown"
        )
        _, payment_data = make_payment_data_from_fineos_data(overpayment_data)
        assert not payment_data.validation_container.has_validation_issues()
        assert (
            payment_data.payment_transaction_type.payment_transaction_type_id
            == PaymentTransactionType.OVERPAYMENT.payment_transaction_type_id
        )

    # Cancellation payment
    cancellation_data = FineosPaymentData(
        event_type="PaymentOut Cancellation", payment_amount="-100.00"
    )
    _, payment_data = make_payment_data_from_fineos_data(cancellation_data)
    assert not payment_data.validation_container.has_validation_issues()
    assert (
        payment_data.payment_transaction_type.payment_transaction_type_id
        == PaymentTransactionType.CANCELLATION.payment_transaction_type_id
    )

    ### Various unknown scenarios
    # Can't be a negative payment when event_type=PaymentOut (the default)
    negative_payment_data = FineosPaymentData(payment_amount="-100.00")
    # Event type is always used if payment amount is not 0
    unknown_event_type_data = FineosPaymentData(event_type="Yet another overpayment event type")
    # A payment missing everything
    bare_minimum_payment_data = FineosPaymentData(False, c_value="1000", i_value="1")

    for unknown_data in [negative_payment_data, unknown_event_type_data, bare_minimum_payment_data]:
        _, payment_data = make_payment_data_from_fineos_data(unknown_data)
        assert payment_data.validation_container.has_validation_issues()
        assert (
            payments_util.ValidationReason.UNEXPECTED_PAYMENT_TRANSACTION_TYPE
            in payment_data.validation_container.get_reasons()
        )
        assert (
            payment_data.payment_transaction_type.payment_transaction_type_id
            == PaymentTransactionType.UNKNOWN.payment_transaction_type_id
        )


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_update_eft_existing_eft_matches_and_approved(
    local_payment_extract_step,
    local_test_db_session,
    mock_s3_bucket,
    set_exporter_env_vars,
    monkeypatch,
):
    # This is the happiest of paths, we've already got the EFT info for the
    # employee and it has already been prenoted.

    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    setup_process_tests(mock_s3_bucket, local_test_db_session, add_eft=False)

    # Set an employee to have the same EFT we know is going to be extracted
    employee = (
        local_test_db_session.query(Employee)
        .join(TaxIdentifier)
        .filter(TaxIdentifier.tax_identifier == "1" * 9)
        .first()
    )
    assert employee is not None
    # Create the EFT record
    pub_eft_record = PubEftFactory.create(
        prenote_state_id=PrenoteState.APPROVED.prenote_state_id,
        routing_nbr="1" * 9,
        account_nbr="1" * 9,
        bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
    )
    EmployeePubEftPairFactory.create(employee=employee, pub_eft=pub_eft_record)

    # Run the process
    local_payment_extract_step.run()

    # Verify the payment isn't marked as having an EFT update
    payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_c_value == "7326", Payment.fineos_pei_i_value == "301")
        .first()
    )
    assert payment is not None
    assert payment.has_eft_update is False
    # The payment should still be connected to the EFT record
    assert payment.pub_eft_id == pub_eft_record.pub_eft_id

    state_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert state_log.end_state_id == State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK.state_id

    # There should not be a DELEGATED_EFT_SEND_PRENOTE record
    employee_state_logs_after = (
        local_test_db_session.query(StateLog)
        .filter(StateLog.employee_id == employee.employee_id)
        .all()
    )
    assert len(employee_state_logs_after) == 0


@pytest.mark.parametrize(
    "prenote_state",
    [(PrenoteState.REJECTED), (PrenoteState.PENDING_PRE_PUB), (PrenoteState.PENDING_WITH_PUB)],
)
@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_update_eft_existing_eft_matches_and_not_approved(
    local_payment_extract_step,
    local_test_db_session,
    mock_s3_bucket,
    set_exporter_env_vars,
    monkeypatch,
    prenote_state,
):
    # This is the happiest of paths, we've already got the EFT info for the
    # employee and it has already been prenoted.

    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    setup_process_tests(mock_s3_bucket, local_test_db_session, add_eft=False)

    # Set an employee to have the same EFT we know is going to be extracted
    employee = (
        local_test_db_session.query(Employee)
        .join(TaxIdentifier)
        .filter(TaxIdentifier.tax_identifier == "1" * 9)
        .first()
    )
    assert employee is not None
    # Create the EFT record
    pub_eft_record = PubEftFactory.create(
        prenote_state_id=prenote_state.prenote_state_id,
        routing_nbr="1" * 9,
        account_nbr="1" * 9,
        prenote_sent_at=get_now(),
        bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
    )
    EmployeePubEftPairFactory.create(employee=employee, pub_eft=pub_eft_record)

    # Run the process
    local_payment_extract_step.run()

    # Verify the payment isn't marked as having an EFT update
    payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_c_value == "7326", Payment.fineos_pei_i_value == "301")
        .first()
    )
    assert payment is not None
    assert payment.has_eft_update is False
    # The payment should still be connected to the EFT record
    assert payment.pub_eft_id == pub_eft_record.pub_eft_id

    state_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )

    # Pending prenotes get put into a restartable error state
    if prenote_state.prenote_state_id in [
        PrenoteState.PENDING_PRE_PUB.prenote_state_id,
        PrenoteState.PENDING_WITH_PUB.prenote_state_id,
    ]:
        assert (
            state_log.end_state_id
            == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE.state_id
        )
    else:
        assert (
            state_log.end_state_id == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id
        )
    issues = state_log.outcome["validation_container"]["validation_issues"]
    assert len(issues) == 1
    assert (
        issues[0]["details"]
        == f"EFT prenote has not been approved, is currently in state [{prenote_state.prenote_state_description}]"
    )

    # Payment is also added to the PEI writeback error flow
    validate_pei_writeback_state_for_payment(
        payment,
        local_test_db_session,
        is_rejected_prenote=prenote_state.prenote_state_id
        == PrenoteState.REJECTED.prenote_state_id,
        is_pending_prenote=prenote_state.prenote_state_id
        in [
            PrenoteState.PENDING_PRE_PUB.prenote_state_id,
            PrenoteState.PENDING_WITH_PUB.prenote_state_id,
        ],
    )

    # There should not be a DELEGATED_EFT_SEND_PRENOTE record
    employee_state_logs_after = (
        local_test_db_session.query(StateLog)
        .filter(StateLog.employee_id == employee.employee_id)
        .all()
    )
    assert len(employee_state_logs_after) == 0


def test_update_eft_existing_eft_matches_and_pending_with_pub(
    local_payment_extract_step,
    local_test_db_session,
    mock_s3_bucket,
    set_exporter_env_vars,
    monkeypatch,
):
    # This is the happiest of paths, we've already got the EFT info for the
    # employee and it has already been prenoted.

    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    setup_process_tests(mock_s3_bucket, local_test_db_session, add_eft=False)

    # Set an employee to have the same EFT we know is going to be extracted
    employee = (
        local_test_db_session.query(Employee)
        .join(TaxIdentifier)
        .filter(TaxIdentifier.tax_identifier == "1" * 9)
        .first()
    )
    assert employee is not None
    # Create the EFT record
    pub_eft_record = PubEftFactory.create(
        prenote_state_id=PrenoteState.PENDING_WITH_PUB.prenote_state_id,
        routing_nbr="1" * 9,
        account_nbr="1" * 9,
        prenote_sent_at=get_now() - timedelta(PRENOTE_PRENDING_WAITING_PERIOD),
        bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
    )
    EmployeePubEftPairFactory.create(employee=employee, pub_eft=pub_eft_record)

    # Run the process
    local_payment_extract_step.run()

    # Verify the payment isn't marked as having an EFT update
    payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_c_value == "7326", Payment.fineos_pei_i_value == "301")
        .first()
    )
    assert payment is not None
    assert payment.has_eft_update is False
    # The payment should still be connected to the EFT record
    assert payment.pub_eft_id == pub_eft_record.pub_eft_id

    state_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert state_log.end_state_id == State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK.state_id

    import_log_report = json.loads(payment.fineos_extract_import_log.report)
    assert import_log_report["prenote_past_waiting_period_approved_count"] == 1

    # The payment should now be approved
    assert pub_eft_record.prenote_state_id == PrenoteState.APPROVED.prenote_state_id
    assert pub_eft_record.prenote_approved_at is not None

    # There should not be a DELEGATED_EFT_SEND_PRENOTE record
    employee_state_logs_after = (
        local_test_db_session.query(StateLog)
        .filter(StateLog.employee_id == employee.employee_id)
        .all()
    )
    assert len(employee_state_logs_after) == 0


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_update_experian_address_pair_fineos_address_no_update(
    local_payment_extract_step,
    local_test_db_session,
    mock_s3_bucket,
    set_exporter_env_vars,
    monkeypatch,
):
    # update_experian_address_pair_fineos_address() has 2 possible outcomes:
    #   1. There is no change to address
    #   2. We create a new ExperianAddressPair
    # In this test, we cover #1. #2 is covered by other tests.

    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    setup_process_tests(mock_s3_bucket, local_test_db_session)

    # Set an employee to have the same address we know is going to be extracted
    employee = (
        local_test_db_session.query(Employee)
        .join(TaxIdentifier)
        .filter(TaxIdentifier.tax_identifier == "1" * 9)
        .first()
    )
    assert employee is not None

    # Add the expected address to another payment associated with the employee
    claim = ClaimFactory.create(employee=employee)
    address_pair = ExperianAddressPairFactory(
        fineos_address=AddressFactory.create(
            address_line_one="AddressLine1-1",
            address_line_two="AddressLine2-1",
            city="City1",
            geo_state_id=GeoState.MA.geo_state_id,
            zip_code="11111",
        )
    )
    payment = PaymentFactory.create(claim=claim, experian_address_pair=address_pair)
    local_test_db_session.commit()

    # Run the process
    local_payment_extract_step.run()
    local_test_db_session.expire_all()

    # Verify the payment isn't marked as having an address update
    payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_c_value == "7326", Payment.fineos_pei_i_value == "301")
        .first()
    )
    assert payment is not None
    assert payment.has_address_update is False


def test_extract_to_staging_tables(payment_extract_step, test_db_session, tmp_path):
    date_str = "2020-12-21-19-20-42"
    test_file_name1 = "vpei.csv"
    test_file_name2 = "vpeiclaimdetails.csv"
    test_file_name3 = "vpeipaymentdetails.csv"
    test_file_name4 = "VBI_REQUESTEDABSENCE.csv"

    test_file_path1 = os.path.join(os.path.dirname(__file__), f"test_files/{test_file_name1}")
    test_file_path2 = os.path.join(os.path.dirname(__file__), f"test_files/{test_file_name2}")
    test_file_path3 = os.path.join(os.path.dirname(__file__), f"test_files/{test_file_name3}")
    test_file_path4 = os.path.join(os.path.dirname(__file__), f"test_files/{test_file_name4}")

    test_file_names = [test_file_path1, test_file_path2, test_file_path3, test_file_path4]

    extract_data = extractor.ExtractData(test_file_names, date_str)
    payment_extract_step.download_and_extract_data(extract_data, tmp_path)

    test_db_session.commit()

    pei_data = test_db_session.query(FineosExtractVpei).all()
    claim_details_data = test_db_session.query(FineosExtractVpeiClaimDetails).all()
    payment_details_data = test_db_session.query(FineosExtractVpeiPaymentDetails).all()
    requested_absence_data = test_db_session.query(FineosExtractVbiRequestedAbsence).all()

    assert len(pei_data) == 3
    assert len(claim_details_data) == 3
    assert len(payment_details_data) == 3
    assert len(requested_absence_data) == 3

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

    for data in requested_absence_data:
        assert data.reference_file_id == ref_file.reference_file_id
        assert data.fineos_extract_import_log_id == payment_extract_step.get_import_log_id()


def test_get_active_payment_state(payment_extract_step, test_db_session):
    non_restartable_states = [
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
        State.DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_CHECK,
        State.PAYMENT_FAILED_ADDRESS_VALIDATION,
    ]
    restartable_states = payments_util.Constants.RESTARTABLE_PAYMENT_STATES

    # Non restartable states should return the state.
    for non_restartable_state in non_restartable_states:
        # Create and load a payment in the non restartable state.
        payment = PaymentFactory.create()
        state_log_util.create_finished_state_log(
            payment, non_restartable_state, EXPECTED_OUTCOME, test_db_session
        )

        # Create a payment with the same C/I value
        new_payment = PaymentFactory.build(
            fineos_pei_c_value=payment.fineos_pei_c_value,
            fineos_pei_i_value=payment.fineos_pei_i_value,
        )

        # We should find that state associated with the payment
        found_state = payment_extract_step.get_active_payment_state(new_payment)
        assert found_state
        assert found_state.state_id == non_restartable_state.state_id

    for restartable_state in restartable_states:
        # Create and load a payment in the restartable state.
        payment = PaymentFactory.create()
        state_log_util.create_finished_state_log(
            payment, restartable_state, EXPECTED_OUTCOME, test_db_session
        )

        # Create a payment with the same C/I value
        new_payment = PaymentFactory.build(
            fineos_pei_c_value=payment.fineos_pei_c_value,
            fineos_pei_i_value=payment.fineos_pei_i_value,
        )
        # We should not find anything
        found_state = payment_extract_step.get_active_payment_state(new_payment)
        assert found_state is None
