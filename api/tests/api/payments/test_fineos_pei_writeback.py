import dataclasses
import logging  # noqa: B1
import os
from datetime import date, timedelta

import faker
import pytest
from freezegun import freeze_time
from sqlalchemy import func

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.config as payments_config
import massgov.pfml.payments.fineos_pei_writeback as writeback
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.csv as csv_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    PaymentMethod,
    PaymentReferenceFile,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import PaymentFactory
from tests.helpers.state_log import AdditionalParams, setup_state_log

# every test in here requires real resources
pytestmark = pytest.mark.integration

fake = faker.Faker()

PENDING_WRITEBACK_EXTRACTION_DATE = date.today() - timedelta(days=fake.random_int())

DISBURSED_WRITEBACK_EXTRACTION_DATE = date.today() - timedelta(days=fake.random_int())
DISBURSED_WRITEBACK_TRANS_STATUS_DATE = DISBURSED_WRITEBACK_EXTRACTION_DATE + timedelta(days=1)
DISBURSED_WRITEBACK_TRANSACTION_STATUS_DESCRIPTION = (
    f"Distributed {PaymentMethod.ACH.payment_method_description}"
)

# Random 3 digit integer as string
PAYMENT_PEI_C_VALUE = str(fake.random_int(min=100, max=999))
PAYMENT_PEI_I_VALUE = str(fake.random_int(min=100, max=999))

# Random 4 digit integer as string
DISBURSED_WRITEBACK_RECORD_PEI_C_VALUE = str(fake.random_int(min=1000, max=9999))
DISBURSED_WRITEBACK_RECORD_PEI_I_VALUE = str(fake.random_int(min=1000, max=9999))
EXTRACTED_WRITEBACK_RECORD_PEI_C_VALUE = str(fake.random_int(min=1000, max=9999))
EXTRACTED_WRITEBACK_RECORD_PEI_I_VALUE = str(fake.random_int(min=1000, max=9999))
WRITEBACK_RECORD_STOCK_NUMBER = str(fake.random_int(min=1000, max=9999))


def generate_extracted_payment(test_db_session):
    payment = PaymentFactory.create(
        fineos_pei_c_value=EXTRACTED_WRITEBACK_RECORD_PEI_C_VALUE,
        fineos_pei_i_value=EXTRACTED_WRITEBACK_RECORD_PEI_I_VALUE,
        fineos_extraction_date=PENDING_WRITEBACK_EXTRACTION_DATE,
        has_address_update=True,
    )
    setup_state_log(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_states=[State.MARK_AS_EXTRACTED_IN_FINEOS],
        test_db_session=test_db_session,
        additional_params=AdditionalParams(payment=payment),
    )
    return payment


def generate_disbursed_payment(test_db_session):
    payment = PaymentFactory.create(
        fineos_pei_c_value=DISBURSED_WRITEBACK_RECORD_PEI_C_VALUE,
        fineos_pei_i_value=DISBURSED_WRITEBACK_RECORD_PEI_I_VALUE,
        fineos_extraction_date=DISBURSED_WRITEBACK_EXTRACTION_DATE,
        disb_method_id=PaymentMethod.ACH.payment_method_id,
        disb_check_eft_number=WRITEBACK_RECORD_STOCK_NUMBER,
        disb_check_eft_issue_date=DISBURSED_WRITEBACK_TRANS_STATUS_DATE,
    )
    setup_state_log(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_states=[State.SEND_PAYMENT_DETAILS_TO_FINEOS],
        test_db_session=test_db_session,
        additional_params=AdditionalParams(payment=payment),
    )
    return payment


def generate_extracted_writeback_record(test_db_session):
    return writeback.PeiWritebackRecord(
        pei_C_value=EXTRACTED_WRITEBACK_RECORD_PEI_C_VALUE,
        pei_I_value=EXTRACTED_WRITEBACK_RECORD_PEI_I_VALUE,
        status=writeback.ACTIVE_WRITEBACK_RECORD_STATUS,
        extractionDate=PENDING_WRITEBACK_EXTRACTION_DATE,
        transactionStatus=writeback.PENDING_WRITEBACK_RECORD_TRANSACTION_STATUS,
    )


