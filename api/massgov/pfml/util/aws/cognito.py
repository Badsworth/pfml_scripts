import secrets
import string
from typing import Optional

import boto3

import massgov.pfml.db as db
from massgov.pfml.cognito_post_confirmation_lambda.lib import leave_admin_create

ACTIVE_DIRECTORY_ATTRIBUTE = "sub"

db_config = db.get_config()
db_session_raw = db.init(db_config)


def generate_temp_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for i in range(10))  # for a 10-character password


def create_cognito_leave_admin_account(email: str, fein: str, cognito_user_pool_id: str) -> None:
    with db.session_scope(db_session_raw, close=True) as db_session:
        active_directory_id: Optional[str] = None
        cognito_client = boto3.client("cognito-idp", region_name="us-east-1")
        temp_password = generate_temp_password()
        cognito_user = cognito_client.admin_create_user(
            UserPoolId=cognito_user_pool_id,
            Username=email,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "true"},
            ],
            TemporaryPassword=temp_password,
            DesiredDeliveryMediums=["EMAIL"],
        )

        for attr in cognito_user["User"]["Attributes"]:
            if attr["Name"] == ACTIVE_DIRECTORY_ATTRIBUTE:
                active_directory_id = attr["Value"]
                break

        if active_directory_id is None:
            raise Exception("Cognito did not return an ID for the user!")

        leave_admin_create(db_session, active_directory_id, email, fein)
