import secrets
import string
import time
from typing import Optional, Union

import boto3
import botocore

import massgov.pfml.db as db
import massgov.pfml.util.logging
from massgov.pfml.api.util.response import Issue, IssueType
from massgov.pfml.cognito_post_confirmation_lambda.lib import leave_admin_create
from massgov.pfml.db.models.employees import User

ACTIVE_DIRECTORY_ATTRIBUTE = "sub"
logger = massgov.pfml.util.logging.get_logger(__name__)


# TODO (CP-1988): Move custom exceptions to an exceptions.py to follow the pattern we use for other modules
class CognitoSubNotFound(Exception):
    pass


class CognitoLookupFailure(Exception):
    """ Error that represents an inability to complete the lookup successfully """

    pass


class CognitoAccountCreationFailure(Exception):
    """Error creating a Cognito user that may not be due to a user/validation error. This does not include network-related errors."""

    pass


class CognitoValidationError(Exception):
    """Error raised due to a user-recoverable Cognito issue

    Attributes:
        message -- Cognito's explanation of the error
        issue -- used for communicating the error to the user
    """

    __slots__ = ["message", "issue"]

    def __init__(self, message: str, issue: Issue):
        self.message = message
        self.issue = issue


class CognitoUserExistsValidationError(CognitoValidationError):
    """Error raised due to a user with the provided email already existing in the Cognito user pool

    Attributes:
        message -- Cognito's explanation of the error
        active_directory_id -- Existing user's ID attribute
        issue -- used for communicating the error to the user
    """

    __slots__ = ["active_directory_id", "issue", "message"]

    def __init__(self, message: str, active_directory_id: Optional[str]):
        self.active_directory_id = active_directory_id
        self.message = message
        self.issue = Issue(field="email_address", type=IssueType.exists, message=message)


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

    # TODO (CP-1987) Use Boto's "Standard retry mode" instead of a custom implementation
    while retries < 3:
        retries += 1
        try:
            response = cognito_client.admin_get_user(
                Username=email, UserPoolId=cognito_user_pool_id
            )
        except cognito_client.exceptions.UserNotFoundException:
            return None
        except cognito_client.exceptions.TooManyRequestsException:
            logger.info("Too many requests error from Cognito; sleeping before retry")
            time.sleep(0.2)
        except botocore.exceptions.ClientError as err:
            logger.warning("Error looking up user in Cognito", exc_info=err)
        else:
            break

    if not response and retries:
        raise CognitoLookupFailure("Cognito did not succeed at looking up email")

    if response and response["UserAttributes"]:
        for attr in response["UserAttributes"]:
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
    cognito_user_pool_id: str,
    cognito_user_pool_client_id: str,
    cognito_client: Optional["botocore.client.CognitoIdentityProvider"] = None,
) -> str:
    """Sign up a new user in the Cognito user pool.

    Returns
    -------
    active_directory_id
        Cognito user sub (id)

    Raises
    ------
    - CognitoAccountCreationFailure
    - CognitoUserExistsValidationError
    - CognitoValidationError
    """

    if cognito_client is None:
        cognito_client = create_cognito_client()

    try:
        response = cognito_client.sign_up(
            ClientId=cognito_user_pool_client_id,
            Username=email_address,
            Password=password,
            ClientMetadata={
                # This can be read by a Pre-Sign up Cognito Lambda function
                "sign_up_source": "pfml_api"
            },
        )
    except cognito_client.exceptions.InvalidPasswordException as error:
        # Thrown for various reasons:
        # 1. When password doesn't conform to our password requirements (length, casing, characters)
        # 2. When password is a commonly used or compromised credential
        # Password requirements are defined on the Cognito user pool in our Terraform script
        message = error.response["Error"]["Message"]
        issue_type = (
            IssueType.insecure
            if "password cannot be used for security reasons" in message
            else IssueType.invalid
        )

        issue = Issue(field="password", type=issue_type, message=message)
        logger.info(
            "Cognito validation issue - InvalidPasswordException",
            extra={"cognito_error": issue.message},
        )

        raise CognitoValidationError(issue.message, issue) from error
    except botocore.exceptions.ParamValidationError as error:
        # Thrown for various reasons:
        # 1. When password is less than 6 characters
        # 2. When username isn't an email
        # Number 2 above will be caught by our OpenAPI validations, which check that email_address
        # is an email, so we interpret this error to indicate something is wrong with the password
        issue = Issue(field="password", type=IssueType.invalid, message="{}".format(error))
        logger.info(
            "Cognito validation issue - ParamValidationError",
            extra={"cognito_error": issue.message},
        )

        raise CognitoValidationError(issue.message, issue) from error
    except cognito_client.exceptions.UsernameExistsException as error:
        message = error.response["Error"]["Message"]
        existing_auth_id = lookup_cognito_account_id(
            email_address, cognito_user_pool_id, cognito_client
        )
        raise CognitoUserExistsValidationError(message, existing_auth_id) from error
    except botocore.exceptions.ClientError as error:
        logger.warning(
            # Alarm policy may be configured based on this message. Check before changing it.
            "Failed to add user to Cognito due to unexpected ClientError",
            extra={"error": error.response["Error"]},
            exc_info=True,
        )

        raise CognitoAccountCreationFailure(
            "create_cognito_account error: {}: {}".format(
                error.response["Error"]["Code"], error.response["Error"]["Message"]
            )
        ) from error

    return response["UserSub"]
