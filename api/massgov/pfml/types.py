import re


class TaxId:
    """
    Represents a SSN or ITIN
    """

    REGEX_UNFORMATTED = re.compile(r"^\d{9}$")
    REGEX_FORMATTED = re.compile(r"^\d{3}-\d{2}-\d{4}$")

    val: str
    is_valid: bool = True

    def __init__(self, val: str) -> None:
        if self.REGEX_FORMATTED.match(val):
            self.val = val
        elif self.REGEX_UNFORMATTED.match(val):
            self.val = "{}-{}-{}".format(val[:3], val[3:5], val[5:])
        else:
            self.val = val
            self.is_valid = False

            raise ValueError(
                f"does not match one of: {self.REGEX_UNFORMATTED.pattern}, {self.REGEX_FORMATTED.pattern}"
            )

    def to_unformatted_str(self) -> str:
        return self.val.replace("-", "")

    def to_formatted_str(self) -> str:
        return self.val

    def to_masked_str(self) -> str:
        return f"***-**-{self.val[-4:]}"

    def __eq__(self, other):
        if not isinstance(other, TaxId):
            return NotImplemented

        return self.val == other.val

    def __str__(self):
        return self.val.replace("-", "")

    def __repr__(self):
        return f"TaxId({self.val})"

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

        if hasattr(val, "tax_identifier"):
            return val.tax_identifier

        if not isinstance(val, str):
            raise TypeError("string required")

        return cls(val)


# inherit from dict to make the class JSON serializable
class Fein(dict):
    """
    Represents a FEIN
    """

    REGEX_UNFORMATTED = re.compile(r"^\d{9}$")
    REGEX_FORMATTED = re.compile(r"^\d{2}-\d{7}$")

    val: str
    is_valid: bool = True

    def __init__(self, val: str) -> None:
        dict.__init__(self, val=val)

        val = str(val)

        if self.REGEX_FORMATTED.match(val):
            self.val = val
        elif self.REGEX_UNFORMATTED.match(val):
            self.val = "{}-{}".format(val[:2], val[2:])
        else:
            self.val = val
            self.is_valid = False

            raise ValueError(
                f"does not match one of: {self.REGEX_UNFORMATTED.pattern}, {self.REGEX_FORMATTED.pattern}"
            )

    def to_unformatted_str(self) -> str:
        return self.val.replace("-", "")

    def to_formatted_str(self) -> str:
        return self.val

    def __eq__(self, other):
        if not isinstance(other, Fein):
            return NotImplemented

        return self.val == other.val

    def __repr__(self):
        return f"Fein({self.val})"

    def __str__(self):
        return self.val.replace("-", "")

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
