from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional

import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.api.services import fineos_actions
from massgov.pfml.db.models.employees import Employer
from massgov.pfml.fineos import FINEOSClientError
from massgov.pfml.util.logging import audit

logger = logging.get_logger("massgov.pfml.fineos.employer_load")


@dataclass
class LoadEmployersReport:
    start: str = datetime.now().isoformat()
    errored_employers_count: int = 0
    loaded_employers_info_count: int = 0
    end: Optional[str] = None
    process_duration_in_ms: float = 0


def handler(event=None, context=None):
    """ECS handler function."""
    audit.init_security_logging()
    logging.init(__name__)

    db_session = db.init()

    start_time = datetime.now()
    report = LoadEmployersReport(start=start_time.isoformat())

    logger.info("Starting loading employers to FINEOS.")

    employers = (
        db_session.query(Employer).filter(Employer.fineos_employer_id.__eq__(None)).yield_per(1000)
    )

    for employer in employers:
        try:
            fineos_customer_nbr, fineos_employer_id = fineos_actions.create_or_update_employer(
                employer.employer_fein, db_session
            )
            fineos_actions.create_service_agreement_for_employer(fineos_employer_id, db_session)
            report.loaded_employers_info_count += 1
        except FINEOSClientError as ex:
            logger.error(ex)
            report.errored_employers_count += 1

    db_session.commit()
    end_time = datetime.now()
    report.end = end_time.isoformat()
    report.process_duration_in_ms = (end_time - start_time).microseconds / 1000
    logger.info("Finished loading employers to FINEOS.", extra={"report": asdict(report)})
