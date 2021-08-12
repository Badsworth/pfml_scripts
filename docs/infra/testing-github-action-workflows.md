# Testing Github Action Workflows

When creating or updating Github Action workflows, it is often difficult to test these due to how workflows are built and triggered. For this reason, it is recommended that every workflow includes an `on: workflow_dispatch` trigger, which will allow anyone with write access to the repository the ability to run the workflow manually in the UI.

If you are editing an existing workflow with a `workflow_dispatch` trigger, you can run the workflow at any time using your feature branch in the UI:

- [Github Actions](https://github.com/EOLWD/pfml/actions)
- Select the workflow from the sidebar 
- Select your branch and fill in any inputs
- Select 'Run Workflow'.

If you are creating a new workflow or editing one that does not allow this trigger, the easiest way to test the workflow is to add an `on: push` trigger. This will cause the workflow to run on every push to the feature branch, and you can push "dummy" commits to force it to run.

```
git commit --allow-empty
```
