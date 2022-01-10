from datetime import datetime
from typing import Optional

import massgov.pfml.db as db
import massgov.pfml.db.lookups as db_lookups
from massgov.pfml.api.models.users.requests import UserUpdateRequest
from massgov.pfml.api.util.phone import convert_to_E164
from massgov.pfml.db.models.employees import (
    LkMFADeliveryPreference,
    LkMFADeliveryPreferenceUpdatedBy,
    User,
)


def update_user(db_session: db.Session, user: User, update_request: UserUpdateRequest) -> User:
    for key in update_request.__fields_set__:
        value = getattr(update_request, key)

        if key == "mfa_delivery_preference":
            delivery_preference = (
                user.mfa_delivery_preference.mfa_delivery_preference_description
                if user.mfa_delivery_preference is not None
                else None
            )
            if delivery_preference != value:
                _add_or_update_mfa_delivery_preference(db_session, user, key, value)
                _update_mfa_preference_audit_trail(db_session, user, key, value)
            continue

        if key == "mfa_phone_number":
            if value is not None:
                value = convert_to_E164(value)

        setattr(user, key, value)

    return user


def _add_or_update_mfa_delivery_preference(
    db_session: db.Session, user: User, key: str, value: Optional[str]
) -> None:
    if value is None:
        setattr(user, key, None)
        return

    mfa_delivery_preference = db_lookups.by_value(db_session, LkMFADeliveryPreference, value)
    setattr(user, key, mfa_delivery_preference)


def _update_mfa_preference_audit_trail(
    db_session: db.Session, user: User, key: str, value: Optional[str]
) -> None:
    if value is None:
        setattr(user, key, None)

    # when a user changes their security preferences
    # we want to record an audit trail of who made the change, and when
    now = datetime.utcnow()
    mfa_delivery_preference_updated_at = "mfa_delivery_preference_updated_at"
    setattr(user, mfa_delivery_preference_updated_at, now)

    mfa_delivery_preference_updated_by_user = db_lookups.by_value(
        db_session, LkMFADeliveryPreferenceUpdatedBy, "User"
    )
    mfa_delivery_preference_updated_by = "mfa_delivery_preference_updated_by"
    setattr(user, mfa_delivery_preference_updated_by, mfa_delivery_preference_updated_by_user)
