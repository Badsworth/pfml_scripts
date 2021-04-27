import io

import massgov.pfml.util.csv as csv_util


def test_encode_row_with_empty_dict():
    assert csv_util.encode_row({}) == {}


def test_encoding_dict_writer_writerow():
    output_file = io.StringIO()

    writer = csv_util.EncodingDictWriter(
        output_file, fieldnames=["foo"], encoders={str: lambda s: "baz"}
    )
    writer.writerow({"foo": "bar"})

    assert output_file.getvalue() == "baz\r\n"


def test_encoding_dict_writer_writerows():
    output_file = io.StringIO()

    writer = csv_util.EncodingDictWriter(
        output_file, fieldnames=["foo"], encoders={str: lambda s: "baz"}
    )
    writer.writerows([{"foo": "bar"}, {"foo": "foo"}])

    assert output_file.getvalue() == "baz\r\nbaz\r\n"
