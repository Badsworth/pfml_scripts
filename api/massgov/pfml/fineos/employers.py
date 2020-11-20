from dataclasses import dataclass
from typing import Any, Iterator, Optional

import massgov.pfml.api.services.fineos_actions as fineos_actions
import massgov.pfml.db as db
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import Employer
from massgov.pfml.fineos import AbstractFINEOSClient
from massgov.pfml.util.datetime import utcnow

logger = massgov.pfml.util.logging.get_logger(__name__)


@dataclass
class LoadEmployersReport:
    start: str = utcnow().isoformat()
    total_employers_count: int = 0
    loaded_employers_count: int = 0
    errored_employers_count: int = 0
    end: Optional[str] = None
    process_duration_in_seconds: float = 0


def load_all(db_session: db.Session, fineos: AbstractFINEOSClient) -> LoadEmployersReport:
    start_time = utcnow()
    report = LoadEmployersReport(start=start_time.isoformat())

    employers = employers_with_no_fineos_id(db_session)

    employers_with_logging = massgov.pfml.util.logging.log_every(
        logger, employers, count=1000, start_time=start_time
    )

    for employer in employers_with_logging:
        report.total_employers_count += 1

        try:
            fineos_actions.create_or_update_employer(fineos, employer)
            fineos_actions.create_service_agreement_for_employer(fineos, employer)

            # commit every update in case something goes wrong later in the
            # process
            db_session.commit()

            report.loaded_employers_count += 1
        except Exception:
            logger.exception(
                "Error creating employer in FINEOS", extra={"employer_id": employer.employer_id}
            )

            db_session.rollback()

            report.errored_employers_count += 1
            continue

    end_time = utcnow()
    report.end = end_time.isoformat()
    report.process_duration_in_seconds = (end_time - start_time).total_seconds()

    return report


def employers_with_no_fineos_id(db_session: db.Session) -> Iterator[Employer]:
    """Generator that uses "SKIP LOCKED" to yield one employer row to work on.

    This uses the PostgreSQL "SELECT ... FOR UPDATE SKIP LOCKED" feature to select the next
    unprocessed row. Multiple processes can do this simultaneously and will never get the same row
    as the row is locked until the end of the transaction.

    After processing a row, the caller must commit or rollback to end the transaction and release
    the lock on the row. (The lock will also be released if the process crashes and disconnects
    from the PostgreSQL server.)

    https://www.2ndquadrant.com/en/blog/what-is-select-skip-locked-for-in-postgresql-9-5/
    """
    last_id: Optional[Any] = None

    while True:
        employer_query = (
            db_session.query(Employer)
            .filter(Employer.fineos_employer_id.is_(None))
            .order_by(Employer.employer_id)
            .with_for_update(skip_locked=True)
        )
        # Ensure that we don't get stuck repeating a failed row.
        if last_id is not None:
            employer_query = employer_query.filter(Employer.employer_id > last_id)

        employer = employer_query.first()

        if employer is None:
            return
        yield employer

        last_id = employer.employer_id