def generate_disbursed_writeback_record(test_db_session):
    return writeback.PeiWritebackRecord(
        pei_C_value=DISBURSED_WRITEBACK_RECORD_PEI_C_VALUE,
        pei_I_value=DISBURSED_WRITEBACK_RECORD_PEI_I_VALUE,
        status=writeback.ACTIVE_WRITEBACK_RECORD_STATUS,
        extractionDate=DISBURSED_WRITEBACK_EXTRACTION_DATE,
        stockNo=WRITEBACK_RECORD_STOCK_NUMBER,
        transStatusDate=DISBURSED_WRITEBACK_TRANS_STATUS_DATE,
        transactionStatus=DISBURSED_WRITEBACK_TRANSACTION_STATUS_DESCRIPTION,
    )


def test_get_records_to_writeback(test_db_session, initialize_factories_session):
    extracted_payment_1 = generate_extracted_payment(test_db_session)
    disbursed_payment_1 = generate_disbursed_payment(test_db_session)

    pei_writeback_items = writeback.get_records_to_writeback(test_db_session)
    assert len(pei_writeback_items) == 2

    payments = [item.payment for item in pei_writeback_items]
    records = [item.writeback_record for item in pei_writeback_items]

    assert payments[0].payment_id == extracted_payment_1.payment_id
    assert payments[0] == extracted_payment_1
    assert records[0] == writeback.PeiWritebackRecord(
        pei_C_value=extracted_payment_1.fineos_pei_c_value,
        pei_I_value=extracted_payment_1.fineos_pei_i_value,
        status=writeback.ACTIVE_WRITEBACK_RECORD_STATUS,
        extractionDate=extracted_payment_1.fineos_extraction_date,
        transactionStatus=writeback.PENDING_WRITEBACK_RECORD_TRANSACTION_STATUS,
    )

    assert payments[1].payment_id == disbursed_payment_1.payment_id
    assert payments[1] == disbursed_payment_1
    assert records[1] == writeback.PeiWritebackRecord(
        pei_C_value=disbursed_payment_1.fineos_pei_c_value,
        pei_I_value=disbursed_payment_1.fineos_pei_i_value,
        status=writeback.ACTIVE_WRITEBACK_RECORD_STATUS,
        extractionDate=disbursed_payment_1.fineos_extraction_date,
        stockNo=disbursed_payment_1.disb_check_eft_number,
        transStatusDate=disbursed_payment_1.disb_check_eft_issue_date,
        transactionStatus=f"Distributed {disbursed_payment_1.disb_method.payment_method_description}",
    )


def test_get_records_both_payments_missing_fields(test_db_session, initialize_factories_session):
    extracted_payment_1 = generate_extracted_payment(test_db_session)
    extracted_payment_1.fineos_extraction_date = None
    test_db_session.add(extracted_payment_1)
    test_db_session.commit()

    disbursed_payment_1 = generate_disbursed_payment(test_db_session)
    disbursed_payment_1.disb_check_eft_issue_date = None
    disbursed_payment_1.disb_check_eft_number = None
    test_db_session.add(disbursed_payment_1)
    test_db_session.commit()

    pei_writeback_items = writeback.get_records_to_writeback(test_db_session)
    assert len(pei_writeback_items) == 0


def test_get_records_one_payment_missing_fields(test_db_session, initialize_factories_session):
    extracted_payment_1 = generate_extracted_payment(test_db_session)

    disbursed_payment_1 = generate_disbursed_payment(test_db_session)
    disbursed_payment_1.disb_check_eft_issue_date = None
    disbursed_payment_1.disb_check_eft_number = None
    test_db_session.add(disbursed_payment_1)
    test_db_session.commit()

    disbursed_payment_2 = generate_disbursed_payment(test_db_session)

    pei_writeback_items = writeback.get_records_to_writeback(test_db_session)
    assert len(pei_writeback_items) == 2

    payments = [item.payment for item in pei_writeback_items]
    records = [item.writeback_record for item in pei_writeback_items]

    assert payments[0] == extracted_payment_1
    assert records[0] == writeback.PeiWritebackRecord(
        pei_C_value=extracted_payment_1.fineos_pei_c_value,
        pei_I_value=extracted_payment_1.fineos_pei_i_value,
        status=writeback.ACTIVE_WRITEBACK_RECORD_STATUS,
        extractionDate=extracted_payment_1.fineos_extraction_date,
        transactionStatus=writeback.PENDING_WRITEBACK_RECORD_TRANSACTION_STATUS,
    )

    assert payments[1] == disbursed_payment_2
    assert records[1] == writeback.PeiWritebackRecord(
        pei_C_value=disbursed_payment_2.fineos_pei_c_value,
        pei_I_value=disbursed_payment_2.fineos_pei_i_value,
        status=writeback.ACTIVE_WRITEBACK_RECORD_STATUS,
        extractionDate=disbursed_payment_2.fineos_extraction_date,
        stockNo=disbursed_payment_2.disb_check_eft_number,
        transStatusDate=disbursed_payment_2.disb_check_eft_issue_date,
        transactionStatus=f"Distributed {disbursed_payment_2.disb_method.payment_method_description}",
    )


