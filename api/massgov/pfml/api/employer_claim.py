"""
/employers/claims/ endpoints
"""

import base64
from typing import Dict, List, Optional, Union
from uuid import UUID

import connexion
import flask
from sqlalchemy.orm.session import Session
from werkzeug.exceptions import BadRequest, Forbidden

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.api.validation.claim_rules as claim_rules
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.exceptions import NotAuthorizedForAccess
from massgov.pfml.api.authorization.flask import READ, requires
from massgov.pfml.api.exceptions import ClaimWithdrawn, ObjectNotFound
from massgov.pfml.api.models.applications.common import OrganizationUnit
from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.api.models.claims.responses import ManagedRequirementResponse
from massgov.pfml.api.services.administrator_fineos_actions import (
    awaiting_leave_info,
    complete_claim_review,
    create_eform,
    download_document_as_leave_admin,
    get_claim_as_leave_admin,
    get_documents_as_leave_admin,
)
from massgov.pfml.api.services.claims import get_claim_from_db
from massgov.pfml.api.services.managed_requirements import update_employer_confirmation_requirements
from massgov.pfml.api.util.claims import user_has_access_to_claim
from massgov.pfml.api.validation.exceptions import (
    ContainsV1AndV2Eforms,
    IssueType,
    ValidationErrorDetail,
)
from massgov.pfml.db.models.employees import (
    Claim,
    Employer,
    ManagedRequirement,
    UserLeaveAdministrator,
)
from massgov.pfml.db.queries.absence_periods import sync_customer_api_absence_periods_to_db
from massgov.pfml.db.queries.managed_requirements import (
    commit_managed_requirements,
    create_or_update_managed_requirement_from_fineos,
)
from massgov.pfml.fineos.models.group_client_api import (
    Base64EncodedFileData,
    ManagedRequirementDetails,
)
from massgov.pfml.fineos.transforms.to_fineos.eforms.employer import (
    EmployerClaimReviewEFormBuilder,
    EmployerClaimReviewV1EFormBuilder,
)
from massgov.pfml.util.logging.absence_periods import log_absence_period_response
from massgov.pfml.util.logging.claims import (
    get_claim_log_attributes,
    get_claim_review_log_attributes,
    get_managed_requirements_log_attributes,
    log_managed_requirement,
)
from massgov.pfml.util.logging.employers import get_employer_log_attributes
from massgov.pfml.util.logging.managed_requirements import (
    get_managed_requirements_update_log_attributes,
    log_managed_requirement_issues,
)
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


def sync_managed_requirements(
    db_session: Session,
    claim: Claim,
    managed_requirements: List[ManagedRequirementDetails],
    log_attributes: dict,
) -> List[ManagedRequirement]:
    """
    Note that commit to db is the responsibility of called functions.
    """
    managed_requirements_from_db = []
    for mr in managed_requirements:
        managed_requirement = create_or_update_managed_requirement_from_fineos(
            db_session, claim.claim_id, mr, log_attributes
        )
        if managed_requirement is not None:
            managed_requirements_from_db.append(managed_requirement)
    commit_managed_requirements(db_session)
    return managed_requirements_from_db


