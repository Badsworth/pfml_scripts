from datetime import datetime, timezone
from typing import Optional

import massgov.pfml.db as db
import massgov.pfml.db.lookups as db_lookups
import massgov.pfml.util.logging
from massgov.pfml.api.models.users.requests import UserUpdateRequest
from massgov.pfml.api.util.phone import convert_to_E164
from massgov.pfml.db.models.employees import (
    LkMFADeliveryPreference,
    LkMFADeliveryPreferenceUpdatedBy,
    User,
)
from massgov.pfml.mfa import handle_mfa_disabled

logger = massgov.pfml.util.logging.get_logger(__name__)


def update_user(
    db_session: db.Session, user: User, update_request: UserUpdateRequest, updated_by: str = "User"
) -> User:
    for key in update_request.__fields_set__:
        value = getattr(update_request, key)

        if key == "mfa_delivery_preference":
            _update_mfa_preference(db_session, user, key, value, updated_by)
            continue

        if key == "mfa_phone_number":
            if value is not None:
                value = convert_to_E164(value)

        setattr(user, key, value)

    return user


def _update_mfa_preference(
    db_session: db.Session, user: User, key: str, value: Optional[str], updated_by: str
) -> None:
    existing_mfa_preference = user.mfa_preference_description()
    if value == existing_mfa_preference:
        return

    mfa_preference = (
        db_lookups.by_value(db_session, LkMFADeliveryPreference, value)
        if value is not None
        else None
    )
    setattr(user, key, mfa_preference)

    # Keep a copy of the last updated timestamp before we update it. This is used later for logging
    # feature metrics
    last_updated_at = user.mfa_delivery_preference_updated_at
    updated_by = updated_by.lower()

    _update_mfa_preference_audit_trail(db_session, user, updated_by)

    log_attributes = {"mfa_preference": value, "updated_by": updated_by}
    logger.info("MFA updated for user", extra=log_attributes)

    if value == "Opt Out" and existing_mfa_preference is not None:
        try:
            handle_mfa_disabled(user, last_updated_at, updated_by)
        except Exception as e:
            logger.error("Error handling MFA disabled side effects", exc_info=e)

            # only re-raise the error if the change wasn't made by a user in the portal
            if updated_by != "user":
                raise e


def _update_mfa_preference_audit_trail(db_session: db.Session, user: User, updated_by: str) -> None:
    # when a user changes their security preferences
    # we want to record an audit trail of who made the change, and when
    now = datetime.now(timezone.utc)
    mfa_delivery_preference_updated_at = "mfa_delivery_preference_updated_at"
    setattr(user, mfa_delivery_preference_updated_at, now)

    if updated_by == "admin":
        mfa_updated_by = db_lookups.by_value(db_session, LkMFADeliveryPreferenceUpdatedBy, "Admin")
    else:
        mfa_updated_by = db_lookups.by_value(db_session, LkMFADeliveryPreferenceUpdatedBy, "User")

    mfa_delivery_preference_updated_by = "mfa_delivery_preference_updated_by"
    setattr(user, mfa_delivery_preference_updated_by, mfa_updated_by)
