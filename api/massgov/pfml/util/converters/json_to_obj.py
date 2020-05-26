def set_object_from_json(json_str, object_instance):
    if json_str is None:
        return None

    for key in json_str:
        setattr(object_instance, key, json_str[key])

    if object_instance is None or vars(object_instance).__len__() == 1:
        return None

    return object_instance


def get_json_from_object(object_instance):
    if object_instance is None:
        return None

    object_dict = vars(object_instance)
    json_str = {}

    for key in object_dict:
        if key != "_sa_instance_state" and object_dict[key] is not None:
            json_str[key] = object_dict[key]

    return json_str
