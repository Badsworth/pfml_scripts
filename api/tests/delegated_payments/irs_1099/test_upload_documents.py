import os
from unittest import mock

import pytest

from massgov.pfml.db.models.applications import DocumentType
from massgov.pfml.db.models.factories import (
    EmployeeFactory,
    Pfml1099BatchFactory,
    Pfml1099Factory,
    TaxIdentifierFactory,
)
from massgov.pfml.delegated_payments.irs_1099.upload_documents import Upload1099DocumentsStep
from massgov.pfml.fineos.mock_client import MockFINEOSClient


@pytest.fixture
def upload_1099_document_step(test_db_session, initialize_factories_session, test_db_other_session):
    return Upload1099DocumentsStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


def test_get_batch_id_as_none(upload_1099_document_step: Upload1099DocumentsStep):
    mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_current_1099_batch",
        return_value=None,
    )

    with pytest.raises(Exception, match="Batch cannot be empty at this point."):
        upload_1099_document_step._get_batch_id()


def test_get_batch_id_as_valid(upload_1099_document_step: Upload1099DocumentsStep):
    batch = Pfml1099BatchFactory.create()
    with mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_current_1099_batch"
    ) as mock_get_current_1099_batch:
        mock_get_current_1099_batch.return_value = batch
        response = upload_1099_document_step._get_batch_id()

    assert response == str(batch.pfml_1099_batch_id)


def test_get_document_type(upload_1099_document_step: Upload1099DocumentsStep):
    response = upload_1099_document_step._get_document_type()

    assert response == DocumentType.IRS_1099G_TAX_FORM_FOR_CLAIMANTS.document_type_description


def test_get_document_content(upload_1099_document_step: Upload1099DocumentsStep):
    response = upload_1099_document_step._get_document_content(
        os.path.join(os.path.dirname(__file__), "test_audit_batch.py")
    )

    assert len(response) > 0


def test_upload_document_success(upload_1099_document_step: Upload1099DocumentsStep):
    batch = Pfml1099BatchFactory.create()
    employee = EmployeeFactory.create()
    tax_identifier = TaxIdentifierFactory.create()
    pfml_1099 = Pfml1099Factory.create(
        pfml_1099_batch_id=batch.pfml_1099_batch_id,
        employee_id=employee.employee_id,
        tax_identifier_id=tax_identifier.tax_identifier_id,
    )
    client = MockFINEOSClient()
    with mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_tax_id"
    ) as mock_get_tax_id, mock.patch("requests.post") as mocked_post:
        mock_get_tax_id.return_value = tax_identifier.tax_identifier
        mocked_post.response_value.ok = True
        mocked_post.response_value.text = "Success"
        response = upload_1099_document_step._upload_document(
            client,
            os.path.join(os.path.dirname(__file__), "test_audit_batch.py"),
            pfml_1099.s3_location,
            DocumentType.IRS_1099G_TAX_FORM_FOR_CLAIMANTS.document_type_description,
            pfml_1099,
            0,
        )

    assert response is None


def test_upload_1099_documents_flag_not_enabled(upload_1099_document_step: Upload1099DocumentsStep):
    with mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.is_upload_1099_pdf_enabled"
    ) as mock_is_upload_1099_pdf_enabled:
        mock_is_upload_1099_pdf_enabled.return_value = False
        response = upload_1099_document_step._upload_1099_documents()

    assert response is None


def test_upload_1099_documents_flag_enabled(upload_1099_document_step: Upload1099DocumentsStep):
    batch = Pfml1099BatchFactory.create()
    employee = EmployeeFactory.create()
    tax_identifier = TaxIdentifierFactory.create()
    pfml_1099 = Pfml1099Factory.create(
        pfml_1099_batch_id=batch.pfml_1099_batch_id,
        employee_id=employee.employee_id,
        tax_identifier_id=tax_identifier.tax_identifier_id,
    )

    with mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.is_upload_1099_pdf_enabled"
    ) as mock_is_upload_1099_pdf_enabled, mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_current_1099_batch"
    ) as mocked_get_current_1099_batch, mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_upload_max_files_to_fineos"
    ) as mocked_get_upload_max_files_to_fineos, mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_1099_record"
    ) as mocked_get_1099_record, mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.upload_documents.Upload1099DocumentsStep._upload_document"
    ) as mocked_upload_document:
        mock_is_upload_1099_pdf_enabled.return_value = True
        mocked_get_current_1099_batch.return_value = batch
        mocked_get_upload_max_files_to_fineos.return_value = 1
        mocked_get_1099_record.return_value = pfml_1099
        mocked_upload_document.return_value = None
        response = upload_1099_document_step._upload_1099_documents()

    assert response is None


def test_upload_1099_documents_flag_enabled_error(
    upload_1099_document_step: Upload1099DocumentsStep,
):
    batch = Pfml1099BatchFactory.create()

    with mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.is_upload_1099_pdf_enabled"
    ) as mock_is_upload_1099_pdf_enabled, mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_current_1099_batch"
    ) as mocked_get_current_1099_batch, mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_upload_max_files_to_fineos"
    ) as mocked_get_upload_max_files_to_fineos, mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_1099_record"
    ) as mocked_get_1099_record, mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.upload_documents.Upload1099DocumentsStep._upload_document"
    ) as mocked_upload_document:
        mock_is_upload_1099_pdf_enabled.return_value = True
        mocked_get_current_1099_batch.return_value = batch
        mocked_get_upload_max_files_to_fineos.return_value = 1
        mocked_get_1099_record.return_value = None
        mocked_upload_document.return_value = None
        response = upload_1099_document_step._upload_1099_documents()

    assert response is None


def test_run_step_success(upload_1099_document_step: Upload1099DocumentsStep):
    with mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.upload_documents.Upload1099DocumentsStep._upload_1099_documents"
    ) as mocked_upload_1099_documents:
        mocked_upload_1099_documents.return_value = None
        response = upload_1099_document_step.run_step()

    assert response is None
