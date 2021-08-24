from typing import Any, Dict, Mapping, Optional, TypeVar

_T = TypeVar("_T")


def set_object_from_json(json_str: Optional[Any], object_instance: Optional[_T]) -> Optional[_T]:
    if json_str is None:
        return None

    if isinstance(json_str, Mapping):
        iterable = json_str.items()
    elif hasattr(json_str, "__dict__"):
        iterable = json_str.__dict__.items()
    else:
        raise Exception("Unknown object type")

    for key, val in iterable:
        setattr(object_instance, key, val)

    if object_instance is None or vars(object_instance).__len__() == 1:
        return None

    return object_instance


def get_json_from_object(object_instance: Optional[Any]) -> Optional[Dict[str, Any]]:
    if object_instance is None:
        return None

    object_dict = vars(object_instance)
    json_str = {}

    for key in object_dict:
        if key != "_sa_instance_state" and object_dict[key] is not None:
            json_str[key] = object_dict[key]

    return json_str