def get_current_user_leave_admin_record(fineos_absence_id: str) -> UserLeaveAdministrator:
    with app.db_session() as db_session:
        associated_employer_id: Optional[UUID] = None

        current_user = app.current_user()

        claim = get_claim_from_db(fineos_absence_id)

        if claim is not None:
            associated_employer_id = claim.employer_id

        if claim is None or associated_employer_id is None:
            logger.warning(
                "Claim does not exist for given absence ID",
                extra={"absence_case_id": fineos_absence_id},
            )
            raise Forbidden(description="Claim does not exist for given absence ID")

        user_leave_admin = (
            db_session.query(UserLeaveAdministrator)
            .filter(
                (UserLeaveAdministrator.user_id == current_user.user_id)
                & (UserLeaveAdministrator.employer_id == associated_employer_id)
            )
            .one_or_none()
        )

        log_attributes = {
            "absence_case_id": fineos_absence_id,
            "user_id": current_user.user_id,
            "associated_employer_id": associated_employer_id,
        }

        if user_leave_admin is None:
            logger.warning(
                "The leave admin is None",
                extra=log_attributes,
            )
            raise NotAuthorizedForAccess(
                description="User does not have leave administrator record for this employer",
                error_type=IssueType.unauthorized_leave_admin,
            )

        if user_leave_admin.fineos_web_id is None:
            logger.warning(
                "The leave admin has no FINEOS ID",
                extra=log_attributes,
            )
            raise VerificationRequired(
                user_leave_admin, "User has no leave administrator FINEOS ID"
            )

        if not user_leave_admin.verified:
            logger.warning(
                "The leave admin is not verified",
                extra=log_attributes,
            )
            raise VerificationRequired(user_leave_admin, "User is not Verified")

        if not user_has_access_to_claim(claim, current_user):
            logger.warning(
                "The leave admin cannot access claims of this organization unit",
                extra={
                    "has_verification_data": user_leave_admin.employer.has_verification_data,
                    "claim_organization_unit": OrganizationUnit.from_orm(
                        claim.organization_unit
                    ).dict(),
                    "leave_admin_fineos_web_id": user_leave_admin.fineos_web_id,
                    "leave_admin_organization_unit_ids": ",".join(
                        [str(o.organization_unit_id) for o in user_leave_admin.organization_units]
                    ),
                    **log_attributes,
                },
            )
            raise NotAuthorizedForAccess(
                description="The leave admin cannot access claims of this organization unit",
                error_type="unauthorized_leave_admin",
            )

        return user_leave_admin


@requires(READ, "EMPLOYER_API")
def employer_document_download(fineos_absence_id: str, fineos_document_id: str) -> flask.Response:
    """
    Calls out to the FINEOS Group Client API to download a document for a specified claim.
    The requesting user must be of the EMPLOYER role.

    GET /employers/claims/{fineos_absence_id}/documents/{fineos_document_id}
    """

    log_attr: Dict[str, Union[str, int]] = {}

    try:
        user_leave_admin = get_current_user_leave_admin_record(fineos_absence_id)
    except NotAuthorizedForAccess as not_authorized:
        logger.error(
            f"employer_document_download failed - {not_authorized.description}",
            extra=log_attr,
        )
        return not_authorized.to_api_response()
    except VerificationRequired as not_verified:
        logger.error(
            f"employer_document_download failed - {not_verified.description}",
            extra=log_attr,
        )
        return not_verified.to_api_response()
    log_attr.update(get_employer_log_attributes(user_leave_admin.user))

    try:
        document_data: Base64EncodedFileData = download_document_as_leave_admin(
            user_leave_admin.fineos_web_id, fineos_absence_id, fineos_document_id, log_attr  # type: ignore
        )
    except ObjectNotFound as not_found:
        logger.error(
            f"employer_document_download failed - {not_found.description}",
            extra=log_attr,
        )
        return not_found.to_api_response()
    except NotAuthorizedForAccess as not_authorized:
        logger.error(
            f"employer_document_download failed - {not_authorized.description}",
            extra=log_attr,
        )
        return not_authorized.to_api_response()

    file_bytes = base64.b64decode(document_data.base64EncodedFileContents.encode("ascii"))
    content_type = document_data.contentType or "application/octet-stream"
    claim = get_claim_from_db(fineos_absence_id)
    if claim:
        log_attr.update(get_claim_log_attributes(claim))

    logger.info(
        "employer_document_download success",
        extra=log_attr,
    )
    return flask.Response(
        file_bytes,
        content_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={document_data.fileName}"},
    )


