# low level methods and processes for scripted releases here
from git import Repo
import os
import re
import semantic_version


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
    git.checkout(
        branch_name, "origin/main"
    )  # avoids possible complications with in-progress local directories.
    logger.info(f"branch {branch_name} created from origin/main")


def tag_branch(branch_name, tag_name):
    fetch_remotes()
    git.tag(tag_name)  # possible without checking out branch
    logger.info(f"pushing tag: {tag_name} to origin")
    git.push("origin", tag_name)


def to_semver(version_str: str) -> semantic_version.Version:
    # for portal, update as minor.patch
    if version_str.startswith("portal/v"):
        ver = "0." + version_str.split("portal/v")[-1] # portal versions don't have a third number, which makes their versions invalid semver
        return semantic_version.Version(ver)
    elif version_str.startswith("api/v"):
        return semantic_version.Version(version_str.split("api/v")[-1])
    else:
        raise ValueError(f"Unrecognized version string '{version_str}'")


def from_semver(sem_ver: semantic_version.Version, is_portal=False) -> str:
    if is_portal:
        return "portal/v" + str(sem_ver).split("0.")[-1]
    else:
        return "api/v" + str(sem_ver)
