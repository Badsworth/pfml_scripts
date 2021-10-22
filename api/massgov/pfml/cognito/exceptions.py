from typing import Optional

from massgov.pfml.api.validation.exceptions import IssueType, ValidationErrorDetail


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

    def __init__(self, message: str, issue: ValidationErrorDetail):
        self.message = message
        self.issue = issue


class CognitoUserExistsValidationError(CognitoValidationError):
    """Error raised due to a user with the provided email already existing in the Cognito user pool

    Attributes:
        message -- Cognito's explanation of the error
        sub_id -- Existing user's ID attribute
        issue -- used for communicating the error to the user
    """

    __slots__ = ["sub_id", "issue", "message"]

    def __init__(self, message: str, sub_id: Optional[str]):
        self.sub_id = sub_id
        self.message = message
        self.issue = ValidationErrorDetail(
            field="email_address", type=IssueType.exists, message=message
        )
