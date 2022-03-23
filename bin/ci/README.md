# Scripted Releases

---

## Installation Instructions

`scripted-releases` is a Python project managed with [Poetry](https://python-poetry.org/). It makes heavy use of [GitPython](https://gitpython.readthedocs.io/en/stable/intro.html) to hook into
your machine's local `git` binary, which is used to manipulate the `EOLWD/pfml` monorepo in various ways.

Use either Poetry or `pip` to bootstrap the project's dependencies before you use it for anything.

- To install the necessary dependencies, cd into this directory (bin/ci) and run `poetry install`.

🟢 Scripted Releases is now available through Github Actions 🟢
  - No installation steps required and no CLI needed.
  - Job located here - [Scripted Releases](https://github.com/EOLWD/pfml/actions/workflows/scripted-releases.yml)
  - ⚠️ Merge conflicts must be resolved manually using `git` then the Action can be re-ran ⚠️

---

## Usage Instructions

There's a multitude of ways to use this project to accomplish your release tasks. Choose whichever works best for you.

You can always provide the `-h / --help` flag instead of any other args to see detailed usage and syntax instructions.

### ...via Github Actions
- Github Actions utilizes Poetry to run Scripted Releases.
- Just select the **Application**, **Scripted Release Task**, and **Arguments** (not required for `start-release` task)
- Examples:
  - 1️⃣**Application**: `api` 2️⃣**Scripted Release Task**: `start-release` 3️⃣**Arguments**:
  - 1️⃣**Application**: `api` 2️⃣**Scripted Release Task**: `update-release` 3️⃣**Arguments**: `-r release/api/v2.25.0 --with-branch main`
  - 1️⃣**Application**: `api` 2️⃣**Scripted Release Task**: `finalize-release` 3️⃣**Arguments**: `-r release/api/v2.25.0`
  - 1️⃣**Application**: `api` 2️⃣**Scripted Release Task**: `hotfix` 3️⃣**Arguments**: `-r release/api/v2.25.0 -c DEADBEEF -c ABADCAFE`
  - 1️⃣**Application**: `portal` 2️⃣**Scripted Release Task**: `update-release` 3️⃣**Arguments**: `-r release/portal/v49.0 -c ABCDEFGH`
- ⚠️ Merge conflicts must be resolved manually using `git` then the Action can be re-ran ⚠️

### ...via Poetry
- Once you've got the project installed, run these scripts from `bin/ci` with `poetry run scripted-releases <args>`.
- Examples:
  - `poetry run scripted-releases -a api start-release`
  - `poetry run scripted-releases -a api update-release -r release/api/v2.25.0 -c DEADBEEF`
  - `poetry run scripted-releases -a portal update-release -r release/portal/v49.0 --with-branch main`
  - `poetry run scripted-releases -a portal finalize-release -r release/portal/v49.0`
  - `poetry run scripted-releases -a portal hotfix -r release/portal/v49.0 -c DEADBEEF -c ABADCAFE`
  - `poetry run scripted-releases -a admin-portal update-release -r release/admin-portal/v2.0 --with-branch main`
  - `poetry run scripted-releases -a admin-portal finalize-release -r release/admin-portal/v2.0`
  - `poetry run scripted-releases -a admin-portal hotfix -r release/admin-portal/v2.0 -c DEADBEEF -c ABADCAFE`

### ...via API or Portal makefiles
- There are some convenient hooks for invoking the various release tasks from the API, Portal or Admin Portal makefiles.
- To use the script this way, first CD into the directory, then use `make` to start your task.
- Examples:
  - `someone@nava: ~/code/pfml/api $ make start-release`
  - `someone@nava: ~/code/pfml/api $ make update-release args="-r release/api/v2.25.0 -c DEADBEEF"`
  - `someone@nava: ~/code/pfml/portal $ make update-release args="-r release/portal/v49.0 --with-branch main"`
  - `someone@nava: ~/code/pfml/portal $ make finalize-release args="-r release/portal/v49.0"`
  - `someone@nava: ~/code/pfml/portal $ make hotfix args="-r release/portal/v49.0 -c DEADBEEF -c ABADCAFE"`
  - `someone@nava: ~/code/pfml/admin $ make update-release args="-r release/portal/v49.0 --with-branch main"`
  - `someone@nava: ~/code/pfml/admin $ make finalize-release args="-r release/portal/v49.0"`
  - `someone@nava: ~/code/pfml/admin $ make hotfix args="-r release/portal/v49.0 -c DEADBEEF -c ABADCAFE"`
- NOTE: You don't need to provide the `-a / --app` arg when running tasks from the makefiles.
  (The Makefile sets it automatically.)

### ...via plain Python
- If you'd rather skip all the bells and whistles, this script can still be run using a plain Python interpreter.
- First ensure you've installed all the dependencies in `pyproject.toml` using `pip` or your favorite package manager.
- Then, CD into `bin/ci` and invoke the main script just as you would through Poetry, with `python release.py <args>`.
- Examples:
  - `python release.py -a api start-release`
  - `python release.py -a api update-release -r release/api/v2.25.0 -c DEADBEEF`
  - `python release.py -a portal update-release -r release/portal/v49.0 --with-branch main`
  - `python release.py -a portal finalize-release -r release/portal/v49.0`
  - `python release.py -a portal hotfix -r release/portal/v49.0 -c DEADBEEF -c ABADCAFE`
  - `python release.py -a admin-portal update-release -r release/admin-portal/v2.0 --with-branch main`
  - `python release.py -a admin-portal finalize-release -r release/admin-portal/v2.0`
  - `python release.py -a admin-portal hotfix -r release/admin-portal/v2.0 -c DEADBEEF -c ABADCAFE`

---

## Operational Instructions

The above section covers _how to start_ the release tasks. For _which task needs to be started_, refer to these guidelines.

Broadly, there are only four "tasks" - four distinct things - that an engineer will typically need to do with a release:
- `start-release`, to increment a significant version number, and kick off a new weekly series of releases with a fresh `-rc1`.
  - (`major-release` is a special case of `start-release` and is not expected to be used regularly.)
- `update-release`, to produce new release candidates on top of an `-rc1` or its successor RCs.
- `finalize-release`, to mark a weekly release candidate as DFML-approved, which permits it to be deployed to PROD.
- `hotfix`, to repair a buggy or incomplete release that's already been deployed to PROD.


### Starting a release
- To start a new series of releases, run the `start-release` task.
  - This task will automatically create the next API or Portal release branch from `main`.
  - It will also tag the HEAD of that new branch (so, HEAD of `main` at time of execution) with the appropriate `-rc1` tag.
  - This task is aware of the existing history, in Git, of all previous release series, 
    so you don't need to specify _which_ release series you're starting.

### Updating a release with a new RC
- To update a release series with new commits and a new RC number, run the `update-release` task.
  - You'll need to provide the name of the release series you're updating in "git branch" form, 
    e.g. `release/api/v1.2.0` or `release/portal/v4.0`.
  - You'll also need to provide either the hashes of some Git commits, or the name of another Git branch.
    If you provide commits, they will be cherry-picked onto the release series with `git cherry-pick`;
    if you provide a branch name, it will be merged into the release series with `git merge`.
- This task will only function for a release series that has **not yet been finalized** through `finalize-release`.
  - **Caution:** Merge conflicts must be resolved manually.
  
### When a release is ready to go to prod
- To mark a release series as ready for production deployment, run the `finalize-release` task.
  - You'll need to provide the name of the release series you're finalizing, as in `update-release.`
  - This task double-tags the most recent RC on that series with a bare semver, e.g. the commit tagged `api/v2.5.0-rc4` also gets tagged `api/v2.5.0`.
- Once you've done this to a given release series, `update-release` **will no longer work** for that series.
- Once you've done this to a given release series, `hotfix` will **start working** for that series.

> #### NB: On Versioning
> A finalized release series _cannot_ gain new RCs, but it _can_ gain new hotfixes.
> 
> A release series that isn't yet finalized _can_ gain new RCs, but it _cannot_ gain hotfixes (until after it's been finalized.)
> 
> This is mostly pedantry. The same Git operations happen either way, and the only real difference is in the Git tags.
> Still, it's _important_ pedantry, so pay attention to the distinction.


### When prod needs to be hotfixed
- To add new production hotfixes to a finalized release series, run the `hotfix` task.
  - This task works identically to `update-release`,
    except that it produces incremented semver tags instead of incremented RC tags.
  - You'll need to provide the name of the release series you're hotfixing in "git branch" form,
      e.g. `release/api/v1.2.0` or `release/portal/v4.0`.
  - You'll also need to provide either the hashes of some Git commits, or the name of another Git branch.
    If you provide commits, they will be cherry-picked onto the release series with `git cherry-pick`;
    if you provide a branch name, it will be merged into the release series with `git merge`.
- This task will only function on a release series that has been finalized through `finalize-release`.
  - **Caution:** Merge conflicts must be resolved manually.

---

## Unit Tests

- To run the tests, use `pytest scripted_releases/tests`. 
- These tests will later be integrated into the API's test suite, but for now they're independent.
