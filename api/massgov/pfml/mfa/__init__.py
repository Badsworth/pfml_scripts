from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

import massgov.pfml.api.app as app
import massgov.pfml.cognito.config as cognito_config
import massgov.pfml.util.aws.cognito as cognito
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import MFADeliveryPreferenceUpdatedBy, User
from massgov.pfml.util.aws.ses import EmailRecipient, send_templated_email

logger = massgov.pfml.util.logging.get_logger(__name__)


# Constants used for indicating who initiated MFA activation and deactivation. These identify if
# MFA has been enabled/disabled by the user or by an admin
class MFAUpdatedBy(Enum):
    USER = MFADeliveryPreferenceUpdatedBy.USER.description.lower()
    ADMIN = MFADeliveryPreferenceUpdatedBy.ADMIN.description.lower()


def handle_mfa_enabled(cognito_auth_token: str) -> None:
    """Helper method for handling necessary actions after MFA is enabled for a user. This handles
    logging and enabling MFA in Cognito"""

    logger.info("MFA enabled for user")

    try:
        cognito.enable_user_mfa(cognito_auth_token)
    except Exception as error:
        logger.error("Error enabling MFA", exc_info=error)
        raise error


def handle_mfa_disabled(
    user: User,
    last_enabled_at: Optional[datetime],
    sync_cognito_preferences: bool,
    cognito_auth_token: str,
) -> None:
    """Helper method for handling necessary actions after MFA is disabled for a user. This handles logging,
    sending an MFA disabled email, and optionally disabling MFA in Cognito"""
    # These values should always be set by the time a user disables MFA but the
    # linter doesn't know that. This prevents a linter failure
    assert user.email_address
    assert user.mfa_phone_number_last_four()

    updated_by = MFAUpdatedBy.USER
    log_attributes = _collect_log_attributes(updated_by, last_enabled_at)
    log_attributes.update({"sync_cognito_preferences": sync_cognito_preferences})
    logger.info("MFA disabled for user", extra=log_attributes)

    try:
        # todo: rename the disable_sending_emails flag to something more generic
        if app.get_config().environment == "local" and app.get_config().disable_sending_emails:
            logger.info(
                "Skipping updating Cognito or sending an MFA disabled notification email",
                extra=log_attributes,
            )
        else:
            if sync_cognito_preferences:
                cognito.disable_user_mfa(cognito_auth_token)

            _send_mfa_disabled_email(user.email_address, user.mfa_phone_number_last_four())
    except Exception as error:
        logger.error("Error disabling user MFA", exc_info=error)
        raise error


def _collect_log_attributes(
    updated_by: MFAUpdatedBy, last_enabled_at: Optional[datetime]
) -> Dict[str, Any]:
    log_attributes: Dict[str, Any] = {"updated_by": updated_by.value}

    # TODO: investigate why this is happening: https://lwd.atlassian.net/browse/PORTAL-1678
    if last_enabled_at is None:
        logger.error("MFA disabled, but no last_enabled_at timestamp was available")
    else:
        now = datetime.now(timezone.utc)
        diff = now - last_enabled_at
        time_since_enabled_in_sec = round(diff.total_seconds())

        log_attributes.update(
            {
                "last_enabled_at": last_enabled_at,
                "time_since_enabled_in_sec": time_since_enabled_in_sec,
            }
        )

    return log_attributes


def _send_mfa_disabled_email(recipient_email: str, phone_number_last_four: str) -> None:
    email_config = cognito_config.get_email_config()
    sender_email = email_config.pfml_email_address
    template = "MfaHasBeenDisabled"
    template_data = {"phone_number_last_four": phone_number_last_four}

    recipient = EmailRecipient(to_addresses=[recipient_email])
    send_templated_email(
        recipient,
        template,
        sender_email,
        email_config.bounce_forwarding_email_address,
        email_config.bounce_forwarding_email_address_arn,
        template_data,
    )


def handle_mfa_disabled_by_admin(
    user: User,
    last_enabled_at: Optional[datetime],
) -> None:
    """Helper method for handling necessary actions after MFA is disabled for a user by an admin. This handles
    logging, sending an MFA disabled email, and disabling MFA in Cognito"""
    # These values should always be set by the time a user disables MFA but the
    # linter doesn't know that. This prevents a linter failure
    assert user.email_address
    assert user.mfa_phone_number_last_four()

    updated_by = MFAUpdatedBy.ADMIN
    log_attributes = _collect_log_attributes(updated_by, last_enabled_at)
    logger.info("MFA disabled for user", extra=log_attributes)

    try:
        # todo: rename the disable_sending_emails flag to something more generic
        if app.get_config().environment == "local" and app.get_config().disable_sending_emails:
            logger.info(
                "Skipping updating Cognito or sending an MFA disabled notification email",
                extra=log_attributes,
            )
        else:
            cognito.admin_disable_user_mfa(user.email_address)
            _send_mfa_disabled_email(user.email_address, user.mfa_phone_number_last_four())
    except Exception as error:
        logger.error("Error disabling user MFA", exc_info=error)
        raise error
