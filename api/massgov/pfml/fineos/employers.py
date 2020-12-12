from dataclasses import dataclass
from typing import Optional

import massgov.pfml.api.services.fineos_actions as fineos_actions
import massgov.pfml.db as db
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import Employer, EmployerLog
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

    employers_query = db_session.query(Employer).filter(Employer.fineos_employer_id.is_(None))

    employers = db.skip_locked_query(employers_query, Employer.employer_id)

    employers_with_logging = massgov.pfml.util.logging.log_every(
        logger, employers, count=100, start_time=start_time
    )

    for employer in employers_with_logging:
        report.total_employers_count += 1

        # we must commit or rollback the transaction for each item to ensure the
        # row lock put in place by `skip_locked_query` is released
        try:
            fineos_actions.create_or_update_employer(fineos, employer)
            fineos_actions.create_service_agreement_for_employer(fineos, employer)

            db_session.commit()

            report.loaded_employers_count += 1
        except Exception:
            logger.exception(
                "Error creating/updating employer in FINEOS",
                extra={
                    "internal_employer_id": employer.employer_id,
                    "fineos_employer_id": employer.fineos_employer_id,
                },
            )

            db_session.rollback()

            report.errored_employers_count += 1
            continue

    end_time = utcnow()
    report.end = end_time.isoformat()
    report.process_duration_in_seconds = (end_time - start_time).total_seconds()

    return report


def load_updates(db_session: db.Session, fineos: AbstractFINEOSClient) -> LoadEmployersReport:
    start_time = utcnow()
    report = LoadEmployersReport(start=start_time.isoformat())

    updated_employer_ids_query = (
        db_session.query(EmployerLog.employer_id)
        .filter(EmployerLog.action.in_(["INSERT", "UPDATE"]))
        .group_by(EmployerLog.employer_id)
    )

    updated_employers_query = db_session.query(Employer).filter(
        Employer.employer_id.in_(updated_employer_ids_query)
    )

    employers = db.skip_locked_query(updated_employers_query, Employer.employer_id)

    employers_with_logging = massgov.pfml.util.logging.log_every(
        logger, employers, count=1000, start_time=start_time
    )

    for employer in employers_with_logging:
        report.total_employers_count += 1

        # we must commit or rollback the transaction for each item to ensure the
        # row lock put in place by `skip_locked_query` is released
        try:
            fineos_actions.create_or_update_employer(fineos, employer)
            fineos_actions.create_service_agreement_for_employer(fineos, employer)

            db_session.commit()

            report.loaded_employers_count += 1
        except Exception:
            logger.exception(
                "Error creating/updating employer in FINEOS",
                extra={
                    "internal_employer_id": employer.employer_id,
                    "fineos_employer_id": employer.fineos_employer_id,
                },
            )

            db_session.rollback()

            report.errored_employers_count += 1
            continue

    end_time = utcnow()
    report.end = end_time.isoformat()
    report.process_duration_in_seconds = (end_time - start_time).total_seconds()

    return report
