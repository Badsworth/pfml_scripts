from dataclasses import dataclass
from typing import Iterable, Optional

import massgov.pfml.api.services.fineos_actions as fineos_actions
import massgov.pfml.db as db
import massgov.pfml.fineos.util.log_tables as fineos_log_tables_util
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


def load_updates(
    db_session: db.Session, fineos: AbstractFINEOSClient, process_id: int = 1, batch_size: int = 100
) -> LoadEmployersReport:
    start_time = utcnow()
    report = LoadEmployersReport(start=start_time.isoformat())

    logger.info("Starting Employer updates load to FINEOS", extra={"process_id": process_id})

    employers = get_new_or_updated_employers(
        db_session, batch_size, process_id, pickup_existing_at_start=True
    )
    employers_with_logging = massgov.pfml.util.logging.log_every(
        logger,
        employers,
        count=1,
        start_time=start_time,
        item_name="Employer",
        extra={"process_id": process_id},
    )

    for employer in employers_with_logging:
        report.total_employers_count += 1

        # we must commit or rollback the transaction for each item to ensure the
        # row lock put in place by `skip_locked_query` is released
        try:
            is_create = employer.fineos_employer_id is None

            fineos_actions.create_or_update_employer(fineos, employer)
            fineos_actions.create_service_agreement_for_employer(fineos, employer)

            db_session.commit()

            report.loaded_employers_count += 1

            # Delete the entries for this Employer that triggered this
            # particular update process...
            db_session.query(EmployerLog).filter(
                EmployerLog.process_id == process_id,
                EmployerLog.employer_id == employer.employer_id,
            ).delete(synchronize_session=False)

            # ...and clean up any entries we created in the process.
            #
            # Scoping the above delete to `process_id` will miss the
            # "UPDATE" entry that could be added from updating the
            # `employer.fineos_employer_id` column. So if we think we are
            # creating the FINEOS employer and will therefore have updated
            # the row in `employer`, delete the latest "UPDATE" event for
            # that employer from EmployerLog.
            if is_create:
                fineos_log_tables_util.delete_most_recent_update_entry_for_employer(
                    db_session, employer
                )

            # finalize the deletes before moving on
            db_session.commit()
        except Exception:
            logger.exception(
                "Error creating/updating employer in FINEOS",
                extra={
                    "internal_employer_id": employer.employer_id,
                    "fineos_employer_id": employer.fineos_employer_id,
                    "process_id": process_id,
                },
            )

            db_session.rollback()

            report.errored_employers_count += 1

    end_time = utcnow()
    report.end = end_time.isoformat()
    report.process_duration_in_seconds = (end_time - start_time).total_seconds()

    return report


def get_new_or_updated_employers(
    db_session: db.Session, batch_size: int, process_id: int, pickup_existing_at_start: bool = True
) -> Iterable[Employer]:
    """Yields Employers with entries in EmployerLog that have not been marked as being processed by another process_id, until none are left.

    This claims `batch_size` number of Employers for the given `process_id` at a
    time. Yielding one Employer from that batch until empty, then grabbing
    another `batch_size` number and so on.

    The yielded Employer will have its DB row locked FOR UPDATES, so the caller
    should commit/rollback its transaction when it is done with the Employer.

    This function does not delete the claimed rows from the EmployerLog table as
    it iterates through. The caller is responsible for deleting the related
    Employer rows for its `process_id` after it is done processing them.
    """

    pickup_existing = pickup_existing_at_start

    # If there is a process that is already tagged to handle a particular
    # Employer, don't let other processes attempt to grab other records for it
    # until the current process is done.
    #
    # It should generally be harmless to allow this, repeatedly updating an
    # Employer should be safe, but should be more robust to allow any existing
    # processes to successfully finish their handling of the Employer.
    employer_ids_that_are_already_tagged_with_different_process_id_query = db_session.query(
        EmployerLog.employer_id
    ).filter(EmployerLog.process_id.isnot(None), EmployerLog.process_id != process_id)

    while True:
        db_session.execute(f"LOCK TABLE {EmployerLog.__table__} IN ACCESS EXCLUSIVE MODE;")

        # build up query for this batch of Employer records
        updated_employer_ids_for_process_query = db_session.query(EmployerLog.employer_id)

        # the basic WHERE clauses, looking at only EmployerLog records that have
        # not been tagged by another process yet
        core_filter = [
            EmployerLog.action.in_(["INSERT", "UPDATE"]),
            EmployerLog.process_id.is_(None),
            EmployerLog.employer_id.notin_(
                employer_ids_that_are_already_tagged_with_different_process_id_query
            ),
        ]

        # apply the filters and aggregation
        updated_employer_ids_for_process_query = (
            updated_employer_ids_for_process_query.filter(*core_filter)
            .group_by(EmployerLog.employer_id)
            .limit(batch_size)
        )

        # then actually retrieve the next set of Employer IDs
        updated_employer_ids = updated_employer_ids_for_process_query.all()

        # include records that are already marked for this process if asked,
        # primary scenario is to include records that failed during a previous
        # run
        #
        # note these are in addition to the requested batch size, so if most of
        # a previous run failed, this could be several times larger than
        # expected
        if pickup_existing:
            existing_employer_ids_for_this_process_id = (
                db_session.query(EmployerLog.employer_id)
                .filter(EmployerLog.process_id == process_id)
                .all()
            )
            updated_employer_ids.extend(existing_employer_ids_for_this_process_id)

        # if there are no more records to handle, release the lock by committing
        # transaction and break the loop
        if len(updated_employer_ids) == 0:
            db_session.commit()
            break

        # if there are more records, tag them with this process_id and release
        # the lock
        db_session.query(EmployerLog).filter(
            EmployerLog.employer_id.in_(updated_employer_ids)
        ).update({EmployerLog.process_id: process_id}, synchronize_session=False)

        db_session.commit()

        # then build query to get the (new) Employer records for this batch
        updated_employers_query = db_session.query(Employer).filter(
            Employer.employer_id.in_(updated_employer_ids)
        )

        # yielding them one at a time
        for employer in db.skip_locked_query(updated_employers_query, Employer.employer_id):
            yield employer

        # after we've done our first batch trying any failed records from a
        # previous run, don't pickup new failed records
        if pickup_existing_at_start and pickup_existing:
            pickup_existing = False
