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

Code reviews are intended to help all of us grow as engineers and improve the quality of what we ship.
These guidelines are meant to reinforce those two goals.

### For authors or requesters:

- Include the JIRA ticket number in the title. For example: `PFML-123: Implement API endpoint`. A single JIRA ticket may be associated with multiple pull requests.

    Every change should have an associated JIRA ticket unless it is a documentation change. This makes it easier to search for PRs and generates a link in the Jira ticket to the pull request, which provides the program with an audit trail for verifying the relevant code changes, approvals, and test cases.

  - For tickets that have subtasks, use the parent ticket's id in the title, and include the subtask in the PR description. 

  - If it is a documentation change, please prefix with docs: `docs: Clean up CONTRIBUTING.md`.

- Include a [GitHub label](https://github.com/EOLWD/pfml/labels) if relevant.
These labels can be a helpful wayfinding and context building tool, especially for new engineers onboarding into the codebase.

    - The `architecture` label should be used for changes to abstractions or interfaces that usually affect multiple existing files.

    - The `pattern` label should be used for a new structure or interface that will be reused later.

    - The `operations` label should be used for changes to engineering operations, such as dev set-up or deployment.

- If your PR is a work-in-progress, or if you are looking for specific feedback on things,
create a [Draft Pull Request](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-requests#draft-pull-requests)
and state what you are looking for in the description.

Your PR should be small enough that a reviewer can reasonably respond within 1-2 business days.
For larger changes, break them down into a series of PRs.
If refactors are included in your changes, try to split them out as recommended below.

As a PR writer, you should consider your description and comments as documentation;
current and future team members will refer to it to understand your design decisions.
Include relevant context and business requirements, and add preemptive comments (in code or PR)
for sections of code that may be confusing or worth debate.

When you're ready to request a review, consider including folks who are less familiar with that part of the codebase.
This allows others to see what you're working on, along with your development/communication style and ways of working.

You may also reference a specific team for review using the teams defined in [Github Teams and Codeowners](./github-teams-and-codeowners.md).

Once you've received feedback, acknowledge each comment with a response or code change.

### For reviewers:

Aim to respond to code reviews within 1 business day.

Remember to highlight things that you like and appreciate while reading through the changes,
and to make any other feedback clearly actionable by indicating if it is optional preference, an important consideration, or an error.

Don't be afraid to comment with a question, or to ask for clarification, or provide a suggestion,
whenever you don’t understand what is going on at first glance — or if you think an approach or decision can be improved.
Code reviews give us a chance to learn from one another, and to reflect, iterate on, and document why certain decisions are made.

Once you're ready to approve or request changes, err on the side of trust.
Send a vote of approval if the PR looks ready except for small minor changes,
and trust that the recipient will address your comments before merging by replying via comment or code to any asks.
Use "request changes" sparingly, unless there's a blocking issue or major refactors that should be done.

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
