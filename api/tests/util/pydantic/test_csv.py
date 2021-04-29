import io

from pydantic import BaseModel, Field

from massgov.pfml.util.pydantic.csv import DataWriter


class ExampleRow(BaseModel):
    foo: str


def test_data_writer_writerow():
    output_file = io.StringIO()

    writer = DataWriter(output_file, row_type=ExampleRow)
    writer.writeheader()
    writer.writerow(ExampleRow(foo="bar"))

    assert output_file.getvalue() == "\r\n".join(["foo", "bar"]) + "\r\n"


def test_data_writer_writerow_supports_dictionary():
    output_file = io.StringIO()

    writer = DataWriter(output_file, row_type=ExampleRow)
    writer.writeheader()
    writer.writerow({"foo": "bar"})

    assert output_file.getvalue() == "\r\n".join(["foo", "bar"]) + "\r\n"


def test_data_writer_writerows():
    output_file = io.StringIO()

    writer = DataWriter(output_file, row_type=ExampleRow)
    writer.writeheader()
    writer.writerows([ExampleRow(foo="bar"), ExampleRow(foo="baz")])

    assert output_file.getvalue() == "\r\n".join(["foo", "bar", "baz"]) + "\r\n"


def test_data_writer_writerows_supports_dictionary():
    output_file = io.StringIO()

    writer = DataWriter(output_file, row_type=ExampleRow)
    writer.writeheader()
    writer.writerows([{"foo": "bar"}, {"foo": "baz"}])

    assert output_file.getvalue() == "\r\n".join(["foo", "bar", "baz"]) + "\r\n"


class ExampleRowAliases(BaseModel):
    foo: str = Field(..., alias="FOO")

    class Config:
        allow_population_by_field_name = True


def test_data_writer_writerow_alias():
    output_file = io.StringIO()

    writer = DataWriter(output_file, row_type=ExampleRowAliases)
    writer.writeheader()
    writer.writerow(ExampleRowAliases(foo="bar"))

    assert output_file.getvalue() == "\r\n".join(["FOO", "bar"]) + "\r\n"


def test_data_writer_writerows_alias():
    output_file = io.StringIO()

    writer = DataWriter(output_file, row_type=ExampleRowAliases)
    writer.writeheader()
    writer.writerows([ExampleRowAliases(foo="bar"), ExampleRowAliases(foo="baz")])

    assert output_file.getvalue() == "\r\n".join(["FOO", "bar", "baz"]) + "\r\n"
