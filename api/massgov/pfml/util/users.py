from typing import Optional, Tuple

import boto3
import botocore
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import MultipleResultsFound

import massgov.pfml.cognito_post_confirmation_lambda.lib as lib
import massgov.pfml.util.logging
from massgov.pfml import db, fineos
from massgov.pfml.api.services.administrator_fineos_actions import (
    RegisterFINEOSDuplicateRecord,
    register_leave_admin_with_fineos,
)
from massgov.pfml.db.models.employees import Role, User, UserRole
from massgov.pfml.util.aws.cognito import (
    CognitoAccountCreationFailure,
    CognitoLookupFailure,
    CognitoPasswordSetFailure,
    create_cognito_leave_admin_account,
    lookup_cognito_account_id,
)
from massgov.pfml.util.employers import lookup_employer

logger = massgov.pfml.util.logging.get_logger(__name__)


def create_or_update_user_record(
    db_session: db.Session,
    fein: str,
    email: str,
    cognito_pool_id: str,
    consume_use: Optional[bool] = False,
    cognito_client: Optional["botocore.client.CognitoIdentityProvider"] = None,
    fineos_client: Optional[fineos.AbstractFINEOSClient] = None,
) -> Tuple[bool, str]:
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
                .filter(User.active_directory_id == existing_cognito_id)
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
            user = create_cognito_leave_admin_account(
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
        except ValueError as e:
            logger.warning("Received an error processing FINEOS registration ", exc_info=e)
            retry_count += 1
        else:
            return True, "Successed!"
    return False, "Unable to register user in FINEOS"
