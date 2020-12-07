from datetime import timedelta
from typing import Optional

from massgov.pfml import db
from massgov.pfml.db.models.employees import Employer
from massgov.pfml.db.models.verifications import Verification, VerificationCode, VerificationType
from massgov.pfml.util.datetime import utcnow
from massgov.pfml.util.employers import lookup_employer

CONTACT_CENTER_VERIFICATION_CODE = "U9A6BD"  # This code was provided to the Contact Center
CONTACT_CENTER_VERIFICATION = None


def verify(
    db_session: db.Session,
    verification_code: str,
    email: str,
    employer: Employer,
    consume_use: Optional[bool] = False,
) -> bool:
    # verified = False

    verification_code_record = (
        db_session.query(VerificationCode)
        .filter(VerificationCode.verification_code == verification_code)
        .one_or_none()
    )

    verification_employer = None
    if verification_code_record:
        if verification_code_record.employer_id:
            verification_employer = lookup_employer(
                db_session=db_session, employer_id=verification_code_record.employer_id
            )
        elif verification_code_record.employer_fein:
            verification_employer = lookup_employer(
                db_session=db_session, employer_fein=verification_code_record.employer_fein
            )

        if verification_employer and verification_employer.employer_id == employer.employer_id:
            # This is a verified employer; the entered FEIN matches the verification code data
            # create a Verification record for this
            # verified = True
            verification = Verification(
                verification_type_id=VerificationType.VERIFICATION_CODE.verification_type_id,
                verification_code_id=verification_code_record.verification_code_id,
                email_address=email,
            )
            db_session.add(verification)
            if consume_use:
                verification_code_record.remaining_uses = (
                    verification_code_record.remaining_uses - 1
                )
                db_session.add(verification_code_record)
            db_session.commit()
            return True
    return False


def ensure_contact_center_verification(db_session: db.Session) -> None:
    global CONTACT_CENTER_VERIFICATION
    if not CONTACT_CENTER_VERIFICATION:
        verification = (
            db_session.query(VerificationCode)
            .filter(VerificationCode.verification_code == CONTACT_CENTER_VERIFICATION_CODE)
            .one_or_none()
        )

        if not verification:
            verification = VerificationCode(
                verification_code=CONTACT_CENTER_VERIFICATION_CODE,
                expires_at=(utcnow() + timedelta(days=365)),
                remaining_uses=100000,
            )
            db_session.add(verification)
            db_session.commit()
        CONTACT_CENTER_VERIFICATION = True
