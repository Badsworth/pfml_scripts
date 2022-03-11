#
# Tests for CheckReader class.
#

import datetime
import decimal
import io

import pytest

from massgov.pfml.delegated_payments.pub import check_return

OUTSTANDING_ISSUES_CSV = (
    "Begin Date,End Date,TRC Number,Bank Name,Account Number,Account Type,Account Name,Type,"
    "Type Detail,Check Number,Issued Date,Issued Amount,Payee Name,Payee ID,BFC Code\r\n"
    "04/05/2021,04/15/2021,221172186,PEOPLES UNITED BANK 136,400000000,Checking,PFML,Outstanding,"
    "Outstanding,25,03/22/2021,55.75,Test Aaa,A100,B100\r\n"
    "04/05/2021,04/15/2021,221172186,PEOPLES UNITED BANK 136,400000000,Checking,PFML,Outstanding,"
    "Void,28,03/25/2021,60.75,Test Bbb,A100,B100\r\n"
)

PAID_CHECKS_CSV = (
    "Begin Date,End Date,TRC Number,Bank Name,Account Number,Account Type,Account Name,Type,"
    "Type Detail,Check Number,Posted Date,Posted Amount,Payee Name,Payee ID,BFC Code\r\n"
    "04/05/2021,04/15/2021,221172186,PEOPLES UNITED BANK 136,400000000,Checking,PFML,Debit,"
    "Check,25,03/22/2021,-55.75,Test Aaa,A100,B100\r\n"
    "04/05/2021,04/15/2021,221172186,PEOPLES UNITED BANK 136,400000000,Checking,PFML,Debit,"
    "Check,28,03/25/2021,-60.75,Test Bbb,A100,B100\r\n"
)

OUTSTANDING_ISSUES_WITH_INVALID_LINES_CSV = (
    "Begin Date,End Date,TRC Number,Bank Name,Account Number,Account Type,Account Name,Type,"
    "Type Detail,Check Number,Issued Date,Issued Amount,Payee Name,Payee ID,BFC Code\r\n"
    "04/05/2021,04/15/2021,221172186,PEOPLES UNITED BANK 136,400000000,Checking,PFML,Outstanding,"
    "Broken,25,03/22/2021,100.75,Test Aaa,A100,B100\r\n"
    "04/05/2021,04/15/2021,221172186,PEOPLES UNITED BANK 136,400000000,Checking,PFML,Outstanding,"
    "Void,26,25/03/2021,200.75,Test Bbb,A100,B100\r\n"
    "04/05/2021,04/15/2021,221172186,PEOPLES UNITED BANK 136,400000000,Checking,PFML,Outstanding,"
    "Void,27,03/25/2021,30.0.75,Test Ccc,A100,B100\r\n"
    "04/05/2021,04/15/2021,221172186,PEOPLES UNITED BANK 136,400000000,Checking,PFML,Outstanding,"
    "Void,28,03/25/2021,400.75,Test Ddd,A100,B100\r\n"
)

INVALID_CSV = (
    "Begin Date,End Date,TRC Number,Bank Name,Account Number,Account Type,Account Name,Type,"
    "Check Number,Issued Date,Payee Name,Payee ID,BFC Code\r\n"
    "04/05/2021,04/15/2021,221172186,PEOPLES UNITED BANK 136,400000000,Checking,PFML,Outstanding,"
    "25,03/22/2021,Test Aaa,A100,B100\r\n"
)


def test_check_reader_outstanding_issues():
    stream = io.StringIO(OUTSTANDING_ISSUES_CSV, newline=None)
    reader = check_return.CheckReader(stream)
    payments = reader.get_check_payments()
    line_errors = reader.get_line_errors()

    assert reader.is_outstanding_issues is True
    assert reader.is_paid_checks is False
    assert payments == [
        check_return.CheckPayment(
            line_number=2,
            raw_line="04/05/2021,04/15/2021,221172186,PEOPLES UNITED BANK 136,400000000,Checking,"
            "PFML,Outstanding,Outstanding,25,03/22/2021,55.75,Test Aaa,A100,B100\n",
            status=check_return.PaidStatus.OUTSTANDING,
            check_number="25",
            payee_name="Test Aaa",
            issued_date=datetime.date(2021, 3, 22),
            paid_date=None,
            amount=decimal.Decimal("55.75"),
        ),
        check_return.CheckPayment(
            line_number=3,
            raw_line="04/05/2021,04/15/2021,221172186,PEOPLES UNITED BANK 136,400000000,Checking,"
            "PFML,Outstanding,Void,28,03/25/2021,60.75,Test Bbb,A100,B100\n",
            status=check_return.PaidStatus.VOID,
            check_number="28",
            payee_name="Test Bbb",
            issued_date=datetime.date(2021, 3, 25),
            paid_date=None,
            amount=decimal.Decimal("60.75"),
        ),
    ]
    assert line_errors == []


