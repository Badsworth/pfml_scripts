import base64
from typing import Optional

import connexion
import flask
from werkzeug.exceptions import BadRequest, Forbidden, NotFound, Unauthorized

import massgov.pfml.api.app as app
import massgov.pfml.api.services.claim_rules as claim_rules
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.exceptions import NotAuthorizedForAccess
from massgov.pfml.api.authorization.flask import READ, can, requires
from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.api.models.claims.responses import ClaimResponse
from massgov.pfml.api.services.administrator_fineos_actions import (
    DOWNLOADABLE_DOC_TYPES,
    awaiting_leave_info,
    complete_claim_review,
    create_eform,
    download_document_as_leave_admin,
    get_claim_as_leave_admin,
    get_documents_as_leave_admin,
)
from massgov.pfml.db.models.applications import Application
from massgov.pfml.db.models.employees import Claim, Employer, UserLeaveAdministrator
from massgov.pfml.fineos.models.group_client_api import Base64EncodedFileData
from massgov.pfml.fineos.transforms.to_fineos.eforms.employer import EmployerClaimReviewEFormBuilder
from massgov.pfml.util import feature_gate
from massgov.pfml.util.paginate.paginator import PaginationAPIContext, page_for_api_context
from massgov.pfml.util.sqlalchemy import get_or_404

logger = massgov.pfml.util.logging.get_logger(__name__)


class VerificationRequired(Forbidden):
    user_leave_admin: UserLeaveAdministrator
    status_code = Forbidden

    def __init__(self, user_leave_admin, description):
        self.user_leave_admin = user_leave_admin
        self.description = description

    def to_api_response(self):
        employer_id = self.user_leave_admin.employer_id
        has_verification_data = self.user_leave_admin.employer.has_verification_data
        return response_util.error_response(
            status_code=self.status_code,
            message=self.description,
            errors=[],
            data={"employer_id": employer_id, "has_verification_data": has_verification_data},
        ).to_api_response()


def get_current_user_leave_admin_record(fineos_absence_id: str) -> UserLeaveAdministrator:
    with app.db_session() as db_session:
        associated_employer_id: Optional[str] = None

        current_user = app.current_user()
        if current_user is None:
            raise Unauthorized()

        claim = (
            db_session.query(Claim)
            .filter(Claim.fineos_absence_id == fineos_absence_id)
            .one_or_none()
        )

        if claim is not None:
            associated_employer_id = claim.employer_id

        if associated_employer_id is None:
            raise Forbidden(description="Claim does not exist for given absence ID")

        user_leave_admin = (
            db_session.query(UserLeaveAdministrator)
            .filter(
                (UserLeaveAdministrator.user_id == current_user.user_id)
                & (UserLeaveAdministrator.employer_id == associated_employer_id)
            )
            .one_or_none()
        )

        if user_leave_admin is None:
            raise NotAuthorizedForAccess(
                description="User does not have leave administrator record for this employer",
                error_type="unauthorized_leave_admin",
            )

        if user_leave_admin.fineos_web_id is None:
            raise VerificationRequired(
                user_leave_admin, "User has no leave administrator FINEOS ID"
            )

        # TODO: Remove this after rollout https://lwd.atlassian.net/browse/EMPLOYER-962
        verification_required = app.get_config().enforce_verification or feature_gate.check_enabled(
            feature_name=feature_gate.LEAVE_ADMIN_VERIFICATION,
            user_email=current_user.email_address,
        )
        if verification_required and not user_leave_admin.verified:
            raise VerificationRequired(user_leave_admin, "User is not Verified")

        return user_leave_admin


