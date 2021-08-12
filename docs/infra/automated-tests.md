# Automated Tests

## Terraform Testing

Currently, we do not use any infrastructure unit or integration testing tools like [terratest](https://terratest.gruntwork.io/) and [kitchen terraform](https://github.com/newcontext-oss/kitchen-terraform) as mentioned in [Terraform: Module Testing Experiments](https://www.terraform.io/docs/language/modules/testing-experiment.html). Additionally, we do not use validation enhancements such as [Open Policy Agent](https://www.openpolicyagent.org/docs/latest/terraform/) (further reference [here](https://blog.styra.com/blog/policy-based-infrastructure-guardrails-with-terraform-and-opa)), [tflint](https://github.com/terraform-linters/tflint), and [tfsec](https://tfsec.dev/).

However, we do run `terraform plan` on affected modules whenever relevant code is updated. This is run using the [Infra CI Validation](https://github.com/EOLWD/pfml/actions/workflows/infra-validate.yml) Github Actions workflow (definition [here](https://github.com/EOLWD/pfml/blob/main/.github/workflows/infra-validate.yml)). This is a static validation for terraform formatting and module correctness, although certain domain-specific errors may occur when changes are actually applied.

For most infrastructure changes, it is recommended that you follow the instructions for deploying your feature branch to the TEST environment in [Deployment](../deployment.md). For monitoring changes, follow the steps in [Making Changes to Alerts](./making-changes-to-alerts.md).

Common failure modes that are not caught by automated testing include:

- Invalid AWS configuration options
- Missing environment variables or parameter store secrets for a given environment

## JS Lambda Tests

Some Portal infrastructure runs within lambda functions. These are associated with small test suites in the [\_\_tests\_\_ directory](../../infra/portal/template/__tests__/) which are run automatically on pull requests by the [Portal Infra CI](../../.github/workflows/portal-infra-ci.yml) workflow.

To run the test suite locally:

```
npm test
```

Update _all_ Jest snapshots, accepting any updates as expected changes:

```
npm run test:update-snapshot
```

Run the project's test suite in watch mode:

```
npm run test:watch
```

> By default, this will attempt to identify which tests to run based on which files have changed in the current repository. After running, you can interact with the prompt to configure or filter which test files are ran.

For more details, see [Portal Test Suite](../docs/portal/tests.md) and [Jest Snapshots](../docs/portal/tests.md#Snapshot%20tests). While the linked documentation is in the context of the Portal application, the same test libraries apply for JS lambda tests.
