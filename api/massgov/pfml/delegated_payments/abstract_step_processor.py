import abc
from typing import Any, Optional

from massgov.pfml import db
from massgov.pfml.delegated_payments.step import Step


class AbstractStepProcessor(abc.ABC, metaclass=abc.ABCMeta):

    step: Step
    db_session: db.Session

    def __init__(self, step: Step) -> None:
        self.step = step
        self.db_session = step.db_session

    def set_metrics(self, metrics: Any) -> None:
        self.step.set_metrics(metrics)

    def increment(self, name: str, increment: int = 1) -> None:
        self.step.increment(name, increment)

    def get_import_log_id(self) -> Optional[int]:
        return self.step.get_import_log_id()
