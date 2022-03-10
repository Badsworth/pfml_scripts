import time
from typing import Optional, Union

import boto3
import botocore
from botocore.exceptions import ClientError

import massgov.pfml.api.app as app
import massgov.pfml.util.logging
from massgov.pfml.api.validation.exceptions import IssueType, ValidationErrorDetail
from massgov.pfml.cognito.exceptions import (
    CognitoAccountCreationFailure,
    CognitoLookupFailure,
    CognitoSubNotFound,
    CognitoUserExistsValidationError,
    CognitoValidationError,
)

USER_ID_ATTRIBUTE = "sub"
USER_MFA_VERIFIED_ATTRIBUTE = "phone_number_verified"
logger = massgov.pfml.util.logging.get_logger(__name__)


def create_cognito_client():
    return boto3.client("cognito-idp", region_name="us-east-1")


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
            if attr["Name"] == USER_ID_ATTRIBUTE:
                return attr["Value"]

        raise CognitoSubNotFound("Cognito did not return an ID for the user!")
    return None


def is_mfa_phone_verified(email: str, cognito_user_pool_id: str) -> Union[bool, None]:
    cognito_client = create_cognito_client()
    response = cognito_client.admin_get_user(Username=email, UserPoolId=cognito_user_pool_id)

    if response and response["UserAttributes"]:
        for attr in response["UserAttributes"]:
            if attr["Name"] == USER_MFA_VERIFIED_ATTRIBUTE:
                return True if attr["Value"] == "true" else False

    return False


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
    sub_id
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
    except (
        cognito_client.exceptions.InvalidPasswordException,
        cognito_client.exceptions.InvalidParameterException,
    ) as error:
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

        issue = ValidationErrorDetail(field="password", type=issue_type, message=message)
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
        issue = ValidationErrorDetail(
            field="password", type=IssueType.invalid, message="{}".format(error)
        )
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


def set_user_mfa(email: str, mfa_enabled: bool, cognito_auth_token: str) -> None:
    cognito_client = create_cognito_client()

    try:
        cognito_client.set_user_mfa_preference(
            SMSMfaSettings={"Enabled": mfa_enabled,}, AccessToken=cognito_auth_token
        )
    except Exception as error:
        log_attr = {"mfa_enabled": mfa_enabled}
        if isinstance(error, ClientError) and "InvalidParameterException" in str(error.__class__):
            logger.error(
                "Error updating MFA preference in Cognito - Invalid parameter in request",
                exc_info=error,
                extra=log_attr,
            )
        elif isinstance(error, ClientError) and "UserNotFoundException" in str(error.__class__):
            logger.error(
                "Error updating MFA preference in Cognito - User not found",
                exc_info=error,
                extra=log_attr,
            )
        else:
            logger.error("Error updating MFA preference in Cognito", exc_info=error, extra=log_attr)

        raise error


def admin_disable_user_mfa(email: str) -> None:
    cognito_client = create_cognito_client()
    cognito_user_pool_id = app.get_config().cognito_user_pool_id

    try:
        cognito_client.admin_set_user_mfa_preference(
            SMSMfaSettings={"Enabled": False}, Username=email, UserPoolId=cognito_user_pool_id
        )
    except Exception as error:
        if isinstance(error, ClientError) and "InvalidParameterException" in str(error.__class__):
            logger.error(
                "Error disabling MFA preference in Cognito as admin - Invalid parameter in request",
                exc_info=error,
            )
        elif isinstance(error, ClientError) and "UserNotFoundException" in str(error.__class__):
            logger.error(
                "Error disabling MFA preference in Cognito as admin - User not found with email",
                exc_info=error,
            )
        else:
            logger.error("Error disabling MFA preference in Cognito as admin", exc_info=error)

        raise error
