from massgov.pfml.util.files.file_format import FieldFormat, FileFormat

test_format = (
    FieldFormat("name", 4),
    FieldFormat("age", 3, int),
    FieldFormat("active", 1, lambda b: b == "T"),
)

test_line = line = "Jane27 T"


def test_file_format():
    file_format = FileFormat(test_format)
    parsed_obj = file_format.parse_line(line)

    assert parsed_obj["name"] == "Jane"
    assert parsed_obj["age"] == 27
    assert parsed_obj["active"] is True
