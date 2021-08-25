from dataclasses import dataclass
from typing import Optional


SUFFIXES = [
    'jr',
    'jnr',
    'junior',
    'sr',
    'snr',
    'i',
    'ii',
    'iii',
    'iv',
    'v',
]


@dataclass
class Name:
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    suffix: Optional[str] = None


def is_name_suffix(maybe_suffix: str) -> bool:
  maybe_suffix_lower = maybe_suffix.lower()
  for suffix in SUFFIXES:
    if maybe_suffix_lower in suffix:
      return True
  return False


def parse_name(fullname: str) -> Name:
    name_parts = fullname.split(" ")
    name_parts_length = len(name_parts)

    if name_parts_length == 1:
        return Name(last_name=name_parts[0])

    if name_parts_length == 2:
        return Name(first_name=name_parts[0], last_name=name_parts[1])

    if name_parts_length == 3:
        if is_name_suffix(name_parts[2]):
            return Name(first_name=name_parts[0], last_name=name_parts[1], suffix=name_parts[2])
        else:
            return Name(first_name=name_parts[0], middle_name=name_parts[1], last_name=name_parts[2])
    
    if name_parts_length >= 4:
        if is_name_suffix(name_parts[name_parts_length-1]):
            middle_name = name_parts[1:name_parts_length-2]
            return Name(first_name=name_parts[0], middle_name=" ".join(middle_name), last_name=name_parts[name_parts_length-2], suffix=name_parts[name_parts_length-1])
        else:
            middle_name = name_parts[1:name_parts_length-1]
            return Name(first_name=name_parts[0], middle_name=" ".join(middle_name), last_name=name_parts[name_parts_length-1])