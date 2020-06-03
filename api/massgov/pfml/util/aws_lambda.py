from typing import Any, Dict, Literal

from pydantic import BaseModel


class LambdaCognitoIdentity(BaseModel):
    cognito_identity_id: str
    cognito_identity_pool_id: str


class LambdaClientContextMobileClient(BaseModel):
    installation_id: str
    app_title: str
    app_version_name: str
    app_version_code: str
    app_package_name: str


class LambdaClientContext(BaseModel):
    client: LambdaClientContextMobileClient
    custom: Dict[str, Any]
    env: Dict[str, Any]


class LambdaContext(BaseModel):
    """AWS Lambda context object

    https://docs.aws.amazon.com/lambda/latest/dg/python-context.html
    """

    function_name: str
    function_version: str
    invoked_function_arn: str
    memory_limit_in_mb: int
    aws_request_id: str
    log_group_name: str
    log_stream_name: str
    identity: LambdaCognitoIdentity
    client_context: LambdaClientContext

    @staticmethod
    def get_remaining_time_in_millis() -> int:
        return 0


class CognitoUserPoolEventCallerContext(BaseModel):
    awsSdkVersion: str
    clientId: str


class CognitoUserPoolEventRequest(BaseModel):
    userAttributes: Dict[str, Any]


class CognitoUserPoolEvent(BaseModel):
    """General User Pool Trigger Event

    https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools-working-with-aws-lambda-triggers.html#cognito-user-pools-lambda-trigger-event-parameter-shared
    """

    version: str
    # https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools-working-with-aws-lambda-triggers.html#cognito-user-identity-pools-working-with-aws-lambda-trigger-sources
    triggerSource: Literal[
        "CreateAuthChallenge_Authentication",
        "CustomMessage_AdminCreateUser",
        "CustomMessage_Authentication",
        "CustomMessage_ForgotPassword",
        "CustomMessage_ResendCode",
        "CustomMessage_SignUp",
        "CustomMessage_UpdateUserAttribute",
        "CustomMessage_VerifyUserAttribute",
        "DefineAuthChallenge_Authentication",
        "PostAuthentication_Authentication",
        "PostConfirmation_ConfirmForgotPassword",
        "PostConfirmation_ConfirmSignUp",
        "PreAuthentication_Authentication",
        "PreSignUp_AdminCreateUser",
        "PreSignUp_ExternalProvider",
        "PreSignUp_SignUp",
        "TokenGeneration_AuthenticateDevice",
        "TokenGeneration_Authentication",
        "TokenGeneration_HostedAuth",
        "TokenGeneration_NewPasswordChallenge",
        "TokenGeneration_RefreshTokens",
        "UserMigration_Authentication",
        "UserMigration_ForgotPassword",
        "VerifyAuthChallengeResponse_Authentication",
    ]
    region: str
    userPoolId: str
    userName: str
    callerContext: CognitoUserPoolEventCallerContext
    request: CognitoUserPoolEventRequest
    response: Dict[str, Any]
