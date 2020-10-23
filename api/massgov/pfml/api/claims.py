import connexion
import flask
from werkzeug.exceptions import Forbidden, Unauthorized

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
from massgov.pfml.api.authorization.flask import READ, ensure, requires
from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.api.services.administrator_fineos_actions import (
    get_claim_as_leave_admin,
    get_documents_as_leave_admin,
)
from massgov.pfml.db.models.employees import Employer, UserLeaveAdministrator
from massgov.pfml.fineos.transforms.to_fineos.eforms import TransformEmployerClaimReview
from massgov.pfml.util.sqlalchemy import get_or_404


@requires(READ, "EMPLOYER_API")
def employer_update_claim_review(fineos_absence_id: str) -> flask.Response:
    body = connexion.request.json

    claim_request = EmployerClaimReview.parse_obj(body)

    TransformEmployerClaimReview.to_fineos(claim_request)

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
    with app.db_session() as db_session:
        # TODO EMPLOYER-458
        # Eventually will need to check for the existence of an Employer
        # in the context of this user as well aka
        # UserLeaveAdministrator.employer_id == selected_employer_id
        current_user = app.current_user()
        if current_user is None:
            raise Unauthorized()

        user_leave_admin = (
            db_session.query(UserLeaveAdministrator)
            .filter(UserLeaveAdministrator.user_id == current_user.user_id)
            .one_or_none()
        )

        if user_leave_admin is None:
            raise Forbidden(description="User is not a leave administrator")

        employer = get_or_404(db_session, Employer, user_leave_admin.employer_id)
        ensure(READ, employer)

        if user_leave_admin.fineos_web_id is None:
            raise Forbidden(description="User has no leave administrator FINEOS ID")

        claim = get_claim_as_leave_admin(
            user_leave_admin.fineos_web_id, fineos_absence_id, employer.employer_fein
        )
        return response_util.success_response(
            message="Successfully retrieved claim", data=claim.dict(), status_code=200
        ).to_api_response()


@requires(READ, "EMPLOYER_API")
def employer_get_claim_documents(fineos_absence_id: str) -> flask.Response:
    """
    Calls out to the FINEOS Group Client API to document data for a specified claim.
    The requesting user must be of the EMPLOYER role.
    """
    with app.db_session() as db_session:
        # TODO EMPLOYER-458
        # Eventually will need to check for the existence of an Employer
        # in the context of this user as well aka
        # UserLeaveAdministrator.employer_id == selected_employer_id
        current_user = app.current_user()
        if current_user is None:
            raise Unauthorized()

        user_leave_admin = (
            db_session.query(UserLeaveAdministrator)
            .filter(UserLeaveAdministrator.user_id == current_user.user_id)
            .one_or_none()
        )

        if user_leave_admin is None:
            raise Forbidden(description="User is not a leave administrator")

        if user_leave_admin.fineos_web_id is None:
            raise Forbidden(description="User has no leave administrator FINEOS ID")

        documents = get_documents_as_leave_admin(user_leave_admin.fineos_web_id, fineos_absence_id)
        documents_list = [doc.dict() for doc in documents]
        return response_util.success_response(
            message="Successfully retrieved documents", data=documents_list, status_code=200
        ).to_api_response()
