import os

import newrelic.agent


def init_newrelic() -> None:
    newrelic.agent.initialize(
        config_file=os.path.join(os.path.dirname(__file__), "../../../..", "newrelic.ini"),
        environment=os.environ.get("ENVIRONMENT", "local"),
    )
