def deepgetattr(obj, attr):
    """Recurses through an attribute chain to get the ultimate value. Returns None if nothing is found."""
    fields = attr.split(".")
    value = obj

    for field in fields:
        # Bail at the first instance where a field is empty
        if value is None:
            return None
        else:
            value = getattr(value, field, None)

    return value
