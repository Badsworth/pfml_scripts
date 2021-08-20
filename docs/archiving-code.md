# Process for Archiving Code

When a major feature is deprecated, the code being removed can represent a major engineering effort. It is often useful to be able to reference previously used design patterns and approaches to problems.

## To archive code:

1. Create a branch at the point in time to snapshot: `git checkout -b archive/ctr-payments`
1. Push the branch to github: `git push origin archive/ctr-payments`
1. Update the archive documentation `docs/<api or portal>/archive-reference.md` with:
   - a link to the git branch
   - a description of what the archived feature is
   - a explanation for why it is being archived
1. Create a PR to remove the code from the main branch and link to the archive branch in the PR description.
