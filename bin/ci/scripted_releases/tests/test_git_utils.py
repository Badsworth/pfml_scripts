# testing for the git internals for the automated deploy process
import re

from scripted_releases import git_utils

from semver import VersionInfo
import pytest
from unittest.mock import Mock, patch

def test_to_semver_admin_portal():
    with pytest.raises(ValueError):
        git_utils.to_semver("admin-portal/v23.4.9")

    assert git_utils.to_semver("admin-portal/v19.1") == VersionInfo(major=0, minor=19, patch=1)
    assert git_utils.to_semver("admin-portal/v15.0-rc1") == VersionInfo(major=0, minor=15, patch=0, prerelease="rc1")


def test_to_semver_api():
    with pytest.raises(ValueError):
        git_utils.to_semver("api/v26.2")

    with pytest.raises(ValueError, match="Unrecognized version string '9.2.17.17-SOM-C7.0.1-SNAPSHOT'"):
        git_utils.to_semver("9.2.17.17-SOM-C7.0.1-SNAPSHOT")  # this is a fineos version number

    assert git_utils.to_semver("api/v23.9.0") == VersionInfo(major=23, minor=9, patch=0)
    assert git_utils.to_semver("api/v24.7.0-rc1") == VersionInfo(major=24, minor=7, patch=0, prerelease='rc1')
    assert git_utils.to_semver("api/v24.7.1") == VersionInfo(major=24, minor=7, patch=1)


def test_to_semver_portal():
    with pytest.raises(ValueError):
        git_utils.to_semver("portal/v23.4.9")

    assert git_utils.to_semver("portal/v19.1") == VersionInfo(major=0, minor=19, patch=1)
    assert git_utils.to_semver("portal/v15.0-rc1") == VersionInfo(major=0, minor=15, patch=0, prerelease="rc1")


def test_from_semver_admin_portal():
    assert git_utils.from_semver(VersionInfo(major=0, minor=19, patch=1), app='admin-portal') == "admin-portal/v19.1"
    assert git_utils.from_semver(VersionInfo(major=0, minor=15, patch=0, prerelease='rc1'),
                                 app='admin-portal') == "admin-portal/v15.0-rc1"


def test_from_semver_api():
    assert git_utils.from_semver(VersionInfo(major=23, minor=9, patch=0), app='api') == "api/v23.9.0"
    assert git_utils.from_semver(VersionInfo(major=24, minor=7, patch=0, prerelease='rc1'),
                                 app='api') == "api/v24.7.0-rc1"
    assert git_utils.from_semver(VersionInfo(major=24, minor=7, patch=1), app='api') == "api/v24.7.1"


def test_from_semver_portal():
    assert git_utils.from_semver(VersionInfo(major=0, minor=19, patch=1), app='portal') == "portal/v19.1"
    assert git_utils.from_semver(VersionInfo(major=0, minor=15, patch=0, prerelease='rc1'),
                                 app='portal') == "portal/v15.0-rc1"


# NB: Inputs to the Git binary cannot be mocked. This test depends on a real "mock release branch" in the PFML repo.
def test_release_series_is_not_finalized(monkeypatch):
    monkeypatch.setattr(
        git_utils, 'PROD_RELEASE_VERSION_REGEX',
        re.compile(r"(finished|unfinished)\/v([0-9]+)\.([0-9]+)(\.{0,1}([0-9]+){0,1})$")
    )
    assert git_utils.is_finalized("release/unfinished/v5.5.0") is False


# NB: Inputs to the Git binary cannot be mocked. This test depends on a real "mock release branch" in the PFML repo.
def test_release_series_is_finalized(monkeypatch):
    monkeypatch.setattr(
        git_utils, 'PROD_RELEASE_VERSION_REGEX',
        re.compile(r"(finished|unfinished)\/v([0-9]+)\.([0-9]+)(\.{0,1}([0-9]+){0,1})$")
    )
    assert git_utils.is_finalized("release/finished/v7.7.0") is True

@patch("scripted_releases.git_utils.get_sha", return_value='12345')
@patch("scripted_releases.git_utils.collect_tags", return_value = ['portal/v1.10', 'portal/v1.9', 'portal/v1.1'])
def test_get_latest_version(mock_collect_tags, mock_get_sha, monkeypatch):

    # should make sure that tests match regex and stay in order (aka 9 won't be returned if 10 is present)
    monkeypatch.setattr(git_utils, 'RELEASE_VERSION_REGEX', r"portal\/v([0-9]+)\.([0-9]+)(\.{0,1}([0-9]+){0,1})(\-rc\d+)?")

    assert git_utils.get_latest_version('portal', 'unit_test')[0] == 'portal/v1.10'
    assert git_utils.get_latest_version('portal', 'unit_test')[1] == '12345'
    
# notes for testing with a fake repo - session or test-scoped pytest fixture
# in a tmpdir: git init, commit some garbage, make branches, create tags, etc.
# would need to monkeypatch git_utils.repo, or refactor git_utils to take repo location as an arg
# git_utils could be refactored to a class, instantiate one instance in release_tasks.py or release.py


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
