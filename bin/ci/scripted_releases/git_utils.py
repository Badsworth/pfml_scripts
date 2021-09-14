# low level methods and processes for scripted releases here
from git import Repo
import os
from re import match
import semver
import logging

logger = logging.getLogger(__name__)

# create an instance of the Repo object
repo = Repo(os.path.join(os.path.dirname(__file__), "../../.."))
git = repo.git

rc_match = r".+-rc[0-9]+"
FORMAL_RELEASE_TAG_REGEX = r"(api|portal|foobar)\/v([0-9]+)\.([0-9]+)(\.{0,1}([0-9]+){0,1})$"

def fetch_remotes():
    # fetch remotes
    origin = repo.remotes.origin
    return origin.fetch()


def checkout_main():
    git.checkout("main")


def checkout(branch_name):
    git.checkout(branch_name)


def reset_head():
    git.reset("--hard", "HEAD")


def pull_main():
    git.pull("origin", "main")


def cherrypick(commit_hash):
    git.cherry_pick(commit_hash)


def merge_branch(branch_name):
    raise NotImplementedError


def create_branch(branch_name):
    fetch_remotes()
    git.branch(branch_name)
    git.push("-u", "origin", branch_name)
    logger.info(f"Branch '{branch_name}' created from origin/main")


def current_branch():
    return git.branch("--show-current")


def most_recent_tag(app):
    t = git.describe("--tags", "--match", f"{app}/v*", "--abbrev=0", "origin/main")
    sha = git.rev_parse(t)
    logger.info(f"Latest {app} tag is '{t}' with commit SHA '{sha[0:9]}'")
    return t


def is_finalized(release_branch) -> bool:
    # hideous triple data munging: 'release/api/v2.23.0' --> 'api/v2.23.0' --> 'api/v2.23.*'
    release_branch_version_series: str = "/".join(release_branch.split("/")[1:])[:-1] + "*"
    logger.debug(f"Scanning for finalization status on '{release_branch_version_series}'")

    version_series_tags: list = git.tag("-l", release_branch_version_series).split("\n")
    logger.debug(f"Found these release tags: {version_series_tags}")

    formal_release_statuses = list(bool(match(FORMAL_RELEASE_TAG_REGEX, tag)) for tag in version_series_tags)
    logger.debug(f"Formal-release status of those tags: {tuple(zip(version_series_tags, formal_release_statuses))}")

    if any(formal_release_statuses):
        logger.info(f"The release series '{release_branch}' has already been finalized.")
        return True
    else:
        logger.info(f"The release series '{release_branch}' has not yet been finalized.")
        return False


def head_of_branch(branch_name):
    return git.rev_parse(f"origin/{branch_name}")


def tag_branch(branch_name, tag_name):
    fetch_remotes()
    git.tag(tag_name, branch_name)  # possible without checking out branch
    logger.info(f"Pushing tag '{tag_name}' to origin")
    git.push("origin", tag_name)


def branch_exists(branch_name: str) -> bool:
    return f"remotes/origin/{branch_name}" in git.branch("-a").split()


def to_semver(version_str: str) -> semver.VersionInfo:
    # for portal, update as minor.patch
    if version_str.startswith("portal/v"):
        # portal versions don't have a third number, which makes their versions invalid semver
        ver = "0." + version_str.split("portal/v")[-1]
        return semver.VersionInfo.parse(ver)
    elif version_str.startswith("api/v"):
        return semver.VersionInfo.parse(version_str.split("api/v")[-1])
    elif version_str.startswith("foobar/v"):
        return semver.VersionInfo.parse(version_str.split("foobar/v")[-1])
    else:
        raise ValueError(f"Unrecognized version string '{version_str}'")


def from_semver(sem_ver: semver.VersionInfo, app) -> str:
    if app == "portal":
        return "portal/v" + str(sem_ver).split("0.")[-1]
    elif app == "api":
        return "api/v" + str(sem_ver)
    elif app == "foobar":
        return "foobar/v" + str(sem_ver)
    else:
        raise ValueError("from_semver called with malformed app identifier; will now panic")
