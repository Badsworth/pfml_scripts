import re


class Regexes:
    TAX_ID = re.compile(r"^\d{9}$")
    TAX_ID_FORMATTED = re.compile(r"^\d{3}-\d{2}-\d{4}$")
    FEIN = re.compile(r"^\d{9}$")
    FEIN_FORMATTED = re.compile(r"^\d{2}-\d{7}$")


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
