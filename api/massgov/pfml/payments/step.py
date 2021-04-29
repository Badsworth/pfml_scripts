import abc
import collections
from typing import Any, Optional

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

            # Flatten these prefixed with the "before" key since nested values in the
            # metrics dictionary aren’t properly imported into New Relic
            state_log_counts_before = state_log_util.get_state_counts(self.db_session)

            before_map = {"before_state_log_counts": state_log_counts_before}
            flattened_state_log_counts_before = flatten(before_map)

            self.set_metrics(flattened_state_log_counts_before)
            self.run_step()

            # Flatten these prefixed with the "after" key since nested values in the
            # metrics dictionary aren’t properly imported into New Relic
            state_log_counts_after = state_log_util.get_state_counts(self.db_session)

            after_map = {"after_state_log_counts": state_log_counts_after}
            flattened_state_log_counts_after = flatten(after_map)

            self.set_metrics(flattened_state_log_counts_after)

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

    def set_metrics(self, metrics: Any) -> None:
        if not self.log_entry:
            return
        self.log_entry.set_metrics(metrics)

    def increment(self, name: str) -> None:
        if not self.log_entry:
            return
        self.log_entry.increment(name)


def flatten(d, parent_key="", sep="_"):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
