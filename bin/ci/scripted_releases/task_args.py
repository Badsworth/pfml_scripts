import argparse
from . import release_tasks


def configure_start_release_args(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    start_handler = subparsers.add_parser(
        'start-release', help='Creates a new release series, and its "-rc1" tag, automatically from main.'
    )

    start_handler.set_defaults(func=release_tasks.start)
    return start_handler


def configure_update_release_args(raw_args: list, subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    update_handler = subparsers.add_parser(
        'update-release',
        help='Produces a new release candidate by applying Git commits to the specified release series, '
             'tagging the last commit provided with an incremented "-rcX" tag. '
             'This task does not affect semver numbers; see "hotfix" or "start-release" if you want that.'
    )

    update_handler.add_argument(
        "-r", metavar="release_version", dest="release_version", type=str, default='',
        required=('-i' not in raw_args and '--interactive' not in raw_args),
        help="The full name of an API or Portal release branch, "
             "e.g.: '-r release/api/v1.2.0' or '-r release/portal/v4.0'."
    )

    update_handler.add_argument(
        "-c", metavar="git_commits", dest="git_commits", action="append", default=[],
        required=('-i' not in raw_args and '--interactive' not in raw_args),
        help="The commit hash of a Git commit that you want to add to this RC. Can be specified multiple times."
    )

    update_handler.set_defaults(func=release_tasks.update)
    return update_handler


def configure_finalize_release_args(raw_args: list, subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    finalize_handler = subparsers.add_parser(
        'finalize-release',
        help='Marks the specified release series as production-ready. '
             'This series\' most recent RC will be promoted to a formal release.'
             'Running this task on a specified release series will permanently disable the "update-release" task, '
             'and permanently enable the "hotfix" task, for that series.'
    )

    finalize_handler.add_argument(
        "-r", metavar="release_version", dest="release_version",
        required=('-i' not in raw_args and '--interactive' not in raw_args),
        help="The full name of an API or Portal release branch, "
             "e.g.: '-r release/api/v1.2.0' or '-r release/portal/v4.0'."
    )

    finalize_handler.set_defaults(func=release_tasks.finalize)
    return finalize_handler


def configure_hotfix_args(raw_args: list, subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    hotfix_handler = subparsers.add_parser(
        'hotfix',
        help='Creates a new patch version (if API) or minor version (if Portal) '
             'by applying Git commits to a finalized release series, '
             'tagging the last commit provided with an incremented semver number. '
             'Only usable on a previously-finalized release series. '
             'This task does not affect RC numbers; see "update-release" if you want that.'
    )

    hotfix_handler.add_argument(
        "-r", metavar="release_version", dest="release_version", type=str, default='',
        required=('-i' not in raw_args and '--interactive' not in raw_args),
        help="The full name of a finalized API or Portal release branch, "
             "e.g.: '-r release/api/v1.2.0' or '-r release/portal/v4.0'."
    )

    hotfix_handler.add_argument(
        "-c", metavar="git_commits", dest="git_commits", action="append", default=[],
        required=('-i' not in raw_args and '--interactive' not in raw_args),
        help="The commit hash of a Git commit that you want to add to this hotfix. Can be specified multiple times."
    )

    hotfix_handler.set_defaults(func=release_tasks.hotfix)
    return hotfix_handler


def configure_major_release_args(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    major_release_handler = subparsers.add_parser(
        'major-release',
        help='[API only] Creates a new MAJOR version and its "-rc1" tag from main, as in the "start-release" task.')

    major_release_handler.set_defaults(func=release_tasks.major)
    return major_release_handler
