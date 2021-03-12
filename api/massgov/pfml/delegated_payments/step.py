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
            self.log_entry.set_metrics(state_log_counts_before=state_log_counts_before)
            self.run_step()

            state_log_counts_after = state_log_util.get_state_counts(self.db_session)
            self.log_entry.set_metrics(state_log_counts_after=state_log_counts_after)

    @abc.abstractmethod
    def run_step(self) -> None:
        pass

    def get_import_log_id(self) -> Optional[int]:
        # If this is called from within something using run
        # it should never be unset None
        if not self.log_entry:
            return None
        return self.log_entry.import_log.import_log_id
