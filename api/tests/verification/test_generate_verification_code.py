#
# Tests for massgov.pfml.verification.generate_verification_codes.
#
import datetime
import tempfile
from pathlib import Path

import pytest

from massgov.pfml.db.models.factories import EmployerFactory
from massgov.pfml.db.models.verifications import VerificationCode
from massgov.pfml.verification import generate_verification_codes


@pytest.fixture
def employer(initialize_factories_session):
    return EmployerFactory.create()


def get_days_from_now(timestamp):
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    then = datetime.datetime.fromisoformat(timestamp)
    return (then - now).days


class TestGenerateVerificationCode:
    def test_create_code(self, test_db_session, employer):
        code = generate_verification_codes.create_code(
            test_db_session, fein=employer.employer_fein, code_length=10
        )
        assert len(code.verification_code) == 10

        database_row = test_db_session.query(VerificationCode).get(code.verification_code_id)
        assert code.verification_code == database_row.verification_code

    def test_process_file1(self, test_db_session):
        location = Path(__file__).parent / "test1.csv"
        with tempfile.NamedTemporaryFile() as output_file:
            generate_verification_codes.process_file(
                test_db_session, input_csv_filename=location, output_csv_filename=output_file.name
            )
            output_file.seek(0)
            rows = [r for r in generate_verification_codes.CSVSourceWrapper(output_file)]
            assert len(rows) == 2
            assert rows[0]["email"] == rows[1]["email"]
            assert rows[0]["email"] == "webmaster@cheezburger.biz"
            assert (
                len(rows[0]["verification_code"]) == generate_verification_codes.DEFAULT_CODE_LENGTH
            )
            assert (
                get_days_from_now(rows[0]["expiration_date"])
                == generate_verification_codes.DEFAULT_VALID_DAYS - 1
            )

    def test_process_file2(self, test_db_session):
        location = Path(__file__).parent / "test2.csv"
        with tempfile.NamedTemporaryFile() as output_file:
            generate_verification_codes.process_file(
                test_db_session, input_csv_filename=location, output_csv_filename=output_file.name
            )
            output_file.seek(0)
            rows = [r for r in generate_verification_codes.CSVSourceWrapper(output_file)]
            assert len(rows) == 1
            assert rows[0]["email"] == "canuhaz@yahoo.com"
            assert get_days_from_now(rows[0]["expiration_date"]) == 99
            assert len(rows[0]["verification_code"]) == 10
