import io

import pytest

from massgov.pfml.delegated_payments.pub.manual_pub_reject_file_parser import (
    FileParseError,
    ManualPubReject,
    ManualPubRejectFileParser,
)

VALID_CSV = "ID,Notes\n" "P123456,Notes1\n" "2345678,Notes@#@#\n" "1,\n"

INVALID_CSV = "Other,Header\n" "Content,Content\n"


def test_payment_parser_happy_path():
    stream = io.StringIO(VALID_CSV, newline=None)
    parser = ManualPubRejectFileParser(stream)

    manual_pub_rejects = parser.get_manual_pub_rejects()
    line_errors = parser.get_line_errors()

    assert manual_pub_rejects == [
        ManualPubReject(
            line_number=2, raw_line="P123456,Notes1\n", record_id="P123456", notes="Notes1",
        ),
        ManualPubReject(
            line_number=3, raw_line="2345678,Notes@#@#\n", record_id="2345678", notes="Notes@#@#",
        ),
        ManualPubReject(line_number=4, raw_line="1,\n", record_id="1", notes=""),
    ]
    assert len(line_errors) == 0


def test_payment_parser_invalid_csv():
    stream = io.StringIO(INVALID_CSV, newline=None)
    with pytest.raises(
        FileParseError, match="Expected field names not present in manual PUB reject CSV file"
    ):
        ManualPubRejectFileParser(stream)


def test_payment_parser_empty_csv():
    stream = io.StringIO("", newline=None)
    with pytest.raises(
        FileParseError, match="No header row in Manual PUB reject CSV file - empty file"
    ):
        ManualPubRejectFileParser(stream)
