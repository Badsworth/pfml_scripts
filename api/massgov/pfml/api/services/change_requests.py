from datetime import datetime, timezone

import flask
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import NotFound

import massgov
from massgov.pfml import db
from massgov.pfml.api.models.applications.requests import DocumentRequestBody
from massgov.pfml.api.services.document_upload import upload_document_to_fineos
from massgov.pfml.db.models.employees import ChangeRequest

logger = massgov.pfml.util.logging.get_logger(__name__)


def upload_document(
    change_request: ChangeRequest,
    document_details: DocumentRequestBody,
    file: FileStorage,
    db_session: db.Session,
) -> flask.Response:
    application = change_request.application

    if application is None:
        raise NotFound(
            description="Could not find associated application for change request with ID {}".format(
                change_request.change_request_id
            )
        )

    # TODO: validate the documents

    document_response = upload_document_to_fineos(application, document_details, file)

    # mark that documents have been successfully submitted to FINEOS
    change_request.documents_submitted_at = datetime.now(timezone.utc)
    db_session.commit()

    return document_response
