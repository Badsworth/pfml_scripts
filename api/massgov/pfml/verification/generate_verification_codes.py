""" This script is intended to do the following actions by default
1. Read a CSV file containing Employer FEINs and a quantity of codes to generate
2. Create VerificationCode records for each FEIN in the quantity requested
3. Output a CSV file containing Employer FEINs and Verification Codes as requested
"""

import argparse
import csv
import datetime
import random
import string

import smart_open

from massgov.pfml import db
from massgov.pfml.db.models.employees import Employer
from massgov.pfml.db.models.verifications import VerificationCode

OUTPUT_CSV_FIELDS = ["fein", "verification_code", "uses", "expiration_date", "contact", "email"]
DEFAULT_CODE_LENGTH = 6
DEFAULT_VALID_DAYS = 90


class CSVSourceWrapper:
    """ Simple wrapper for reading dicts out of CSV files """

    def __init__(self, file_path: str):
        self._file_path = file_path

    def __iter__(self):
        with smart_open.open(self._file_path, "r") as csvfile:
            dict_reader = csv.DictReader(csvfile, delimiter=",")
            for row in dict_reader:
                yield row


def create_code(
    db_session: db.Session,
    fein: str,
    code_length: int = DEFAULT_CODE_LENGTH,
    uses: int = 1,
    valid_for: int = DEFAULT_VALID_DAYS,
) -> VerificationCode:
    """ Create a new VerificationCode record given the values provided """
    # Looks up to see if an existing Employer row exists to assign an employer_id to the record
    employer_row = db_session.query(Employer).filter(Employer.employer_fein == fein).one_or_none()
    employer_id = employer_row.employer_id if employer_row else None

    code = VerificationCode(
        employer_id=employer_id,
        employer_fein=fein,
        verification_code="".join(
            random.choices(string.ascii_uppercase + string.digits, k=code_length)
        ),
        expires_at=datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        + datetime.timedelta(days=valid_for),
        remaining_uses=uses,
    )
    db_session.add(code)
    db_session.flush()
    db_session.refresh(code)
    return code


def process_file(db_session: db.Session, input_csv_filename: str, output_csv_filename: str) -> None:
    """ Ingest a CSV file, generate codes in the DB, output a CSV file """

    csv_input = CSVSourceWrapper(input_csv_filename)
    with smart_open.open(output_csv_filename, "w") as output_file:
        csv_output = csv.DictWriter(
            output_file, fieldnames=OUTPUT_CSV_FIELDS, restval="", extrasaction="ignore",
        )
        csv_output.writeheader()

        for row in csv_input:
            quantity = row.pop("quantity", 1)
            for _ in range(0, int(quantity)):
                code = create_code(
                    db_session,
                    fein=row["fein"],
                    code_length=int(row.get("code_length") or DEFAULT_CODE_LENGTH),
                    valid_for=int(row.get("valid_for") or DEFAULT_VALID_DAYS),
                    uses=int(row.get("uses") or 1),
                )
                csv_output.writerow(
                    {
                        **row,
                        "verification_code": code.verification_code,
                        "expiration_date": code.expires_at,
                        "uses": code.remaining_uses,
                    }
                )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create Verification Code records based on CSV file contents",
        epilog=(
            "Requires a database connection; will use environment variables "
            "such as DB_HOST, DB_USERNAME, DB_PASSWORD, DB_PORT"
        ),
    )
    parser.add_argument("--input", help="CSV filename containing at least the column [fein]")
    parser.add_argument("--output", help="CSV filename to store resulting data in")
    args = parser.parse_args()
    if not args.input and args.output:
        parser.print_help()
        exit(1)
    return args


def main():
    """ Run the whole program """
    args = parse_args()

    db_session_raw = db.init()

    with db.session_scope(db_session_raw) as db_session:
        process_file(
            db_session, args.input, args.output,
        )


if __name__ == "__main__":
    main()
