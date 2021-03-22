from massgov.pfml.api.util.deepgetattr import deepgetattr


def test_deepgetattr_single_level():
    class TestData:
        name = "Bud Baxter"
        birthdate = None

    assert deepgetattr(TestData(), "name") == "Bud Baxter"
    assert deepgetattr(TestData(), "birthdate") is None
    # Non-existant field
    assert deepgetattr(TestData(), "reason") is None


def test_deepgetattr_multi_level():
    class TestAddress:
        line_1 = "123 St"

    class TestData:
        address = TestAddress()

    assert deepgetattr(TestData(), "address.line_1") == "123 St"
    # Non-existant fields
    assert deepgetattr(TestData(), "address.line_2") is None
    assert deepgetattr(TestData(), "mailing_address.line_1") is None
