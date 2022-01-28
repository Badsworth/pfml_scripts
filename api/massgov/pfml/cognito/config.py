import massgov.pfml.util.logging
from massgov.pfml.util.pydantic import PydanticBaseSettings

logger = massgov.pfml.util.logging.get_logger(__name__)


class MfaEmailConfig(PydanticBaseSettings):
    """Config for MFA emails

    These fields have default values automatically loaded from corresponding environment variables
    """

    # "Send to" address for bounced back outgoing emails (ARN)
    bounce_forwarding_email_address_arn: str
    # "Send to" address for bounced back outgoing emails
    bounce_forwarding_email_address: str
    # "Send from" address for outgoing emails sent to claimants and leave administrators
    pfml_email_address: str


def get_email_config() -> MfaEmailConfig:
    email_config = MfaEmailConfig()

    logger.info(
        "Constructed MFA email configuration",
        extra={
            "pfml_email_address": email_config.pfml_email_address,
            "bounce_forwarding_email_address": email_config.bounce_forwarding_email_address,
            "bounce_forwarding_email_address_arn": email_config.bounce_forwarding_email_address_arn,
        },
    )

    return email_config
