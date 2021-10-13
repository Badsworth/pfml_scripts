# Github Action Workflows

Github Action workflows are defined in [.github/workflows](../../.github/workflows). Github has [helpful tutorials](https://docs.github.com/en/actions/learn-github-actions) for learning syntax and usage.

## Testing workflows

When creating or updating Github Action workflows, it is often difficult to test them due to how workflows are built and triggered. For this reason, it is recommended that every workflow includes an `on: workflow_dispatch` trigger, which will allow anyone with write access to the repository the ability to run the workflow manually in the UI once it's in the main branch.

If you are editing an existing workflow with a `workflow_dispatch` trigger, you can run the workflow at any time using your feature branch in the UI:

- [Github Actions](https://github.com/EOLWD/pfml/actions)
- Select the workflow from the sidebar 
- Select your branch and fill in any inputs
- Select 'Run Workflow'.

If you are creating a new workflow or editing one that does not allow this trigger in the main branch, the easiest way to test the workflow is to add an `on: push` trigger. This will cause the workflow to run on every push to the feature branch. You can then push "dummy" commits to force it to run.

```
git commit --allow-empty
```

If you are testing in this way, please provide testing documentation and results in the body of your pull request for historical purposes, and so reviewers can follow along.
