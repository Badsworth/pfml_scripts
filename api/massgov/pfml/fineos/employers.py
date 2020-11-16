from dataclasses import dataclass
from typing import Optional

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

    employers_query = db_session.query(Employer).filter(Employer.fineos_employer_id.is_(None))

    employers = db.windowed_query(employers_query, Employer.employer_id, 1000)

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
            report.errored_employers_count += 1
            continue

    end_time = utcnow()
    report.end = end_time.isoformat()
    report.process_duration_in_seconds = (end_time - start_time).total_seconds()

    return report
