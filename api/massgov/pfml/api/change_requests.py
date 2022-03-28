from uuid import UUID

import connexion
import flask
from werkzeug.exceptions import BadRequest, NotFound

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.api.validation.claim_rules as claim_rules
import massgov.pfml.util.logging
from massgov.pfml.api.models.applications.requests import DocumentRequestBody
from massgov.pfml.api.models.claims.common import ChangeRequest, ChangeRequestType
from massgov.pfml.api.models.claims.requests import ChangeRequestUpdate
from massgov.pfml.api.models.claims.responses import ChangeRequestResponse
from massgov.pfml.api.services.change_requests import (
    add_change_request_to_db,
    get_change_requests_from_db,
    update_change_request_db,
    upload_document,
)
from massgov.pfml.api.services.claims import get_claim_from_db
from massgov.pfml.db.models.employees import ChangeRequest as change_request_db_model
from massgov.pfml.util.datetime import utcnow
from massgov.pfml.util.sqlalchemy import get_or_404

logger = massgov.pfml.util.logging.get_logger(__name__)


def post_change_request(fineos_absence_id: str) -> flask.Response:
    body = connexion.request.json
    change_request: ChangeRequest = ChangeRequest.parse_obj(body)

    claim = get_claim_from_db(fineos_absence_id)
    if claim is None:
        logger.warning(
            "Claim does not exist for given absence ID",
            extra={"absence_case_id": fineos_absence_id},
        )
        error = response_util.error_response(
            status_code=NotFound,
            message="Claim does not exist for given absence ID",
            errors=[],
            data={},
        )
        return error.to_api_response()

    db_change_request = add_change_request_to_db(change_request, claim.claim_id)

    issues = claim_rules.get_change_request_issues(db_change_request, claim)

    response_data = ChangeRequestResponse.from_orm(db_change_request)

    return response_util.success_response(
        message="Successfully posted change request",
        data=response_data.dict(),
        status_code=201,
        warnings=issues,
    ).to_api_response()


def get_change_requests(fineos_absence_id: str) -> flask.Response:
    claim = get_claim_from_db(fineos_absence_id)

    if claim is None:
        logger.warning(
            "Claim does not exist for given absence ID",
            extra={"absence_case_id": fineos_absence_id},
        )
        error = response_util.error_response(
            NotFound,
            "Claim does not exist for given absence ID",
            errors=[],
        )
        return error.to_api_response()

    with app.db_session() as db_session:
        change_requests = get_change_requests_from_db(claim.claim_id, db_session)

    change_requests_dict = []
    for request in change_requests:
        change_request = ChangeRequestResponse(
            fineos_absence_id=fineos_absence_id,
            change_request_type=ChangeRequestType(request.type),
            start_date=request.start_date,
            end_date=request.end_date,
            submitted_time=request.submitted_time,
        )
        change_requests_dict.append(change_request.dict())

    return response_util.success_response(
        message="Successfully retrieved change requests",
        data={"absence_case_id": fineos_absence_id, "change_requests": change_requests_dict},
        status_code=200,
    ).to_api_response()


def submit_change_request(change_request_id: str) -> flask.Response:
    with app.db_session() as db_session:
        change_request = get_or_404(db_session, change_request_db_model, UUID(change_request_id))

    if issues := claim_rules.get_change_request_issues(change_request, change_request.claim):
        return response_util.error_response(
            status_code=BadRequest,
            message="Invalid change request",
            errors=issues,
            data={},
        ).to_api_response()

    # TODO: Post change request to FINEOS - https://lwd.atlassian.net/browse/PORTAL-1710
    change_request.submitted_time = utcnow()

    response_data = ChangeRequestResponse.from_orm(change_request)

    return response_util.success_response(
        message="Successfully submitted Change Request to FINEOS",
        data=response_data.dict(),
        status_code=200,
    ).to_api_response()


def delete_change_request(change_request_id: str) -> flask.Response:
    with app.db_session() as db_session:
        change_request = get_or_404(db_session, change_request_db_model, UUID(change_request_id))

        if change_request.submitted_time is not None:
            error = response_util.error_response(
                BadRequest,
                "Cannot delete a submitted request",
                data={},
                errors=[],
            )
            return error.to_api_response()

        db_session.delete(change_request)

    return response_util.success_response(
        message="Successfully deleted change request",
        data={},
        status_code=200,
    ).to_api_response()


def update_change_request(change_request_id: str) -> flask.Response:
    body = connexion.request.json
    update_request: ChangeRequestUpdate = ChangeRequestUpdate.parse_obj(body)

    with app.db_session() as db_session:
        change_request = get_or_404(db_session, change_request_db_model, UUID(change_request_id))
        update_change_request_db(db_session, update_request, change_request)

    issues = claim_rules.get_change_request_issues(change_request, change_request.claim)

    response_data = ChangeRequestResponse.from_orm(change_request)

    return response_util.success_response(
        message="Successfully updated change request",
        data=response_data.dict(),
        status_code=200,
        warnings=issues,
    ).to_api_response()


# TODO (PORTAL-1997): add tests for this method
def upload_document_for_change_request(change_request_id, body, file):
    with app.db_session() as db_session:
        change_request = get_or_404(db_session, change_request_db_model, change_request_id)

    # Parse the document details from the form body
    document_details: DocumentRequestBody = DocumentRequestBody.parse_obj(body)

    return upload_document(change_request, document_details, file, db_session)
