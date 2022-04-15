import uuid
from datetime import date
from unittest import mock
from unittest.mock import MagicMock

import pytest
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import NotFound

import massgov.pfml.db.models.employees as db_models
from massgov.pfml.api.models.applications.requests import DocumentRequestBody
from massgov.pfml.api.models.claims.common import ChangeRequest, ChangeRequestType
from massgov.pfml.api.services.change_requests import (
    add_change_request_to_db,
    get_change_requests_from_db,
    update_change_request_db,
    upload_document,
)
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


class TestAddChangeRequestToDB:
    @pytest.fixture
    def change_request(self, claim) -> ChangeRequest:
        return ChangeRequest(
            claim_id=claim.claim_id,
            change_request_type=ChangeRequestType.WITHDRAWAL,
            start_date=None,
            end_date=None,
        )

    def test_successful_request(self, test_db_session, app, claim, change_request):
        # Run app.preprocess_request before calling method, to ensure we have access to a db_session
        # (set up by a @flask_app.before_request method in app.py)
        with app.app.test_request_context(
            f"/v1/change-request?fineos_absence_id={claim.fineos_absence_id}"
        ):
            app.app.preprocess_request()
            db_model = add_change_request_to_db(change_request, claim.claim_id)
            assert db_model.claim_id == claim.claim_id
            assert db_model.start_date is None
            assert db_model.end_date is None
            assert (
                db_model.change_request_type_instance.change_request_type_description
                == "Withdrawal"
            )
            test_db_session.commit()
            db_entry = (
                test_db_session.query(db_models.ChangeRequest)
                .filter(db_models.ChangeRequest.claim_id == claim.claim_id)
                .one_or_none()
            )
            assert db_entry is not None


class TestGetChangeRequestsFromDB:
    def test_success(self, initialize_factories_session, test_db_session, change_request):
        change_requests = get_change_requests_from_db(change_request.claim_id, test_db_session)
        assert change_requests[0].claim_id == change_request.claim_id
        assert change_requests[0].change_request_type_id == 1
        assert (
            change_requests[0].change_request_type_instance.change_request_type_description
            == "Modification"
        )

    def test_no_change_requests(self, test_db_session):
        change_requests = get_change_requests_from_db(uuid.uuid4(), test_db_session)
        assert len(change_requests) == 0


class TestUpdateChangeRequestsDB:
    def test_success(self, initialize_factories_session, test_db_session, change_request):
        update_request = ChangeRequest(
            change_request_type="Medical To Bonding Transition", start_date="2022-05-01"
        )
        update_change_request_db(test_db_session, update_request, change_request)
        test_db_session.commit()
        test_db_session.expire(change_request)
        assert change_request.type == "Medical To Bonding Transition"
        assert change_request.start_date == date(2022, 5, 1)
