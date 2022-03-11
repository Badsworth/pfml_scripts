#
# Tests for massgov.pfml.delegated_payments.ach.reader.
#

import decimal
import io
import os.path
import random
import string

import pytest

import massgov.pfml.util.files
from massgov.pfml.delegated_payments.util.ach import reader

SIMPLE_RETURN = (
    "101 122287329 6910001340705312050F094101ABC CREDIT UNION       ABC APPLICATION SUPERVI        \r\n"
    "5200ABC             USPS-070525-1805    1222873290PPDUSPS TRANS      0705301521091000010004352\r\n"
    "626122287329130009783        0000089373A1001          Emily Schenck           1091000012930258\r\n"
    "799R0106300004000010100000024823818                                            091000012930258\r\n"
    "626122287329823795428        0000480954B1002          The Beatles             1091000012930258\r\n"
    "799R0106300004000010200000073088833                                            091000012930258\r\n"
    "626122287329456630883        0000006293A1003          John Krazit             1091000012930258\r\n"
    "799R0906300004000010300000020844164                                            091000012930258\r\n"
    "626122287329657340609        0000008352B1003          Debbie Glasser          1091000012930258\r\n"
    "799R0206300004000010400000078087339                                            091000012930258\r\n"
    "626122287329362060253        0000000393A1004          Daniel Longest          1091000012930258\r\n"
    "799R0206300004000010500000086084788                                            091000012930258\r\n"
    "820000000200122287320000000056870000000000001222873290                         091000010012637\r\n"
    "9000001000001000000100024457464000000019387000000000000                                       \r\n"
    "9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999\r\n"
)


def build_rr_from_return(return_str, line_number):
    split = return_str.split("\r\n")
    data = split[line_number - 1]
    type_code = int(data[0:1])

    return reader.RawRecord(type_code=type_code, line_number=line_number, data=data)


EXPECTED_SIMPLE_ACH_RETURNS = [
    reader.ACHReturn(
        id_number="A1001",
        return_reason_code="R01",
        original_dfi_id="24823818",
        dfi_account_number="130009783",
        amount=decimal.Decimal("893.73"),
        name="Emily Schenck",
        line_number=3,
        raw_record=build_rr_from_return(SIMPLE_RETURN, 3),
    ),
    reader.ACHReturn(
        id_number="B1002",
        return_reason_code="R01",
        original_dfi_id="73088833",
        dfi_account_number="823795428",
        amount=decimal.Decimal("4809.54"),
        name="The Beatles",
        line_number=5,
        raw_record=build_rr_from_return(SIMPLE_RETURN, 5),
    ),
    reader.ACHReturn(
        id_number="A1003",
        return_reason_code="R09",
        original_dfi_id="20844164",
        dfi_account_number="456630883",
        amount=decimal.Decimal("62.93"),
        name="John Krazit",
        line_number=7,
        raw_record=build_rr_from_return(SIMPLE_RETURN, 7),
    ),
    reader.ACHReturn(
        id_number="B1003",
        return_reason_code="R02",
        original_dfi_id="78087339",
        dfi_account_number="657340609",
        amount=decimal.Decimal("83.52"),
        name="Debbie Glasser",
        line_number=9,
        raw_record=build_rr_from_return(SIMPLE_RETURN, 9),
    ),
    reader.ACHReturn(
        id_number="A1004",
        return_reason_code="R02",
        original_dfi_id="86084788",
        dfi_account_number="362060253",
        amount=decimal.Decimal("3.93"),
        name="Daniel Longest",
        line_number=11,
        raw_record=build_rr_from_return(SIMPLE_RETURN, 11),
    ),
]


def test_ach_reader_simple():
    stream = io.StringIO(SIMPLE_RETURN)
    ach_reader = reader.ACHReader(stream)
    assert ach_reader.get_ach_returns() == EXPECTED_SIMPLE_ACH_RETURNS
    assert ach_reader.get_change_notifications() == []
    assert ach_reader.get_warnings() == []


def test_ach_reader_simple_from_s3(mock_s3_bucket_resource):
    mock_s3_bucket_resource.put_object(Key="tst.ach", Body=SIMPLE_RETURN)
    stream = massgov.pfml.util.files.open_stream("s3://%s/tst.ach" % mock_s3_bucket_resource.name)
    ach_reader = reader.ACHReader(stream)
    assert ach_reader.get_ach_returns() == EXPECTED_SIMPLE_ACH_RETURNS
    assert ach_reader.get_change_notifications() == []
    assert ach_reader.get_warnings() == []


