#!/usr/bin/env python3

import argparse
import pathlib
from scripted_releases import audit_logger, release_tasks, task_args, guardrails
import sys
import logging

NO_SUBCOMMAND = "A subcommand must be provided unless running this script with '-h' / '--help'."
AUDIT_LOGS_STORAGE_LOCATION = f"{pathlib.Path(__file__).parent.resolve()}/logs"

logger = logging.getLogger(__name__)


def entrypoint():
    """
    Scripted releases core infrastructure. Handles global state, I/O management,
    audit logging, mode selection, and hand-off to more specialized subprograms.
    """
    # Store the audit log in /bin/ci/logs, relative to the repo root.
    # This storage is meant to be temporary. Eventually this file will live in AWS.
    audit_logger.setup(file_loc=AUDIT_LOGS_STORAGE_LOCATION)

    # permits unit testing; see bucket.py
    main(sys.argv[1:])


def main(raw_args: list) -> None:
    def audit_logging_exception_hook(exc_type, exc_info, _traceback):
        logger.exception(f"Caught {exc_type.__name__} - {exc_info}", exc_info=exc_info)

    args = parse_args(raw_args)

    # Avert your eyes!
    sys.excepthook = audit_logging_exception_hook

    logger.info("*** Scripted Releases v. 00004 ***")
    logger.info(f"Args: {repr(args)}")
    logger.info(f"Script is running in {'interactive' if args.interactive else 'autonomous'} mode.")

    if not hasattr(args, 'func'):
        raise RuntimeError(NO_SUBCOMMAND)

    if args.func in {release_tasks.start, release_tasks.major}:
        guardrails.for_new_release()
    elif args.func in {release_tasks.update, release_tasks.hotfix}:
        guardrails.for_altered_release(args)
    elif args.func is release_tasks.finalize:
        guardrails.for_finalized_release(args)

    # Hand off execution to the method defined at 'args.func'
    args.func(args)
    logger.info("Exit release.py\n")


def parse_args(raw_args: list) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scripted releases. Create, update, finalize, hotfix & version bump.",
                                     prog="release.py")
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="If present: run the script interactively. "
                             "If not present: run the script from command-line arguments.")
    parser.add_argument("-a", "--app", choices=['api', 'portal'], required=True,
                        help='Are you releasing the Portal or the API?')

    subparsers = parser.add_subparsers()

    start_handler = task_args.configure_start_release_args(subparsers)
    update_handler = task_args.configure_update_release_args(raw_args, subparsers)
    finalize_handler = task_args.configure_finalize_release_args(raw_args, subparsers)
    hotfix_handler = task_args.configure_hotfix_args(raw_args, subparsers)
    major_handler = task_args.configure_major_release_args(subparsers)

    parsed_args = parser.parse_args(raw_args)
    return parsed_args


if __name__ == "__main__":
    entrypoint()
