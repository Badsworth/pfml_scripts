import dataclasses
import os
from datetime import date

from freezegun import freeze_time
from pytest import raises

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.config as payments_config
import massgov.pfml.payments.fineos_pei_writeback as writeback
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    PaymentMethod,
    PaymentReferenceFile,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.db.models.factories import PaymentFactory
from tests.helpers.state_log import AdditionalParams, setup_state_log


def generate_extracted_payment(test_db_session):
    payment = PaymentFactory.create(
        fineos_pei_c_value="123", fineos_pei_i_value="456", fineos_extraction_date=date(2021, 1, 7)
    )
    setup_state_log(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        start_states=[State.PAYMENT_EXPORT_ERROR_REPORT_SENT],
        end_states=[State.MARK_AS_EXTRACTED_IN_FINEOS],
        test_db_session=test_db_session,
        additional_params=AdditionalParams(payment=payment),
    )
    return payment


def generate_disbursed_payment(test_db_session):
    payment = PaymentFactory.create(
        fineos_pei_c_value="123",
        fineos_pei_i_value="456",
        fineos_extraction_date=date(2021, 1, 7),
        disb_method_id=PaymentMethod.CHECK.payment_method_id,
        disb_check_eft_number="11111",
        disb_check_eft_issue_date=date(2021, 1, 6),
    )
    setup_state_log(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        start_states=[State.PAYMENT_COMPLETE],
        end_states=[State.SEND_PAYMENT_DETAILS_TO_FINEOS],
        test_db_session=test_db_session,
        additional_params=AdditionalParams(payment=payment),
    )
    return payment


def generate_extracted_writeback_record(test_db_session):
    return writeback.PeiWritebackRecord(
        pei_C_value="1234",
        pei_I_value="4567",
        status="Active",
        extractionDate=date(2021, 1, 7),
        transactionStatus="Pending",
    )


def generate_disbursed_writeback_record(test_db_session):
    return writeback.PeiWritebackRecord(
        pei_C_value="1234",
        pei_I_value="4567",
        status="Active",
        extractionDate=date(2020, 1, 12),
        stockNo="5452",
        transStatusDate=date(2020, 1, 13),
        transactionStatus=f"Distributed {PaymentMethod.ACH.payment_method_description}",
    )


