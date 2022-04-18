from typing import Optional, Tuple, Union

import phonenumbers


def convert_to_E164(
    phone: str, int_code: Optional[str] = None, raise_if_invalid: bool = False
) -> Union[str, None]:
    parsed_phone_number = parse_number(phone, int_code)

    if not parsed_phone_number:
        return None

    internationalized_phone_number = phonenumbers.format_number(
        parsed_phone_number, phonenumbers.PhoneNumberFormat.E164
    )

    if raise_if_invalid and not phonenumbers.is_valid_number(parsed_phone_number):
        raise ValueError("Phone number is not valid.")

    return internationalized_phone_number


def parse_number(phone: str, int_code: Optional[str] = None) -> Optional[phonenumbers.PhoneNumber]:
    """Converts a str to E.164 format - for example, 1-123-4567 to +11234567"""
    parsed_phone_number: Optional[phonenumbers.PhoneNumber] = None
    # First, try parsing the number as provided

    try:
        parsed_phone_number = phonenumbers.parse(phone)
    except phonenumbers.NumberParseException:
        pass

    # If above fails, try parsing again after adding the provided country
    # code or as US number if no country code was provided
    #
    # test_applications_import_has_customer_contact_details passes in
    # US numbers without region codes
    if not parsed_phone_number:
        try:
            if int_code:
                parsed_phone_number = phonenumbers.parse(f"+{int_code}{phone}")
            else:
                parsed_phone_number = phonenumbers.parse(phone, "US")
        except phonenumbers.NumberParseException:
            # We couldn't parse the number, so return None
            return None

    return parsed_phone_number


def get_area_code_and_number(phone: str) -> Tuple:
    """Receives phone str and returns area code and number remainder separately."""
    parsed_phone_number = parse_number(phone)
    if not parsed_phone_number:
        return None, None
    area_code = str(parsed_phone_number.national_number)[:3]
    number_remainder = str(parsed_phone_number.national_number)[-7:]
    return area_code, number_remainder
