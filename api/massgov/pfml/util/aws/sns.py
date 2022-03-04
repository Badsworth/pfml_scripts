import boto3
from botocore.exceptions import ClientError

import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)


def create_sns_client():
    return boto3.client("sns", region_name="us-east-1")


def check_phone_number_opt_out(phone_number: str) -> bool:
    """Check whether a phone number is in the SNS opt-out list (i.e. we can't sent messages to them)"""
    client = create_sns_client()
    try:
        response = client.check_if_phone_number_is_opted_out(phoneNumber=phone_number)
        return response["isOptedOut"]
    except Exception as error:
        if isinstance(error, ClientError) and "InvalidParameterException" in str(error.__class__):
            logger.error(
                "Error checking SNS opt out list - Invalid parameter in request", exc_info=error
            )
        else:
            logger.error("Error checking SNS opt out list", exc_info=error)
        raise error


def opt_in_phone_number(phone_number: str) -> None:
    """Opt a phone number back into receiving messages from SNS
    We can only perform this operation for a given phone number once every 30 days.
    Ref: https://docs.aws.amazon.com/sns/latest/api/API_OptInPhoneNumber.html
    """
    client = create_sns_client()
    try:
        client.opt_in_phone_number(phoneNumber=phone_number)
    except Exception as error:
        if isinstance(error, ClientError) and "InvalidParameterException" in str(error.__class__):
            logger.error(
                "Error opting in phone number to SNS - Invalid parameter in request", exc_info=error
            )
        if isinstance(error, ClientError) and "ThrottledException" in str(error.__class__):
            logger.error("Error opting in phone number to SNS - Too many requests", exc_info=error)
        else:
            logger.error("Error opting in phone number to SNS", exc_info=error)
        raise error
