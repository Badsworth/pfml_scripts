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

    # guardrails will have vetted args.release_version
    # guardrails will have vetted args.git_commits

    # autonomous flow:
    # TODO - most_recent_tag is not detecting 'foobar' RC tags correctly; finds only rc1 as newest, not rc2
    git_utils.fetch_remotes()
    recent_tag = git_utils.most_recent_tag(args.app)
    v = git_utils.to_semver(recent_tag)

    if not git_utils.branch_exists(args.release_version):
        logger.error(f"Could not find the branch '{args.release_version}' on GitHub.")
        logger.error("Script cannot proceed and will now terminate.")
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
        logger.warning(f"Reverting '{args.release_version}' back to previous HEAD...")
        git_utils.reset_head()
        logger.warning("Done. Will now halt.")
        return False
    finally:
        logger.warning("Task is finishing, will check out 'main' locally")  # TODO: check out original branch instead
        git_utils.checkout("main")

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


def hotfix(args): # production hotfix, args are a branch name and a list of commits
    # args are a release branch and a list of commits
    # release branch will be cut from the prod deploy branch
    #  add more loggers
    # guardrails are supposed to vet args.release_verison and args.commits
    # add guardrails for make finalize_release
    logger.info(f"Running 'hotfix'; args: {repr(args)}")

    git_utils.fetch_remotes()
    recent_tag = git_utils.most_recent_tag(args.app)
    v = git_utils.to_semver(recent_tag)

    version_name = git_utils.from_semver(v.bump_patch(), args.app)
 
    git_utils.branch_from_release(args.release_version, f"origin/deploy/{args.app}/prod")
    git_utils.tag_branch(args.release_version, version_name)
    git_utils.cherrypick(args.git_commits) # assumes these are coming from main


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
