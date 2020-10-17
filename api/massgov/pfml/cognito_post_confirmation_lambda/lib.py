from typing import Any, Dict, Literal, Optional

from sqlalchemy.exc import IntegrityError

import massgov.pfml.db as db
import massgov.pfml.util.aws_lambda as aws_lambda
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import User

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
    # the Post Confirmation trigger also happens during password resets, we only
    # care about the sign up event
    if event.triggerSource != "PostConfirmation_ConfirmSignUp":
        return event

    cognito_user_attrs = event.request.userAttributes

    user = User(
        active_directory_id=cognito_user_attrs["sub"], email_address=cognito_user_attrs["email"],
    )

    logger.info("creating user", extra={"active_directory_id": user.active_directory_id})
    try:
        db_session.add(user)
        db_session.commit()

        logger.info("successfully created user", extra={"user_id": user.user_id})
    except IntegrityError as ie:
        if 'violates unique constraint "user_active_directory_id_key"' in str(ie):
            logger.info(
                "active_directory_id already exists",
                extra={"active_directory_id": cognito_user_attrs["sub"]},
            )
            db_session.rollback()
        else:
            db_session.rollback()
            raise ie

    return event
