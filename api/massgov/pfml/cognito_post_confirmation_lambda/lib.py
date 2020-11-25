import re
from typing import Any, Dict, Literal, Optional

import boto3

import massgov.pfml.util.aws_lambda as aws_lambda
import massgov.pfml.util.config as config
import massgov.pfml.util.logging
from massgov.pfml import db, fineos
from massgov.pfml.api.services.administrator_fineos_actions import register_leave_admin_with_fineos
from massgov.pfml.db.models.employees import Employer, Role, User, UserRole

logger = massgov.pfml.util.logging.get_logger(__name__)

fineos_client_config = fineos.factory.FINEOSClientConfig.from_env()
if fineos_client_config.oauth2_client_secret is None:
    aws_ssm = boto3.client("ssm", region_name="us-east-1")
    fineos_client_config.oauth2_client_secret = config.get_secret_from_env(
        aws_ssm, "FINEOS_CLIENT_OAUTH2_CLIENT_SECRET"
    )

fineos_client = fineos.create_client(fineos_client_config)


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

    logger.info(
        "handle post confirmation event",
        extra={
            "triggerSource": event.triggerSource,
            "isEmployer": cognito_metadata is not None and "ein" in cognito_metadata,
        },
    )
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
        return event

    if cognito_metadata is not None and "ein" in cognito_metadata:
        logger.info("Creating a leave administrator account")
        leave_admin_create(
            db_session=db_session,
            active_directory_id=cognito_user_attrs["sub"],
            email=cognito_user_attrs["email"],
            employer_fein=re.sub("-", "", cognito_metadata["ein"]),
        )

        return event

    user = User(
        active_directory_id=cognito_user_attrs["sub"], email_address=cognito_user_attrs["email"],
    )
    logger.info(
        "Creating a claimant account", extra={"active_directory_id": user.active_directory_id}
    )

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

    logger.info("Creating user in Fineos")

    register_leave_admin_with_fineos(
        # TODO: Set a real admin full name - https://lwd.atlassian.net/browse/EMPLOYER-540
        admin_full_name="Leave Administrator",
        admin_email=email,
        admin_area_code=None,
        admin_phone_number=None,
        employer=employer,
        user=user,
        db_session=db_session,
        fineos_client=fineos_client,
    )

    db_session.commit()

    return user
