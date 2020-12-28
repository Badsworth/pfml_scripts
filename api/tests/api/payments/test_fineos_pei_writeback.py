import dataclasses
import os
from datetime import date

import faker
from freezegun import freeze_time

import massgov.pfml.payments.fineos_pei_writeback as writeback
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import PaymentReferenceFile, ReferenceFile, ReferenceFileType
from massgov.pfml.db.models.factories import ClaimFactory, EmployerFactory, PaymentFactory


def generate_payment(test_db_session, absence_id, extraction_date=None):
    employer = EmployerFactory.create()
    claim = ClaimFactory.create(employer_id=employer.employer_id, fineos_absence_id=absence_id)
    if not extraction_date:
        fake = faker.Faker()
        extraction_date = fake.date_object()
    return PaymentFactory.create(
        claim=claim,
        fineos_pei_c_value="123",
        fineos_pei_i_value="456",
        fineos_extraction_date=extraction_date,
    )


@freeze_time("2020-12-21 12:00:01", tz_offset=5)
def test_upload_writebacks_to_s3(
    test_db_session, set_exporter_env_vars, initialize_factories_session
):
    payment_a = generate_payment(test_db_session, absence_id="NTN-01-ABS-01")
    payment_b = generate_payment(test_db_session, absence_id="NTN-01-ABS-02")
    payments = [payment_a, payment_b]

    uploaded_filepath = writeback.upload_writeback_csv(test_db_session, payments)

    expected_file_name = "2020-12-21-12-00-01-pei_writeback.csv"
    expected_file_location = os.path.join(
        payments_util.get_s3_config().pfml_fineos_outbound_path, "sent", expected_file_name
    )
    assert expected_file_location == uploaded_filepath

    # Confirm that file is in PFML S3 bucket
    saved_files = file_util.list_files(
        os.path.join(payments_util.get_s3_config().pfml_fineos_outbound_path, "sent")
    )
    assert len(saved_files) == 1
    assert set(saved_files) == set([expected_file_name])

    # Also confirm that file is in FINEOS S3 bucket
    saved_files = file_util.list_files(f"{payments_util.get_s3_config().fineos_data_import_path}")
    assert len(saved_files) == 1
    assert set(saved_files) == set([expected_file_name])


def test_save_writeback_reference_files(
    test_db_session, set_exporter_env_vars, initialize_factories_session
):
    s3_filepath = os.path.join(
        payments_util.get_s3_config().pfml_fineos_outbound_path,
        "sent",
        "2020-12-21-12-00-01-pei_writeback.csv",
    )
    payment_a = generate_payment(test_db_session, absence_id="NTN-01-ABS-03")
    payment_b = generate_payment(test_db_session, absence_id="NTN-01-ABS-04")
    payments = [payment_a, payment_b]

    writeback.write_to_s3_and_save_reference_files(payments, test_db_session, s3_filepath)
    assert test_db_session.query(ReferenceFile).count() == 1
    saved_ref_file = test_db_session.query(ReferenceFile).first()
    assert (
        saved_ref_file.reference_file_type_id
        == ReferenceFileType.PEI_WRITEBACK.reference_file_type_id
    )

    assert test_db_session.query(PaymentReferenceFile).count() == 2
    first_payment_ref = test_db_session.query(PaymentReferenceFile).first()
    assert first_payment_ref.reference_file_id == saved_ref_file.reference_file_id
    assert first_payment_ref.payment_id == payments[0].payment_id

    second_payment_ref = test_db_session.query(PaymentReferenceFile).all()[1]
    assert second_payment_ref.reference_file_id == saved_ref_file.reference_file_id
    assert second_payment_ref.payment_id == payments[1].payment_id


@freeze_time("2020-12-21 12:00:01", tz_offset=5)
def test_pei_writeback_to_s3(test_db_session, set_exporter_env_vars, initialize_factories_session):
    payment_a = generate_payment(
        test_db_session, absence_id="NTN-01-ABS-05", extraction_date=date(2020, 12, 23)
    )
    payment_b = generate_payment(
        test_db_session, absence_id="NTN-01-ABS-06", extraction_date=date(2020, 12, 22)
    )
    payments = [payment_a, payment_b]

    uploaded_filepath = writeback.upload_writeback_csv(test_db_session, payments)

    lines = list(file_util.read_file_lines(uploaded_filepath))
    assert lines[0] == ",".join([f.name for f in dataclasses.fields(writeback.PeiWritebackRecord)])
    assert lines[1] == "123,456,Active,,,,12/23/2020,,Pending,"
    assert lines[2] == "123,456,Active,,,,12/22/2020,,Pending,"

    file_name = "2020-12-21-12-00-01-pei_writeback.csv"
    fineos_filepath = os.path.join(payments_util.get_s3_config().fineos_data_import_path, file_name)
    lines = list(file_util.read_file_lines(fineos_filepath))
    assert lines[0] == ",".join([f.name for f in dataclasses.fields(writeback.PeiWritebackRecord)])
    assert lines[1] == "123,456,Active,,,,12/23/2020,,Pending,"
    assert lines[2] == "123,456,Active,,,,12/22/2020,,Pending,"
