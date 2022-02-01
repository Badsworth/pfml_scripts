import re
from typing import Optional, Union

import massgov.pfml.util.pydantic.mask as mask
from massgov.pfml.db.models.employees import TaxIdentifier
from massgov.pfml.util.strings import format_tax_identifier


class Regexes:
    TAX_ID = re.compile(r"^\d{9}$")
    TAX_ID_FORMATTED = re.compile(r"^\d{3}-\d{2}-\d{4}$")
    TAX_ID_MASKED = re.compile(r"^((\*{3}-\*{2}-\d{4})|(\*{3}\*{2}\d{4}))$")
    FEIN = re.compile(r"^\d{9}$")
    FEIN_FORMATTED = re.compile(r"^\d{2}-\d{7}$")
    STREET_NUMBER = re.compile(r"^\d+")
    MASS_ID = re.compile(r"^(\d{9}|S(\d{8}|A\d{7}))$")
    ROUTING_NUMBER = re.compile(
        r"^((0[0-9])|(1[0-2])|(2[1-9])|(3[0-2])|(6[1-9])|(7[0-2])|80)([0-9]{7})$"
    )
    MASKED_ACCOUNT_NUMBER = re.compile(r"^\*{2,13}\d{4}$")
    DATE_OF_BIRTH = re.compile(r"^\*{4}-\d{2}-\d{2}$")
    MASKED_ZIP = re.compile(r"^[0-9]{5}-\*{4}$")
    MASKED_PHONE = re.compile(r"^\*{3}\-?\*{3}\-?[0-9]{4}$")


class TaxIdUnformattedStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val):
        if not isinstance(val, str):
            raise TypeError("is not a str")

        elif Regexes.TAX_ID_FORMATTED.match(val):
            return val.replace("-", "")

        elif Regexes.TAX_ID.match(val):
            return val

        raise ValueError(
            f"does not match one of: {Regexes.TAX_ID.pattern}, {Regexes.TAX_ID_FORMATTED}"
        )


class TaxIdFormattedStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val: Optional[Union[TaxIdentifier, str]]) -> str:
        if isinstance(val, TaxIdentifier):
            val = val.tax_identifier

        if not isinstance(val, str):
            raise TypeError("is not a str")

        elif Regexes.TAX_ID.match(val):
            return format_tax_identifier(val)

        elif Regexes.TAX_ID_FORMATTED.match(val):
            return val

        raise ValueError(
            f"does not match one of: {Regexes.TAX_ID.pattern}, {Regexes.TAX_ID_FORMATTED}"
        )


class MaskedTaxIdFormattedStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val: Optional[Union[TaxIdentifier, str]]) -> Optional[str]:
        if val is None:
            return None

        if isinstance(val, TaxIdentifier):
            return mask.mask_tax_identifier(val.tax_identifier)

        return mask.mask_tax_identifier(val)


class FEINUnformattedStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val):
        if not isinstance(val, str):
            raise TypeError("is not a str")

        elif Regexes.FEIN_FORMATTED.match(val):
            return val.replace("-", "")

        elif Regexes.FEIN.match(val):
            return val

        raise ValueError(f"does not match one of: {Regexes.FEIN.pattern}, {Regexes.FEIN_FORMATTED}")


class FEINFormattedStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val):
        if val is None:
            return None

        elif Regexes.FEIN.match(val):
            return "{}-{}".format(val[:2], val[2:])

        elif Regexes.FEIN_FORMATTED.match(val):
            return val


class MaskedFinancialAcctNum(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val):
        if not isinstance(val, str):
            raise TypeError("is not a str")

        return mask.mask_financial_account_number(val)


class FinancialRoutingNumber(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val):
        if not isinstance(val, str):
            raise TypeError("is not a str")

        elif Regexes.ROUTING_NUMBER.match(val):
            return val

        raise ValueError(f"does not match: {Regexes.ROUTING_NUMBER.pattern}")


class MaskedFinancialRoutingNumber(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val):
        if not isinstance(val, str):
            raise TypeError("is not a str")

        return mask.mask_routing_number(val)


class MassIdStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val):
        if not isinstance(val, str):
            raise TypeError("is not a str")

        elif Regexes.MASS_ID.match(val):
            return val

        raise ValueError(f"does not match: {Regexes.MASS_ID.pattern}")


class MaskedMassIdStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val):
        if not isinstance(val, str):
            raise TypeError("is not a str")

        elif Regexes.MASS_ID.match(val):
            return mask.mask_mass_id(val)

        raise ValueError(f"does not match: {Regexes.MASS_ID.pattern}")


class MaskedDateStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val):
        if val is None:
            return None

        return mask.mask_date(val)
