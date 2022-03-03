from unittest import mock

import pytest

from massgov.pfml.db.models.factories import Pfml1099BatchFactory
from massgov.pfml.delegated_payments.irs_1099.merge_documents import Merge1099Step


@pytest.fixture
def merge_1099_document_step(test_db_session, initialize_factories_session, test_db_other_session):
    return Merge1099Step(db_session=test_db_session, log_entry_db_session=test_db_other_session)


def test_get_1099_batch_id_as_none(merge_1099_document_step: Merge1099Step):
    mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_current_1099_batch",
        return_value=None,
    )

    with pytest.raises(
        Exception, match="Batch cannot be empty at this point.",
    ):
        merge_1099_document_step.get_1099_batch_id()


def test_get_1099_batch_id_as_valid(merge_1099_document_step: Merge1099Step):
    batch = Pfml1099BatchFactory.create()
    with mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.get_current_1099_batch"
    ) as mock_current_batch:
        mock_current_batch.return_value = batch
        response = merge_1099_document_step.get_1099_batch_id()

    assert response is not None


def test_merge_document_success(merge_1099_document_step: Merge1099Step):
    batch = Pfml1099BatchFactory.create()

    with mock.patch("requests.post") as mocked_post:
        mocked_post.response_value.ok = True
        mocked_post.response_value.text = "Success"

        response = merge_1099_document_step.merge_document(
            str(batch.pfml_1099_batch_id), "http://localhost:5001/api/pdf/merge"
        )

    assert response is None


def test_merge_1099_documents_flag_not_enabled(merge_1099_document_step: Merge1099Step):
    with mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.is_merge_1099_pdf_enabled"
    ) as mock_is_merge_1099_pdf_enabled:
        mock_is_merge_1099_pdf_enabled.return_value = False
        response = merge_1099_document_step._merge_1099_documents()

    assert response is None


def test_merge_1099_documents_flag_enabled(merge_1099_document_step: Merge1099Step):
    batch = Pfml1099BatchFactory.create()

    with mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.pfml_1099_util.is_merge_1099_pdf_enabled"
    ) as mock_is_merge_1099_pdf_enabled, mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.merge_documents.Merge1099Step.get_1099_batch_id"
    ) as mock_get_record, mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.merge_documents.Merge1099Step.merge_document"
    ) as mock_merge_document:
        mock_is_merge_1099_pdf_enabled.return_value = True
        mock_get_record.return_value = batch
        mock_merge_document.return_value = None
        merge_1099_document_step.pdfApiEndpoint = ""
        response = merge_1099_document_step._merge_1099_documents()

    assert response is None


def test_run_step_success(merge_1099_document_step: Merge1099Step):
    with mock.patch(
        "massgov.pfml.delegated_payments.irs_1099.merge_documents.Merge1099Step._merge_1099_documents"
    ) as mock_merge_1099_documents:
        mock_merge_1099_documents.return_value = None
        response = merge_1099_document_step.run_step()

    assert response is None