@requires(READ, "EMPLOYER_API")
def employer_get_claim_documents(fineos_absence_id: str) -> flask.Response:
    """
    Calls out to the FINEOS Group Client API to get a list of documents attached to a specified claim.
    The requesting user must be of the EMPLOYER role.

    GET /employers/claims/{fineos_absence_id}/documents
    """
    try:
        user_leave_admin = get_current_user_leave_admin_record(fineos_absence_id)
    except (VerificationRequired, NotAuthorizedForAccess) as error:
        return error.to_api_response()

    documents = get_documents_as_leave_admin(user_leave_admin.fineos_web_id, fineos_absence_id)  # type: ignore
    documents_list = [doc.dict() for doc in documents]

    log_attributes = get_employer_log_attributes(user_leave_admin.user)

    claim = get_claim_from_db(fineos_absence_id)
    if claim:
        log_attributes.update(get_claim_log_attributes(claim))

    logger.info(
        "employer_get_claim_documents success",
        extra={**log_attributes},
    )
    return response_util.success_response(
        message="Successfully retrieved documents", data=documents_list, status_code=200
    ).to_api_response()


@requires(READ, "EMPLOYER_API")
def employer_get_claim_review(fineos_absence_id: str) -> flask.Response:
    """
    Calls out to various FINEOS API endpoints to retrieve leave data.
    The requesting user must be of the EMPLOYER role.
    """
    try:
        user_leave_admin = get_current_user_leave_admin_record(fineos_absence_id)
    except (VerificationRequired, NotAuthorizedForAccess) as error:
        return error.to_api_response()

    log_attributes = get_employer_log_attributes(user_leave_admin.user)
    log_attributes = {"absence_case_id": fineos_absence_id, **log_attributes}

    # get_claim_as_leave_admin takes str for the first argument;
    # this effectively unwraps Optional[str] to be used as str,
    # satisfying the type requirement for mypy.
    # It is not expected that this will ever raise an AssertionError.
    assert user_leave_admin.fineos_web_id is not None

    with app.db_session() as db_session:
        employer = get_or_404(db_session, Employer, user_leave_admin.employer_id)

        try:
            (
                fineos_claim_review_response,
                fineos_managed_requirements,
                fineos_absence_periods,
            ) = get_claim_as_leave_admin(
                user_leave_admin.fineos_web_id,
                fineos_absence_id,
                employer,
                db_session,
            )
        except (ContainsV1AndV2Eforms) as error:
            return response_util.error_response(
                status_code=error.status_code,
                message=error.description,
                errors=[
                    ValidationErrorDetail(
                        message="Claim contains both V1 and V2 eforms.",
                        type=IssueType.contains_v1_and_v2_eforms,
                    )
                ],
                data={},
            ).to_api_response()
        except ClaimWithdrawn as error:
            return error.to_api_response()

        claim_from_db = get_claim_from_db(fineos_absence_id)

        # If claim exists, handle db sync side effects and updates to response object
        if claim_from_db:
            log_attributes.update(get_claim_log_attributes(claim_from_db))
            # TODO (PORTAL-1962): Set missing Claim.employee association using employee SSN retrieved from Fineos

            if claim_from_db.fineos_absence_status:
                fineos_claim_review_response.status = (
                    claim_from_db.fineos_absence_status.absence_status_description
                )

            db_absence_periods = sync_customer_api_absence_periods_to_db(
                fineos_absence_periods, claim_from_db, db_session, log_attributes
            )

            managed_requirements = sync_managed_requirements(
                db_session,
                claim_from_db,
                fineos_managed_requirements,
                log_attributes,
            )

            updated_db_requirements = (
                db_session.query(ManagedRequirement)
                .filter(ManagedRequirement.claim_id == claim_from_db.claim_id)
                .all()
            )

            log_managed_requirement_issues(
                fineos_managed_requirements,
                updated_db_requirements,
                db_absence_periods,
                log_attributes,
            )
            fineos_claim_review_response.managed_requirements = [
                ManagedRequirementResponse.from_orm(mr) for mr in managed_requirements
            ]

            log_attributes.update(
                get_managed_requirements_log_attributes(
                    fineos_claim_review_response.managed_requirements
                )
            )
            for requirement in fineos_claim_review_response.managed_requirements:
                log_managed_requirement(requirement, fineos_absence_id)

        log_attributes.update(
            {
                "num_absence_periods": len(fineos_claim_review_response.absence_periods),
            }
        )

        for period in fineos_claim_review_response.absence_periods:
            log_absence_period_response(
                fineos_absence_id, period, "get_claim_review - Found absence period for claim"
            )

        logger.info(
            "employer_get_claim_review success",
            extra=log_attributes,
        )
        return response_util.success_response(
            message="Successfully retrieved claim",
            data=fineos_claim_review_response.dict(),
            status_code=200,
        ).to_api_response()


