#
# Dictionaries with additional behaviour.
#

import collections
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple


class LeastRecentlyUsedDict(collections.OrderedDict):
    """A dict with a maximum size, evicting the least recently written key when full.

    Getting a key that is not present returns a default value of 0.

    Setting a key marks it as most recently used and removes the oldest key if full.

    May be useful for tracking the count of items where limited memory usage is needed even if
    the set of items can be unlimited.

    Based on the example at
    https://docs.python.org/3/library/collections.html#ordereddict-examples-and-recipes
    """

    def __init__(self, maxsize=128, *args, **kwargs):
        self.maxsize = maxsize
        super().__init__(*args, **kwargs)

    def __getitem__(self, key):
        if key in self:
            return super().__getitem__(key)
        return 0

    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)
        super().__setitem__(key, value)
        if self.maxsize < len(self):
            self.popitem(last=False)


def make_keys_lowercase(data: Dict[str, Any]) -> Dict[str, Any]:
    return {k.lower(): v for k, v in data.items()}


def filter_dict(dict: Dict[str, Any], allowed_keys: Set[str]) -> Dict[str, Any]:
    """
    Filter a dictionary to a specified set of allowed keys.
    If the key isn't present, will not cause an issue (i.e.. when we delete columns in the DB)
    """

    return {k: v for k, v in dict.items() if k in allowed_keys}


def flatten(
    d: Mapping[Any, Any],
    key_prefix: Optional[str] = None,
    separator: str = ".",
    *,
    depth: int = 0,
    max_depth: Optional[int] = None,
) -> Dict[str, Any]:
    """Collapse nested dictionaries into a single level.

    Example:
        {"foo": {"bar": 1}} -> {"foo.bar": 1}

    Args:
        key_prefix: String to prepend to first level of keys.
        separator: String to use when combining nested keys.
        max_depth: Nesting level at which to stop flattening process. Any value
            below this will dumped as its raw string representation.
    """
    current_depth = depth + 1
    items: List[Tuple[str, Any]] = []

    for old_key, value in d.items():
        key = key_prefix + separator + str(old_key) if key_prefix else str(old_key)

        if isinstance(value, Mapping):
            if max_depth is not None and (current_depth > max_depth):
                items.append((key, str(value)))
            else:
                items.extend(
                    flatten(
                        value,
                        key_prefix=key,
                        separator=separator,
                        depth=current_depth,
                        max_depth=max_depth,
                    ).items()
                )
        else:
            items.append((key, value))

    return dict(items)
