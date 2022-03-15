from typing import List, Optional


def split_str(val: Optional[str] = None, delim: str = ",") -> List[str]:
    if val is None or val.strip() == "":
        return []
    return val.split(delim)


def snake_to_camel(string: str) -> str:
    return "".join(word.capitalize() for word in string.split("_"))


def capitalize(string: str) -> str:
    return string.capitalize()


def join_with_coordinating_conjunction(
    terms: List[str], separator: str = ",", conjunction: str = "and"
) -> str:
    """Generate a simple, human readable series of terms (for standard English)."""
    if len(terms) == 0:
        return ""

    if len(terms) == 1:
        return terms[0]

    if len(terms) == 2:
        return f"{terms[0]} {conjunction} {terms[1]}"

    all_but_last_term_joined = f"{separator} ".join(terms[:-1])
    return f"{all_but_last_term_joined}{separator} {conjunction} {terms[-1]}"


def sanitize_fein(fein: str) -> str:
    return fein.replace("-", "").zfill(9)


def format_fein(fein: str) -> str:
    return f"{fein[:2]}-{fein[2:]}"


def format_tax_identifier(tax_identifier: str) -> str:
    return "{}-{}-{}".format(tax_identifier[:3], tax_identifier[3:5], tax_identifier[5:])


def remove_unicode_replacement_char(text: str) -> str:
    # This character has appeared a few times in files
    # the payments process reads that the PI team makes.
    # We aren't sure of the exact cause, but just replace
    # it with a space as that appears to be the correct char.
    return text.replace("\ufffd", " ")