@requires(READ, "EMPLOYER_API")
def employer_update_claim_review(fineos_absence_id: str) -> flask.Response:
    current_user = app.current_user()
    body = connexion.request.json
    claim_review: EmployerClaimReview = EmployerClaimReview.parse_obj(body)

    if issues := claim_rules.get_employer_claim_review_issues(claim_review):
        return response_util.error_response(
            status_code=BadRequest,
            message="Invalid claim review body",
            errors=issues,
            data={},
        ).to_api_response()

    try:
        user_leave_admin = get_current_user_leave_admin_record(fineos_absence_id)
    except (VerificationRequired, NotAuthorizedForAccess) as error:
        return error.to_api_response()

    claim = get_claim_from_db(fineos_absence_id)

    log_attributes: Dict[str, Union[bool, str, int, UUID, None]]

    log_attributes = {
        "absence_case_id": fineos_absence_id,
        "user_leave_admin.employer_id": user_leave_admin.employer_id,
        **get_claim_review_log_attributes(claim_review),
        **get_employer_log_attributes(current_user),
        **get_claim_log_attributes(claim),
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
                ValidationErrorDetail(
                    type=IssueType.outstanding_information_request_required,
                    message="No outstanding information request for claim",
                )
            ],
        ).to_api_response()

    if (
        claim_review.employer_decision == "Approve"
        and not claim_review.has_amendments
        and not claim_review.comment
        and not claim_review.relationship_inaccurate_reason
    ):
        complete_claim_review(fineos_web_id, fineos_absence_id)
        logger.info("Completed claim review", extra=log_attributes)
    else:
        if claim_review.uses_second_eform_version:
            transformed_eform = EmployerClaimReviewEFormBuilder.build(claim_review)
            create_eform(fineos_web_id, fineos_absence_id, transformed_eform)
            logger.info("Created v2 eform", extra=log_attributes)
        else:
            transformed_eform = EmployerClaimReviewV1EFormBuilder.build(claim_review)
            create_eform(fineos_web_id, fineos_absence_id, transformed_eform)
            logger.info("Created eform", extra=log_attributes)

    logger.info("Updated claim", extra=log_attributes)
    with app.db_session() as db_session:
        # Try updating managed requirements after claim update
        try:
            fineos = massgov.pfml.fineos.create_client()
            fineos_managed_requirements = fineos.get_managed_requirements(
                str(fineos_web_id), fineos_absence_id
            )

            updated_managed_requirements = update_employer_confirmation_requirements(
                db_session,
                user_leave_admin.user_id,
                fineos_managed_requirements,
            )

            log_attributes = {
                **log_attributes,
                **get_managed_requirements_update_log_attributes(
                    fineos_managed_requirements, updated_managed_requirements
                ),
            }

        # On exception, log the error and pass so API returns normally
        except Exception as ex:
            logger.warning(
                "Unable to update managed requirements", exc_info=ex, extra=log_attributes
            )
            db_session.rollback()

    claim_response = {"claim_id": fineos_absence_id}
    return response_util.success_response(
        message="Successfully updated claim",
        data=claim_response,
    ).to_api_response()
