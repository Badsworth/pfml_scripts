import massgov.pfml.delegated_payments.irs_1099.pfml_1099_util as pfml_1099_util


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

