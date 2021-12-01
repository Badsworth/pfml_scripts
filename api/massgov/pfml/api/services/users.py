from typing import Optional

import massgov.pfml.api.app as app
import massgov.pfml.db as db
import massgov.pfml.db.lookups as db_lookups
from massgov.pfml.api.models.users.requests import UserUpdateRequest
from massgov.pfml.api.util.phone import convert_to_E164
from massgov.pfml.db.models.employees import LkMFADeliveryPreference, User


def update_user(user: User, update_request: UserUpdateRequest) -> User:
    with app.db_session() as db_session:
        for key in update_request.__fields_set__:
            value = getattr(update_request, key)

            if key == "mfa_delivery_preference":
                _add_or_update_mfa_delivery_preference(db_session, user, key, value)
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
