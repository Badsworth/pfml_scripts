import re
from . import git_utils

"""
Argument-handling guardrails for the various different ways to invoke release.py.
Each set of subcommands takes slightly different arguments and has slightly different validation needs.
"""

# TODO: regex polishing: don't match portal versions with >2 semver numbers.
RELEASE_VERSION_REGEX = re.compile(r"release\/(api|portal|foobar)\/v([0-9]+)\.([0-9]+)\.?([0-9]*)")
COMMIT_REGEX = re.compile(r"[0-9a-f]{7,40}")  # allows both short and long-form hash types

CLI_ARGS_WHEN_INTERACTIVE = "No additional command-line arguments should be provided in interactive mode."

NO_RELEASE_VERSION = "No release version was supplied."
BAD_RELEASE_VERSION = "The provided release version wasn't recognized as a valid API or Portal release branch name."

NO_SOURCE_DATA = "Neither Git commits nor the name of a source branch were supplied."
BAD_GIT_COMMITS = "One or more commit hashes weren't recognized as valid commits."
BAD_SOURCE_BRANCH = "The provided source branch does not appear to exist on GitHub. " \
                    "Check your spelling, push the branch to origin, or use commit hashes instead."


def for_new_release():
    # start-release and major-release don't take any extra args and need no additional sanity checking
    pass


def for_altered_release(args):
    if args.interactive and any([args.release_version, args.git_commits, args.source_branch]):
        raise RuntimeError(CLI_ARGS_WHEN_INTERACTIVE)

    if not args.interactive:
        if not bool(args.release_version):
            raise ValueError(NO_RELEASE_VERSION)
        elif not RELEASE_VERSION_REGEX.match(args.release_version):
            raise ValueError(BAD_RELEASE_VERSION)

        #  Note: args.source_branch, if given as a commit hash, MIGHT afford the ability
        #  to merge PARTIAL histories of a branch -- i.e. merge all commits to this point, but no further.
        #  The guardrails currently prohibit this behavior, so it is not implemented. But it might be implementable.
        if len(args.git_commits) <= 0 and not args.source_branch:
            raise ValueError(NO_SOURCE_DATA)
        elif len(args.git_commits) <= 0 and not git_utils.branch_exists(args.source_branch):
            raise ValueError(BAD_SOURCE_BRANCH)
        elif not all(COMMIT_REGEX.match(git_commit) for git_commit in args.git_commits):
            raise ValueError(BAD_GIT_COMMITS)


def for_finalized_release(args):
    if args.interactive and args.release_version:
        raise RuntimeError(CLI_ARGS_WHEN_INTERACTIVE)

    if not args.interactive:
        if not bool(args.release_version):
            raise ValueError(NO_RELEASE_VERSION)
        elif not RELEASE_VERSION_REGEX.match(args.release_version):
            raise ValueError(BAD_RELEASE_VERSION)