def test_extracted_payment_missing_fields(test_db_session, initialize_factories_session):
    extracted_payment = generate_extracted_payment(test_db_session)
    extracted_payment.fineos_pei_c_value = None
    extracted_payment.fineos_pei_i_value = None
    extracted_payment.fineos_extraction_date = None

    with pytest.raises(
        Exception,
        match=f"Payment {extracted_payment.payment_id} cannot be converted to PeiWritebackRecord for extracted payments because it is missing fields.",
    ):
        writeback._extracted_payment_to_pei_writeback_record(extracted_payment)


def test_disbursed_payment_missing_fields(test_db_session, initialize_factories_session):
    disbursed_payment = generate_extracted_payment(test_db_session)
    disbursed_payment.fineos_extraction_date = None
    disbursed_payment.disb_check_eft_number = None
    disbursed_payment.disb_check_eft_issue_date = None

    with pytest.raises(
        Exception,
        match=f"Payment {disbursed_payment.payment_id} cannot be converted to PeiWritebackRecord for disbursed payments because it is missing fields.",
    ):
        writeback._disbursed_payment_to_pei_writeback_record(disbursed_payment)


def test_return_early_from_process_payments_for_writeback_if_no_records(test_db_session, caplog):
    caplog.set_level(logging.INFO)  # noqa: B1
    writeback.process_payments_for_writeback(test_db_session)
    assert "No payment records for PEI writeback. Exiting early." in caplog.text


@pytest.mark.parametrize(
    "payment_count", ((0), (1), (fake.random_int(min=2, max=10)),), ids=["zero", "one", "many"],
)
def test_create_db_records_for_payments(
    local_test_db_session,
    local_test_db_other_session,
    local_initialize_factories_session,
    payment_count,
):
    pei_writeback_items = []
    for _i in range(payment_count):
        payment = generate_disbursed_payment(local_test_db_session)
        writeback_record = writeback._disbursed_payment_to_pei_writeback_record(payment)

        pei_writeback_items.append(
            writeback.PeiWritebackItem(
                payment=payment,
                writeback_record=writeback_record,
                prior_state=State.SEND_PAYMENT_DETAILS_TO_FINEOS,
                end_state=State.PAYMENT_COMPLETE,
                encoded_row=csv_util.encode_row(
                    writeback_record, writeback.PEI_WRITEBACK_CSV_ENCODERS
                ),
            )
        )

    reference_file = ReferenceFile(
        file_location="s3://some-test-bucket/path/to/file.txt",
        reference_file_type_id=ReferenceFileType.PEI_WRITEBACK.reference_file_type_id,
    )
    local_test_db_session.add(reference_file)

    writeback._create_db_records_for_payments(
        pei_writeback_items, local_test_db_session, reference_file
    )

    # Assert that no records are saved to the database before we commit the changes.
    assert (
        local_test_db_other_session.query(func.count(PaymentReferenceFile.payment_id)).scalar() == 0
    )

    # Assert that we've saved the records to the database after committing changes.
    local_test_db_session.commit()
    assert (
        local_test_db_other_session.query(func.count(PaymentReferenceFile.payment_id)).scalar()
        == payment_count
    )
    assert (
        len(
            local_test_db_other_session.query(StateLog)
            .filter(StateLog.end_state == State.PAYMENT_COMPLETE)
            .all()
        )
        == payment_count
    )


