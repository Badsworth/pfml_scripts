from scripted_releases import git_utils
import git
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

    # TODO - most_recent_tag is not detecting 'foobar' RC tags correctly; finds only rc1 as newest, not rc2
    git_utils.fetch_remotes()
    original_branch = git_utils.current_branch()  # Save this to check it back out after work's done

    recent_tag = git_utils.most_recent_tag(args.app)
    v = git_utils.to_semver(recent_tag)

    if not git_utils.branch_exists(args.release_version):
        logger.error(f"Could not find the branch '{args.release_version}' on GitHub.")
        logger.error("Script cannot proceed and will now terminate.")
        return False

    if git_utils.is_finalized(args.release_version):
        logger.error(f"'{args.release_version}' can only take hotfixes.")
        logger.error("Try running this script again, but with the 'hotfix' task instead.")
        return False

    old_head = git_utils.head_of_branch(args.release_version)
    logger.info(f"HEAD of '{args.release_version}' on origin is '{old_head[0:9]}'")
    logger.info("Will save this HEAD and revert back to it if anything goes wrong.")

    try:
        git_utils.checkout(args.release_version)
        logger.info(f"Checked out '{args.release_version}'.")
        logger.info(f"Now {'cherry picking commits' if args.git_commits else f'merging in {args.source_branch}'}...")
    except git.exc.GitCommandError as e:
        logger.warning(f"Ran into a problem: {e}")
        return False
    finally:
        logger.warning(f"Task is finishing, will check out '{original_branch}' locally")
        git_utils.checkout(original_branch)

    #   check out the branch at args.release_version
    #       NB: will the check-out break everything if the release branch lacks this code?
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
