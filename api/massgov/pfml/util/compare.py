def compare_attributes(first: object, second: object, field: str) -> bool:
    """Compare attributes of two objects in a case-insensitive manner, stripping whitespace if applicable"""
    value1 = getattr(first, field)
    value2 = getattr(second, field)

    if type(value1) is str:
        value1 = value1.strip().lower()
    if type(value2) is str:
        value2 = value2.strip().lower()

    if value1 is None:
        value1 = ""
    if value2 is None:
        value2 = ""

    return value1 == value2
