from typing import Optional


def str_to_int(initial: Optional[str]) -> Optional[int]:
    if not initial:
        return None
    try:
        parsed = int(initial)
        return parsed
    except ValueError:
        return None
