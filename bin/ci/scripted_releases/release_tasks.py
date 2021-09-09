from scripted_releases import git_utils
import semver
import logging

logger = logging.getLogger(__name__)


def start(args):
    # increments minor release number
    logger.info(f"Running 'start-release'...")
    logger.debug(f"Args: {repr(args)}")

    # getting the proper tags/branches for the release
    git_utils.fetch_remotes()
    recent_tag = git_utils.most_recent_tag(args.app)

    v = git_utils.to_semver(recent_tag)  # convert tag to semver object
    version_name = git_utils.from_semver(v.bump_minor(), args.app)
    branch_name = "release/" + version_name

    # making sure the tag has the proper release candidate flag
    tag_name = version_name + "-rc1"
    git_utils.create_branch(branch_name)

    # add -rc before tagging and pushing branch
    git_utils.tag_branch(branch_name, tag_name)


def update(args):
    logger.info(f"Running 'update-release'...")
    logger.debug(f"Args: {repr(args)}")

    # guardrails will have vetted args.release_version
    # guardrails will have vetted args.git_commits

    # autonomous flow:
    #   fetch_remotes()
    #   get most recent tag for args.app, convert to semver
    #   check out the branch at args.release_version
    #       NB: will the check-out break everything if the release branch lacks this code?
    #       NB: save a pointer to the old HEAD of args.release_version in case of error
    #   for each git commit in args.git_commits:
    #       cherry-pick that commit onto the branch at args.release_version
    #       if merge conflicts or any other Git error, STOP. Hard reset to the saved pointer and exit 1.
    #   once all commits cherry-picked:
    #       increment semver 'prerelease' version by one
    #       tag new HEAD of args.release_version with incremented semver
    #       push (force-push?) updated branch to origin


def finalize(args):
    logger.info(f"Running 'finalize-release'...")
    logger.debug(f"Args: {repr(args)}")


def hotfix(args):
    logger.info(f"Running 'hotfix'...")
    logger.debug(f"Args: {repr(args)}")


def major(args):
    # API ONLY!!! Increments major release number
    logger.info(f"Running 'major-release'...")
    logger.debug(f"Args: {repr(args)}")

    if args.app != 'api':
        raise NotImplementedError("This task is for API releases only")
    else:
        # getting the proper tags/branches for the release
        git_utils.fetch_remotes()
        recent_tag = git_utils.most_recent_tag(args.app)

        v = git_utils.to_semver(recent_tag)  # convert tag to semver object
        version_name = git_utils.from_semver(v.bump_major(), args.app)
        branch_name = "release/" + version_name

        # making sure the tag has the proper release candidate flag
        tag_name = version_name + "-rc1"
        git_utils.create_branch(branch_name)

        # add -rc before tagging and pushing branch
        git_utils.tag_branch(branch_name, tag_name)
