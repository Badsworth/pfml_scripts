import abc
import enum
import uuid
from datetime import datetime
from typing import Any, Optional, Set

import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    Employee,
    EmployeeReferenceFile,
    ImportLogReportQueue,
    Payment,
    PaymentReferenceFile,
    ReferenceFile,
)
from massgov.pfml.util.batch.log import LogEntry, latest_import_log_for_metric
from massgov.pfml.util.datetime.business_day import BusinessDay

logger = logging.get_logger(__name__)


class Step(abc.ABC, metaclass=abc.ABCMeta):
    log_entry: Optional[LogEntry] = None
    db_session: db.Session
    log_entry_db_session: db.Session

    payments_in_reference_file: Set[uuid.UUID]
    employees_in_reference_file: Set[uuid.UUID]

    should_add_to_report_queue: bool

    class Metrics(str, enum.Enum):
        pass

    def __init__(
        self,
        db_session: db.Session,
        log_entry_db_session: db.Session,
        should_add_to_report_queue: bool = False,
    ) -> None:
        self.db_session = db_session
        self.log_entry_db_session = log_entry_db_session
        self.payments_in_reference_file = set()
        self.employees_in_reference_file = set()
        self.should_add_to_report_queue = should_add_to_report_queue

    def cleanup_on_failure(self) -> None:
        pass

    def get_import_type(self) -> str:
        """Override in subclass steps to set the type of the import log"""
        return ""

    def run(self) -> None:
        with LogEntry(
            self.log_entry_db_session, self.__class__.__name__, self.get_import_type()
        ) as log_entry:
            self.log_entry = log_entry

            self.initialize_metrics()

            logger.info(
                "Running step %s with batch ID %i",
                self.__class__.__name__,
                self.get_import_log_id(),
            )

            try:
                self.run_step()
                self.add_to_report_queue()
                self.db_session.commit()

            except Exception:
                # Rollback for any exception
                self.db_session.rollback()
                logger.exception(
                    "Error processing step %s:. Cleaning up after failure if applicable.",
                    self.__class__.__name__,
                )

                # If there was a file-level exception anywhere in the processing,
                # we move the file from received to error
                # perform any cleanup necessary by the step.
                self.cleanup_on_failure()
                raise

    @abc.abstractmethod
    def run_step(self) -> None:
        pass

    # The below are all wrapper functions around the import
    # log to handle it not being set. Any calls to run() will
    # have it set in subsequent processing, but specific calls
    # in tests may not have it set.

    def get_import_log_id(self) -> Optional[int]:
        if not self.log_entry:
            return None
        return self.log_entry.import_log.import_log_id

    def initialize_metrics(self) -> None:
        zero_metrics_dict = {metric.value: 0 for metric in self.Metrics}
        self.set_metrics(zero_metrics_dict)

    def set_metrics(self, metrics: Any) -> None:
        if not self.log_entry:
            return
        self.log_entry.set_metrics(metrics)

    def increment(self, name: str, increment: int = 1) -> None:
        if not self.log_entry:
            return
        self.log_entry.increment(name, increment)

    def add_payment_reference_file(self, payment: Payment, reference_file: ReferenceFile) -> None:
        # Add a payment reference file. If a particular job finds a payment
        # multiple times in a reference file, don't readd it to avoid primary key conflicts
        if payment.payment_id in self.payments_in_reference_file:
            return
        self.payments_in_reference_file.add(payment.payment_id)

        payment_reference_file = PaymentReferenceFile(
            payment=payment, reference_file=reference_file
        )
        self.db_session.add(payment_reference_file)

    def add_employee_reference_file(
        self, employee: Employee, reference_file: ReferenceFile
    ) -> None:
        # Add an employee reference file. If a particular job finds an employee
        # multiple times in a reference file, don't readd it to avoid primary key conflicts
        if employee.employee_id in self.employees_in_reference_file:
            return
        self.employees_in_reference_file.add(employee.employee_id)

        employee_reference_file = EmployeeReferenceFile(
            employee=employee, reference_file=reference_file
        )
        self.db_session.add(employee_reference_file)

    def add_to_report_queue(self):
        if not self.should_add_to_report_queue:
            return
        if not (import_log_id := self.get_import_log_id()):
            return

        self.log_entry_db_session.add(ImportLogReportQueue(import_log_id=import_log_id))

    @classmethod
    def check_if_processed_within_x_days(
        cls, db_session: db.Session, metric: str, business_days: int
    ) -> bool:
        source = cls.__name__
        found_import_log = latest_import_log_for_metric(
            db_session=db_session, source=source, metric=metric
        )

        if found_import_log is None:
            logger.error(f"No data was found for step {cls.__name__} with results for {metric}.")
        else:
            business_day = BusinessDay(found_import_log.created_at)
            days = business_day.days_between(datetime.utcnow())
            if days <= business_days:
                return True

            logger.error(
                f"Last time processing step {cls.__name__} with results for {metric} was greater than {business_days} days.",
                extra={"import_log_created_at": found_import_log.created_at},
            )
        return False
