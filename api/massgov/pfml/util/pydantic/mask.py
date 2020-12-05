from datetime import date
from typing import Optional

# Throw some static values up here for comparison elsewhere.
MASS_ID_MASK = "*********"
ADDRESS_MASK = "*******"
ROUTING_NUMBER_MASK = "*********"


def mask_tax_identifier(tax_id: Optional[str]) -> Optional[str]:
    if tax_id is None:
        return None

    return f"***-**-{tax_id[-4:]}"


def mask_mass_id(mass_id: Optional[str]) -> Optional[str]:
    if mass_id is None:
        return None
    return MASS_ID_MASK


def mask_date(date_val: Optional[date]) -> Optional[str]:
    if date_val is None:
        return None
    return date_val.strftime("****-%m-%d")


def mask_address(address: Optional[str]) -> Optional[str]:
    # Do not attempt to mask the address if the input address is either 1) None or 2) an empty string.
    if not address:
        return None
    return ADDRESS_MASK


def mask_zip(zip_code: Optional[str]) -> Optional[str]:
    if zip_code is None:
        return None
    if len(zip_code) > 5:
        return f"{zip_code[:5]}-****"
    return zip_code


def mask_financial_account_number(account_number: Optional[str]) -> Optional[str]:
    if account_number is None:
        return None
    masked_digits = "*" * (len(account_number) - 4)
    return masked_digits + account_number[-4:]


def mask_routing_number(routing_number: Optional[str]) -> Optional[str]:
    if routing_number is None:
        return None
    return ROUTING_NUMBER_MASK


def mask_phone(phone_number: Optional[str]) -> Optional[str]:
    if phone_number is None:
        return None
    return f"{phone_number[:-4]}****"