@requires(READ, "EMPLOYER_API")
def employer_update_claim_review(fineos_absence_id: str) -> flask.Response:
    body = connexion.request.json

    claim_request: EmployerClaimReview = EmployerClaimReview.parse_obj(body)

    if issues := claim_rules.get_employer_claim_review_issues(claim_request):
        return response_util.error_response(
            status_code=BadRequest,
            message="Invalid claim review body",
            errors=[response_util.validation_issue(issue) for issue in issues],
            data={},
        ).to_api_response()

    try:
        user_leave_admin = get_current_user_leave_admin_record(fineos_absence_id)
    except (VerificationRequired, NotAuthorizedForAccess) as error:
        return error.to_api_response()

    log_attributes = {
        "absence_case_id": fineos_absence_id,
        "user_leave_admin.employer_id": user_leave_admin.employer_id,
        "claim_request.employer_decision": claim_request.employer_decision,
        "claim_request.fraud": claim_request.fraud,
        "claim_request.has_amendments": claim_request.has_amendments,
        "claim_request.has_comment": str(bool(claim_request.comment)),
    }

    fineos_web_id = user_leave_admin.fineos_web_id

    if fineos_web_id is None:
        raise ValueError("User admin does not have a FINEOS user")

    # can now use `fineos_web_id` as if it was non-None

    if not awaiting_leave_info(fineos_web_id, fineos_absence_id):
        logger.warning("No outstanding information request for claim", extra=log_attributes)
        return response_util.error_response(
            status_code=BadRequest,
            message="No outstanding information request for claim",
            errors=[
                response_util.custom_issue(
                    "outstanding_information_request_required",
                    "No outstanding information request for claim",
                )
            ],
        ).to_api_response()

    if (
        claim_request.employer_decision == "Approve"
        and not claim_request.has_amendments
        and not claim_request.comment
    ):
        complete_claim_review(fineos_web_id, fineos_absence_id)
        logger.info("Completed claim review", extra=log_attributes)
    else:
        transformed_eform = EmployerClaimReviewEFormBuilder.build(claim_request)
        create_eform(fineos_web_id, fineos_absence_id, transformed_eform)
        logger.info("Created eform", extra=log_attributes)

    logger.info("Updated claim", extra=log_attributes)

    claim_response = {"claim_id": fineos_absence_id}
    return response_util.success_response(
        message="Successfully updated claim", data=claim_response,
    ).to_api_response()


@requires(READ, "EMPLOYER_API")
def employer_get_claim_review(fineos_absence_id: str) -> flask.Response:
    """
    Calls out to the FINEOS Group Client API to retrieve claim data and returns it.
    The requesting user must be of the EMPLOYER role.
    """
    try:
        user_leave_admin = get_current_user_leave_admin_record(fineos_absence_id)
    except (VerificationRequired, NotAuthorizedForAccess) as error:
        return error.to_api_response()

    with app.db_session() as db_session:
        employer = get_or_404(db_session, Employer, user_leave_admin.employer_id)

        claim_review_response = get_claim_as_leave_admin(
            user_leave_admin.fineos_web_id, fineos_absence_id, employer  # type: ignore
        )

        if claim_review_response is None:
            raise NotFound(
                description="Could not fetch Claim from FINEOS with given absence ID {}".format(
                    fineos_absence_id
                )
            )

        claim_from_db = (
            db_session.query(Claim)
            .filter(Claim.fineos_absence_id == fineos_absence_id)
            .one_or_none()
        )

        if claim_from_db and claim_from_db.fineos_absence_status:
            claim_review_response.status = (
                claim_from_db.fineos_absence_status.absence_status_description
            )

        return response_util.success_response(
            message="Successfully retrieved claim",
            data=claim_review_response.dict(),
            status_code=200,
        ).to_api_response()


@requires(READ, "EMPLOYER_API")
def employer_get_claim_documents(fineos_absence_id: str) -> flask.Response:
    """
    Calls out to the FINEOS Group Client API to get a list of documents attached to a specified claim.
    The requesting user must be of the EMPLOYER role.
    """
    try:
        user_leave_admin = get_current_user_leave_admin_record(fineos_absence_id)
    except (VerificationRequired, NotAuthorizedForAccess) as error:
        return error.to_api_response()

    documents = get_documents_as_leave_admin(user_leave_admin.fineos_web_id, fineos_absence_id)  # type: ignore
    documents_list = [doc.dict() for doc in documents]
    return response_util.success_response(
        message="Successfully retrieved documents", data=documents_list, status_code=200
    ).to_api_response()


