import io

import pytest
from xmlschema import XMLSchema

from massgov.pfml.fineos.wscomposer.schemas import FINEOSConverter


@pytest.fixture
def simple_schema():
    simple_xsd = io.StringIO(
        """<?xml version="1.0" encoding="UTF-8" ?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="test">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="foo" type="xs:string" nillable="true" />
                <xs:element name="bar" type="xs:string" />
            </xs:sequence>
        </xs:complexType>
    </xs:element>
</xs:schema>"""
    )

    return XMLSchema(source=simple_xsd, converter=FINEOSConverter)


def test_fineos_converter_nil_is_none(simple_schema):
    decoded_data = simple_schema.decode(
        """
        <test xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <foo xsi:nil="true" />
            <bar>baz</bar>
        </test>
    """
    )

    assert decoded_data["foo"] is None
    assert decoded_data["bar"] == "baz"


def test_fineos_converter_nil_is_none_even_if_value(simple_schema):
    decoded_data = simple_schema.decode(
        """
        <test xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <foo xsi:nil="true">bar</foo>
            <bar>baz</bar>
        </test>
    """,
        # disable validation for this test, since a nil=true attribute with a
        # value will cause a validation error normally (as it should)
        validation="skip",
    )

    assert decoded_data["foo"] is None
    assert decoded_data["bar"] == "baz"


def test_fineos_converter_non_nil_works(simple_schema):
    decoded_data = simple_schema.decode(
        """
        <test xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <foo>bar</foo>
            <bar>baz</bar>
        </test>
    """
    )

    assert decoded_data["foo"] == "bar"
    assert decoded_data["bar"] == "baz"
