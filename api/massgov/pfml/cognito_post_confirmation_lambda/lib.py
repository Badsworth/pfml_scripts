import re
from typing import Any, Dict, Literal, Optional

from sqlalchemy.exc import SQLAlchemyError

import massgov.pfml.util.aws_lambda as aws_lambda
import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import Employer, Role, User, UserLeaveAdministrator, UserRole
from massgov.pfml.util.employers import lookup_employer
from massgov.pfml.util.users import leave_admin_create

logger = massgov.pfml.util.logging.get_logger(__name__)


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

        employer = lookup_employer(db_session, re.sub("-", "", cognito_metadata["ein"]))
        if employer is None:
            raise ValueError("Invalid employer_fein")

        user = leave_admin_create(
            db_session=db_session,
            user=User(
                active_directory_id=cognito_user_attrs["sub"],
                email_address=cognito_user_attrs["email"],
            ),
            employer=employer,
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
