from typing import Union

import phonenumbers

from massgov.pfml.api.models.common import Phone


def convert_to_E164(phone: Phone) -> Union[str, None]:
    """Converts a Phone to E.164 format - for example, 1-123-4567 to +11234567"""
    int_code = phone.int_code
    phone_number = phone.phone_number

    if phone_number is None:
        return None

    parsed_phone_number = phonenumbers.parse(f"+{int_code}{phone_number}")
    internationalized_phone_number = phonenumbers.format_number(
        parsed_phone_number, phonenumbers.PhoneNumberFormat.E164
    )

    return internationalized_phone_number
