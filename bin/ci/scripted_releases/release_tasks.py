from scripted_releases import git_utils
import semver

def start(args, logger):
    # increments minor release number
    logger.info(f"Running 'start-release', args: {str(args)}")

    # getting the proper tags/branches for the release
    git_utils.fetch_remotes()

    recent_tag = git_utils.most_recent_tag(args.app) # get most recent tag

    v = git_utils.to_semver(recent_tag) # convert tag to semver object
    version_name = git_utils.from_semver(v.bump_minor(), args.app)
    branch_name = "release/" + version_name

    # making sure the tag has the proper release candidate flag
    tag_name = version_name + "-rc1"
    git_utils.create_branch(branch_name)

    # add -rc before tagging and pushing branch
    git_utils.tag_branch(branch_name, tag_name)


def update(args, logger):
    logger.info(f"Running 'update-release', args: {repr(args)}")


def finalize(args, logger):
    logger.info(f"Running 'finalize-release', args: {repr(args)}")


def hotfix(args, logger):
    logger.info(f"Running 'hotfix'; args, {repr(args)}")


def major(args, logger):
    logger.info(f"Running 'major-release'; args, {repr(args)}")
