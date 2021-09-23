from scripted_releases import git_utils
import git
import logging

logger = logging.getLogger(__name__)


def start(args):
    # increments minor release number
    logger.info(f"Running 'start-release'...")
    logger.debug(f"Args: {repr(args)}")

    # getting the proper tags/branches for the release.
    # NB: most_recent_tag() will return incorrect results on main (compared to the correct result on a release branch)
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

    git_utils.fetch_remotes()
    original_branch = git_utils.current_branch()  # Save this to check it back out after work's done

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

    try:
        git_utils.checkout(args.release_version)
        logger.info(f"Checked out '{args.release_version}'.")

        if args.git_commits:
            logger.info("Now cherry picking commits...")
            git_utils.cherrypick("-x", args.git_commits)
        else:
            logger.info(f"Now merging in {args.source_branch}...")
            git_utils.merge_in_branch(args.source_branch)

        logger.info("Done.")
        git_utils.tag_and_push(args.release_version, f"{args.app}/v{v.bump_prerelease()}")

    except git.exc.GitCommandError as e:
        # hard reset to old_head, and discard any tags or commits descended from old_head
        # also abort any in-process cherry pick; these leave dirty state if not cleaned up
        logger.warning(f"Ran into a problem: {e}")

        try:
            git_utils.cherrypick("--abort")  # not actually a "commit_hash", but a valid switch for `git cherry-pick`
            logger.warning("Cleaned up an in-process cherry-pick")
        except git.exc.GitCommandError as e2:
            logger.debug(f"No cherry-pick was in progress (or something else went wrong) - {e2}")

        logger.warning(f"Resetting '{args.release_version}' back to {old_head}.")
        git_utils.reset_head(old_head)
        return False
    finally:
        logger.warning(f"Task is finishing, will check out '{original_branch}' locally")
        git_utils.checkout(original_branch)


# ----------------------------------------------------------------------------------------------------
def finalize(args):
    logger.info(f"Running 'finalize-release'...")
    logger.debug(f"Args: {repr(args)}")

    with git_utils.git_rollback():
        if not git_utils.is_finalized(args.release_version):
            git_utils.checkout(args.release_version)
            logger.info(f"Checked out '{args.release_version}'.")

            latest_rc, rc_commit_hash = git_utils.most_recent_tag(args.app, args.release_version)
            v = git_utils.to_semver(latest_rc)
            formal_release_number = git_utils.from_semver(v.finalize_version(), args.app)

            logger.info(f"Finalizing {args.release_version}")
            logger.info(f"Commit {rc_commit_hash} ({latest_rc}) will also be tagged {formal_release_number}")
            git_utils.tag_and_push(args.release_version, formal_release_number)
        else:
            logger.error(f"The series: {args.release_version} has already been finalized")
            return False


# ----------------------------------------------------------------------------------------------------
def hotfix(args):  # production hotfix, args are a branch name and a list of commits
    # TODO: is it safe to delete any local copy of args.release_version before making git changes?
    # TODO: vet safety and correctness of hotfix/update tasks when run across multiple computers
    logger.info(f"Running 'hotfix'...")
    logger.debug(f"Args: {repr(args)}")

    git_utils.fetch_remotes()
    original_branch = git_utils.current_branch()  # Save this to check it back out after work's done

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

    logger.warn("If there is a merge conflict, it must be resolved manually.")
    try:
        git_utils.checkout(args.release_version)

        logger.info(f"Checked out '{args.release_version}'.")

        if args.git_commits:
            logger.info("Now cherry picking commits...")
            git_utils.cherrypick("-x", args.git_commits)
        else:
            logger.info(f"Now merging in {args.source_branch}...")
            git_utils.merge_in_branch(args.source_branch)

        logger.info("Done.")
        git_utils.tag_and_push(args.release_version, f"{args.app}/v{v.bump_patch()}")

    except git.exc.GitCommandError as e:
        # hard reset to old_head, and discard any tags or commits descended from old_head
        # also abort any in-process cherry pick; these leave dirty state if not cleaned up
        logger.warning(f"Ran into a problem: {e}")

        try:
            git_utils.cherrypick("--abort")
            logger.warning("Cleaned up an in-process cherry-pick")
        except git.exc.GitCommandError as e2:
            logger.debug(f"No cherry-pick was in progress (or something else went wrong) - {e2}")

        logger.warning(f"Resetting '{args.release_version}' back to {old_head}.")
        git_utils.reset_head(old_head)
        return False
    finally:
        logger.warning(f"Task is finishing, will check out '{original_branch}' locally")
        git_utils.checkout(original_branch)


# ----------------------------------------------------------------------------------------------------
def major(args):
    # API ONLY!!! Increments major release number
    logger.info(f"Running 'major-release'...")
    logger.debug(f"Args: {repr(args)}")

    if args.app != 'api':
        raise NotImplementedError("This task is for API releases only")
    else:
        # getting the proper tags/branches for the release
        # NB: most_recent_tag() returns incorrect results on main (compared to the correct result on a release branch)
        # ...but it will return a "correct enough" tag for the purposes of just bumping its minor version number.
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