def test_check_reader_paid_checks():
    stream = io.StringIO(PAID_CHECKS_CSV, newline=None)
    reader = check_return.CheckReader(stream)
    payments = reader.get_check_payments()
    line_errors = reader.get_line_errors()

    assert reader.is_outstanding_issues is False
    assert reader.is_paid_checks is True
    assert payments == [
        check_return.CheckPayment(
            line_number=2,
            raw_line="04/05/2021,04/15/2021,221172186,PEOPLES UNITED BANK 136,400000000,Checking,"
            "PFML,Debit,Check,25,03/22/2021,-55.75,Test Aaa,A100,B100\n",
            status=check_return.PaidStatus.PAID,
            check_number="25",
            payee_name="Test Aaa",
            issued_date=None,
            paid_date=datetime.date(2021, 3, 22),
            amount=decimal.Decimal("55.75"),
        ),
        check_return.CheckPayment(
            line_number=3,
            raw_line="04/05/2021,04/15/2021,221172186,PEOPLES UNITED BANK 136,400000000,Checking,"
            "PFML,Debit,Check,28,03/25/2021,-60.75,Test Bbb,A100,B100\n",
            status=check_return.PaidStatus.PAID,
            check_number="28",
            payee_name="Test Bbb",
            issued_date=None,
            paid_date=datetime.date(2021, 3, 25),
            amount=decimal.Decimal("60.75"),
        ),
    ]
    assert line_errors == []


def test_check_reader_invalid_lines():
    stream = io.StringIO(OUTSTANDING_ISSUES_WITH_INVALID_LINES_CSV, newline=None)
    reader = check_return.CheckReader(stream)
    payments = reader.get_check_payments()
    line_errors = reader.get_line_errors()

    assert reader.is_outstanding_issues is True
    assert reader.is_paid_checks is False
    assert payments == [
        check_return.CheckPayment(
            line_number=5,
            raw_line="04/05/2021,04/15/2021,221172186,PEOPLES UNITED BANK 136,400000000,Checking,"
            "PFML,Outstanding,Void,28,03/25/2021,400.75,Test Ddd,A100,B100\n",
            status=check_return.PaidStatus.VOID,
            check_number="28",
            payee_name="Test Ddd",
            issued_date=datetime.date(2021, 3, 25),
            paid_date=None,
            amount=decimal.Decimal("400.75"),
        )
    ]
    assert line_errors == [
        check_return.CheckParseLineError(
            line_number=2,
            raw_line="04/05/2021,04/15/2021,221172186,PEOPLES UNITED BANK 136,400000000,Checking,"
            "PFML,Outstanding,Broken,25,03/22/2021,100.75,Test Aaa,A100,B100\n",
            field_name="Type Detail",
            warning="invalid status",
        ),
        check_return.CheckParseLineError(
            line_number=3,
            raw_line="04/05/2021,04/15/2021,221172186,PEOPLES UNITED BANK 136,400000000,Checking,"
            "PFML,Outstanding,Void,26,25/03/2021,200.75,Test Bbb,A100,B100\n",
            field_name="Issued Date",
            warning="invalid date",
        ),
        check_return.CheckParseLineError(
            line_number=4,
            raw_line="04/05/2021,04/15/2021,221172186,PEOPLES UNITED BANK 136,400000000,Checking,"
            "PFML,Outstanding,Void,27,03/25/2021,30.0.75,Test Ccc,A100,B100\n",
            field_name="Issued Amount",
            warning="invalid decimal",
        ),
    ]


# Test otherwise valid CSV with each character in turn replaced by "z".
@pytest.mark.parametrize("offset", range(len(OUTSTANDING_ISSUES_CSV) - 1))
def test_check_reader_fuzz(offset):
    modified_csv = OUTSTANDING_ISSUES_CSV[:offset] + "z" + OUTSTANDING_ISSUES_CSV[offset + 1 :]
    stream = io.StringIO(modified_csv, newline=None)
    # One of these cases must happen:
    #  1. A fatal parse error (CheckParseError).
    #  2. Both lines were parsed successfully.
    #  3. One line parsed successfully and one is a line error.
    #  4. Both lines have line errors.
    try:
        reader = check_return.CheckReader(stream)
    except check_return.CheckParseError:
        return
    payments = reader.get_check_payments()
    line_errors = reader.get_line_errors()
    assert (len(payments), len(line_errors)) in {(2, 0), (1, 1), (0, 2)}
    assert {item.line_number for item in payments + line_errors} == {2, 3}


def test_check_reader_invalid_csv():
    stream = io.StringIO(INVALID_CSV, newline=None)
    with pytest.raises(check_return.CheckParseError):
        check_return.CheckReader(stream)


def test_check_reader_empty_csv():
    stream = io.StringIO("", newline=None)
    with pytest.raises(check_return.CheckParseError):
        check_return.CheckReader(stream)
