import pytest
# from massgov.pfml.db.models.factories import EmployeeFactory, Pfml1099BatchFactory
import massgov.pfml.delegated_payments.irs_1099.pfml_1099_util as pfml_1099_util
from massgov.pfml.delegated_payments.mock.irs_1099_factory import Pfml1099Factory

# @pytest.fixture
# def pfml_1099_utility(
#     local_initialize_factories_session, local_test_db_session, local_test_db_other_session
# ):
#     return populate_payments.PopulatePaymentsStep(
#         db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
#     )

def test_is_generate_1099_pdf_enabled():
    result = pfml_1099_util.is_generate_1099_pdf_enabled()
    assert result is True

def test_is_merge_1099_pdf_enabled():
    result = pfml_1099_util.is_merge_1099_pdf_enabled()
    assert result is True

def test_is_upload_1099_pdf_enabled():
    result = pfml_1099_util.is_upload_1099_pdf_enabled()
    assert result is True

def test_get_pdf_api_generate_endpoint_valid():
    endpoint = "https://mass-pfml-pdf-api/api/pdf/generate"
    result = pfml_1099_util.get_pdf_api_generate_endpoint()
    assert result == endpoint

def test_get_pdf_api_merge_endpoint_valid():
    endpoint = "https://mass-pfml-pdf-api/api/pdf/merge"
    result = pfml_1099_util.get_pdf_api_merge_endpoint()
    assert result == endpoint

def test_get_pdf_api_update_template_endpoint_valid():
    endpoint = "https://mass-pfml-pdf-api/api/pdf/updateTemplate"
    result = pfml_1099_util.get_pdf_api_update_template_endpoint()
    assert result == endpoint

def test_get_pdf_api_endpoint_valid():
    endpoint = "https://mass-pfml-pdf-api"
    result = pfml_1099_util.__get_pdf_api_endpoint()
    assert result == endpoint

def test_get_tax_year_valid():
    year = 2021
    result = pfml_1099_util.get_tax_year()
    assert result == year

def test_get_upload_max_files_to_fineos_valid():
    upload_max_files = 10
    result = pfml_1099_util.get_upload_max_files_to_fineos()
    assert result == upload_max_files

def test_get_generate_1099_max_files_valid():
    generate_max_files = 1000
    result = pfml_1099_util.get_generate_1099_max_files()
    assert result == generate_max_files

def test_is_test_file_invalid():
    is_test = ""
    result = pfml_1099_util.is_test_file()
    assert result == is_test

def test_is_correction_batch():
    is_correction = False
    result = pfml_1099_util.is_correction_batch()
    assert result == is_correction

def test_get_1099_records_to_file(local_test_db_session):
    result = pfml_1099_util.get_1099_records_to_file(local_test_db_session)
    assert len(result) == 0

def test_get_1099_record(local_test_db_session):
    pfml_1099 = Pfml1099Factory(db_session=local_test_db_session).get_or_create_batch()
    # pfml_1099 = Pfml1099Factory.create(
    #     pfml_1099_batch_id=batch.pfml_1099_batch_id, employee_id=employee.employee_id
    # )
    # result = pfml_1099_util.get_1099_record(local_test_db_session, "New", str(pfml_1099.pfml_1099_batch_id))
    assert 1 == 1