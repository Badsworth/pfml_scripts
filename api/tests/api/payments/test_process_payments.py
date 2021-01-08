import os

import massgov.pfml.payments.config as payments_config
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import Employee, Employer, Payment, ReferenceFileType
from massgov.pfml.payments.mock.fineos_extract_generator import GenerateConfig, generate
from massgov.pfml.payments.process_payments import _fineos_process

# == E2E Tests ==


def test_fineos_process(
    test_db_session, mock_fineos_s3_bucket, set_exporter_env_vars, initialize_factories_session
):
    # Setup the data
    # generate_fineos_payment_export_files(test_db_session, mock_fineos_s3_bucket)
    s3_config = payments_config.get_s3_config()
    fineos_data_export_path = s3_config.fineos_data_export_path

    config = GenerateConfig(folder_path=fineos_data_export_path, employee_count=10)
    generate(test_db_session, config)

    mock_fineos_export_files = file_util.list_files(fineos_data_export_path)
    assert len(mock_fineos_export_files) == 6

    # Run the process
    _fineos_process(test_db_session)

    # fetch relevant db models
    employees = test_db_session.query(Employee).all()
    employers = test_db_session.query(Employer).all()
    payments = test_db_session.query(Payment).all()

    # top level assersions
    assert len(employees) == 10
    assert len(employers) == 10
    assert len(payments) == 6

    date_group_str = payments_util.get_date_group_str_from_path(mock_fineos_export_files[0])
    processed_payment_folder_path = os.path.join(
        payments_config.get_s3_config().pfml_fineos_inbound_path,
        payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
        payments_util.get_date_group_folder_name(date_group_str, ReferenceFileType.PAYMENT_EXTRACT),
    )
    processed_payment_files = file_util.list_files_without_folder(processed_payment_folder_path)
    assert len(processed_payment_files) == 3

    processed_vendor_folder_path = os.path.join(
        payments_config.get_s3_config().pfml_fineos_inbound_path,
        payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
        payments_util.get_date_group_folder_name(
            date_group_str, ReferenceFileType.VENDOR_CLAIM_EXTRACT
        ),
    )
    processed_vendor_files = file_util.list_files_without_folder(processed_vendor_folder_path)
    assert len(processed_vendor_files) == 3

    # 1. Validate State Log

    # 1.1 Employee Vendor Export (TODO once API-896 is done)

    # Valid Employees w/ payment method == CHECK => "Identify MMARS status"
    # Valid Employees w/ payment method == EFT => "EFT request received"

    # Invalid Employees w/ state log entry => "Vendor export error report sent"

    # Invalid Employees w/o state log entry => no state log entry

    # 1.2 Employee Payments Export (TODO once state logs are added in API-1018)

    # Successful Payments => "Confirm vendor status in MMARS"
    # Employees with Successful Payments => "Identify MMARS status"

    # Invalid Payments w/ state log entry => "Payment export error report sent"
    # Employee with Invalid Payments w/ state log entry => no state log entry

    # Invalid Payments w/o state log entry => no state log entry
    # Employee with Invalid Payments w/o state log entry => no state log entry

    # 1.3 Unassociated employees (TODO once state logs are added in API-1018)

    # Employees not in the vendor or payments export => no state log entry

    # 2. Validate PEI writeback (TODO)
    pei_writeback_folder_path = os.path.join(
        s3_config.pfml_fineos_outbound_path, payments_util.Constants.S3_OUTBOUND_SENT_DIR
    )
    pei_writeback_files = file_util.list_files(pei_writeback_folder_path)
    assert len(pei_writeback_files) == 1

    # Validate PEI file contents
    # pei_writeback_file_path = os.path.join(pei_writeback_folder_path, pei_writeback_files[0])
    # pei_writeback_csv_contents = file_util.read_file(pei_writeback_file_path)
    # peri_writeback_csv_fieldnames = list(map(lambda f: f.name, dataclasses.fields(PeiWritebackRecord)))
    # dict_reader = csv.DictReader(
    #     pei_writeback_csv_contents,
    #     delimiter=",",
    #     fieldnames=peri_writeback_csv_fieldnames,
    # )

    # next(dict_reader)  # skip header row
    # pei_raw_extract_data = list(dict_reader)
    # assert len(pei_raw_extract_data) == 3

    # 3. Validate Error Reports  (TODO)
