from datetime import datetime, timezone
from typing import List
from uuid import UUID

import flask
from sqlalchemy.orm.session import Session
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import NotFound

import massgov
import massgov.pfml.api.app as app
import massgov.pfml.api.models.claims.common as api_models
import massgov.pfml.db.lookups as db_lookups
from massgov.pfml import db
from massgov.pfml.api.models.applications.requests import DocumentRequestBody
from massgov.pfml.api.services.document_upload import upload_document_to_fineos
from massgov.pfml.db.models.employees import ChangeRequest, LkChangeRequestType

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


def get_change_requests_from_db(claim_id: UUID, db_session: Session) -> List[ChangeRequest]:

    change_requests = (
        db_session.query(ChangeRequest).filter(ChangeRequest.claim_id == claim_id).all()
    )

    return change_requests


def add_change_request_to_db(
    change_request: api_models.ChangeRequest, claim_id: UUID
) -> ChangeRequest:
    with app.db_session() as db_session:
        db_request = change_request.to_db_model(claim_id)
        db_session.add(db_request)
        return db_request


def update_change_request_db(
    db_session: Session,
    update_request: api_models.ChangeRequest,
    change_request: ChangeRequest,
) -> ChangeRequest:
    for key in update_request.__fields_set__:
        value = getattr(update_request, key)

        if key == "change_request_type":
            change_request_type = db_lookups.by_value(db_session, LkChangeRequestType, value)
            assert isinstance(change_request_type, LkChangeRequestType)
            change_request.change_request_type_id = change_request_type.change_request_type_id
        else:
            setattr(change_request, key, value)

    return change_request
