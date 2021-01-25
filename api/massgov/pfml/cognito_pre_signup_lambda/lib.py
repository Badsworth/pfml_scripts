import re
from typing import Dict, Optional

import massgov.pfml.db as db
import massgov.pfml.util.aws_lambda as aws_lambda
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import Employer

logger = massgov.pfml.util.logging.get_logger(__name__)


class PreSignupEventRequest(aws_lambda.CognitoUserPoolEventRequest):
    clientMetadata: Optional[Dict] = None


class PreSignupEvent(aws_lambda.CognitoUserPoolEvent):
    """Cognito PreSignup Event

    https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-sign-up.html#cognito-user-pools-lambda-trigger-syntax-pre-signup
    """

    request: PreSignupEventRequest


def handler(
    db_session: db.Session, event: PreSignupEvent, context: aws_lambda.LambdaContext,
) -> PreSignupEvent:

    cognito_metadata = event.request.clientMetadata

    if cognito_metadata is not None and "ein" in cognito_metadata:
        logger.info("Signup is for a leave administrator account")
        stripped_ein = re.sub("-", "", cognito_metadata["ein"])
        employer = (
            db_session.query(Employer).filter(Employer.employer_fein == stripped_ein).one_or_none()
        )

        if employer is not None and employer.fineos_employer_id is not None:
            logger.info("Signup is for a valid FEIN that is contributing, progressing signup")
            return event
        elif employer is None:
            logger.info("Signup is for an invalid FEIN, denying signup")
            # To deny a signup request, we must raise an error back to Cognito
            raise Exception("No employer found with specified FEIN")
        else:
            logger.info("Signup is for an employer that is not contributing, denying signup")
            # To deny a signup request, we must raise an error back to Cognito
            raise Exception("Invalid employer details")

    else:
        logger.info("Signup is for a claimant account, progressing signup")
        return event
