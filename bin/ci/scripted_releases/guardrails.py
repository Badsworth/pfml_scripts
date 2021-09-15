from re import match

"""
Argument-handling guardrails for the various different ways to invoke release.py.
Each set of subcommands takes slightly different arguments and has slightly different validation needs.
"""

# TODO: regex polishing: don't match portal versions with >2 semver numbers.
RELEASE_VERSION_REGEX = r"release\/(api|portal)\/v([0-9]+)\.([0-9]+)\.{0,1}([0-9]+){0,1}"
COMMIT_REGEX = r"[0-9a-f]{7,40}"  # allows both short and long-form hash types

CLI_ARGS_WHEN_INTERACTIVE = "No additional command-line arguments should be provided in interactive mode."

NO_RELEASE_VERSION = "No release version was supplied."
BAD_RELEASE_VERSION = "The provided release version wasn't recognized as a valid API or Portal release branch name."

NO_GIT_COMMITS = "No Git commits were supplied."
BAD_GIT_COMMITS = "One or more commit hashes weren't recognized as valid commits."


def for_new_release():
    # start-release and major-release don't take any extra args and need no additional sanity checking
    pass


def for_altered_release(args):
    if args.interactive and any([args.release_version, args.git_commits]):
        raise RuntimeError(CLI_ARGS_WHEN_INTERACTIVE)

    if not args.interactive:
        if not bool(args.release_version):
            raise ValueError(NO_RELEASE_VERSION)
        elif not match(RELEASE_VERSION_REGEX, args.release_version):
            raise ValueError(BAD_RELEASE_VERSION)

        if len(args.git_commits) <= 0:
            raise ValueError(NO_GIT_COMMITS)
        elif not all(match(COMMIT_REGEX, git_commit) for git_commit in args.git_commits):
            raise ValueError(BAD_GIT_COMMITS)


def for_finalized_release(args):
    if args.interactive and args.release_version:
        raise RuntimeError(CLI_ARGS_WHEN_INTERACTIVE)

    if not args.interactive:
        if not bool(args.release_version):
            raise ValueError(NO_RELEASE_VERSION)
        elif not match(RELEASE_VERSION_REGEX, args.release_version):
            raise ValueError(BAD_RELEASE_VERSION)