def test_write_rows_to_s3_file(
    test_db_session, set_exporter_env_vars, initialize_factories_session
):
    rows = [
        csv_util.encode_row(
            generate_disbursed_writeback_record(test_db_session),
            writeback.PEI_WRITEBACK_CSV_ENCODERS,
        ),
        csv_util.encode_row(
            generate_extracted_writeback_record(test_db_session),
            writeback.PEI_WRITEBACK_CSV_ENCODERS,
        ),
    ]

    # Confirm content in the PFML FINEOS sent bucket
    s3_dest = os.path.join(
        payments_config.get_s3_config().pfml_fineos_outbound_path,
        payments_util.Constants.S3_OUTBOUND_SENT_DIR,
    )
    writeback._write_rows_to_s3_file(rows, s3_dest)
    lines = list(file_util.read_file_lines(s3_dest))
    assert lines[0] == ",".join([f.name for f in dataclasses.fields(writeback.PeiWritebackRecord)])
    assert lines[1] == "{},{},{},,,{},{},,{},{}".format(
        DISBURSED_WRITEBACK_RECORD_PEI_C_VALUE,
        DISBURSED_WRITEBACK_RECORD_PEI_I_VALUE,
        writeback.ACTIVE_WRITEBACK_RECORD_STATUS,
        WRITEBACK_RECORD_STOCK_NUMBER,
        DISBURSED_WRITEBACK_EXTRACTION_DATE.strftime("%m/%d/%Y"),
        DISBURSED_WRITEBACK_TRANSACTION_STATUS_DESCRIPTION,
        DISBURSED_WRITEBACK_TRANS_STATUS_DATE.strftime("%m/%d/%Y"),
    )
    assert lines[2] == "{},{},{},,,,{},,{},".format(
        EXTRACTED_WRITEBACK_RECORD_PEI_C_VALUE,
        EXTRACTED_WRITEBACK_RECORD_PEI_I_VALUE,
        writeback.ACTIVE_WRITEBACK_RECORD_STATUS,
        PENDING_WRITEBACK_EXTRACTION_DATE.strftime("%m/%d/%Y"),
        writeback.PENDING_WRITEBACK_RECORD_TRANSACTION_STATUS,
    )


def test_save_writeback_reference_files(
    test_db_session, set_exporter_env_vars, initialize_factories_session
):
    payments = [
        generate_disbursed_payment(test_db_session),
        generate_extracted_payment(test_db_session),
    ]

    extracted_payment_state_logs_before = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=State.CONFIRM_VENDOR_STATUS_IN_MMARS,
        db_session=test_db_session,
    )
    assert len(extracted_payment_state_logs_before) == 0
    employee_state_logs_before = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.IDENTIFY_MMARS_STATUS,
        db_session=test_db_session,
    )
    assert len(employee_state_logs_before) == 0

    disbursed_payment_state_logs_before = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=State.PAYMENT_COMPLETE,
        db_session=test_db_session,
    )
    assert len(disbursed_payment_state_logs_before) == 0

    reference_file_state_logs_before = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.REFERENCE_FILE,
        end_state=State.SEND_PEI_WRITEBACK,
        db_session=test_db_session,
    )
    assert len(reference_file_state_logs_before) == 0

    writeback.process_payments_for_writeback(test_db_session)

    # Confirm ReferenceFile is created correctly
    assert test_db_session.query(ReferenceFile).count() == 1
    saved_ref_file = test_db_session.query(ReferenceFile).first()
    assert (
        saved_ref_file.reference_file_type_id
        == ReferenceFileType.PEI_WRITEBACK.reference_file_type_id
    )

    # Confirm StateLogs are created for each payment.
    extracted_payment_state_logs_after = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=State.CONFIRM_VENDOR_STATUS_IN_MMARS,
        db_session=test_db_session,
    )
    assert len(extracted_payment_state_logs_after) == 1
    employee_state_logs_after = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.IDENTIFY_MMARS_STATUS,
        db_session=test_db_session,
    )
    assert len(employee_state_logs_after) == 1

    disbursed_payment_state_logs_after = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=State.PAYMENT_COMPLETE,
        db_session=test_db_session,
    )
    assert len(disbursed_payment_state_logs_after) == 1

    # Confirm both PaymentReferenceFiles are created correctly
    payment_ids = [payment.payment_id for payment in payments]
    assert test_db_session.query(PaymentReferenceFile).count() == len(payments)
    for payment_ref_file in test_db_session.query(PaymentReferenceFile).all():
        assert payment_ref_file.reference_file_id == saved_ref_file.reference_file_id
        assert payment_ref_file.payment_id in payment_ids


