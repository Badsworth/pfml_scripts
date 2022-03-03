import re
from typing import Optional

EFT_PRENOTE_ID_PATTERN = re.compile(r"^E([1-9][0-9]*)$")
PAYMENT_ID_PATTERN = re.compile(r"^P([1-9][0-9]*)$")


def parse_eft_prenote_pub_individual_id(id_number: str) -> Optional[int]:
    if match := EFT_PRENOTE_ID_PATTERN.match(id_number):
        return int(match.group(1))
    return None


def parse_payment_pub_individual_id(id_number: str) -> Optional[int]:
    if match := PAYMENT_ID_PATTERN.match(id_number):
        return int(match.group(1))
    return None


class IteratorKeepingLastItem:
    """An iterator that keeps a copy of the last item that was yielded."""

    def __init__(self, it):
        self.it = it

    def __next__(self):
        self.current_item = next(self.it)
        return self.current_item

    def __iter__(self):
        return self
