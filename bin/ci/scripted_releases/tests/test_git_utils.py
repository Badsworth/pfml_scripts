# testing for the git internals for the automated deploy process
from scripted_releases import git_utils
from semantic_version import Version
from git import Actor, Repo 
import os 
import pytest
from unittest import mock
from datetime import datetime


def test_to_semver_api():
  with pytest.raises(ValueError):
    git_utils.to_semver("api/v26.2")

  with pytest.raises(ValueError, match="Unrecognized version string '9.2.17.17-SOM-C7.0.1-SNAPSHOT'"):
    git_utils.to_semver("9.2.17.17-SOM-C7.0.1-SNAPSHOT") # this is a fineos version number

  assert git_utils.to_semver("api/v23.9.0")     == Version("23.9.0")
  assert git_utils.to_semver("api/v24.7.0-rc1") == Version("24.7.0-rc1")
  assert git_utils.to_semver("api/v24.7.1")     == Version("24.7.1")

  

def test_to_semver_portal():
  with pytest.raises(ValueError):
    git_utils.to_semver("portal/v23.4.9")

  assert git_utils.to_semver("portal/v19.1")      == Version("0.19.1")
  assert git_utils.to_semver("portal/v15.0-rc1")  == Version("0.15.0-rc1")


def test_from_semver_api():
  assert git_utils.from_semver(Version("23.9.0"))     == "api/v23.9.0"
  assert git_utils.from_semver(Version("24.7.0-rc1")) == "api/v24.7.0-rc1"
  assert git_utils.from_semver(Version("24.7.1"))     == "api/v24.7.1"

def test_from_semver_portal():
  assert git_utils.from_semver(Version("0.19.1"), is_portal=True)     == "portal/v19.1"
  assert git_utils.from_semver(Version("0.15.0-rc1"), is_portal=True) == "portal/v15.0-rc1"


# update these when working on major/minor releases
# def test_incrementer_api():
#   # major release
#   # minor release
#   # hotfix
#   # rc scenario
#   pass

# def test_incrementer_portal():
#   # major release
#   # minor
#   # check that patch num isn't changed
#   pass