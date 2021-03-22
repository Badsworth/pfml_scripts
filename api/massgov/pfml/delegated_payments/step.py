import abc
from typing import Optional

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.util.batch.log import LogEntry

logger = logging.get_logger(__name__)


class Step(abc.ABC, metaclass=abc.ABCMeta):
    log_entry: Optional[LogEntry] = None
    db_session: db.Session
    log_entry_db_session: db.Session

    def __init__(self, db_session: db.Session, log_entry_db_session: db.Session) -> None:
        self.db_session = db_session
        self.log_entry_db_session = log_entry_db_session

    def run(self) -> None:
        with LogEntry(self.log_entry_db_session, self.__class__.__name__) as log_entry:
            self.log_entry = log_entry

            logger.info(
                "Running step %s with batch ID %i",
                self.__class__.__name__,
                self.get_import_log_id(),
            )
            state_log_counts_before = state_log_util.get_state_counts(self.db_session)
            self.set_metrics(state_log_counts_before=state_log_counts_before)
            self.run_step()

            state_log_counts_after = state_log_util.get_state_counts(self.db_session)
            self.set_metrics(state_log_counts_after=state_log_counts_after)

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

    def set_metrics(self, **metrics) -> None:
        if not self.log_entry:
            return
        self.log_entry.set_metrics(**metrics)

    def increment(self, name: str) -> None:
        if not self.log_entry:
            return
        self.log_entry.increment(name)
