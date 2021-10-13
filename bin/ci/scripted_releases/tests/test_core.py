from scripted_releases import release_tasks, guardrails
import os
import release
import pytest


# to produce mock input on stdin for testing interactive mode:
#       monkeypatch.setattr('sys.stdin', io.StringIO('my input'))
# TODO: add screl tests to the api-ci.yml testing matrix


@pytest.fixture(autouse=True, scope="session")
def clean_up_audit_logs():
    audit_logs_dir = os.path.join(os.path.dirname(__file__), "../../logs")

    audit_logs_before_tests_run = os.listdir(audit_logs_dir)
    yield  # Test logic runs, audit logs are generated
    audit_logs_after_tests_ran = os.listdir(audit_logs_dir)

    for filename in audit_logs_after_tests_ran:
        if filename not in audit_logs_before_tests_run:
            os.remove(audit_logs_dir + '/' + filename)


# Make sure the unit tests never perform any real GitOps.
@pytest.fixture(autouse=True)
def mock_each_release_task(monkeypatch):
    monkeypatch.setattr(release_tasks, 'start', lambda args: None)
    monkeypatch.setattr(release_tasks, 'update', lambda args: None)
    monkeypatch.setattr(release_tasks, 'finalize', lambda args: None)
    monkeypatch.setattr(release_tasks, 'hotfix', lambda args: None)
    monkeypatch.setattr(release_tasks, 'major', lambda args: None)


def test_basic_arg_handling():
    # Argparse will throw an exception if called with unrecognized command-line flags.
    # SystemExit errors produce an exit code, not a message: no point trying to match on them.
    with pytest.raises(SystemExit):
        release.main(["-z"])
        release.main(["--nonesuch"])

    release.main(["--app", "portal", "start-release"])


def test_subcommand_arg_handling():
    release.main(["--interactive", "--app", "api", "update-release"])
    release.main(["--app", "api", "update-release", "-r", "release/api/v1.2.0", "-c", "a1b2c3d4"])


def test_subcommand_is_required():
    # Argparse requires the "--app" switch and at least one subcommand.
    with pytest.raises(SystemExit):
        release.main(["-i"])
        release.main(["--app", "api"])

    # Argparse will throw an exception if called with an invalid subcommand.
    with pytest.raises(SystemExit):
        release.main(["--app", "api", "nonesuch"])

    release.main(["--app", "api", "start-release"])


def test_no_blowups_in_correctly_invoked_subcommands():
    release.main(["--app", "api", "start-release"])
    release.main(["--app", "api", "update-release", "-r", "release/api/v1.2.0", "-c", "a1b2c3d4"])
    release.main(["--app", "api", "finalize-release", "-r", "release/api/v1.2.0"])
    release.main(["--app", "api", "hotfix", "-r", "release/api/v1.2.0", "-c", "d4e5f6107"])
    release.main(["--app", "api", "major-release"])

    release.main(["--app", "portal", "start-release"])
    release.main(["--app", "portal", "update-release", "-r", "release/portal/v4.0", "-c", "a1b2c3d4"])
    release.main(["--app", "portal", "finalize-release", "-r", "release/portal/v4.0"])
    release.main(["--app", "portal", "hotfix", "-r", "release/portal/v4.0", "-c", "d4e5f6107"])


def test_start_release_arg_handling():
    # No additional args needed to start a new release series.
    with pytest.raises(SystemExit):
        release.main(["--app", "api", "start-release", "-z"])
        release.main(["--app", "api", "start-release", "--nonesuch"])

    release.main(["--app", "api", "start-release"])
    release.main(["--app", "api", "-i", "start-release"])
    release.main(["--app", "portal", "start-release"])
    release.main(["--app", "portal", "-i", "start-release"])