def test_ach_reader_simple_newline():
    stream = io.StringIO(SIMPLE_RETURN.replace("\r\n", "\n"))
    ach_reader = reader.ACHReader(stream)
    assert ach_reader.get_ach_returns() == EXPECTED_SIMPLE_ACH_RETURNS
    assert ach_reader.get_change_notifications() == []
    assert ach_reader.get_warnings() == []


INVALID_LENGTH_LINES_RETURN = (
    "101 122287329 6910001340705312050F094101ABC CREDIT UNION       ABC APPLICATION SUPERVI        \r\n"
    "5200ABC             USPS-070525-1805    1222873290PPDUSPS TRANS      0705301521091000010004352\r\n"
    "626122287329130009783        0000089373A1001          Emily Schenck             1091000012930258\r\n"
    "799R0106300004000010100000024823818                                             091000012930258\r\n"
    "626122287329362060253        0000000393B1002          Daniel Longest          1091000012930258\r\n"
    "799R0206300004000010500000086084788                                           091000012930258\r\n"
)


def test_ach_reader_invalid_length_lines():
    stream = io.StringIO(INVALID_LENGTH_LINES_RETURN)
    ach_reader = reader.ACHReader(stream)
    assert ach_reader.get_ach_returns() == []
    assert ach_reader.get_change_notifications() == []
    assert warnings_summary(ach_reader.get_warnings()) == (
        (6, "missing FILE_CONTROL at end of file"),
        (6, "missing BATCH_CONTROL at end of batch"),
        (3, "invalid line length 96 (expected 94)"),
        (4, "invalid line length 95 (expected 94)"),
        (6, "invalid line length 93 (expected 94)"),
    )


def warnings_summary(warnings):
    return tuple(map(lambda w: (w.raw_record.line_number, w.warning), warnings))


MISSING_ADDENDA_RETURN = (
    "101 122287329 6910001340705312050F094101ABC CREDIT UNION       ABC APPLICATION SUPERVI        \r\n"
    "5200ABC             USPS-070525-1805    1222873290PPDUSPS TRANS      0705301521091000010004352\r\n"
    "626122287329130009783        0000089373A1001          Emily Schenck           1091000012930258\r\n"
    "626122287329657340609        0000008352B1003          Debbie Glasser          0091000012930258\r\n"
    "799R0206300004000010400000078087339                                            091000012930258\r\n"
    "626122287329362060253        0000000393B1002          Daniel Longest          1091000012930258\r\n"
    "799R0206300004000010500000086084788                                            091000012930258\r\n"
)


def test_ach_reader_missing_addenda():
    stream = io.StringIO(MISSING_ADDENDA_RETURN)
    ach_reader = reader.ACHReader(stream)
    assert ach_reader.get_ach_returns() == [
        reader.ACHReturn(
            id_number="B1002",
            return_reason_code="R02",
            original_dfi_id="86084788",
            dfi_account_number="362060253",
            amount=decimal.Decimal("3.93"),
            name="Daniel Longest",
            line_number=6,
            raw_record=build_rr_from_return(MISSING_ADDENDA_RETURN, 6),
        )
    ]
    assert ach_reader.get_change_notifications() == []
    assert warnings_summary(ach_reader.get_warnings()) == (
        (7, "missing FILE_CONTROL at end of file"),
        (7, "missing BATCH_CONTROL at end of batch"),
        (3, "unexpected types (<TypeCode.ENTRY_DETAIL: 6>,) (expected ENTRY_DETAIL, ADDENDA)"),
        (4, "expected addenda indicator"),
    )


INVALID_ADDENDA_CODE_RETURN = (
    "101 122287329 6910001340705312050F094101ABC CREDIT UNION       ABC APPLICATION SUPERVI        \r\n"
    "5200ABC             USPS-070525-1805    1222873290PPDUSPS TRANS      0705301521091000010004352\r\n"
    "626122287329130009783        0000089373A1001          Emily Schenck           1091000012930258\r\n"
    "701R0106300004000010100000024823818                                            091000012930258\r\n"
)


