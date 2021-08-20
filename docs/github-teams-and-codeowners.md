# Github Teams and Code Owners

## Code Owners

Many parts of the code have owners, defined in the [`CODEOWNERS` file](../.github/CODEOWNERS).

Code owners help to improve the quality of the code by:

- Reviewing changes (see below)
- Encouraging consistency and maintainability
- Refactoring the code as it grows

Normally each module or file has two or more owners that share these tasks.

### Auto-Assignment

Code owners will be automatically assigned for review when the relevant code paths are edited in a pull request.

## Github Teams

We use [GitHub teams](https://help.github.com/en/github/setting-up-and-managing-organizations-and-teams/organizing-members-into-teams) to make it easier to request reviews and specify code owners.

Teams exist for select disciplines:

- API engineers: [`@pfml-api`](https://github.com/orgs/EOLWD/teams/pfml-api)
- Portal engineers: [`@pfml-portal`](https://github.com/orgs/EOLWD/teams/pfml-portal)
- Infra engineers: [`@pfml-infra`](https://github.com/orgs/EOLWD/teams/pfml-infra)
- E2E engineers: [`@pfml-e2e`](https://github.com/orgs/EOLWD/teams/pfml-e2e)

Additionally, certain scrum teams have their own Github team:

- [`@pfml-beacon-hill`](https://github.com/orgs/EOLWD/teams/pfml-beacon-hill)
- [`@pfml-dorchester`](https://github.com/orgs/EOLWD/teams/pfml-dorchester)
- [`@pfml-newbury`](https://github.com/orgs/EOLWD/teams/pfml-newbury)

Some teams are configured so that PR review requests are automatically assigned to a member of the team via a round robin algorithm,
with the goal of equally distributing PR reviews across the team.
