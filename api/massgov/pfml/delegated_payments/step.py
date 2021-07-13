import abc
import collections
import enum
from typing import Any, Dict, Optional

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.util.batch.log import LogEntry

logger = logging.get_logger(__name__)


class Step(abc.ABC, metaclass=abc.ABCMeta):
    log_entry: Optional[LogEntry] = None
    db_session: db.Session
    log_entry_db_session: db.Session

    class Metrics(str, enum.Enum):
        pass

    def __init__(self, db_session: db.Session, log_entry_db_session: db.Session) -> None:
        self.db_session = db_session
        self.log_entry_db_session = log_entry_db_session

    def run(self) -> None:
        with LogEntry(self.log_entry_db_session, self.__class__.__name__) as log_entry:
            self.log_entry = log_entry

            self.initialize_metrics()

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

            # Calculate the difference in counts for the metrics
            state_log_diff = calculate_state_log_count_diff(
                state_log_counts_before, state_log_counts_after
            )
            self.set_metrics(state_log_diff)

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


def calculate_state_log_count_diff(
    state_log_counts_before: Dict[str, int], state_log_counts_after: Dict[str, int]
) -> Dict[str, int]:
    # First, create a map of state log description to a tuple of before count/after count
    # Note that a state log that isn't present means there was 0.
    # We need to iterate over both so that we account for any that only appear before or after.
    count_map = {}
    for key, value in state_log_counts_before.items():
        count_map[key] = [value, 0]

    for key, value in state_log_counts_after.items():
        if key not in count_map:
            count_map[key] = [0, 0]

        count_map[key][1] = value

    # Calculate the diffs
    diff_map = {}
    for description, counts in count_map.items():
        count_before = counts[0]
        count_after = counts[1]

        diff = count_after - count_before
        # If it didn't change, don't bother adding it
        if diff == 0:
            continue

        key_name = f"diff_state_log_counts_{description}"
        diff_map[key_name] = diff

    return diff_map


def flatten(d, parent_key="", sep="_"):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.abc.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
