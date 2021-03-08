import secrets
import string
import time
from typing import Optional, Union

import boto3
import botocore

import massgov.pfml.db as db
import massgov.pfml.util.logging
from massgov.pfml.cognito_post_confirmation_lambda.lib import leave_admin_create
from massgov.pfml.db.models.employees import User

ACTIVE_DIRECTORY_ATTRIBUTE = "sub"
logger = massgov.pfml.util.logging.get_logger(__name__)


class CognitoSubNotFound(Exception):
    pass


class CognitoLookupFailure(Exception):
    """ Error that represents an inability to complete the lookup successfully """

    pass


class CognitoAccountCreationFailure(Exception):
    pass


class CognitoPasswordSetFailure(Exception):
    pass


def create_cognito_client():
    return boto3.client("cognito-idp", region_name="us-east-1")


def generate_temp_password() -> str:
    alphabet = string.ascii_letters + string.digits + string.punctuation
    while True:
        has_punctuation = False
        has_upper = False
        has_lower = False
        has_number = False
        password = "".join(secrets.choice(alphabet) for i in range(16))
        for letter in password:
            if letter in string.punctuation:
                has_punctuation = True
            elif letter.isupper():
                has_upper = True
            elif letter.islower():
                has_lower = True
            elif letter in string.digits:
                has_number = True
        if has_punctuation and has_upper and has_lower and has_number:
            return password


def lookup_cognito_account_id(
    email: str,
    cognito_user_pool_id: str,
    cognito_client: Optional["botocore.client.CognitoIdentityProvider"] = None,
) -> Union[str, None]:
    if not cognito_client:
        cognito_client = create_cognito_client()
    retries = 0
    response = None
    while retries < 3:
        try:
            response = cognito_client.list_users(
                UserPoolId=cognito_user_pool_id, Limit=1, Filter=f'email="{email}"'
            )
        except botocore.exceptions.ClientError as err:
            if (
                err.response
                and err.response.get("Error", {}).get("Code") == "TooManyRequestsException"
            ):
                logger.info(
                    "Too many requests error from Cognito looking up %s; sleeping before retry",
                    email,
                )
                time.sleep(0.2)
            else:
                logger.warning("Error looking up user in Cognito", exc_info=err)
        else:
            break
    if not response and retries:
        raise CognitoLookupFailure("Cognito did not succeed at looking up email")

    if response and response["Users"]:
        for attr in response["Users"][0]["Attributes"]:
            if attr["Name"] == ACTIVE_DIRECTORY_ATTRIBUTE:
                return attr["Value"]
        raise CognitoSubNotFound("Cognito did not return an ID for the user!")
    return None


def create_verified_cognito_leave_admin_account(
    db_session: db.Session,
    email: str,
    fein: str,
    cognito_user_pool_id: str,
    cognito_client: Optional["botocore.client.CognitoIdentityProvider"] = None,
) -> User:
    """Create Cognito and API records for a leave admin with a verified email and temporary password"""

    active_directory_id: Optional[str] = None
    if cognito_client is None:
        cognito_client = create_cognito_client()
    temp_password = generate_temp_password()

    try:
        cognito_user = cognito_client.admin_create_user(
            UserPoolId=cognito_user_pool_id,
            Username=email,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "true"},
            ],
            DesiredDeliveryMediums=["EMAIL"],
            MessageAction="SUPPRESS",
        )
    except botocore.exceptions.ClientError as exc:
        logger.warning("Unable to create account for user", exc_info=exc)
        raise CognitoAccountCreationFailure("Unable to create account for user")

    for attr in cognito_user["User"]["Attributes"]:
        if attr["Name"] == ACTIVE_DIRECTORY_ATTRIBUTE:
            active_directory_id = attr["Value"]
            break

    if active_directory_id is None:
        raise CognitoSubNotFound("Cognito did not return an ID for the user!")

    try:
        cognito_client.admin_set_user_password(
            UserPoolId=cognito_user_pool_id, Username=email, Password=temp_password, Permanent=True
        )
    except botocore.exceptions.ClientError as exc:
        logger.warning("Unable to set password for user", exc_info=exc)
        raise CognitoPasswordSetFailure("Unable to set password for user")

    log_attributes = {
        "auth_id": active_directory_id,
    }
    return leave_admin_create(db_session, active_directory_id, email, fein, log_attributes)


def create_cognito_account(
    email_address: str,
    password: str,
    cognito_user_pool_client_id: str,
    cognito_client: Optional["botocore.client.CognitoIdentityProvider"] = None,
) -> str:
    """Sign up a new user in the Cognito user pool. Returns Cognito user sub."""
    if cognito_client is None:
        cognito_client = create_cognito_client()

    try:
        response = cognito_client.sign_up(
            ClientId=cognito_user_pool_client_id, Username=email_address, Password=password
        )
    except botocore.exceptions.ClientError as exc:
        # TODO (CP-1764): Handle the full range of Cognito exceptions:
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cognito-idp.html#CognitoIdentityProvider.Client.sign_up
        raise exc

    return response["UserSub"]
