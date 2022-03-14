from typing import Dict, List, Optional, Union

import botocore

import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.cognito.exceptions import CognitoUserExistsValidationError
from massgov.pfml.db.models.employees import (
    Employer,
    LkRole,
    Role,
    User,
    UserLeaveAdministrator,
    UserRole,
)
from massgov.pfml.util.aws.cognito import create_cognito_account

logger = massgov.pfml.util.logging.get_logger(__name__)


def create_user(
    db_session: db.Session,
    email_address: str,
    auth_id: str,
    employer_for_leave_admin: Optional[Employer],
) -> User:
    """Create API records for a new user (claimant or leave admin)"""
    user = User(sub_id=auth_id, email_address=email_address)

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
    user_leave_admin = UserLeaveAdministrator(user=user, employer=employer, fineos_web_id=None)
    db_session.add(user_role)
    db_session.add(user_leave_admin)
    return user


def remove_leave_admins_and_role(db_session: db.Session, user: User) -> User:
    """A helper function to remove the employer role and leave admin link from the user"""
    # user.user_leave_administrators.remove(la) causes a not-null violation
    # since it tries to set the user_id to NULL.
    row_count = (
        db_session.query(UserLeaveAdministrator)
        .filter(UserLeaveAdministrator.user_id == user.user_id)
        .delete()
    )
    logger.info(
        "deleted from link_user_leave_administrator",
        extra=dict(count=row_count, user_id=user.user_id),
    )
    row_count = (
        db_session.query(UserRole)
        .filter(UserRole.user_id == user.user_id and UserRole.role_id == Role.EMPLOYER.role_id)
        .delete()
    )
    logger.info("deleted from link_user_role", extra=dict(count=row_count, user_id=user.user_id))
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


def has_role_in(user: User, accepted_roles: List[LkRole]) -> bool:
    accepted_role_ids = set(role.role_id for role in accepted_roles)
    for role in user.roles:
        if role.role_id in accepted_role_ids:
            return True

    return False


def get_user_log_attributes(user: User) -> Dict[str, Union[bool, str, None]]:
    attributes: Dict[str, Union[bool, str, None]] = {
        "current_user.user_id": str(user.user_id),
        "current_user.auth_id": str(user.sub_id),
        "current_user.role_ids": ",".join(str(role.role_id) for role in user.roles),
        "current_user.role_names": ",".join(str(role.role_description) for role in user.roles),
    }

    for role in user.roles:
        attributes[f"current_user.has_role_id_{role.role_id}"] = True
        attributes[f"current_user.has_role_{role.role_description}"] = True

    return attributes