def test_update_release_arg_handling():
    # If -i is not present, updating a release requires both -r and -c arguments.
    with pytest.raises(SystemExit):
        release.main(["--app", "api", "update-release"])
        release.main(["--app", "api", "update-release", "-r", "release/api/v1.2.0"])
        release.main(["--app", "api", "update-release", "-c", "abc123"])

    # If -i IS present, neither -r nor -c should be given at all.
    with pytest.raises(RuntimeError, match=guardrails.CLI_ARGS_WHEN_INTERACTIVE):
        release.main(["--app", "api", "-i", "update-release", "-r", "release/api/v1.2.0"])
        release.main(["--app", "api", "-i", "update-release", "-c", "abc123"])

    # A release branch can be updated with EITHER arbitrary commits OR an arbitrary branch, not both.
    with pytest.raises(SystemExit):
        release.main(
            ["--app", "api", "update-release",
             "-r", "release/api/v1.2.0",
             "-c", "a1b2c3d4",
             "--with-branch", "main"]
        )
        release.main(
            ["--app", "portal", "update-release",
             "-r", "release/portal/v4.0",
             "-c", "a1b2c3d4",
             "--with-branch", "main"]
        )

    release.main(["--app", "api", "-i", "update-release"])


def test_update_release_input_validations():
    # The -r argument should look like a release branch, and -c arguments should look like git commits.
    with pytest.raises(ValueError, match=guardrails.BAD_RELEASE_VERSION):
        release.main(["--app", "api", "update-release", "-r", "not_a_release_branch_oh_no", "-c", "abc123"])

    with pytest.raises(ValueError, match=guardrails.BAD_GIT_COMMITS):
        release.main(["--app", "api", "update-release", "-r", "release/api/v1.2.3", "-c", "not_a_git_commit_oh_no"])


def test_finalize_release_arg_handling():
    # TODO: specific operational tests for when it is or isn't OK to finalize a release.
    # The -r argument should look like a release branch.
    with pytest.raises(ValueError, match=guardrails.BAD_RELEASE_VERSION):
        release.main(["--app", "portal", "finalize-release", "-r", "relsear://portal/.5:67:890"])
        release.main(["--app", "api", "finalize-release", "-r", "iam.defintelynotan.api_release"])

    release.main(["--app", "api", "finalize-release", "-r", "release/api/v1.2.0"])
    release.main(["--app", "portal", "finalize-release", "-r", "release/portal/v4.0"])

    release.main(["--app", "api", "-i", "finalize-release"])


def test_hotfix_arg_handling():
    # TODO: specific operational tests for when it is or isn't OK to hotfix a release.
    # If -i is not present, hotfixing a finalized release requires both -r and -c arguments.
    with pytest.raises(SystemExit):
        release.main(["--app", "api", "hotfix"])
        release.main(["--app", "api", "hotfix", "-r", "release/api/v1.2.0"])
        release.main(["--app", "api", "hotfix", "-c", "abc123"])

        # Ensure only commits or a branch is provided when applying a hotfix
        release.main(["--app", "api", "hotfix", "-r" "release/api/v1.2.0", "-c", "abc123", "--with-branch", "main"])

    # If -i IS present, neither -r nor -c should be given at all.
    with pytest.raises(RuntimeError, match=guardrails.CLI_ARGS_WHEN_INTERACTIVE):
        release.main(["--app", "api", "-i", "hotfix", "-r", "release/api/v1.2.0"])
        release.main(["--app", "api", "-i", "hotfix", "-c", "abc123"])

    release.main(["--app", "api", "-i", "hotfix"])
    release.main(["--app", "api", "hotfix", "-r", "release/api/v1.2.0", "-c", "a1b2c3d4e"])
    release.main(["--app", "api", "hotfix", "-r", "release/api/v1.2.0", "--with-branch", "main"])


def test_major_release_arg_handling():
    # No additional args needed to create a new API major release.
    with pytest.raises(SystemExit):
        release.main(["--app", "api", "major-release", "-z"])
        release.main(["--app", "api", "major-release", "--nonesuch"])

    release.main(["--app", "api", "major-release"])
    release.main(["--app", "api", "-i", "major-release"])
