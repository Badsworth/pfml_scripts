from scripted_releases import git_utils
import git
import logging

logger = logging.getLogger(__name__)


def start(args):
    # increments minor release number
    logger.info(f"Running 'start-release'...")
    logger.debug(f"Args: {repr(args)}")

    with git_utils.rollback():
        # getting the proper tags/branches for the release.
        # NB: most_recent_tag() will return incorrect results on main
        # (compared to the correct result on a release branch)
        # ...but it will return a "correct enough" tag for the purposes of just bumping its minor version number.
        git_utils.fetch_remotes()
        recent_tag, tag_sha = git_utils.most_recent_tag(args.app, "main")

        v = git_utils.to_semver(recent_tag)  # convert tag to semver object
        version_name = git_utils.from_semver(v.bump_minor(), args.app)
        branch_name = "release/" + version_name

        # making sure the tag has the proper release candidate flag
        tag_name = version_name + "-rc1"
        git_utils.create_branch(branch_name)

        # add -rc before tagging and pushing branch
        git_utils.tag_and_push(branch_name, tag_name)


# ----------------------------------------------------------------------------------------------------
# Produces new release candidates from an arbitrary list of git commits, or an arbitrary source branch
def update(args):
    # TODO: is it safe to delete any local copy of args.release_version before making git changes?
    # TODO: vet safety and correctness of hotfix/update tasks when run across multiple computers
    logger.info(f"Running 'update-release'...")
    logger.debug(f"Args: {repr(args)}")
    logger.warning("Merge conflicts must be resolved manually.")

    git_utils.fetch_remotes()
    recent_tag, tag_sha = git_utils.most_recent_tag(args.app, args.release_version)
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

    with git_utils.rollback(old_head):
        git_utils.checkout(args.release_version)
        logger.info(f"Checked out '{args.release_version}'.")

        if args.git_commits:
            logger.info("Now cherry picking commits...")
            git_utils.cherrypick("-x", args.git_commits)
        else:
            logger.info(f"Now merging in {args.source_branch}...")
            git_utils.merge(args.source_branch)

        logger.info("Done.")
        git_utils.tag_and_push(args.release_version, f"{args.app}/v{v.bump_prerelease()}")


# ----------------------------------------------------------------------------------------------------
def finalize(args):
    logger.info(f"Running 'finalize-release'...")
    logger.debug(f"Args: {repr(args)}")

    with git_utils.rollback():
        if not git_utils.is_finalized(args.release_version):
            git_utils.checkout(args.release_version)
            logger.info(f"Checked out '{args.release_version}'.")

            latest_rc, rc_commit_hash = git_utils.most_recent_tag(args.app, args.release_version)
            v = git_utils.to_semver(latest_rc)
            formal_release_number = git_utils.from_semver(v.finalize_version(), args.app)

            logger.info(f"Finalizing {args.release_version}")
            logger.info(f"Commit {rc_commit_hash[0:9]} ({latest_rc}) will also be tagged {formal_release_number}")
            git_utils.tag_and_push(args.release_version, formal_release_number)
        else:
            return False


# ----------------------------------------------------------------------------------------------------
def hotfix(args):  # production hotfix, args are a branch name and a list of commits
    # TODO: is it safe to delete any local copy of args.release_version before making git changes?
    # TODO: vet safety and correctness of hotfix/update tasks when run across multiple computers
    logger.info(f"Running 'hotfix'...")
    logger.debug(f"Args: {repr(args)}")
    logger.warning("Merge conflicts must be resolved manually.")

    git_utils.fetch_remotes()
    recent_tag, tag_sha = git_utils.most_recent_tag(args.app, args.release_version)
    v = git_utils.to_semver(recent_tag)

    if not git_utils.branch_exists(args.release_version):
        logger.error(f"Could not find the branch '{args.release_version}' on GitHub.")
        logger.error("Script cannot proceed and will now terminate.")
        return False

    if not git_utils.is_finalized(args.release_version):
        logger.error(f"'{args.release_version}' can only take new RCs.")
        logger.error("Try running this script again, but with the 'update-release' task instead.")
        return False

    old_head = git_utils.head_of_branch(args.release_version)
    logger.info(f"HEAD of '{args.release_version}' on origin is '{old_head[0:9]}'")
    logger.info("Will save this HEAD and revert back to it if anything goes wrong.")

    with git_utils.rollback(old_head):
        git_utils.checkout(args.release_version)
        logger.info(f"Checked out '{args.release_version}'.")

        if args.git_commits:
            logger.info("Now cherry picking commits...")
            git_utils.cherrypick("-x", args.git_commits)
        else:
            logger.info(f"Now merging in {args.source_branch}...")
            git_utils.merge(args.source_branch)

        logger.info("Done.")
        git_utils.tag_and_push(args.release_version, f"{args.app}/v{v.bump_patch()}")


# ----------------------------------------------------------------------------------------------------
def major(args):
    # API ONLY!!! Increments major release number
    logger.info(f"Running 'major-release'...")
    logger.debug(f"Args: {repr(args)}")

    if args.app != 'api':
        raise NotImplementedError("This task is for API releases only")
    else:
        with git_utils.rollback():
            # getting the proper tags/branches for the release
            git_utils.fetch_remotes()
            recent_tag, tag_sha = git_utils.most_recent_tag(args.app, "main")

            v = git_utils.to_semver(recent_tag)  # convert tag to semver object
            version_name = git_utils.from_semver(v.bump_major(), args.app)
            branch_name = "release/" + version_name

            # making sure the tag has the proper release candidate flag
            tag_name = version_name + "-rc1"
            git_utils.create_branch(branch_name)

            # add -rc before tagging and pushing branch
            git_utils.tag_and_push(branch_name, tag_name)
