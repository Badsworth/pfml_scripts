from massgov.pfml.delegated_payments.pub.pub_util import (
    parse_eft_prenote_pub_individual_id,
    parse_payment_pub_individual_id,
)


def test_parse_eft_prenote_pub_individual_id():
    # Valid Scenarios
    assert parse_eft_prenote_pub_individual_id("E12345") == 12345
    assert parse_eft_prenote_pub_individual_id("E2111111") == 2111111
    assert parse_eft_prenote_pub_individual_id("E1") == 1
    assert parse_eft_prenote_pub_individual_id("E96743121346") == 96743121346

    # Invalid Scenarios
    assert not parse_eft_prenote_pub_individual_id("P12345")
    assert not parse_eft_prenote_pub_individual_id("E02345")
    assert not parse_eft_prenote_pub_individual_id("E1a")
    assert not parse_eft_prenote_pub_individual_id("E12b34")
    assert not parse_eft_prenote_pub_individual_id("EE2345")
    assert not parse_eft_prenote_pub_individual_id("12345")


def test_parse_payment_pub_individual_id():
    # Valid Scenarios
    assert parse_payment_pub_individual_id("P5555") == 5555
    assert parse_payment_pub_individual_id("P6789") == 6789
    assert parse_payment_pub_individual_id("P2") == 2
    assert parse_payment_pub_individual_id("P743121246") == 743121246

    # Invalid Scenarios
    assert not parse_payment_pub_individual_id("E12345")
    assert not parse_payment_pub_individual_id("P02345")
    assert not parse_payment_pub_individual_id("P1a")
    assert not parse_payment_pub_individual_id("P12b34")
    assert not parse_payment_pub_individual_id("PP2345")
    assert not parse_payment_pub_individual_id("12345")
