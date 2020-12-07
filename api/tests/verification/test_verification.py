import pytest

from massgov.pfml.db.models.factories import EmployerFactory
from massgov.pfml.db.models.verifications import Verification, VerificationCode
from massgov.pfml.verification import generate_verification_codes, verification


@pytest.fixture
def employer(initialize_factories_session):
    return EmployerFactory.create()


class TestGenerateVerificationCode:
    def test_verify_consume_use(self, test_db_session, employer):
        """ Test the valid case """
        code = generate_verification_codes.create_code(
            test_db_session, fein=employer.employer_fein, code_length=10
        )

        result = verification.verify(
            test_db_session,
            verification_code=code.verification_code,
            email="employer@fake.com",
            employer=employer,
            consume_use=True,
        )
        assert result is True

        db_verification_code_record = test_db_session.query(VerificationCode).get(
            code.verification_code_id
        )
        assert db_verification_code_record.remaining_uses == 0

        db_verification_record = (
            test_db_session.query(Verification)
            .filter(
                Verification.verification_code_id
                == db_verification_code_record.verification_code_id
            )
            .one_or_none()
        )
        assert db_verification_record.email_address == "employer@fake.com"

    def test_verify_no_consume_use(self, test_db_session, employer):
        """ Test the valid case; no consume remaining_use """
        code = generate_verification_codes.create_code(
            test_db_session, fein=employer.employer_fein, code_length=10
        )

        result = verification.verify(
            test_db_session,
            verification_code=code.verification_code,
            email="employer@fake.com",
            employer=employer,
            consume_use=False,
        )
        assert result is True

        db_verification_code_record = test_db_session.query(VerificationCode).get(
            code.verification_code_id
        )
        assert db_verification_code_record.remaining_uses == 1

        db_verification_record = (
            test_db_session.query(Verification)
            .filter(
                Verification.verification_code_id
                == db_verification_code_record.verification_code_id
            )
            .one_or_none()
        )
        assert db_verification_record.email_address == "employer@fake.com"

    def test_verify_employer_mismatch(self, test_db_session, employer):
        """ Code associated with a different employer """
        wrong_employer = EmployerFactory.create()
        code = generate_verification_codes.create_code(
            test_db_session, fein=employer.employer_fein, code_length=10
        )

        result = verification.verify(
            test_db_session,
            verification_code=code.verification_code,
            email="employer@fake.com",
            employer=wrong_employer,
            consume_use=False,
        )
        assert result is False

        db_verification_record = (
            test_db_session.query(Verification)
            .filter(Verification.verification_code_id == code.verification_code_id)
            .one_or_none()
        )
        assert db_verification_record is None

    def test_verify_no_employer_on_code(self, test_db_session, employer):
        """ Verification code had no employer """
        code = generate_verification_codes.create_code(test_db_session, fein="", code_length=10)

        result = verification.verify(
            test_db_session,
            verification_code=code.verification_code,
            email="employer@fake.com",
            employer=employer,
            consume_use=False,
        )
        assert result is False

        db_verification_record = (
            test_db_session.query(Verification)
            .filter(Verification.verification_code_id == code.verification_code_id)
            .one_or_none()
        )
        assert db_verification_record is None

    def test_ensure_contact_center_code(self, test_db_session):
        """ Check that the code gets created when ensure_contact_center_verification is called """
        verification.ensure_contact_center_verification(test_db_session)
        db_verification_code_record = (
            test_db_session.query(VerificationCode)
            .filter(
                VerificationCode.verification_code == verification.CONTACT_CENTER_VERIFICATION_CODE
            )
            .one_or_none()
        )
        assert db_verification_code_record

    def test_ensure_contact_center_code_no_lookup(self, test_db_session):
        """ Check that the code doesn't get looked up if CONTACT_CENTER_VERIFICATION is set """
        verification.CONTACT_CENTER_VERIFICATION = True
        verification.ensure_contact_center_verification(test_db_session)
        db_verification_code_record = (
            test_db_session.query(VerificationCode)
            .filter(
                VerificationCode.verification_code == verification.CONTACT_CENTER_VERIFICATION_CODE
            )
            .one_or_none()
        )
        assert db_verification_code_record is None
