def validate_elements(element, expected_elements):
    """
    Utility method for easily validating the inner most elements of a comptroller document.
    Note that expected elements is a map of: attribute tag -> value
    This method also checks a few other static values
    """

    assert len(element.childNodes) == len(expected_elements)

    for tag, text in expected_elements.items():
        subelements = element.getElementsByTagName(tag)
        assert len(subelements) == 1

        subelement = subelements[0]
        assert subelement.tagName == tag
        validate_attributes(subelement, {"Attribute": "Y"})
        assert len(subelement.childNodes) == 1  # Should just have a CDATA

        cdata = subelement.childNodes[0]
        assert cdata.data == text


def validate_attributes(element, expected_attributes):
    """ Elements have an _attrs map, but its from attribute name to
        and attrs object with a value stored within it.
    """
    assert len(element._attrs) == len(expected_attributes)
    for name, value in expected_attributes.items():
        assert element._attrs[name].value == value
