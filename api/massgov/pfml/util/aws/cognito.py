import secrets
import string
from typing import Optional, Union

import boto3
import botocore

import massgov.pfml.db as db
from massgov.pfml.cognito_post_confirmation_lambda.lib import leave_admin_create
from massgov.pfml.db.models.employees import User

ACTIVE_DIRECTORY_ATTRIBUTE = "sub"


class CognitoSubNotFound(Exception):
    pass


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
        cognito_client = boto3.client("cognito-idp", region_name="us-east-1")
    response = cognito_client.list_users(
        UserPoolId=cognito_user_pool_id, Limit=1, Filter=f'email="{email}"'
    )
    if response["Users"]:
        for attr in response["Users"][0]["Attributes"]:
            if attr["Name"] == ACTIVE_DIRECTORY_ATTRIBUTE:
                return attr["Value"]
        raise CognitoSubNotFound("Cognito did not return an ID for the user!")
    return None


def create_cognito_leave_admin_account(
    db_session: db.Session,
    email: str,
    fein: str,
    cognito_user_pool_id: str,
    cognito_client: Optional["botocore.client.CognitoIdentityProvider"] = None,
) -> User:
    active_directory_id: Optional[str] = None
    if cognito_client is None:
        cognito_client = boto3.client("cognito-idp", region_name="us-east-1")
    temp_password = generate_temp_password()

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

    for attr in cognito_user["User"]["Attributes"]:
        if attr["Name"] == ACTIVE_DIRECTORY_ATTRIBUTE:
            active_directory_id = attr["Value"]
            break

    if active_directory_id is None:
        raise CognitoSubNotFound("Cognito did not return an ID for the user!")

    cognito_client.admin_set_user_password(
        UserPoolId=cognito_user_pool_id, Username=email, Password=temp_password, Permanent=True
    )

    log_attributes = {
        "auth_id": active_directory_id,
    }
    return leave_admin_create(db_session, active_directory_id, email, fein, log_attributes)
