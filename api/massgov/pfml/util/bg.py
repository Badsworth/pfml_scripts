import contextlib

import newrelic.agent

import massgov.pfml.util.logging
import massgov.pfml.util.logging.audit
from massgov.pfml.util.newrelic import init_newrelic

# This will only be set if the current context is a running background_task
CURRENT_TASK_NAME = None


# Accesses the set task name if it has happened, for use with ImportLogs
def get_current_task_name():
    return CURRENT_TASK_NAME


@contextlib.contextmanager
def background_task(name):
    """
    Context manager for any ECS Task entrypoint function.

    This encapsulates the setup required by all ECS tasks, making it easy to:
    - add new shared intialization steps
    - write new ECS task code without thinking about the boilerplate

    Usage:
      @background_task('your-ecs-task-name')
      def entrypoint():
        do_cool_stuff()

    Parameters:
      name (str): Name of the ECS task
    """
    init_newrelic()
    massgov.pfml.util.logging.init(name)
    massgov.pfml.util.logging.audit.init_security_logging()

    application = newrelic.agent.register_application(timeout=10.0)

    global CURRENT_TASK_NAME
    if CURRENT_TASK_NAME is None:
        CURRENT_TASK_NAME = name

    with newrelic.agent.BackgroundTask(application, name=name, group="Python/ECSTask"):
        yield
