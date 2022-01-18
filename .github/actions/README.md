## Best Practices for Building Github Actions

When building Github Action workflows, consider similar patterns to normal application code. Individual workflows should be human-readable and concise enough to understand at a glance, and individual workflows or actions should be built to do a single logical piece of work.

To create an independent, reusable module, there are two main ways to do so:

- Composite Actions are a way to join a series of steps into a single reusable module. These live in the `actions` folder.
- Reusable Workflows are a way to join a set of jobs into a single reusable module. These live directly in the `workflows` folder with the `reusable-` prefix. These do not have outputs thaht are accessible by the caller. They also require a specific branch or tag version reference when being called, making it more difficult to make and verify updates on a feature branch.

Both methodologies have similar practical limitations and there is currently no recommendation between the two; reusable workflows are more flexible but require a more specific ref to be used as a reference in workflows, which makes them a more hindering choice for actions with a lot of development activity or manual triggers.

The following are best practices to follow when creating a reusable module:

- All secrets should be passed in explicitly from the calling workflow. This is a Github Actions limitation, but also serves to make it more transparent which sensitive secrets are being used in a workflow without having to traverse multiple nested modules.
- Similarly, all needed environment variables from the caller should be passed in explicitly as inputs.

