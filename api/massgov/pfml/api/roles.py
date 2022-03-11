import connexion
from werkzeug.exceptions import BadRequest

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import EDIT, ensure
from massgov.pfml.api.models.roles.requests import RoleUserDeleteRequest
from massgov.pfml.api.util.deepgetattr import deepgetattr
from massgov.pfml.api.validation.user_rules import get_users_convert_claimant_issues
from massgov.pfml.db.models.employees import Role, User
from massgov.pfml.util.sqlalchemy import get_or_404
from massgov.pfml.util.users import remove_leave_admins_and_role

logger = massgov.pfml.util.logging.get_logger(__name__)


def roles_users_delete():
    """
    The only role deletion currently supported is the employer role.
    """
    body = RoleUserDeleteRequest.parse_obj(connexion.request.json)
    user_id = body.user_id
    role_description = deepgetattr(body, "role.role_description")
    delete_employer_role = role_description == Role.EMPLOYER.role_description

    with app.db_session() as db_session:
        user = get_or_404(db_session, User, user_id)
        ensure(EDIT, user)
        if delete_employer_role:
            convert_claimant_issues = get_users_convert_claimant_issues(user)
            if convert_claimant_issues:
                logger.info(
                    "roles_users_delete failure - Couldn't convert user to claimant account"
                )
                return response_util.error_response(
                    status_code=BadRequest,
                    message="Couldn't convert user to claimant account",
                    errors=convert_claimant_issues,
                    data={},
                ).to_api_response()
            remove_leave_admins_and_role(db_session, user)
            return response_util.success_response(
                message="Role was deleted from user successfully", status_code=200, data={}
            ).to_api_response()
    logger.warning(
        "Unsupported role deletion", extra=dict(role_description=role_description, user_id=user_id)
    )
    return response_util.error_response(
        status_code=BadRequest, message="Unsupported role deletion", errors=[], data={}
    ).to_api_response()