# Freeze time because the file name includes seconds and this test may run over a second boundary.
@freeze_time()
def test_writeback_files_uploaded_to_s3(
    test_db_session, set_exporter_env_vars, initialize_factories_session
):
    pei_writeback_items = []

    disbursed_payment = generate_disbursed_payment(test_db_session)
    disbursed_payment_writeback_record = writeback._disbursed_payment_to_pei_writeback_record(
        disbursed_payment
    )
    pei_writeback_items.append(
        writeback.PeiWritebackItem(
            payment=disbursed_payment,
            writeback_record=disbursed_payment_writeback_record,
            prior_state=State.SEND_PAYMENT_DETAILS_TO_FINEOS,
            end_state=State.PAYMENT_COMPLETE,
            encoded_row=csv_util.encode_row(
                disbursed_payment_writeback_record, writeback.PEI_WRITEBACK_CSV_ENCODERS
            ),
        )
    )

    extracted_payment = generate_extracted_payment(test_db_session)
    extracted_payment_writeback_record = writeback._extracted_payment_to_pei_writeback_record(
        extracted_payment
    )
    pei_writeback_items.append(
        writeback.PeiWritebackItem(
            payment=extracted_payment,
            writeback_record=extracted_payment_writeback_record,
            prior_state=State.MARK_AS_EXTRACTED_IN_FINEOS,
            end_state=State.CONFIRM_VENDOR_STATUS_IN_MMARS,
            encoded_row=csv_util.encode_row(
                extracted_payment_writeback_record, writeback.PEI_WRITEBACK_CSV_ENCODERS
            ),
        )
    )

    writeback.upload_writeback_csv_and_save_reference_files(test_db_session, pei_writeback_items)

    now = payments_util.get_now()
    expected_file_name = now.strftime("%Y-%m-%d-%H-%M-%S-pei_writeback.csv")

    # Confirm that file is in PFML S3 bucket
    saved_files = file_util.list_files(
        os.path.join(
            payments_config.get_s3_config().pfml_fineos_outbound_path,
            payments_util.Constants.S3_OUTBOUND_SENT_DIR,
        )
    )
    assert len(saved_files) == 1
    assert set(saved_files) == set([expected_file_name])

    # Also confirm that file is in FINEOS S3 bucket
    saved_files = file_util.list_files(f"{payments_config.get_s3_config().fineos_data_import_path}")
    assert len(saved_files) == 1
    assert set(saved_files) == set([expected_file_name])

    # Confirm content in the FINEOS data import bucket
    fineos_filepath = os.path.join(
        payments_config.get_s3_config().fineos_data_import_path, expected_file_name
    )
    lines = list(file_util.read_file_lines(fineos_filepath))
    assert lines[0] == ",".join([f.name for f in dataclasses.fields(writeback.PeiWritebackRecord)])
    assert lines[1] == "{},{},{},,,{},{},,{},{}".format(
        DISBURSED_WRITEBACK_RECORD_PEI_C_VALUE,
        DISBURSED_WRITEBACK_RECORD_PEI_I_VALUE,
        writeback.ACTIVE_WRITEBACK_RECORD_STATUS,
        WRITEBACK_RECORD_STOCK_NUMBER,
        DISBURSED_WRITEBACK_EXTRACTION_DATE.strftime("%m/%d/%Y"),
        DISBURSED_WRITEBACK_TRANSACTION_STATUS_DESCRIPTION,
        DISBURSED_WRITEBACK_TRANS_STATUS_DATE.strftime("%m/%d/%Y"),
    )
    assert lines[2] == "{},{},{},,,,{},,{},".format(
        EXTRACTED_WRITEBACK_RECORD_PEI_C_VALUE,
        EXTRACTED_WRITEBACK_RECORD_PEI_I_VALUE,
        writeback.ACTIVE_WRITEBACK_RECORD_STATUS,
        PENDING_WRITEBACK_EXTRACTION_DATE.strftime("%m/%d/%Y"),
        writeback.PENDING_WRITEBACK_RECORD_TRANSACTION_STATUS,
    )


def test_after_vendor_check_initiated_no_updates(
    test_db_session, initialize_factories_session, caplog
):
    # Create a payment associated with an employee with a StateLog in a non-restartable state.
    payment = generate_extracted_payment(test_db_session)
    payment.has_address_update = False
    payment.has_eft_update = False
    state_log_util.create_finished_state_log(
        associated_model=payment.claim.employee,
        end_state=State.ADD_TO_VCM_REPORT,
        outcome=state_log_util.build_outcome(
            "Start Vendor Check flow after receiving payment in payment extract"
        ),
        db_session=test_db_session,
    )
    test_db_session.commit()

    employee_state_logs_before = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.ADD_TO_VCM_REPORT,
        db_session=test_db_session,
    )
    assert len(employee_state_logs_before) == 1

    caplog.set_level(logging.INFO)  # noqa: B1
    writeback._after_vendor_check_initiated(payment, test_db_session)
    assert (
        f"Payment (C: {payment.fineos_pei_c_value}, I: {payment.fineos_pei_i_value}) has no address or EFT updates. Not initiating VENDOR_CHECK flow."
        in caplog.text
    )

    employee_state_logs_after = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.ADD_TO_VCM_REPORT,
        db_session=test_db_session,
    )
    assert len(employee_state_logs_before) == len(employee_state_logs_after)
