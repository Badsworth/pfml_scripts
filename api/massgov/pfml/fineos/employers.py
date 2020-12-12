from dataclasses import dataclass
from typing import Iterable, MutableSet, Optional

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


def load_updates(
    db_session: db.Session, fineos: AbstractFINEOSClient, process_id: int = 1
) -> LoadEmployersReport:
    start_time = utcnow()
    report = LoadEmployersReport(start=start_time.isoformat())

    logger.info("Starting Employer updates load to FINEOS", extra={"process_id": process_id})

    batch_size = 100
    errored_employer_ids: MutableSet[str] = set()
    employer_batches = get_update_batches(db_session, batch_size, process_id, errored_employer_ids)
    employer_batches_with_logging = massgov.pfml.util.logging.log_every(
        logger,
        employer_batches,
        count=1,
        start_time=start_time,
        item_name="Employer Batch",
        extra={"process_id": process_id},
    )

    for employers in employer_batches_with_logging:
        for employer in employers:
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
                    db_session.query(EmployerLog).filter(
                        EmployerLog.employer_log_id
                        == (
                            db_session.query(EmployerLog.employer_log_id)
                            .filter(
                                EmployerLog.employer_id == employer.employer_id,
                                EmployerLog.action == "UPDATE",
                            )
                            .order_by(EmployerLog.modified_at)
                            .limit(1)
                        )
                    ).delete(synchronize_session=False)
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

                errored_employer_ids.add(employer.employer_id)
                report.errored_employers_count += 1
                continue

    end_time = utcnow()
    report.end = end_time.isoformat()
    report.process_duration_in_seconds = (end_time - start_time).total_seconds()

    return report


def get_update_batches(
    db_session: db.Session, batch_size: int, process_id: int, employer_ids_to_skip: MutableSet[str]
) -> Iterable[Iterable[Employer]]:
    """Yields batches of Employers that have not been marked as being processed by another process_id, until none are left."""

    while True:
        with db_session.begin_nested():
            db_session.execute(f"LOCK TABLE {EmployerLog.__table__} IN ACCESS EXCLUSIVE MODE;")

            employer_ids_that_are_already_tagged_with_different_process_id_query = db_session.query(
                EmployerLog.employer_id
            ).filter(EmployerLog.process_id.isnot(None), EmployerLog.process_id != process_id)

            updated_employer_ids_for_process_query = (
                db_session.query(EmployerLog.employer_id)
                .filter(
                    EmployerLog.action.in_(["INSERT", "UPDATE"]),
                    EmployerLog.employer_id.notin_(
                        employer_ids_that_are_already_tagged_with_different_process_id_query
                    ),
                    EmployerLog.employer_id.notin_(employer_ids_to_skip),
                )
                .group_by(EmployerLog.employer_id)
                .limit(batch_size)
            )

            db_session.query(EmployerLog).filter(
                EmployerLog.employer_id.in_(updated_employer_ids_for_process_query)
            ).update({EmployerLog.process_id: process_id}, synchronize_session=False)

        updated_employer_ids_query = (
            db_session.query(EmployerLog.employer_id)
            .filter(EmployerLog.process_id == process_id)
            .group_by(EmployerLog.employer_id)
        )

        updated_employers_query = db_session.query(Employer).filter(
            Employer.employer_id.in_(updated_employer_ids_query)
        )

        employer_count = updated_employers_query.count()

        if employer_count == 0:
            break

        yield db.skip_locked_query(updated_employers_query, Employer.employer_id)
