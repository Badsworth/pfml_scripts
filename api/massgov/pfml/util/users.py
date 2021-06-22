from typing import Dict, Optional, Tuple

import boto3
import botocore
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import MultipleResultsFound

import massgov.pfml.cognito_post_confirmation_lambda.lib as lib
import massgov.pfml.util.logging
from massgov.pfml import db, fineos
from massgov.pfml.api.services.administrator_fineos_actions import (
    RegisterFINEOSDuplicateRecord,
    register_leave_admin_with_fineos,
)
from massgov.pfml.db.models.employees import Employer, Role, User, UserLeaveAdministrator, UserRole
from massgov.pfml.util.aws.cognito import (
    CognitoAccountCreationFailure,
    CognitoLookupFailure,
    CognitoPasswordSetFailure,
    CognitoUserExistsValidationError,
    create_cognito_account,
    create_verified_cognito_leave_admin_account,
    lookup_cognito_account_id,
)
from massgov.pfml.util.employers import lookup_employer

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
        "employer_id": employer_for_leave_admin.employer_id if employer_for_leave_admin else None,
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
        if error.active_directory_id or error.sub_id:
            auth_id = str(error.sub_id if error.sub_id else error.active_directory_id)
            existing_user = (
                db_session.query(User)
                .filter(or_(User.active_directory_id == auth_id, User.sub_id == auth_id,))
                .one_or_none()
            )

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


def register_or_update_leave_admin(
    db_session: db.Session,
    fein: str,
    email: str,
    force_registration: bool,
    cognito_pool_id: str,
    cognito_client: Optional["botocore.client.CognitoIdentityProvider"] = None,
    fineos_client: Optional[fineos.AbstractFINEOSClient] = None,
) -> Tuple[bool, str]:
    """Create or update Cognito and API records for a Leave Admin.
    Creates a Cognito user with a verified email and generated password, if a user doesn't already exist
    """

    if not cognito_client:
        cognito_client = boto3.client("cognito-idp", region_name="us-east-1")

    requested_employer = lookup_employer(db_session=db_session, employer_fein=fein)
    if not requested_employer:
        logger.warning("No employer found %s", fein, extra={"FEIN": fein})
        return False, "No employer found"

    try:
        existing_cognito_id = lookup_cognito_account_id(
            email=email, cognito_user_pool_id=cognito_pool_id, cognito_client=cognito_client
        )
    except CognitoLookupFailure:
        return False, "Unable to look up user in Cognito"

    if existing_cognito_id:
        # We may or may not need to create user records
        logger.debug("Existing cognito user found", extra={"auth_id": existing_cognito_id})
        try:
            user = (
                db_session.query(User)
                .filter(
                    or_(
                        User.active_directory_id == existing_cognito_id,
                        User.sub_id == existing_cognito_id,
                    )
                )
                .one_or_none()
            )
        except MultipleResultsFound:
            return False, "Multiple User records found in database"
        if user:
            logger.debug("Existing PFML user found", extra={"user_id": user.user_id})
        else:
            try:
                user = lib.leave_admin_create(
                    db_session, existing_cognito_id, email, fein, {"auth_id": existing_cognito_id}
                )
            except lib.LeaveAdminCreationError:
                return False, "Unable to create database records for user"
        if not user.roles:
            try:
                db_session.add(UserRole(user=user, role_id=Role.EMPLOYER.role_id))
                db_session.commit()
            except SQLAlchemyError as exc:
                logger.warning(
                    "Unable to store UserRole record or commit transaction", exc_info=exc
                )
                return False, "Unable to store UserRole record or commit transaction"
    else:
        logger.debug("Creating new Cognito user", extra={"email": email})
        try:
            user = create_verified_cognito_leave_admin_account(
                db_session=db_session,
                email=email,
                fein=fein,
                cognito_user_pool_id=cognito_pool_id,
                cognito_client=cognito_client,
            )
        except lib.LeaveAdminCreationError:
            return False, "Unable to create records for user"
        except CognitoAccountCreationFailure:
            return False, "Unable to create Cognito account for user"
        except CognitoPasswordSetFailure:
            return False, "Unable to set Cognito password for user"

    if not force_registration:
        return True, "Successfully added user to Cognito and API DB"

    retry_count = 0
    while retry_count < 3:
        try:
            register_leave_admin_with_fineos(
                # TODO: Set a real admin full name - https://lwd.atlassian.net/browse/EMPLOYER-540
                admin_full_name="Leave Administrator",
                admin_email=email,
                admin_area_code=None,
                admin_phone_number=None,
                employer=requested_employer,
                user=user,
                db_session=db_session,
                fineos_client=fineos_client,
            )
        except RegisterFINEOSDuplicateRecord:
            logger.warning(
                "Duplicate user leave administrators found for user_id %s, employer_id %s",
                user.user_id,
                requested_employer.employer_id,
            )
            return False, "Duplicate user leave administrators found"
        except Exception as e:
            logger.warning("Received an error processing FINEOS registration ", exc_info=e)
            retry_count += 1
        else:
            return True, "Successed!"
    return False, "Unable to register user in FINEOS"
