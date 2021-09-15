# bin/ci

Binaries and unit tests for the automated-release-process tasks in the API and Portal Makefiles.

---

## Makefile Usage

This is the preferred way to use these tasks to do various release-related things.
The Makefile tasks are just proxies through to the Python implementation at the command line,
so you should provide all your arguments through the `args=""` construct that many other Makefile tasks implement.

#### Examples:
- `make start-release args="-i"`
- `make update-release args="-r release/api/v2.25.0 -c a_git_commit_hash"`
- `make finalize-release args="-r release/api/v2.25.0"`
- `make hotfix args="-r release/portal/v30.0 -c a_commit -c another_commit"`

### Starting a release
- To start a new series of releases, run `make start-release`.
  - This task will automatically create the next API or Portal release branch from `main`.
  - It will also tag the HEAD of that new branch (so, HEAD of `main` at time of execution) with the appropriate `-rc1` tag.
  - This task is aware of the existing history, in Git, of all previous release series, 
    so you don't need to specify _which_ release series you're starting.

### Updating a release with a new RC
- To update a release series with new commits and a new RC number, run `make update-release`.
  - You'll need to provide the name of the release series you're updating in "git branch" form, 
    e.g. `release/api/v1.2.0` or `release/portal/v4.0`.
  - You'll also need to provide the hashes of all Git commits you wish to be a part of the next RC.
    Best practice is to use the merge commits from already-merged PRs, but in theory any git commit is permissible.
- This task will only function for a release series that has **not yet been finalized** through `make finalize-release`.
  - **Caution:** Merge conflicts must be resolved manually.
  
### When a release is ready to go to prod
- To mark a release series as ready for production deployment, run `make finalize-release`.
  - You'll need to provide the name of the release series you're finalizing, as in `make update-release.`
  - This task double-tags the most recent RC on that series with a bare semver, e.g. the commit tagged `api/v2.5.0-rc4` also gets tagged `api/v2.5.0`.
- Once you've done this to a given release series, `make update-release` **will no longer work** for that series.
- Once you've done this to a given release series, `make hotfix` will **start working** for that series. 

> #### NB: On Versioning
> A finalized release series _cannot_ gain new RCs, but it _can_ gain new hotfixes.
> 
> A release series that isn't yet finalized _can_ gain new RCs, but it _cannot_ gain hotfixes (until after it's been finalized.)
> 
> This is mostly pedantry. The same Git operations happen either way, and the only real difference is in the Git tags.
> Still, it's _important_ pedantry, so pay attention to the distinction.


### When prod needs to be hotfixed
- To add new production hotfixes to a finalized release series, run `make hotfix`.
  - This task works identically to `make update-release`,
    except that it produces incremented semver tags instead of incremented RC tags.
  - You'll need to provide the name of the release series you're hotfixing in "git branch" form,
      e.g. `release/api/v1.2.0` or `release/portal/v4.0`.
  - You'll also need to provide the hashes of all Git commits you wish to be a part of the next hotfix.
    Best practice is to use the merge commits from already-merged PRs, but in theory any git commit is permissible.
- This task will only function on a release series that has been finalized through `make finalize-release`.
  - **Caution:** Merge conflicts must be resolved manually.

---

## CLI Usage

These tasks were written to be invoked from the API and Portal makefiles,
but you can also invoke them directly from the command line if that's how you'd rather use them.

If invoking from CLI, please make sure to run the below commands with this README's directory, `bin/ci`, as your CWD.

- To see the help docs, use `python release.py --help`.
- To execute a real release task **autonomously from CLI**, run `python release.py --app [api|portal] <subcommand-name>`.
  - Depending on the subcommand you're running, you'll also need an `-r name_of_release_series` flag, 
    and one or more `-c a_git_commit_hash` flags.
- To execute a real release task **with interactive prompts**, run `python release.py --app [api|portal] (-i or --interactive) <subcommand-name>`.
  - Provide no other flags if you're running the script this way. 
    You'll supply everything necessary on stdin while the task is running.

---

## Unit Tests

- To run the tests, use `pytest scripted_releases/tests`. 
- These tests may later be integrated into the API's existing test suite, but for now they're independent.