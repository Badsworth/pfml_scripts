# Contributing

## Delivery Workflow

Please see the [Delivery Workflow](https://lwd.atlassian.net/wiki/spaces/DD/pages/306577409/Delivery+Workflow)
Confluence page for guidance on how to pick up tickets, when to deploy, which environment to deploy to, etc.

## Local Development

For practical instructions on getting set up locally, see the repo [README](../README.md).
Below are guidelines for working once you're ready.

- Commit in your own branch, and include your name in the branch name, e.g. `lorenyu/pfml-123-new-feature`.

- Try to keep commits small and focused on one thing.
If you find yourself using “and” and “also” in your title or description,
that may be a sign to break things up into smaller chunks.
You can selectively `git add` files or use the interactive option: `git add -p`.

- Note that after a PR is merged, your commit message history will be squashed and rewritten.
Your local commit history will persist on the PR's page unless you force-push a squashed version of the branch.

- Informative commit messages can help when context-switching between branches, or for PR clarity in larger PRs.
See _[Seven Rules](https://chris.beams.io/posts/git-commit/#seven-rules)_ for an external reference on commit message best practices.

- To keep your branch updated with others' changes, you can:

    - Rebase your changes onto main with `git rebase main`, or
  
    - Merge main onto your own branch: `git merge main`.
  
    The favored pathway to keep your branch updated is to use `git merge main.`
It's still possible to rebase and force-push your branch using `git rebase main`, but this pathway should be avoided
if your branch is being worked on by more than one person at a time, due to the risk of causing unnecessary conflicts.

## Code Reviews

See [code reviews](./code-reviews)
## Merging a PR

### How to merge

When merging a PR, _use the PR description as a starting point_. Copy it into the merge commit body and clean it up as desired.

**Please verify that the commit title includes the JIRA ticket.**

If the PR only has a single commit, GitHub will default to using that commit
subject and description. This is often incorrect, missing the JIRA ticket.

Example to follow:

    PFML-540: Implement GET claims endpoint (#145)

    https://lwd.atlassian.net/browse/PFML-540

    Implements /claims endpoint which is a GET that takes a valid user ID and returns their first claim from the database.

    Demo: Unit tests and adhoc testing via swagger UI.
    
Example to avoid:

    add claims endpoint (#145)
    
    * formatting
    
    * fix
    
    * change endpoint
    
    * initial endpoint

### When to merge

A PR should only be merged when all its automated checks have returned green
and when the PR has received at least one approval.
Although GitHub does not block the merge of a PR that fails its checks, any failed checks
should be treated as a blocking issue and resolved before the PR is merged.

### Merges & the API database

A particular source of danger when merging a PR is the risk that the merge will introduce conflicts
to the PFML API's database schema. This scenario is not uncommon, especially for branches that
introduce new database migrations and that have not yet been updated with the latest changes to main.
The API's test suite cannot detect these conflicts, so they have historically been discovered
only after PR merge, when deployment of the API begins to fail.

To mitigate this risk, any engineer who introduces new database migrations to the API should pay special attention to the
"Pre-Merge Conflict Check", an automated check that should appear on any pull request that makes changes to `api/massgov/pfml/db/migrations/versions`.
This special 'pseudo-check' will diff your branch against main, and fail if it detects that your branch is missing any
database migrations that are already present on main.

To mitigate the risk that updates to main will, occasionally, introduce new database conflicts to unmerged branches,
this pseudo-check will automatically re-run itself whenever a new database migration is pushed to main,
and additionally whenever new commits are pushed to your PR's feature branch.

For these reasons, please make sure you check the status of any database conflicts before merging an approved PR.
To avoid these conflicts, any PR that alters the database _must_ be updated with the latest changes to main before being merged.
