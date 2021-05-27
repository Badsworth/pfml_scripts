#
# Tool for cleaning up MMARS vendor customer codes in the PFML API database.
#
# See API-1529.
#
# Finds all employees in the PFML API db that have a TIN and a VC code and performs the
# Data Mart query for the employee's TIN.
# - If the VC code in Data Mart matches the VC code in the PFML API db, then no action is
#   needed.
# - If the VC code does not match, update the PFML API db with the correct VC code.
# - If no VC code is found in Data Mart, remove the bad data from the PFML API db.

import argparse
import sys
from typing import List, Optional

from sqlalchemy.orm.exc import MultipleResultsFound

import massgov.pfml.db as db
import massgov.pfml.payments.data_mart as data_mart
import massgov.pfml.util.batch.log as batch_log
import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import Employee, TaxIdentifier
from massgov.pfml.util.logging import audit

logger = logging.get_logger(__name__)


class Configuration:
    commit: bool = False

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(
            description="Cleanup employees with incorrect MMARS vendor customer codes."
        )
        parser.add_argument(
            "--commit",
            help="Setting this argument will disable dry run (default mode).",
            action="store_true",
        )
        args = parser.parse_args(input_args)

        self.commit = args.commit


def main():
    """Main entry point for MMARS vendor customer code cleanup tool."""
    audit.init_security_logging()
    logging.init(__name__)
    logger.info("Start MMARS vendor customer code cleanup")

    config = Configuration(sys.argv[1:])
    logger.info("Commit is %s", config.commit)

    run_vc_code_cleanup_process(config)

    logger.info("Done MMARS vendor customer code cleanup")


def run_vc_code_cleanup_process(config: Configuration) -> None:
    db_session_raw = db.init(sync_lookups=True)
    try:
        with batch_log.LogEntry(
            db_session_raw, "MMARS vendor customer code cleanup"
        ) as log_entry, db.session_scope(db_session_raw) as db_session:
            log_entry.set_metrics(vars(config))
            cleanup_ctr_vendor_customer_codes(config, db_session, log_entry)
    except Exception as ex:
        logger.exception("%s", ex)
        sys.exit(1)


def cleanup_ctr_vendor_customer_codes(
    config: Configuration, db_session: db.Session, log_entry: batch_log.LogEntry
) -> None:
    all_employees_with_vc_codes = (
        db_session.query(Employee)
        .join(TaxIdentifier)
        .filter(Employee.ctr_vendor_customer_code.isnot(None))
        .all()
    )
    logger.info(
        "Processing employees that have a MMARS vendor customer code saved in the PFML API database"
    )

    if not all_employees_with_vc_codes:
        logger.info("No employees have MMARS vendor customer codes")
        return

    log_entry.set_metrics({"total": len(all_employees_with_vc_codes)})

    for employee in logging.log_every(
        logger,
        all_employees_with_vc_codes,
        count=10,
        total_count=len(all_employees_with_vc_codes),
        start_time=datetime_util.utcnow(),
        item_name="employee",
    ):
        try:
            update_required = cleanup_single_employee(config, employee)
            if update_required:
                log_entry.increment("update_required")
            else:
                log_entry.increment("no_update_required")
        except Exception:
            log_entry.increment("exception")

    db_session.commit()


def cleanup_single_employee(config: Configuration, employee: Employee) -> bool:
    """Query Data Mart and compare vendor customer codes.

    Raises:
        - Exception: if Data Mart query returns more than one result or other
            error occurs
    Returns:
        - True: if the vendor customer codes do not match and an update to the PFML API
            database is required
        - False: if the vendor customer codes match
    """
    extra = {
        "employee_id": employee.employee_id,
        "ctr_vendor_customer_code_in_db": employee.ctr_vendor_customer_code,
    }

    if employee.fineos_customer_number:
        extra.update(fineos_customer_number=employee.fineos_customer_number)

    if employee.tax_identifier is None:
        error_str = "Employee is missing a tax identifier"
        logger.error(error_str, extra=extra)
        raise Exception(error_str)
    else:
        tin = employee.tax_identifier.tax_identifier

    try:
        vendor_info = get_vendor_info(tin)
    except MultipleResultsFound:
        logger.exception(
            "Data Mart query returned more than one result; something is wrong", extra=extra
        )
        raise
    except Exception:
        logger.exception("Unexpected Data Mart query exception", extra=extra)
        raise

    # No record was found in Data Mart, so we should delete the erroneous vendor customer
    # code in the PFML API db.
    if vendor_info is None:
        logger.warning("Warning: No match found in Data Mart", extra=extra)
        if config.commit:
            employee.ctr_vendor_customer_code = None
            logger.info("Deleted MMARS vendor customer code from PFML API db", extra=extra)
        return True

    extra.update(data_mart_vc_code=vendor_info.vendor_customer_code)

    # The record found in Data Mart doesn't match the PFML API db, so we should update
    # the PFML API db with the correct vendor customer code.
    if employee.ctr_vendor_customer_code != vendor_info.vendor_customer_code:
        logger.warning("Warning: VC code in PFML API db does not match Data Mart", extra=extra)
        if config.commit:
            employee.ctr_vendor_customer_code = vendor_info.vendor_customer_code
            logger.info("Updated MMARS vendor customer code in PFML API db", extra=extra)
        return True

    # The record found in Data Mart matches!
    else:
        logger.info("Success: VC code in PFML API db matches Data Mart", extra=extra)
        return False


def get_vendor_info(tin: str) -> Optional[data_mart.VendorInfoResult]:
    """Connect to Data Mart and retrieve vendor info."""
    data_mart_config = data_mart.DataMartConfig()
    data_mart_engine = data_mart.init(data_mart_config)
    with data_mart_engine.connect() as data_mart_conn:
        vendor_info = data_mart.get_vendor_info(data_mart_conn, tin)
    return vendor_info
