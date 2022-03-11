import re


class TaxId:
    """
    Represents a SSN or ITIN
    """

    REGEX_UNFORMATTED = re.compile(r"^\d{9}$")
    REGEX_FORMATTED = re.compile(r"^\d{3}-\d{2}-\d{4}$")
    REGEX_FORMATTED_MASKED = re.compile(r"^((\*{3}-\*{2}-\d{4})|(\*{3}\*{2}\d{4}))$")

    _formatted_val: str

    def __init__(self, val: str) -> None:
        print(val)
        if self.REGEX_FORMATTED.match(val):
            self._formatted_val = val
        elif self.REGEX_UNFORMATTED.match(val):
            self._formatted_val = "{}-{}-{}".format(val[:3], val[3:5], val[5:])
        else:
            raise ValueError(
                f"does not match one of: {self.REGEX_UNFORMATTED.pattern}, {self.REGEX_FORMATTED.pattern}"
            )

    def to_unformatted_str(self) -> str:
        return self._formatted_val.replace("-", "")

    def to_formatted_str(self) -> str:
        return self._formatted_val

    def last4(self) -> str:
        return self._formatted_val[-4:]

    def to_masked_str(self) -> str:
        return f"***-**-{self._formatted_val[-4:]}"

    def __eq__(self, other):
        if not isinstance(other, TaxId):
            return NotImplemented

        return self._formatted_val == other._formatted_val

    def __str__(self):
        return self.to_unformatted_str()

    def __repr__(self):
        return f"TaxId({self._formatted_val})"

    def __hash__(self):
        return hash(repr(self))

    @classmethod
    def __modify_schema__(cls, field_schema):
        # __modify_schema__ should mutate the dict it receives in place,
        # the returned value will be ignored
        field_schema.update(
            pattern=f"^({cls.REGEX_UNFORMATTED.pattern}|{cls.REGEX_FORMATTED.pattern})$",
            examples=["000-00-0000"],
        )

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val):

        if hasattr(val, "tax_identifier") and isinstance(val.tax_identifier, TaxId):
            return val.tax_identifier

        if not isinstance(val, str):
            raise TypeError("string required")

        return cls(val)


# inherit from dict to make the class JSON serializable
class Fein:
    """
    Represents a FEIN
    """

    REGEX_UNFORMATTED = re.compile(r"^\d{9}$")
    REGEX_FORMATTED = re.compile(r"^\d{2}-\d{7}$")

    _formatted_val: str

    def __init__(self, val: str) -> None:
        if self.REGEX_FORMATTED.match(val):
            self._formatted_val = val
        elif self.REGEX_UNFORMATTED.match(val):
            self._formatted_val = "{}-{}".format(val[:2], val[2:])
        else:
            raise ValueError(
                f"{val} does not match one of: {self.REGEX_UNFORMATTED.pattern}, {self.REGEX_FORMATTED.pattern}"
            )

    def to_unformatted_str(self) -> str:
        return self._formatted_val.replace("-", "")

    def to_formatted_str(self) -> str:
        return self._formatted_val

    def __eq__(self, other):
        if not isinstance(other, Fein):
            return NotImplemented

        return self._formatted_val == other._formatted_val

    def __repr__(self):
        return f"Fein({self._formatted_val})"

    def __str__(self):
        return self.to_unformatted_str()

    def __hash__(self):
        return hash(repr(self))

    @classmethod
    def __modify_schema__(cls, field_schema):
        # __modify_schema__ should mutate the dict it receives in place,
        # the returned value will be ignored
        field_schema.update(
            pattern=f"^({cls.REGEX_UNFORMATTED.pattern}|{cls.REGEX_FORMATTED.pattern})$",
            examples=["00-0000000"],
        )

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val):
        if not isinstance(val, str):
            raise TypeError("string required")

        return cls(val)
