def start(args, logger):
    logger.info(f"Running 'start-release', args: {str(args)}")


def update(args, logger):
    logger.info(f"Running 'update-release', args: {repr(args)}")


def finalize(args, logger):
    logger.info(f"Running 'finalize-release', args: {repr(args)}")


def hotfix(args, logger):
    logger.info(f"Running 'hotfix'; args, {repr(args)}")


def major(args, logger):
    logger.info(f"Running 'major-release'; args, {repr(args)}")
