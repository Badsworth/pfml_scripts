import massgov.pfml.util.logging as logging
from massgov.pfml.util.logging import audit

logger = logging.get_logger(__name__)


def ctr_process():
    """ Run the whole program """
    audit.init_security_logging()
    logging.init(__name__)

    logger.info("Payments CTR Process placeholder ECS task")


if __name__ == "__main__":
    ctr_process()
