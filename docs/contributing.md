# Contributing

## Local Development:

For practical instructions on getting set up locally, see the repo [README](../README.md). Below are guidelines for working once you're ready.

- Commit in your own branch, and include your name in the branch name, e.g. `lorenyu/pfml-123-new-feature`.

- Try to keep commits small and focused on one thing. If you find yourself using “and” and “also” in your title or description, that may be a sign to break things up into smaller chunks. You can selectively `git add` files or use the interactive option: `git add -p`.

- Note that after a PR is merged, your commit message history will be squashed and rewritten, so your local commit history can be for you and you alone.

  However, informative commit messages can help when context-switching between branches, or for PR clarity in larger PRs. See _[Seven Rules](https://chris.beams.io/posts/git-commit/#seven-rules)_ for an external reference on commit message best practices.

- To keep your branch updated with others' changes, you can:
  - Rebase your changes onto master with `git rebase master`, or
  - Merge master onto your own branch: `git merge master`

## Code Reviews

Code reviews are intended to help all of us as a team grow as engineers and improve the quality of our results. These guidelines are meant to reinforce those two goals.

### For requesters:

- Include the JIRA ticket number in the title if it exists. For example: `PFML-123: Implement API endpoint`

- If it’s a work-in-progress or you are looking for specific feedback on things, create a [Draft Pull Request](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-requests#draft-pull-requests) and state what you are looking for in the description.

Your PR should be small enough that a reviewer can reasonably respond within 1 business day. For larger changes, break them down into a series of PRs. If refactors are included in your changes, try to split them out as recommended below.

As a PR writer, you should consider your description and comments as documentation; current and future team members will refer to it to understand your design decisions. Include relevant context and business requirements, and add preemptive comments (in code or PR) for sections of code that may be confusing or worth debate.

When you're ready to request a review, consider including folks who are less familiar with that part of the codebase. This allows others to see what you're working on, along with your development/communication style and ways of working.

Once you've received feedback, acknowledge each comment with a response or code change.

### For reviewers:

Aim to respond to code reviews within 1 business day.

Remember to highlight things that you like and appreciate while reading through the changes, and to make any other feedback clearly actionable by indicating if it is optional preference, an important consideration, or an error.

Don't be afraid to comment with a question, ask for clarification, or provide a suggestion if you don’t understand what is going on at first glance — or if you think an approach or decision can be improved. Code reviews give us a chance to learn from one another, and to reflect, iterate on, and document why certain decisions are made.

Once you're ready to approve or request changes, err on the side of trust. Send a vote of approval if the PR looks ready except for small minor changes, and trust that the recipient will address your comments before merging by replying via comment or code to any asks. Use request changes sparingly unless there's a blocking issue or major refactors that should be done.

### Auto assignment

Code review assignment can be setup to occur automatically when a Pull Request is created, through a combination of the [`CODEOWNERS` file](../.github/CODEOWNERS) and [GitHub teams](https://help.github.com/en/github/setting-up-and-managing-organizations-and-teams/organizing-members-into-teams).

Teams exist for the API and Portal engineers:

- API engineers: [`@pfml-api`](https://github.com/orgs/EOLWD/teams/pfml-api)
- Portal engineers: [`@pfml-portal`](https://github.com/orgs/EOLWD/teams/pfml-portal)

The Portal engineering team [is configured](https://github.com/orgs/EOLWD/teams/pfml-portal/edit/review_assignment) so that PR reviews are automatically assigned to a member of the team via a round robin algorithm, with the goal of equally distributing PR reviews across the team.

## Merge Commit Messages

When merging a PR, use the PR description as a starting point. Copy it into the merge commit body and clean it up as desired.

Example:

    PFML-540: Implement GET claims endpoint (#145)

    https://jira.cms.gov/browse/PFML-540

    Implements /claims endpoint which is a GET that takes a valid user ID and returns their first claim from the database.

    Demo: Unit tests and adhoc testing via swagger UI.