def test_ach_reader_invalid_addenda_code():
    stream = io.StringIO(INVALID_ADDENDA_CODE_RETURN)
    ach_reader = reader.ACHReader(stream)
    assert ach_reader.get_ach_returns() == []
    assert ach_reader.get_change_notifications() == []
    assert warnings_summary(ach_reader.get_warnings()) == (
        (4, "missing FILE_CONTROL at end of file"),
        (4, "missing BATCH_CONTROL at end of batch"),
        (4, "unexpected addenda type code 1"),
    )


def test_ach_reader_empty_file():
    stream = io.StringIO("")
    with pytest.raises(reader.ACHFatalParseError, match="empty file"):
        reader.ACHReader(stream)


def test_ach_reader_large():
    test_files = os.path.join(os.path.dirname(__file__), "test_files")

    return_str = open(
        os.path.join(test_files, "PUBACHRTRN__scrambled.txt"), mode="r", newline=""
    ).read()
    stream = open(os.path.join(test_files, "PUBACHRTRN__scrambled.txt"), mode="r")
    ach_reader = reader.ACHReader(stream)

    assert len(ach_reader.get_ach_returns()) == 399
    assert len(ach_reader.get_change_notifications()) == 974

    assert ach_reader.get_ach_returns()[0] == reader.ACHReturn(
        id_number="PREN11270247",
        return_reason_code="R03",
        original_dfi_id="01140153",
        dfi_account_number="3308780523",
        amount=decimal.Decimal("0"),
        name="BPBHSR  BPSPPP",
        line_number=3,
        raw_record=build_rr_from_return(return_str, 3),
    )
    assert ach_reader.get_change_notifications()[0] == reader.ACHChangeNotification(
        id_number="20629",
        return_reason_code="C02",  # C02 - incorrect transit/routing number
        original_dfi_id="01140153",
        dfi_account_number="1316271169",
        amount=decimal.Decimal("0"),
        name="BPBH X APDHAX",
        addenda_information="211070175",
        line_number=53,
        raw_record=build_rr_from_return(return_str, 53),
    )
    assert warnings_summary(ach_reader.get_warnings()) == ()


ENTRY_COUNT_WRONG_RETURN = (
    "101 122287329 6910001340705312050F094101ABC CREDIT UNION       ABC APPLICATION SUPERVI        \r\n"
    "5200ABC             USPS-070525-1805    1222873290PPDUSPS TRANS      0705301521091000010004352\r\n"
    "626122287329130009783        0000089373A1001          Emily Schenck           1091000012930258\r\n"
    "799R0106300004000010100000024823818                                            091000012930258\r\n"
    "820000000200122287320000000056870000000000001222873290                         091000010012637\r\n"
    "9000003000001000000050024457464000000019387000000000000                                       \r\n"
    "9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999\r\n"
)


def test_ach_reader_entry_count_wrong():
    stream = io.StringIO(ENTRY_COUNT_WRONG_RETURN)
    ach_reader = reader.ACHReader(stream)
    assert ach_reader.get_ach_returns() == [
        reader.ACHReturn(
            id_number="A1001",
            return_reason_code="R01",
            original_dfi_id="24823818",
            dfi_account_number="130009783",
            amount=decimal.Decimal("893.73"),
            name="Emily Schenck",
            line_number=3,
            raw_record=build_rr_from_return(ENTRY_COUNT_WRONG_RETURN, 3),
        )
    ]
    assert ach_reader.get_change_notifications() == []
    assert warnings_summary(ach_reader.get_warnings()) == (
        (6, "batch count mismatch (found 1, control 3)"),
        (6, "entry count mismatch (found 2, control 5)"),
    )


NO_FILE_HEADER_RETURN = (
    "5200ABC             USPS-070525-1805    1222873290PPDUSPS TRANS      0705301521091000010004352\r\n"
    "626122287329130009783        0000089373A1001          Emily Schenck           1091000012930258\r\n"
    "799R0106300004000010100000024823818                                            091000012930258\r\n"
)


def test_ach_reader_no_file_header():
    stream = io.StringIO(NO_FILE_HEADER_RETURN)
    with pytest.raises(reader.ACHFatalParseError, match="unexpected type for first record"):
        reader.ACHReader(stream)


NO_BATCH_HEADER_RETURN = (
    "101 122287329 6910001340705312050F094101ABC CREDIT UNION       ABC APPLICATION SUPERVI        \r\n"
    "626122287329130009783        0000089373A1001          Emily Schenck           1091000012930258\r\n"
    "799R0106300004000010100000024823818                                            091000012930258\r\n"
)


