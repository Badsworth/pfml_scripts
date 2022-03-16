from unittest import mock
from unittest.mock import MagicMock

import pytest
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import NotFound

from massgov.pfml.api.models.applications.requests import DocumentRequestBody
from massgov.pfml.api.services.change_requests import upload_document
from massgov.pfml.db.models.applications import DocumentType


class TestUploadDocument:
    # Run `initialize_factories_session` for all tests,
    # so that it doesn't need to be manually included
    @pytest.fixture(autouse=True)
    def setup_factories(self, initialize_factories_session):
        return

    @pytest.fixture
    def document_details(self) -> DocumentRequestBody:
        return DocumentRequestBody(document_type=DocumentType.PASSPORT)

    @pytest.fixture
    def file(self) -> FileStorage:
        return MagicMock()

    @mock.patch("massgov.pfml.api.services.change_requests.upload_document_to_fineos")
    def test_success(self, mock_upload, change_request, document_details, file, test_db_session):
        mock_response = {"status_code": 200, "data": {}}
        mock_upload.return_value = mock_response

        response = upload_document(change_request, document_details, file, test_db_session)
        assert response == mock_response

        mock_upload.assert_called_with(change_request.claim.application, document_details, file)

    @mock.patch("massgov.pfml.api.services.change_requests.upload_document_to_fineos")
    def test_submitted_at_updated(
        self, mock_upload, change_request, document_details, file, test_db_session
    ):
        assert change_request.documents_submitted_at is None

        upload_document(change_request, document_details, file, test_db_session)

        # expire uncommited changes, so that change_request represents only what's in the db
        test_db_session.expire(change_request)
        assert change_request.documents_submitted_at is not None

    def test_no_application(self, change_request, document_details, file, test_db_session):
        change_request.claim.application = None

        with pytest.raises(Exception) as exc_info:
            upload_document(change_request, document_details, file, test_db_session)

        error = exc_info.value

        assert type(error) == NotFound
        assert "Could not find associated application for change request" in str(error)
