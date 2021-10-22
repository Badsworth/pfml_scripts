from typing import Dict, Optional

import botocore

import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.cognito.exceptions import CognitoUserExistsValidationError
from massgov.pfml.db.models.employees import Employer, Role, User, UserLeaveAdministrator, UserRole
from massgov.pfml.util.aws.cognito import create_cognito_account

logger = massgov.pfml.util.logging.get_logger(__name__)


def create_user(
    db_session: db.Session,
    email_address: str,
    auth_id: str,
    employer_for_leave_admin: Optional[Employer],
) -> User:
    """Create API records for a new user (claimant or leave admin)"""
    user = User(sub_id=auth_id, email_address=email_address,)

    try:
        db_session.add(user)

        if employer_for_leave_admin:
            add_leave_admin_and_role(db_session, user, employer_for_leave_admin)

        db_session.commit()
    except Exception as error:
        logger.warning(
            # Alarm policy may be configured based on this message. Check before changing it.
            "API User records failed to save, but a Cognito account was created. User account is now in a bad state.",
            extra=get_register_user_log_attributes(employer_for_leave_admin, auth_id),
            exc_info=True,
        )
        raise error

    return user


def add_leave_admin_and_role(db_session: db.Session, user: User, employer: Employer) -> User:
    """A helper function to create the first user leave admin and role"""
    user_role = UserRole(user=user, role_id=Role.EMPLOYER.role_id)
    user_leave_admin = UserLeaveAdministrator(user=user, employer=employer, fineos_web_id=None,)
    db_session.add(user_role)
    db_session.add(user_leave_admin)
    return user


def get_register_user_log_attributes(
    employer_for_leave_admin: Optional[Employer], auth_id: Optional[str] = None
) -> Dict[str, Optional[str]]:
    """Extra data to include in register_user logs"""

    # This log should provide enough info to support manually creating records if necessary
    return {
        "current_user.auth_id": auth_id,
        "employer_id": str(employer_for_leave_admin.employer_id)
        if employer_for_leave_admin
        else None,
        "is_employer": str(employer_for_leave_admin is not None),
    }


def register_user(
    db_session: db.Session,
    cognito_user_pool_id: str,
    cognito_user_pool_client_id: str,
    email_address: str,
    password: str,
    employer_for_leave_admin: Optional[Employer] = None,
    cognito_client: Optional["botocore.client.CognitoIdentityProvider"] = None,
) -> User:
    """Create a new Cognito and API user for authenticating and performing authenticated API requests

    Raises
    ------
    - CognitoValidationError
    - CognitoAccountCreationFailure
    """

    try:
        auth_id = create_cognito_account(
            email_address,
            password,
            cognito_user_pool_id,
            cognito_user_pool_client_id,
            cognito_client=cognito_client,
        )
        logger.info(
            "Successfully created Cognito user",
            extra=get_register_user_log_attributes(employer_for_leave_admin, auth_id),
        )
    except CognitoUserExistsValidationError as error:
        # Cognito user already exists, but confirm we have DB records for the user. If we do then reraise the error (bc claimant is trying to create a duplicate account) and if we don't then continue to create the DB records (bc somehow this step failed the last time).
        if error.sub_id:
            auth_id = str(error.sub_id)
            existing_user = db_session.query(User).filter(User.sub_id == auth_id).one_or_none()

            if existing_user is not None:
                raise error

            logger.warning(
                "Cognito user existed but DB records did not. Attempting to create DB records.",
                extra=get_register_user_log_attributes(employer_for_leave_admin, auth_id),
            )

    user = create_user(db_session, email_address, auth_id, employer_for_leave_admin)
    logger.info(
        "Successfully created User records",
        extra=get_register_user_log_attributes(employer_for_leave_admin, auth_id),
    )

    return user
