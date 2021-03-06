import argparse
from dataclasses import asdict
from enum import Enum
from typing import Optional

from pydantic import Field

import massgov.pfml.fineos.employers
import massgov.pfml.util.batch.log
import massgov.pfml.util.logging as logging
import massgov.pfml.util.pydantic
from massgov.pfml import db, fineos
from massgov.pfml.util.bg import background_task

logger = logging.get_logger(__name__)


class EmployerLoadMode(Enum):
    ONLY_NEW = "only_new"
    UPDATES = "updates"


class EmployerLoadConfig(massgov.pfml.util.pydantic.PydanticBaseSettings):
    mode: EmployerLoadMode = Field(EmployerLoadMode.ONLY_NEW, env="EMPLOYER_LOAD_MODE")
    update_employer_number_limit: Optional[int] = Field(
        None, env="EMPLOYER_UPDATE_LIMIT"
    )  # Only applies to "updates" mode


def parse_args():
    parser = argparse.ArgumentParser(description="Load Employers to FINEOS")
    parser.add_argument(
        "--process-id",
        help="Identifier for the update process task. Need when multiple tasks are running simultaneously.",
        type=int,
        default=1,
    )
    return parser.parse_args()


@background_task("load-employers-to-fineos")
def handler():
    """ECS handler function."""
    logger.info("Starting loading employers to FINEOS.")

    args = parse_args()
    config = EmployerLoadConfig()

    db_session_raw = db.init()

    fineos_client = fineos.create_client()

    with db.session_scope(db_session_raw, close=True) as db_session:
        report_log_entry = massgov.pfml.util.batch.log.create_log_entry(
            db_session, "Employer load", config.mode.name.lower()
        )

        if config.mode is EmployerLoadMode.UPDATES:
            report = massgov.pfml.fineos.employers.load_updates(
                db_session,
                fineos_client,
                args.process_id,
                employer_update_limit=config.update_employer_number_limit,
            )
        else:
            report = massgov.pfml.fineos.employers.load_all(db_session, fineos_client)

        massgov.pfml.util.batch.log.update_log_entry(
            db_session, report_log_entry, "success", report
        )

    logger.info(
        "Finished loading employers to FINEOS.",
        extra={"report": asdict(report), "process_id": args.process_id},
    )
