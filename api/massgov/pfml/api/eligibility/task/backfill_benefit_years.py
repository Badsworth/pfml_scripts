from typing import List

import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.api.eligibility import benefit_year
from massgov.pfml.db.models.employees import BenefitYear, Claim, Employee
from massgov.pfml.util.batch import log
from massgov.pfml.util.bg import background_task

logger = logging.get_logger(__name__)


class Metrics:
    CLAIMANTS_TO_BACKFILL = "claimants_to_backfill"
    CLAIMANTS_BENEFIT_YEARS_CREATED = "claimants_benefit_years_created"
    CLAIMANTS_NO_BENEFIT_YEARS_CREATED = "claimants_no_benefit_years_created"
    TOTAL_BENEFIT_YEARS_CREATED = "total_benefit_years_created"
    STATUS = "status"


@background_task("backfill-benefit-years")
def main():
    with db.session_scope(db.init(), close=True) as db_session, db.session_scope(
        db.init(), close=True
    ) as log_entry_db_session:
        with log.LogEntry(log_entry_db_session, "BackfillBenefitYears") as log_entry:
            logger.info("Getting claimants to backfill")
            claimants_to_backfill = get_claimants_to_backfill(db_session)
            logger.info("Starting benefit year backfill")
            backfill_benefit_years(db_session, claimants_to_backfill, log_entry)
            logger.info("Finished benefit year backfill", extra={"Metrics": log_entry.metrics})


def backfill_benefit_years(
    db_session: db.Session, claimants_to_backfill: List[Employee], log_entry: log.LogEntry
) -> None:
    num_claimants_to_backfill = len(claimants_to_backfill)
    log_entry.set_metrics({Metrics.CLAIMANTS_TO_BACKFILL: num_claimants_to_backfill})

    for claimant in claimants_to_backfill:
        employee_id = claimant.employee_id
        new_benefit_years = benefit_year._create_benefit_years_from_leave_absence_history(
            db_session, employee_id
        )
        benefit_year_count = len(new_benefit_years)

        if benefit_year_count == 0:
            # Note: given how we're filtering claimants in get_claimants_to_backfill this should never occur
            log_entry.increment(Metrics.CLAIMANTS_NO_BENEFIT_YEARS_CREATED)

            logger.warning(
                "No benefit year created for claimant", extra={"employee_id": employee_id}
            )
        else:
            try:
                db_session.commit()
            except Exception as error:
                logger.error(
                    "An error occured while backfilling benefit years from previous claims",
                    extra={"employee_id": employee_id, "error_message": str(error)},
                )
                db_session.rollback()
                log_entry.increment(Metrics.CLAIMANTS_NO_BENEFIT_YEARS_CREATED)
            else:
                log_entry.increment(Metrics.CLAIMANTS_BENEFIT_YEARS_CREATED)
                log_entry.increment(Metrics.TOTAL_BENEFIT_YEARS_CREATED, benefit_year_count)
                logger.info(
                    "Successfully backfilled benefit years",
                    extra={"employee_id": employee_id, "benefit_years_created": benefit_year_count},
                )

    claimants_benefit_years_created = log_entry.metrics.get(
        Metrics.CLAIMANTS_BENEFIT_YEARS_CREATED, 0
    )
    claimants_no_benefit_years_created = log_entry.metrics.get(
        Metrics.CLAIMANTS_NO_BENEFIT_YEARS_CREATED
    )

    if claimants_benefit_years_created == num_claimants_to_backfill:
        log_entry.set_metrics({Metrics.STATUS: "Backfill completed succesfully"})
    elif (
        claimants_benefit_years_created + claimants_no_benefit_years_created
    ) == num_claimants_to_backfill:
        log_entry.set_metrics(
            {
                Metrics.STATUS: "Backfill completed, but some claimants did not have benefit years created"
            }
        )
    else:
        log_entry.set_metrics({Metrics.STATUS: "Backfill did not run for all expected claimants"})


def get_claimants_to_backfill(db_session: db.Session) -> List[Employee]:
    # Get all claimants with approved or compelted claims that do no currently have benefit years

    claimants = (
        db_session.query(Employee)
        .join(Claim)
        .outerjoin(BenefitYear)
        .filter(
            Claim.fineos_absence_status_id.in_(benefit_year.ABSENCE_STATUSES_WITH_BENEFIT_YEAR),
            BenefitYear.benefit_year_id.is_(None),
        )
        .all()
    )

    return claimants