def test_ach_reader_no_batch_header():
    stream = io.StringIO(NO_BATCH_HEADER_RETURN)
    ach_reader = reader.ACHReader(stream)
    assert ach_reader.get_ach_returns() == [
        reader.ACHReturn(
            id_number="A1001",
            return_reason_code="R01",
            original_dfi_id="24823818",
            dfi_account_number="130009783",
            amount=decimal.Decimal("893.73"),
            name="Emily Schenck",
            line_number=2,
            raw_record=build_rr_from_return(NO_BATCH_HEADER_RETURN, 2),
        )
    ]
    assert ach_reader.get_change_notifications() == []
    assert warnings_summary(ach_reader.get_warnings()) == (
        (3, "missing FILE_CONTROL at end of file"),
        (2, "missing BATCH_HEADER at start of batch"),
        (3, "missing BATCH_CONTROL at end of batch"),
    )


RANDOM_CHARACTERS = string.ascii_uppercase + (string.digits * 10) + (" " * 20)
FILE_HEADER = "101 122287329 6910001340705312050F094101ABC CREDIT UNION       ABC APPLICATION SUPERVI        \r\n"


@pytest.mark.parametrize("seed", range(20))
def test_ach_reader_fuzz(seed):
    random.seed(seed)
    stream = io.StringIO()
    stream.write(FILE_HEADER)
    for _i in range(10):
        stream.write("".join(random.choices(RANDOM_CHARACTERS, k=94)))
        stream.write("\r\n")
    stream.seek(0)
    with pytest.raises(reader.ACHFatalParseError, match="invalid type code"):
        reader.ACHReader(stream)


@pytest.mark.parametrize("seed", range(20))
def test_ach_reader_fuzz_valid_start(seed):
    random.seed(seed)
    stream = io.StringIO()
    stream.write(FILE_HEADER)
    for _i in range(10):
        stream.write(random.choice("156789"))
        stream.write("".join(random.choices(string.digits, k=2)))
        stream.write("".join(random.choices(RANDOM_CHARACTERS, k=91)))
        stream.write("\r\n")
    stream.seek(0)
    ach_reader = reader.ACHReader(stream)
    assert len(ach_reader.get_warnings()) >= 4


@pytest.mark.parametrize("line", SIMPLE_RETURN.split("\r\n"))
def test_ach_reader_fuzz_single_line(line):
    stream = io.StringIO(FILE_HEADER + line)
    ach_reader = reader.ACHReader(stream)
    assert len(ach_reader.get_warnings()) >= 1


def build_rr(type_code, line_number):
    return reader.RawRecord(
        type_code=type_code, line_number=line_number, data="line %i" % line_number
    )


batch1, batch2, batch3 = (build_rr(reader.TypeCode.BATCH_HEADER, i) for i in range(1, 4))
entry1, entry2, entry3, entry4 = (build_rr(reader.TypeCode.ENTRY_DETAIL, i) for i in range(1, 5))
control1, control2 = (build_rr(reader.TypeCode.BATCH_CONTROL, i) for i in range(1, 3))


@pytest.mark.parametrize(
    "raw_records,type_code,expected_partitions",
    (
        ((), reader.TypeCode.BATCH_HEADER, []),
        ([batch1], reader.TypeCode.BATCH_HEADER, [[batch1]]),
        ([entry1], reader.TypeCode.BATCH_HEADER, [[entry1]]),
        ([batch1, entry1, entry2], reader.TypeCode.BATCH_HEADER, [[batch1, entry1, entry2]]),
        (
            (entry1, batch1, entry2, entry3),
            reader.TypeCode.BATCH_HEADER,
            [[entry1], [batch1, entry2, entry3]],
        ),
        (
            [batch1, entry1, entry2, control1, batch2, batch3, entry3, entry4, control2],
            reader.TypeCode.BATCH_HEADER,
            [[batch1, entry1, entry2, control1], [batch2], [batch3, entry3, entry4, control2]],
        ),
        (
            [batch1, entry1, entry2, batch2, batch3, entry3, entry4],
            reader.TypeCode.FILE_CONTROL,
            [[batch1, entry1, entry2, batch2, batch3, entry3, entry4]],
        ),
    ),
)
def test_partition_by_type_code(raw_records, type_code, expected_partitions):
    assert reader.partition_by_type_code(raw_records, type_code) == expected_partitions