def test_get_records_to_writeback(test_db_session, initialize_factories_session):
    extracted_payment_1 = generate_extracted_payment(test_db_session)
    disbursed_payment_1 = generate_disbursed_payment(test_db_session)

    payments, records = writeback.get_records_to_writeback(test_db_session)
    assert len(records) == 2
    assert payments[0].payment_id == extracted_payment_1.payment_id
    assert payments[0] == extracted_payment_1
    assert records[0] == writeback.PeiWritebackRecord(
        pei_C_value=extracted_payment_1.fineos_pei_c_value,
        pei_I_value=extracted_payment_1.fineos_pei_i_value,
        status="Active",
        extractionDate=extracted_payment_1.fineos_extraction_date,
        transactionStatus="Pending",
    )

    assert payments[1].payment_id == disbursed_payment_1.payment_id
    assert payments[1] == disbursed_payment_1
    assert records[1] == writeback.PeiWritebackRecord(
        pei_C_value=disbursed_payment_1.fineos_pei_c_value,
        pei_I_value=disbursed_payment_1.fineos_pei_i_value,
        status="Active",
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

    payments, records = writeback.get_records_to_writeback(test_db_session)
    assert len(records) == 0
    assert len(payments) == 0


def test_get_records_one_payment_missing_fields(test_db_session, initialize_factories_session):
    extracted_payment_1 = generate_extracted_payment(test_db_session)

    disbursed_payment_1 = generate_disbursed_payment(test_db_session)
    disbursed_payment_1.disb_check_eft_issue_date = None
    disbursed_payment_1.disb_check_eft_number = None
    test_db_session.add(disbursed_payment_1)
    test_db_session.commit()

    disbursed_payment_2 = generate_disbursed_payment(test_db_session)

    payments, records = writeback.get_records_to_writeback(test_db_session)
    assert len(payments) == 2
    assert len(records) == 2

    assert payments[0] == extracted_payment_1
    assert records[0] == writeback.PeiWritebackRecord(
        pei_C_value=extracted_payment_1.fineos_pei_c_value,
        pei_I_value=extracted_payment_1.fineos_pei_i_value,
        status="Active",
        extractionDate=extracted_payment_1.fineos_extraction_date,
        transactionStatus="Pending",
    )

    assert payments[1] == disbursed_payment_2
    assert records[1] == writeback.PeiWritebackRecord(
        pei_C_value=disbursed_payment_2.fineos_pei_c_value,
        pei_I_value=disbursed_payment_2.fineos_pei_i_value,
        status="Active",
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

    with raises(
        Exception,
        match=f"Payment {extracted_payment.payment_id} cannot be converted to PeiWritebackRecord for extracted payments because it is missing fields.",
    ):
        writeback._extracted_payment_to_pei_writeback_record(extracted_payment)


def test_disbursed_payment_missing_fields(test_db_session, initialize_factories_session):
    disbursed_payment = generate_extracted_payment(test_db_session)
    disbursed_payment.fineos_extraction_date = None
    disbursed_payment.disb_check_eft_number = None
    disbursed_payment.disb_check_eft_issue_date = None

    with raises(
        Exception,
        match=f"Payment {disbursed_payment.payment_id} cannot be converted to PeiWritebackRecord for disbursed payments because it is missing fields.",
    ):
        writeback._disbursed_payment_to_pei_writeback_record(disbursed_payment)


@freeze_time("2020-12-21 12:00:01", tz_offset=5)
def test_writing_writeback_csv_in_s3(
    test_db_session, set_exporter_env_vars, initialize_factories_session
):
    records = [
        generate_disbursed_writeback_record(test_db_session),
        generate_extracted_writeback_record(test_db_session),
    ]

    # Confirm content in the PFML FINEOS sent bucket
    s3_dest = os.path.join(
        payments_config.get_s3_config().pfml_fineos_outbound_path,
        payments_util.Constants.S3_OUTBOUND_SENT_DIR,
    )
    writeback.write_to_s3(records, test_db_session, s3_dest)
    lines = list(file_util.read_file_lines(s3_dest))
    assert lines[0] == ",".join([f.name for f in dataclasses.fields(writeback.PeiWritebackRecord)])
    assert (
        lines[1] == "1234,4567,Active,,,5452,01/12/2020,,Distributed Elec Funds Transfer,01/13/2020"
    )
    assert lines[2] == "1234,4567,Active,,,,01/07/2021,,Pending,"


def test_save_writeback_reference_files(
    test_db_session, set_exporter_env_vars, initialize_factories_session
):
    s3_filepath = os.path.join(
        payments_config.get_s3_config().pfml_fineos_outbound_path,
        "ready",
        "2020-12-21-12-00-01-pei_writeback.csv",
    )
    payments = [
        generate_disbursed_payment(test_db_session),
        generate_extracted_payment(test_db_session),
    ]

    writeback.save_reference_files(payments, test_db_session, s3_filepath)

    # Confirm ReferenceFile is created correctly
    assert test_db_session.query(ReferenceFile).count() == 1
    saved_ref_file = test_db_session.query(ReferenceFile).first()
    assert (
        saved_ref_file.reference_file_type_id
        == ReferenceFileType.PEI_WRITEBACK.reference_file_type_id
    )

    # Confirm both PaymentReferenceFiles are created correctly
    assert test_db_session.query(PaymentReferenceFile).count() == 2
    first_payment_ref = test_db_session.query(PaymentReferenceFile).first()
    assert first_payment_ref.reference_file_id == saved_ref_file.reference_file_id
    assert first_payment_ref.payment_id == payments[0].payment_id

    second_payment_ref = test_db_session.query(PaymentReferenceFile).all()[1]
    assert second_payment_ref.reference_file_id == saved_ref_file.reference_file_id
    assert second_payment_ref.payment_id == payments[1].payment_id


@freeze_time("2020-12-21 12:00:01", tz_offset=5)
def test_writeback_files_uploaded_to_s3(
    test_db_session, set_exporter_env_vars, initialize_factories_session
):
    writeback_records = [
        generate_disbursed_writeback_record(test_db_session),
        generate_extracted_writeback_record(test_db_session),
    ]
    payments = [
        generate_disbursed_payment(test_db_session),
        generate_extracted_payment(test_db_session),
    ]

    writeback.upload_writeback_csv_and_save_reference_files(
        test_db_session, writeback_records, payments
    )

    expected_file_name = "2020-12-21-12-00-01-pei_writeback.csv"

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
    assert (
        lines[1] == "1234,4567,Active,,,5452,01/12/2020,,Distributed Elec Funds Transfer,01/13/2020"
    )
    assert lines[2] == "1234,4567,Active,,,,01/07/2021,,Pending,"
