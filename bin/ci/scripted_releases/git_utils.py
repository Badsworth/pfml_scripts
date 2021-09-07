# low level methods and processes for scripted releases here
from git import Repo
import os
import re
import semver
import logging

logger = logging.getLogger(__name__)

# create an instance of the Repo object
repo = Repo(os.path.join(os.path.dirname(__file__), "../../.."))
git = repo.git

rc_match = r".+-rc[0-9]+"


def fetch_remotes():
    # fetch remotes
    origin = repo.remotes.origin
    return origin.fetch()


def checkout_main():
    git.checkout("main")


def reset_head():
    git.reset("--hard", "HEAD")


def pull_main():
    git.pull("origin", "main")


def cherrypick(commit_hash):
    git.cherry_pick(commit_hash)


def create_branch(branch_name):
    fetch_remotes()
    git.branch(branch_name)
    git.push("-u", "origin", branch_name)
    logger.info(f"Branch '{branch_name}' created from origin/main")


def most_recent_tag(app):
    return git.describe("--tags", "--match", f"{app}/v*", "--abbrev=0", "origin/main") 


def tag_branch(branch_name, tag_name):
    fetch_remotes()
    git.tag(tag_name, branch_name)  # possible without checking out branch
    logger.info(f"Pushing tag '{tag_name}' to origin")
    git.push("origin", tag_name)


def to_semver(version_str: str) -> semver.VersionInfo:
    # for portal, update as minor.patch
    if version_str.startswith("portal/v"):
        # portal versions don't have a third number, which makes their versions invalid semver
        ver = "0." + version_str.split("portal/v")[-1]
        return semver.VersionInfo.parse(ver)
    elif version_str.startswith("api/v"):
        return semver.VersionInfo.parse(version_str.split("api/v")[-1])
    else:
        raise ValueError(f"Unrecognized version string '{version_str}'")


def from_semver(sem_ver: semver.VersionInfo, app) -> str:
    if app == "portal":
        return "portal/v" + str(sem_ver).split("0.")[-1]
    else:
        return "api/v" + str(sem_ver)
