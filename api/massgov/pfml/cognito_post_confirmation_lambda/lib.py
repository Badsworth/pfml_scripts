from typing import Any, Dict, Literal, Optional

import massgov.pfml.db as db
import massgov.pfml.util.aws_lambda as aws_lambda
import massgov.pfml.util.logging
from massgov.pfml.api.services.administrator_fineos_actions import register_leave_admin_with_fineos
from massgov.pfml.db.models.employees import Employer, Role, User, UserRole

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

    user = (
        db_session.query(User)
        .filter(User.active_directory_id == cognito_user_attrs["sub"])
        .one_or_none()
    )

    if user is not None:
        logger.info(
            "active_directory_id already exists",
            extra={"active_directory_id": user.active_directory_id},
        )
    else:
        user = User(
            active_directory_id=cognito_user_attrs["sub"],
            email_address=cognito_user_attrs["email"],
        )
        logger.info("creating user", extra={"active_directory_id": user.active_directory_id})

        db_session.add(user)
        db_session.commit()

        logger.info("successfully created user", extra={"user_id": user.user_id})

    return event


def leave_admin_create(
    db_session: db.Session, active_directory_id: str, email: str, employer_fein: str,
) -> User:
    employer = (
        db_session.query(Employer).filter(Employer.employer_fein == employer_fein).one_or_none()
    )

    if employer is None:
        raise ValueError("Invalid employer_fein")

    user = User(active_directory_id=active_directory_id, email_address=email,)

    user_role = UserRole(user=user, role_id=Role.EMPLOYER.role_id)

    db_session.add(user)
    db_session.add(user_role)

    register_leave_admin_with_fineos(
        # TODO: Set a real admin full name - https://lwd.atlassian.net/browse/EMPLOYER-540
        admin_full_name="Leave Administrator",
        admin_email=email,
        admin_area_code=None,
        admin_phone_number=None,
        employer=employer,
        user=user,
        db_session=db_session,
    )

    db_session.commit()

    return user
