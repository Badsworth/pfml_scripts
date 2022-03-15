# Code Reviews

Code reviews are intended to help all of us grow as engineers and improve the quality of what we ship.
These guidelines are meant to reinforce those two goals.

## For reviewers

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

## For authors or requesters

### PR titles

Include the JIRA ticket number in the title. For example: `PFML-123: Implement API endpoint`. A single JIRA ticket may be associated with multiple pull requests.

Every change should have an associated JIRA ticket unless it is a documentation change. This makes it easier to search for PRs and generates a link in the Jira ticket to the pull request, which provides the program with an audit trail for verifying the relevant code changes, approvals, and test cases.

  - For tickets that have subtasks, use the parent ticket's id in the title, and include the subtask in the PR description. 

  - If it is a documentation change, please prefix with docs: `docs: Clean up CONTRIBUTING.md`.

### Draft PRs

If your PR is a work-in-progress, or if you are looking for specific feedback on things,
create a [Draft Pull Request](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-requests#draft-pull-requests)
and state what you are looking for in the description.

Your PR should be small enough that a reviewer can reasonably respond within 1-2 business days.
For larger changes, break them down into a series of PRs.
If refactors are included in your changes, try to split them out as recommended below.

As a PR writer, you should consider your description and comments as documentation;
current and future team members will refer to it to understand your design decisions.
Include relevant context and business requirements, and add preemptive comments (in code or PR)
for sections of code that may be confusing or worth debate.

### Requesting reviews from your feature team

Assign the PR to be reviewed by people within your feature team if your changes are within the existing software architecture, uses existing patterns and tools, and you are confident that your changes follows the latest best practices. In this situation, your feature team is most likely to have the most context on the business requirements and whether your changes meets those requirements.

Note that code review culture within each feature team may differ - Some teams are configured so that PR review requests are automatically assigned to a member of the team via a round robin algorithm, with the goal of equally distributing PR reviews across the team.

### Requesting reviews from subject matter experts

If you are making changes that have complexity and may benefit from a pair of eyes with more familiarity with the particular area you are changing, assign the PR to be reviewed by the relevant GitHub team.

Complexity can include:
- Changes in complex and/or critical systems (payments, auth, integrations)
- Changes that have non-functional success criteria that are hard to directly test (accessibility, architecture and security)
- Changes that can potentially impact other features or other teams (infrastructure changes, changes to database schema / data model, tooling)
- Changes in areas of the codebase that have inconsistent practices or are in the midst of a refactor involving introducing new best practices and deprecating legacy practices
- Changes to core areas of the code that aren't changed very often (architecture, tooling)

Reference the following list of teams when considering who you might want to review your PR.

**Component teams**
- [@pfml-payments](https://github.com/orgs/EOLWD/teams/pfml-payments) - Payments processing
- [@pfml-infra](https://github.com/orgs/EOLWD/teams/pfml-infra) - Infrastructure / Terraform
- [@pfml-application-validation](https://github.com/orgs/EOLWD/teams/pfml-application-validation) - Application validation
- [@pfml-database](https://github.com/orgs/EOLWD/teams/pfml-database) - Database
- pfml-portal
  - [@pfml-portal-architecture](https://github.com/orgs/EOLWD/teams/pfml-portal-architecture) - Core portal software architecture like hooks and higher order components
  - [@pfml-portal-auth](https://github.com/orgs/EOLWD/teams/pfml-portal-auth) - Cognito authentication (including MFA)
  - [@pfml-portal-tools](https://github.com/orgs/EOLWD/teams/pfml-portal-tools) - Portal tooling – Jest, test utilities, storybook
- pfml-api
  - [@pfml-api-architecture](https://github.com/orgs/EOLWD/teams/pfml-api-architecture) - Core backend software architecture like authorization
  - [@pfml-api-integrations](https://github.com/orgs/EOLWD/teams/pfml-api-integrations) - Other API integrations (RMV, Experian)
    - [@pfml-fineos-integrations](https://github.com/orgs/EOLWD/teams/pfml-fineos-integrations) - FINEOS API integrations, e-Forms
  - [@pfml-batch-processes](https://github.com/orgs/EOLWD/teams/pfml-batch-processes) - Backend ECS scripts
    - [@pfml-fineos-extracts](https://github.com/orgs/EOLWD/teams/pfml-fineos-extracts) - FINEOS extracts processing

**Practice teams**

- [@pfml-accessibility](https://github.com/orgs/EOLWD/teams/pfml-accessibility) - Accessibility
- [@pfml-observability](https://github.com/orgs/EOLWD/teams/pfml-observability) - Monitoring and Logging
- [@pfml-portal-testing](https://github.com/orgs/EOLWD/teams/pfml-portal-testing) - Portal Testing
- [@pfml-api-testing](https://github.com/orgs/EOLWD/teams/pfml-api-testing) - Backend Testing

For a full list of teams, and to add yourself to any you're interested in, visit the [PFML teams page in GitHub](https://github.com/orgs/EOLWD/teams/pfml/teams)

### Codeowners

The GitHub [`CODEOWNERS` file](../.github/CODEOWNERS) is used to protect sensitive parts of the codebase that have access to secrets stored within GitHub actions. This is a "Separation of Concerns" requirement by the LWD security team to prevent developers from being able to unilaterally make production changes.

### Re-requesting reviews after completing changes

After you make requested changes in response to code review feedback, please re-request reviews from the reviewers to notify them that the work is ready to be reviewed again.

### Labels

Include a [GitHub label](https://github.com/EOLWD/pfml/labels) if relevant.
These labels can be a helpful wayfinding and context building tool, especially for new engineers onboarding into the codebase.

    - The `architecture` label should be used for changes to abstractions or interfaces that usually affect multiple existing files.

    - The `pattern` label should be used for a new structure or interface that will be reused later.

    - The `operations` label should be used for changes to engineering operations, such as dev set-up or deployment.
