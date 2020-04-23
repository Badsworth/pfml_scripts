from typing import List, Optional


def split_str(val: Optional[str] = None, delim: str = ",") -> List[str]:
    if val is None or val.strip() == "":
        return []
    return val.split(delim)
