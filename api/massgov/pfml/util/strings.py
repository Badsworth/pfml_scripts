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


def mask_fein(fein: str) -> str:
    # Log only last 4 of FEIN
    return f"**-***{fein[5:]}"
