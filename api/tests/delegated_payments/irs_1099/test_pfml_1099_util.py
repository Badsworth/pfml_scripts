import massgov.pfml.delegated_payments.irs_1099.pfml_1099_util as pfml_1099_util


def test_is_generate_1099_pdf_not_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_GENERATE_1099_PDF", "0")
    result = pfml_1099_util.is_generate_1099_pdf_enabled()
    assert result is False


def test_is_generate_1099_pdf_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_GENERATE_1099_PDF", "1")
    result = pfml_1099_util.is_generate_1099_pdf_enabled()
    assert result is True


def test_is_merge_1099_pdf_not_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_MERGE_1099_PDF", "0")
    result = pfml_1099_util.is_merge_1099_pdf_enabled()
    assert result is False


def test_is_merge_1099_pdf_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_MERGE_1099_PDF", "1")
    result = pfml_1099_util.is_merge_1099_pdf_enabled()
    assert result is True


def test_is_upload_1099_pdf_not_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_UPLOAD_1099_PDF", "0")
    result = pfml_1099_util.is_upload_1099_pdf_enabled()
    assert result is False


def test_is_upload_1099_pdf_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_UPLOAD_1099_PDF", "1")
    result = pfml_1099_util.is_upload_1099_pdf_enabled()
    assert result is True


def test_get_pdf_api_generate_endpoint_valid(monkeypatch):
    monkeypatch.setenv("PDF_API_HOST", "https://mass-pfml-pdf-api")
    endpoint = "https://mass-pfml-pdf-api/api/pdf/generate"
    result = pfml_1099_util.get_pdf_api_generate_endpoint()
    assert result == endpoint


def test_get_pdf_api_merge_endpoint_valid(monkeypatch):
    monkeypatch.setenv("PDF_API_HOST", "https://mass-pfml-pdf-api")
    endpoint = "https://mass-pfml-pdf-api/api/pdf/merge"
    result = pfml_1099_util.get_pdf_api_merge_endpoint()
    assert result == endpoint


def test_get_pdf_api_update_template_endpoint_valid(monkeypatch):
    monkeypatch.setenv("PDF_API_HOST", "https://mass-pfml-pdf-api")
    endpoint = "https://mass-pfml-pdf-api/api/pdf/updateTemplate"
    result = pfml_1099_util.get_pdf_api_update_template_endpoint()
    assert result == endpoint


def test_get_pdf_api_endpoint_valid(monkeypatch):
    monkeypatch.setenv("PDF_API_HOST", "https://mass-pfml-pdf-api")
    endpoint = "https://mass-pfml-pdf-api"
    result = pfml_1099_util.__get_pdf_api_endpoint()
    assert result == endpoint


def test_get_tax_year_not_valid(monkeypatch):
    monkeypatch.setenv("IRS_1099_TAX_YEAR", "0")
    year = 0
    result = pfml_1099_util.get_tax_year()
    assert result == year


def test_get_tax_year_valid(monkeypatch):
    monkeypatch.setenv("IRS_1099_TAX_YEAR", "2022")
    year = 2022
    result = pfml_1099_util.get_tax_year()
    assert result == year


def test_get_upload_max_files_to_fineos_not_valid(monkeypatch):
    monkeypatch.setenv("UPLOAD_MAX_FILES_TO_FINEOS", "0")
    upload_max_files = 0
    result = pfml_1099_util.get_upload_max_files_to_fineos()
    assert result == upload_max_files


def test_get_upload_max_files_to_fineos_valid(monkeypatch):
    monkeypatch.setenv("UPLOAD_MAX_FILES_TO_FINEOS", "10")
    upload_max_files = 10
    result = pfml_1099_util.get_upload_max_files_to_fineos()
    assert result == upload_max_files


def test_get_generate_1099_max_files_not_valid(monkeypatch):
    monkeypatch.setenv("GENERATE_1099_MAX_FILES", "0")
    generate_max_files = 0
    result = pfml_1099_util.get_generate_1099_max_files()
    assert result == generate_max_files


def test_get_generate_1099_max_files_valid(monkeypatch):
    monkeypatch.setenv("GENERATE_1099_MAX_FILES", "1000")
    generate_max_files = 1000
    result = pfml_1099_util.get_generate_1099_max_files()
    assert result == generate_max_files


def test_is_test_file_not_valid(monkeypatch):
    monkeypatch.setenv("TEST_FILE_GENERATION_1099", "0")
    is_test = ""
    result = pfml_1099_util.is_test_file()
    assert result == is_test


def test_is_test_file_valid(monkeypatch):
    monkeypatch.setenv("TEST_FILE_GENERATION_1099", "1")
    is_test = "T"
    result = pfml_1099_util.is_test_file()
    assert result == is_test


def test_is_correction_batch_not_valid(monkeypatch):
    monkeypatch.setenv("IRS_1099_CORRECTION_IND", "0")
    is_correction = False
    result = pfml_1099_util.is_correction_batch()
    assert result == is_correction


def test_is_correction_batch_valid(monkeypatch):
    monkeypatch.setenv("IRS_1099_CORRECTION_IND", "1")
    is_correction = True
    result = pfml_1099_util.is_correction_batch()
    assert result == is_correction


def test_get_1099_records_to_file(local_test_db_session):
    result = pfml_1099_util.get_1099_records_to_file(local_test_db_session)
    assert len(result) == 0
