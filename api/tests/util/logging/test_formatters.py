#
# Tests for massgov.pfml.util.logging.
#

from massgov.pfml.util.logging import formatters


def test_str_mask_pii():
    assert formatters.str_mask_pii("message", "") == ""
    assert formatters.str_mask_pii("message", 1) == "1"
    assert formatters.str_mask_pii("message", {"a": "x", "b": "y"}) == "{'a': 'x', 'b': 'y'}"
    assert formatters.str_mask_pii("message", None) == "None"


def test_str_mask_pii_with_ssn():
    assert (
        formatters.str_mask_pii("message", "test 999-00-0000 test 999-99-0000")
        == "test ********* test *********"
    )
    assert formatters.str_mask_pii("message", "test 999-00-0000 test") == "test ********* test"
    assert formatters.str_mask_pii("message", "999-00-0000 test") == "********* test"
    assert formatters.str_mask_pii("message", "test 999-00-0000") == "test *********"
    assert formatters.str_mask_pii("message", "999-00-0000") == "*********"
    assert formatters.str_mask_pii("message", "9-990-00000") == "*********"
    assert formatters.str_mask_pii("message", "999000000") == "*********"
    assert formatters.str_mask_pii("message", 999000000) == "*********"
    assert formatters.str_mask_pii("message", "test=999000000.") == "test=*********."
    assert formatters.str_mask_pii("message", "test=999000000,") == "test=*********,"
    assert formatters.str_mask_pii("message", 999000000.5) == "999000000.5"
    assert (
        formatters.str_mask_pii("message", {"a": "x", "b": "999000000"})
        == "{'a': 'x', 'b': '*********'}"
    )


def test_str_mask_pii_with_ssn_excluded_key():
    assert formatters.str_mask_pii("count", 999000000) == "999000000"
    assert formatters.str_mask_pii("created", 999000000) == "999000000"
    assert formatters.str_mask_pii("process", 999000000) == "999000000"
    assert formatters.str_mask_pii("thread", 999000000) == "999000000"


def test_str_mask_pii_not_hostname():
    assert (
        formatters.str_mask_pii("message", "hostname ip-10-11-12-134.ec2.internal")
        == "hostname ip-10-11-12-134.ec2.internal"
    )
