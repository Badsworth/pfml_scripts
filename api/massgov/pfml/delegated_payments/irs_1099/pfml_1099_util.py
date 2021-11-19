from datetime import date
from typing import Dict, Iterable, List, Optional

from sqlalchemy import and_, func

import massgov.pfml.db as db
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import Employee, Payment, StateLog
from massgov.pfml.db.models.payments import (
    FineosExtractEmployeeFeed,
    Pfml1099Batch,
    Pfml1099MMARSPayment,
    Pfml1099Payment,
    Pfml1099Refund,
    Pfml1099Withholding,
)


class Constants:
    CREATED_STATUS = "Created"
    GENERATED_STATUS = "Generated"
    MERGED_STATUS = "Merged"
    COMPLETED_STATUS = "Printed and Mailed"
    REPLACED_STATUS = "Replacement Batch Created: "
    ARCHIVED_STATUS = "Archived: "
    ERRORED_STATUS = "Invalid: "

    TAX_YEAR_CUTOFF = 6

    FEDERAL_WITHHOLDING_TYPE = "FEDERAL"
    STATE_WITHHOLDING_TYPE = "STATE"


ACTIVE_STATES = [
    Constants.CREATED_STATUS,
    Constants.GENERATED_STATUS,
    Constants.MERGED_STATUS,
]

END_STATES = [
    Constants.COMPLETED_STATUS,
    Constants.REPLACED_STATUS,
    Constants.ARCHIVED_STATUS,
    Constants.ERRORED_STATUS,
]


logger = logging.get_logger(__package__)


def get_payments(db_session: db.Session) -> List[Payment]:

    year = get_tax_year()

    payments = (
        db_session.query(Payment)
        .join(StateLog)
        .filter(StateLog.end_state_id.in_(payments_util.Constants.PAYMENT_SENT_STATE_IDS),)
        .filter(
            and_(StateLog.ended_at >= date(year, 1, 1), StateLog.ended_at < date(year + 1, 1, 1),)
        )
        .all()
    )

    logger.info("Number of Payments for %s: %s", year, len(payments))

    return payments


def get_1099_payments(
    db_session: db.Session, batch: Pfml1099Batch, employee: Employee
) -> List[Pfml1099Payment]:

    payments = (
        db_session.query(Pfml1099Payment)
        .filter(
            Pfml1099Payment.pfml_1099_batch_id == batch.pfml_1099_batch_id,
            Pfml1099Payment.employee_id == employee.employee_id,
        )
        .all()
    )

    if payments is not None:
        logger.debug(
            "Number of PUB Payments for [%s] employee=%s: %s",
            batch.pfml_1099_batch_id,
            employee.employee_id,
            len(payments),
        )

    return payments


def get_1099_mmars_payments(
    db_session: db.Session, batch: Pfml1099Batch, employee: Employee
) -> List[Pfml1099MMARSPayment]:

    payments = (
        db_session.query(Pfml1099MMARSPayment)
        .filter(
            Pfml1099MMARSPayment.pfml_1099_batch_id == batch.pfml_1099_batch_id,
            Pfml1099MMARSPayment.employee_id == employee.employee_id,
        )
        .all()
    )

    if payments is not None:
        logger.debug(
            "Number of MMARS Payments for [%s] employee=%s: %s",
            batch.pfml_1099_batch_id,
            employee.employee_id,
            len(payments),
        )

    return payments


def get_1099_refunds(
    db_session: db.Session, batch: Pfml1099Batch, employee: Employee
) -> List[Pfml1099Refund]:

    refunds = (
        db_session.query(Pfml1099Refund)
        .filter(
            Pfml1099Refund.pfml_1099_batch_id == batch.pfml_1099_batch_id,
            Pfml1099Refund.employee_id == employee.employee_id,
        )
        .all()
    )

    if refunds is not None:
        logger.debug(
            "Number of Refunds for [%s] employee=%s: %s",
            batch.pfml_1099_batch_id,
            employee.employee_id,
            len(refunds),
        )

    return refunds


def get_1099_withholdings(
    db_session: db.Session, batch: Pfml1099Batch, employee: Employee, withholding_type: str
) -> List[Pfml1099Withholding]:

    withholdings = (
        db_session.query(Pfml1099Withholding)
        .filter(
            Pfml1099Withholding.pfml_1099_batch_id == batch.pfml_1099_batch_id,
            Pfml1099Withholding.employee_id == employee.employee_id,
        )
        .all()
    )

    if withholdings is not None:
        logger.debug(
            "Number of Withholdings for [%s] employee=%s: %s",
            batch.pfml_1099_batch_id,
            employee.employee_id,
            len(withholdings),
        )

    return withholdings


def get_1099_claimants(db_session: db.Session) -> Iterable[FineosExtractEmployeeFeed]:

    year = get_tax_year()

    subquery = db_session.query(
        FineosExtractEmployeeFeed,
        func.rank()
        .over(
            order_by=[
                FineosExtractEmployeeFeed.fineos_extract_import_log_id.desc(),
                FineosExtractEmployeeFeed.effectivefrom.desc(),
                FineosExtractEmployeeFeed.effectiveto.desc(),
                FineosExtractEmployeeFeed.created_at.desc(),
            ],
            partition_by=FineosExtractEmployeeFeed.customerno,
        )
        .label("R"),
    ).subquery()

    claimants = db_session.query(subquery).filter(subquery.c.R == 1).all()

    if claimants is not None:
        logger.info("Number of Claimants for %s: %s", year, len(claimants))

    return claimants


def get_employee(db_session: db.Session, claimant: FineosExtractEmployeeFeed) -> Optional[Employee]:

    employee = (
        db_session.query(Employee)
        .filter(Employee.fineos_customer_number == claimant.customerno)
        .one_or_none()
    )

    return employee


def get_current_1099_batch(db_session: db.Session) -> Optional[Pfml1099Batch]:

    year = get_tax_year()

    batches = (
        db_session.query(Pfml1099Batch)
        .filter(Pfml1099Batch.tax_year == year)
        .order_by(Pfml1099Batch.batch_run_date.desc())
    ).all()

    if len(batches) == 0:
        logger.info("No current batch exists")
        return None

    logger.info("Found %s batches in %s", len(batches), year)

    for batch in batches:

        if batch.batch_status in ACTIVE_STATES:
            logger.info(
                "Found an existing batch in state=%s: %s",
                batch.batch_status,
                batch.pfml_1099_batch_id,
                extra={"batch": batch.pfml_1099_batch_id},
            )
            return batch

    return None


def get_tax_year() -> int:
    if date.today().month > Constants.TAX_YEAR_CUTOFF:
        return date.today().year
    else:
        return date.today().year - 1


def get_batch_counts(db_session: db.Session) -> Dict[int, int]:
    batches = (
        db_session.query(Pfml1099Batch.tax_year, func.count(Pfml1099Batch.pfml_1099_batch_id),)
        .group_by(Pfml1099Batch.tax_year)
        .all()
    )

    batch_counts = {}
    for record in batches:
        year = record[0]
        count = record[1]
        logger.info(
            "[%i][%i]: %i", year, count, extra={"tax_year": year, "count": count},
        )
        batch_counts[year] = count

    return batch_counts