@requires(READ, "EMPLOYER_API")
def employer_document_download(fineos_absence_id: str, fineos_document_id: str) -> flask.Response:
    """
    Calls out to the FINEOS Group Client API to download a document for a specified claim.
    The requesting user must be of the EMPLOYER role.
    """
    try:
        user_leave_admin = get_current_user_leave_admin_record(fineos_absence_id)
    except (VerificationRequired, NotAuthorizedForAccess) as error:
        return error.to_api_response()

    documents = get_documents_as_leave_admin(user_leave_admin.fineos_web_id, fineos_absence_id)  # type: ignore
    document = next(
        (doc for doc in documents if doc.fineos_document_id == fineos_document_id), None
    )

    if document is None:
        raise Forbidden(description="User does not have access to this document")

    if document.document_type and document.document_type.lower() not in DOWNLOADABLE_DOC_TYPES:
        raise Forbidden(description="User does not have access to this document")

    document_data: Base64EncodedFileData = download_document_as_leave_admin(
        user_leave_admin.fineos_web_id, fineos_absence_id, fineos_document_id  # type: ignore
    )
    file_bytes = base64.b64decode(document_data.base64EncodedFileContents.encode("ascii"))

    content_type = document_data.contentType or "application/octet-stream"

    return flask.Response(
        file_bytes,
        content_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={document_data.fileName}"},
    )


def user_has_access_to_claim(claim: Claim) -> bool:
    current_user = app.current_user()
    if current_user is None:
        return False

    if can(READ, "EMPLOYER_API") and claim.employer in current_user.employers:
        # User is leave admin for the employer associated with claim
        # TODO: Remove this after rollout https://lwd.atlassian.net/browse/EMPLOYER-962
        verification_required = app.get_config().enforce_verification or feature_gate.check_enabled(
            feature_name=feature_gate.LEAVE_ADMIN_VERIFICATION,
            user_email=current_user.email_address,
        )

        if verification_required:
            return current_user.verified_employer(claim.employer)
        return True

    application = claim.application  # type: ignore

    if application and application.user == current_user:
        # User is claimant and this is their claim
        return True

    return False


def get_claim(fineos_absence_id: str) -> flask.Response:
    with app.db_session() as db_session:
        claim = (
            db_session.query(Claim)
            .filter(Claim.fineos_absence_id == fineos_absence_id)
            .one_or_none()
        )

    if claim is None:
        logger.warning("Claim not in database.")
        return response_util.error_response(
            status_code=BadRequest, message="Claim not in database.", errors=[], data={},
        ).to_api_response()

    if not user_has_access_to_claim(claim):
        logger.warning("User does not have access to claim.")
        return response_util.error_response(
            status_code=Forbidden,
            message="User does not have access to claim.",
            errors=[],
            data={},
        ).to_api_response()

    return response_util.success_response(
        message="Successfully retrieved claim",
        data=ClaimResponse.from_orm(claim).dict(),
        status_code=200,
    ).to_api_response()


def get_claims() -> flask.Response:
    current_user = app.current_user()
    is_employer = can(READ, "EMPLOYER_API")

    with PaginationAPIContext(Claim, request=flask.request) as pagination_context:
        with app.db_session() as db_session:
            # The logic here is similar to that in user_has_access_to_claim (except it is applied to multiple claims)
            # so if something changes there it probably needs to be changed here
            if is_employer and current_user and current_user.employers:
                verification_required = app.get_config().enforce_verification or feature_gate.check_enabled(
                    feature_name=feature_gate.LEAVE_ADMIN_VERIFICATION,
                    user_email=current_user.email_address,
                )

                if verification_required:
                    employer_ids_list = [
                        e.employer_id
                        for e in current_user.employers
                        if current_user.verified_employer(e)
                    ]
                else:
                    employer_ids_list = [e.employer_id for e in current_user.employers]

                query = (
                    db_session.query(Claim)
                    .order_by(pagination_context.order_key)
                    .filter(Claim.employer_id.in_(employer_ids_list))
                )
            else:
                query = (
                    db_session.query(Claim)
                    .filter(Claim.application.has(Application.user_id == current_user.user_id))  # type: ignore
                    .order_by(pagination_context.order_key)
                )

        page = page_for_api_context(pagination_context, query)

    logger.info(
        "get_claims success",
        extra={
            "is_employer": str(is_employer),
            "pagination.order_by": pagination_context.order_by,
            "pagination.order_direction": pagination_context.order_direction,
            "pagination.page_offset": pagination_context.page_offset,
            "pagination.total_pages": page.total_pages,
            "pagination.total_records": page.total_records,
        },
    )

    return response_util.paginated_success_response(
        message="Successfully retrieved claims",
        serializer=ClaimResponse(),
        page=page,
        context=pagination_context,
        status_code=200,
    ).to_api_response()
