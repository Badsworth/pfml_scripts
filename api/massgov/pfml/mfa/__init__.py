from datetime import datetime, timezone
from typing import Any, Dict, Optional

import massgov.pfml.api.app as app
import massgov.pfml.cognito.config as cognito_config
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import User
from massgov.pfml.util.aws.ses import EmailRecipient, send_templated_email

logger = massgov.pfml.util.logging.get_logger(__name__)


def handle_mfa_disabled(user: User, last_enabled_at: Optional[datetime], updated_by: str) -> None:
    """Helper method for handling necessary actions after MFA is disabled for a user (send email, logging, etc)"""
    # These values should always be set by the time a user disables MFA but the
    # linter doesn't know that. This prevents a linter failure
    assert user.email_address
    assert user.mfa_phone_number_last_four()

    log_attributes = _collect_log_attributes(updated_by, last_enabled_at)
    logger.info("MFA disabled for user", extra=log_attributes)

    if app.get_config().environment == "local" and app.get_config().disable_sending_emails:
        logger.info("Skipping sending an MFA disabled notification email", extra=log_attributes)
        return

    try:
        _send_mfa_disabled_email(user.email_address, user.mfa_phone_number_last_four())
    except Exception as error:
        logger.error("Error sending MFA disabled email", exc_info=error)
        raise error


def _collect_log_attributes(updated_by: str, last_enabled_at: Optional[datetime]) -> Dict[str, Any]:
    log_attributes: Dict[str, Any] = {"updated_by": updated_by}

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
