import re
from typing import Any, Dict, Literal, Optional

from sqlalchemy.exc import SQLAlchemyError

import massgov.pfml.util.aws_lambda as aws_lambda
import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import Employer, Role, User, UserLeaveAdministrator, UserRole

logger = massgov.pfml.util.logging.get_logger(__name__)


class LeaveAdminCreationError(SQLAlchemyError):
    pass


class PostConfirmationEventRequest(aws_lambda.CognitoUserPoolEventRequest):
    clientMetadata: Optional[Dict[str, Any]] = None


class PostConfirmationEvent(aws_lambda.CognitoUserPoolEvent):
    """Cognito Post Confirmation Event

    https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-post-confirmation.html#cognito-user-pools-lambda-trigger-syntax-post-confirmation
    """

    triggerSource: Literal[
        "PostConfirmation_ConfirmForgotPassword", "PostConfirmation_ConfirmSignUp",
    ]

    request: PostConfirmationEventRequest


# https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-post-confirmation.html
def handler(
    db_session: db.Session, event: PostConfirmationEvent, context: aws_lambda.LambdaContext,
) -> PostConfirmationEvent:

    if event.triggerSource not in (
        "PostConfirmation_ConfirmForgotPassword",
        "PostConfirmation_ConfirmSignUp",
    ):
        return event

    cognito_user_attrs = event.request.userAttributes
    cognito_metadata = event.request.clientMetadata
    auth_id = cognito_user_attrs["sub"]
    is_employer = cognito_metadata is not None and "ein" in cognito_metadata

    log_attributes = {
        "triggerSource": event.triggerSource,
        "auth_id": cognito_user_attrs["sub"],
        "isEmployer": str(is_employer),
    }

    logger.info("Handle post confirmation event", extra=log_attributes)
    user = db_session.query(User).filter(User.active_directory_id == auth_id).one_or_none()

    if user is not None:
        logger.info(
            "User already exists", extra={**log_attributes, "user_id": user.user_id,},
        )
        return event

    if is_employer:
        assert cognito_metadata is not None
        assert "ein" in cognito_metadata

        logger.info("Creating a leave administrator account", extra=log_attributes)

        user = leave_admin_create(
            db_session=db_session,
            auth_id=cognito_user_attrs["sub"],
            email=cognito_user_attrs["email"],
            employer_fein=re.sub("-", "", cognito_metadata["ein"]),
            log_attributes=log_attributes,
        )

        logger.info(
            "Successfully created leave administrator account",
            extra={**log_attributes, "user_id": user.user_id,},
        )

        return event

    user = User(
        active_directory_id=cognito_user_attrs["sub"], email_address=cognito_user_attrs["email"],
    )
    logger.info("Creating a claimant account", extra=log_attributes)

    db_session.add(user)
    db_session.commit()

    logger.info(
        "Successfully created claimant account", extra={**log_attributes, "user_id": user.user_id,}
    )

    return event


def leave_admin_create(
    db_session: db.Session, auth_id: str, email: str, employer_fein: str, log_attributes: dict
) -> User:

    employer = (
        db_session.query(Employer).filter(Employer.employer_fein == employer_fein).one_or_none()
    )

    if employer is None:
        raise ValueError("Invalid employer_fein")

    user = User(active_directory_id=auth_id, email_address=email,)
    user_role = UserRole(user=user, role_id=Role.EMPLOYER.role_id)
    user_leave_admin = UserLeaveAdministrator(user=user, employer=employer, fineos_web_id=None,)
    try:
        db_session.add(user)
        db_session.add(user_role)
        db_session.add(user_leave_admin)
        db_session.commit()
    except SQLAlchemyError as exc:
        logger.exception("Unable to create records for user")
        raise LeaveAdminCreationError("Unable to create records for user") from exc

    return user
