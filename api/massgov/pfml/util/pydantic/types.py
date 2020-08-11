import re


class Regexes:
    TAX_ID = re.compile(r"^\d{9}$")
    TAX_ID_FORMATTED = re.compile(r"^\d{3}-\d{2}-\d{4}$")
    FEIN = re.compile(r"^\d{9}$")
    FEIN_FORMATTED = re.compile(r"^\d{2}-\d{7}$")
    STREET_NUMBER = re.compile(r"^\d+")


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
    def validate_type(cls, val):
        if not isinstance(val, str):
            raise TypeError("is not a str")

        elif Regexes.TAX_ID.match(val):
            return "{}-{}-{}".format(val[:3], val[3:5], val[5:])

        elif Regexes.TAX_ID_FORMATTED.match(val):
            return val

        raise ValueError(
            f"does not match one of: {Regexes.TAX_ID.pattern}, {Regexes.TAX_ID_FORMATTED}"
        )


class FEINStr(str):
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


class MaskedEmailStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val):
        if not isinstance(val, str):
            raise TypeError("is not a str")

        else:
            at_sign_index = val.find("@")
            domain = val[at_sign_index:]

            masked_email = val[0] + "*****" + domain
            return masked_email


class MaskedFinancialAcctNum(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val):
        if not isinstance(val, str):
            raise TypeError("is not a str")

        else:
            length = len(val)
            masked_digits = "*" * (length - 4)
            last_four = val[(length - 4) :]
            partial_acct_num = masked_digits + last_four

            return partial_acct_num
