from unittest import mock

import pytest

from massgov.pfml.db.models.factories import (
    EmployeeFactory,
    Pfml1099BatchFactory,
    Pfml1099Factory,
    TaxIdentifierFactory,
)
from massgov.pfml.delegated_payments.irs_1099.generate_documents import Generate1099DocumentsStep


@pytest.fixture
def generate_1099_document_step(
    test_db_session, initialize_factories_session, test_db_other_session
):
    return Generate1099DocumentsStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


def test_get_1099_batch_id_as_none(generate_1099_document_step: Generate1099DocumentsStep):
    mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_current_1099_batch",
        return_value=None,
    )

    with pytest.raises(Exception, match="Batch cannot be empty at this point."):
        generate_1099_document_step.get_1099_batch_id()


def test_get_1099_batch_id_as_valid(generate_1099_document_step: Generate1099DocumentsStep):
    batch = Pfml1099BatchFactory.create()
    with mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_current_1099_batch"
    ) as mock_get_current_1099_batch:
        mock_get_current_1099_batch.return_value = batch
        response = generate_1099_document_step.get_1099_batch_id()

    assert response == str(batch.pfml_1099_batch_id)


def test_get_records_as_empty(generate_1099_document_step: Generate1099DocumentsStep):
    batch = Pfml1099BatchFactory.create()
    pfml_1099_list = []
    with mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_1099_records_to_generate"
    ) as mock_get_1099_records:
        mock_get_1099_records.return_value = pfml_1099_list
        response = generate_1099_document_step.get_records(batch.pfml_1099_batch_id)

    assert len(response) == 0


def test_get_records_not_empty(generate_1099_document_step: Generate1099DocumentsStep):
    batch = Pfml1099BatchFactory.create()
    employee = EmployeeFactory.create()
    pfml_1099 = Pfml1099Factory.create(
        pfml_1099_batch_id=batch.pfml_1099_batch_id, employee_id=employee.employee_id
    )
    pfml_1099_list = []
    pfml_1099_list.append(pfml_1099)
    with mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_1099_records_to_generate"
    ) as mock_get_1099_records:
        mock_get_1099_records.return_value = pfml_1099_list
        response = generate_1099_document_step.get_records(batch.pfml_1099_batch_id)

    assert len(response) == 1


def test_generate_document_success(generate_1099_document_step: Generate1099DocumentsStep):
    batch = Pfml1099BatchFactory.create()
    employee = EmployeeFactory.create()
    tax_identifier = TaxIdentifierFactory.create()
    pfml_1099 = Pfml1099Factory.create(
        pfml_1099_batch_id=batch.pfml_1099_batch_id,
        employee_id=employee.employee_id,
        tax_identifier_id=tax_identifier.tax_identifier_id,
    )

    with mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_tax_id"
    ) as mock_get_tax_id, mock.patch("requests.post") as mocked_post:
        mock_get_tax_id.return_value = tax_identifier.tax_identifier
        mocked_post.response_value.ok = True
        mocked_post.response_value.text = "Success"
        response = generate_1099_document_step.generate_document(
            pfml_1099, "Sub-batch-1", "http://localhost:5001/api/pdf/merge", "s3://"
        )

    assert response is None


def test_update_1099_template_success(generate_1099_document_step: Generate1099DocumentsStep):
    with mock.patch("requests.get") as mocked_post:
        mocked_post.response_value.ok = True
        mocked_post.response_value.text = "Success"
        response = generate_1099_document_step._update_1099_template()

    assert response is None


def test_update_1099_template_no_success(generate_1099_document_step: Generate1099DocumentsStep):
    with mock.patch("requests.get") as mocked_post:
        mocked_post.response_value.ok = False
        mocked_post.response_value.text = "Error"
        response = generate_1099_document_step._update_1099_template()

    assert response is None


def test_generate_1099_documents_flag_not_enabled(
    generate_1099_document_step: Generate1099DocumentsStep,
):
    with mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.is_generate_1099_pdf_enabled"
    ) as mock_is_generate_1099_pdf_enabled:
        mock_is_generate_1099_pdf_enabled.return_value = False
        response = generate_1099_document_step._generate_1099_documents()

    assert response is None


def test_generate_1099_documents_flag_enabled(
    generate_1099_document_step: Generate1099DocumentsStep,
):
    batch = Pfml1099BatchFactory.create()
    employee = EmployeeFactory.create()
    tax_identifier = TaxIdentifierFactory.create()
    pfml_1099 = Pfml1099Factory.create(
        pfml_1099_batch_id=batch.pfml_1099_batch_id,
        employee_id=employee.employee_id,
        tax_identifier_id=tax_identifier.tax_identifier_id,
    )
    pfml_list = []
    pfml_list.append(pfml_1099)

    with mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.is_generate_1099_pdf_enabled"
    ) as mock_is_generate_1099_pdf_enabled, mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.generate_documents.Generate1099DocumentsStep.get_1099_batch_id"
    ) as mock_get_1099_batch_id, mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.generate_documents.Generate1099DocumentsStep.get_records"
    ) as mock_get_records, mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_1099_generated_count"
    ) as mock_get_1099_generated_count:
        mock_is_generate_1099_pdf_enabled.return_value = True
        mock_get_1099_batch_id.return_value = batch
        mock_get_records.return_value = pfml_list
        mock_get_1099_generated_count.return_value = 0
        generate_1099_document_step._generate_1099_documents()


def test_run_step_success(generate_1099_document_step: Generate1099DocumentsStep):
    batch = Pfml1099BatchFactory.create()
    employee = EmployeeFactory.create()
    tax_identifier = TaxIdentifierFactory.create()
    pfml_1099 = Pfml1099Factory.create(
        pfml_1099_batch_id=batch.pfml_1099_batch_id,
        employee_id=employee.employee_id,
        tax_identifier_id=tax_identifier.tax_identifier_id,
    )
    pfml_list = []
    pfml_list.append(pfml_1099)

    with mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.generate_documents.Generate1099DocumentsStep._update_1099_template"
    ) as mock_update_1099_template, mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.generate_documents.Generate1099DocumentsStep._generate_1099_documents"
    ) as mock_generate_1099_documents:
        mock_update_1099_template.return_value = None
        mock_generate_1099_documents.return_value = None
        generate_1099_document_step.run_step()
